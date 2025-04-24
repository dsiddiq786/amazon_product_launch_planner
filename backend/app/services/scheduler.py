"""Dawood's Code"""
# scheduler.py (refactored with category queue + master recipe control + existing compatibility)

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set

from app.database.mongodb import get_collection, MongoDBCollections
from app.services.analysis import analyze_product, check_and_generate_master_recipes, perform_market_research_analysis
from app.services.competitor_analysis import process_product_analysis

logger = logging.getLogger(__name__)

# In-memory tracking
category_task_queues: Dict[str, Set[str]] = {}     # category_key -> set of product_ids
category_task_locks: Dict[str, asyncio.Lock] = {}  # category_key -> asyncio.Lock


class AnalysisTask:
    """Class to represent a product analysis task"""
    def __init__(self, product_id: str, user_id: str, project_id: str, 
                 scheduled_time: datetime, task_id: str, task_type: str = "standard_analysis",
                 prompt_block_id: str = None):
        self.product_id = product_id
        self.user_id = user_id
        self.project_id = project_id
        self.scheduled_time = scheduled_time
        self.task_id = task_id
        self.task_type = task_type  # "standard_analysis", "competitor_analysis", or "market_research"
        self.prompt_block_id = prompt_block_id  # Only needed for market_research
        self.executed = False
        self.success = False
        self.error = None


class AnalysisScheduler:
    """
    Scheduler for managing product analysis tasks
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AnalysisScheduler, cls).__new__(cls)
            cls._instance.tasks = {}
            cls._instance.running = False
            cls._instance.task_queue = asyncio.Queue()
            cls._instance.timeout = 300  # Task execution timeout in seconds
        return cls._instance

    async def schedule_task(self, product_id: str, user_id: str, project_id: str, 
                           delay_seconds: int = 0, task_type: str = "standard_analysis",
                           prompt_block_id: str = None) -> str:
        """
        Schedule a new product analysis task
        """
        task_id = f"{int(datetime.utcnow().timestamp())}_{product_id}"
        scheduled_time = datetime.utcnow() + timedelta(seconds=delay_seconds)
        task = AnalysisTask(
            product_id=product_id,
            user_id=user_id,
            project_id=project_id,
            scheduled_time=scheduled_time,
            task_id=task_id,
            task_type=task_type,
            prompt_block_id=prompt_block_id
        )

        self.tasks[task_id] = task
        await self.task_queue.put(task)

        # Add to category queue tracking
        await self._track_product_category(product_id)

        # Start processor if not running
        if not self.running:
            asyncio.create_task(self.task_processor())

        return task_id

    async def schedule_competitor_analysis(self, product_id: str, user_id: str, project_id: str,
                                         delay_seconds: int = 0) -> str:
        """
        Schedule a new competitor analysis task
        """
        return await self.schedule_task(
            product_id=product_id,
            user_id=user_id,
            project_id=project_id,
            delay_seconds=delay_seconds,
            task_type="competitor_analysis"
        )

    async def _track_product_category(self, product_id: str):
        """Extract category key and add product_id to in-memory queue"""
        products = get_collection(MongoDBCollections.PRODUCTS)
        product = await products.find_one({"id": product_id})
        if not product:
            return

        hierarchy = product.get("category_hierarchy", {})
        main = hierarchy.get("main_category")
        sub = hierarchy.get("sub_categories", [])[-1] if hierarchy.get("sub_categories") else None
        if not main or not sub:
            return

        key = f"{main}>{sub}"
        if key not in category_task_queues:
            category_task_queues[key] = set()
        if key not in category_task_locks:
            category_task_locks[key] = asyncio.Lock()

        category_task_queues[key].add(product_id)

    async def task_processor(self):
        """
        Background task processor that executes scheduled tasks
        """
        self.running = True

        try:
            while True:
                try:
                    task = await asyncio.wait_for(self.task_queue.get(), timeout=60)
                except asyncio.TimeoutError:
                    if self.task_queue.empty():
                        self.running = False
                        break
                    continue

                now = datetime.utcnow()
                if task.scheduled_time > now:
                    await self.task_queue.put(task)
                    await asyncio.sleep(1)
                    continue

                try:
                    logger.info(f"Executing {task.task_type} task {task.task_id} for product {task.product_id}")

                    # Execute the appropriate analysis task
                    if task.task_type == "competitor_analysis":
                        result = await asyncio.wait_for(
                            process_product_analysis(
                                product_id=task.product_id,
                                user_id=task.user_id,
                                project_id=task.project_id
                            ),
                            timeout=self.timeout
                        )
                    elif task.task_type == "market_research":
                        # For market research, we need the prompt block ID as well
                        prompt_block_id = getattr(task, "prompt_block_id", None)
                        if not prompt_block_id:
                            # If prompt_block_id wasn't included in the task, try to retrieve it
                            prompts_collection = get_collection(MongoDBCollections.PROMPTS)
                            cursor = prompts_collection.find({
                                "prompt_category": "market_research",
                                "is_active": True
                            }).sort("created_at", -1).limit(1)
                            
                            market_research_prompt = await cursor.to_list(length=1)
                            if market_research_prompt:
                                prompt_block_id = market_research_prompt[0]["id"]
                            else:
                                raise ValueError("No active market research prompt found")
                        
                        result = await asyncio.wait_for(
                            perform_market_research_analysis(
                                product_id=task.product_id,
                                user_id=task.user_id,
                                prompt_block_id=prompt_block_id
                            ),
                            timeout=self.timeout
                        )
                    else:
                        # Default to standard analysis
                        result = await asyncio.wait_for(
                            analyze_product(
                                product_id=task.product_id,
                                user_id=task.user_id
                            ),
                            timeout=self.timeout
                        )

                    task.executed = True
                    if result and not (isinstance(result, dict) and "error" in result):
                        task.success = True
                        logger.info(f"{task.task_type} task {task.task_id} completed successfully")
                    else:
                        task.success = False
                        task.error = result.get("error", "Analysis failed with no result") if isinstance(result, dict) else "Analysis failed"
                        logger.error(f"{task.task_type} task {task.task_id} failed: {task.error}")

                except Exception as e:
                    task.executed = True
                    task.success = False
                    task.error = str(e)
                    logger.error(f"Error executing {task.task_type} task {task.task_id}: {str(e)}")

                try:
                    await self._update_task_status(task)
                except Exception as e:
                    logger.error(f"Error updating task status: {str(e)}")

                self.task_queue.task_done()

                # Cleanup queue + maybe trigger master recipe
                await self._cleanup_category_queue(task.product_id)

        except Exception as e:
            logger.error(f"Task processor error: {str(e)}")
        finally:
            self.running = False

    async def _cleanup_category_queue(self, product_id: str):
        """Remove product from category queue and check if queue is empty to trigger master recipe"""
        products = get_collection(MongoDBCollections.PRODUCTS)
        product = await products.find_one({"id": product_id})
        if not product:
            return

        hierarchy = product.get("category_hierarchy", {})
        main = hierarchy.get("main_category")
        sub = hierarchy.get("sub_categories", [])[-1] if hierarchy.get("sub_categories") else None
        if not main or not sub:
            return

        key = f"{main}>{sub}"
        async with category_task_locks[key]:
            category_task_queues[key].discard(product_id)

            if not category_task_queues[key]:
                logger.info(f"[Scheduler] Queue empty for {key}, triggering master recipe...")
                await check_and_generate_master_recipes(main, sub, product["user_id"])

    async def _update_task_status(self, task: AnalysisTask):
        """Update task status in database"""
        tasks_collection = get_collection(MongoDBCollections.ANALYSIS_TASKS)

        task_data = {
            "executed": task.executed,
            "success": task.success,
            "error": task.error,
            "task_type": task.task_type,
            "product_id": task.product_id,
            "user_id": task.user_id,
            "project_id": task.project_id,
            "scheduled_time": task.scheduled_time,
            "completed_at": datetime.utcnow() if task.executed else None
        }
        
        # Only include prompt_block_id if it exists
        if task.prompt_block_id:
            task_data["prompt_block_id"] = task.prompt_block_id

        await tasks_collection.update_one(
            {"task_id": task.task_id},
            {"$set": task_data},
            upsert=True
        )

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a scheduled task
        """
        if task_id in self.tasks:
            task = self.tasks[task_id]
            status_data = {
                "task_id": task.task_id,
                "product_id": task.product_id,
                "user_id": task.user_id,
                "project_id": task.project_id,
                "task_type": task.task_type,
                "scheduled_time": task.scheduled_time,
                "executed": task.executed,
                "success": task.success,
                "error": task.error
            }
            
            # Only include prompt_block_id if it exists
            if task.prompt_block_id:
                status_data["prompt_block_id"] = task.prompt_block_id
            
            return status_data

        tasks_collection = get_collection(MongoDBCollections.ANALYSIS_TASKS)
        return await tasks_collection.find_one({"task_id": task_id})


# Singleton instance
scheduler = AnalysisScheduler()


"""CURSOR CODE"""
# import asyncio
# import logging
# from datetime import datetime, timedelta
# from typing import Dict, Any, List, Optional

# from app.database.mongodb import get_collection, MongoDBCollections
# from app.services.analysis import analyze_product
# from app.services.competitor_analysis import process_product_analysis

# logger = logging.getLogger(__name__)


# class AnalysisTask:
#     """Class to represent a product analysis task"""
#     def __init__(self, product_id: str, user_id: str, project_id: str, 
#                  scheduled_time: datetime, task_id: str, task_type: str = "standard_analysis"):
#         self.product_id = product_id
#         self.user_id = user_id
#         self.project_id = project_id
#         self.scheduled_time = scheduled_time
#         self.task_id = task_id
#         self.task_type = task_type  # "standard_analysis" or "competitor_analysis"
#         self.executed = False
#         self.success = False
#         self.error = None


# class AnalysisScheduler:
#     """
#     Scheduler for managing product analysis tasks
#     """
#     _instance = None
    
#     def __new__(cls):
#         if cls._instance is None:
#             cls._instance = super(AnalysisScheduler, cls).__new__(cls)
#             cls._instance.tasks = {}
#             cls._instance.running = False
#             cls._instance.task_queue = asyncio.Queue()
#             cls._instance.timeout = 300  # Task execution timeout in seconds
#         return cls._instance
    
#     async def schedule_task(self, product_id: str, user_id: str, project_id: str, 
#                            delay_seconds: int = 0, task_type: str = "standard_analysis") -> str:
#         """
#         Schedule a new product analysis task
        
#         Args:
#             product_id: ID of the product to analyze
#             user_id: ID of the user who owns the product
#             project_id: ID of the project the product belongs to
#             delay_seconds: Delay in seconds before executing the task
#             task_type: Type of analysis to perform ("standard_analysis" or "competitor_analysis")
            
#         Returns:
#             Task ID
#         """
#         # Generate a unique task ID using timestamp and product ID
#         task_id = f"{int(datetime.utcnow().timestamp())}_{product_id}"
        
#         # Calculate scheduled time
#         scheduled_time = datetime.utcnow() + timedelta(seconds=delay_seconds)
        
#         # Create task object
#         task = AnalysisTask(
#             product_id=product_id,
#             user_id=user_id,
#             project_id=project_id,
#             scheduled_time=scheduled_time,
#             task_id=task_id,
#             task_type=task_type
#         )
        
#         # Store task
#         self.tasks[task_id] = task
        
#         # Add task to queue
#         await self.task_queue.put(task)
        
#         # Start processor if not running
#         if not self.running:
#             asyncio.create_task(self.task_processor())
        
#         # Return task ID for later reference
#         return task_id
    
#     async def schedule_competitor_analysis(self, product_id: str, user_id: str, project_id: str,
#                                          delay_seconds: int = 0) -> str:
#         """
#         Schedule a new competitor analysis task
        
#         Args:
#             product_id: ID of the product to analyze
#             user_id: ID of the user who owns the product
#             project_id: ID of the project the product belongs to
#             delay_seconds: Delay in seconds before executing the task
            
#         Returns:
#             Task ID
#         """
#         return await self.schedule_task(
#             product_id=product_id,
#             user_id=user_id,
#             project_id=project_id,
#             delay_seconds=delay_seconds,
#             task_type="competitor_analysis"
#         )
    
#     async def task_processor(self):
#         """
#         Background task processor that executes scheduled tasks
#         """
#         self.running = True
        
#         try:
#             while True:
#                 # Get task from queue with timeout
#                 try:
#                     task = await asyncio.wait_for(self.task_queue.get(), timeout=60)
#                 except asyncio.TimeoutError:
#                     # Check if any tasks need to be executed
#                     now = datetime.utcnow()
#                     pending_tasks = [t for t in self.tasks.values() 
#                                     if not t.executed and t.scheduled_time <= now]
                    
#                     if not pending_tasks:
#                         # If no pending tasks and queue is empty, we can stop the processor
#                         if self.task_queue.empty():
#                             break
#                         continue
                    
#                     # Put the first pending task in the queue
#                     await self.task_queue.put(pending_tasks[0])
#                     continue
                
#                 # Check if it's time to execute the task
#                 now = datetime.utcnow()
#                 if task.scheduled_time > now:
#                     # Put the task back in the queue and sleep
#                     await self.task_queue.put(task)
#                     await asyncio.sleep(1)
#                     continue
                
#                 # Execute the task
#                 try:
#                     logger.info(f"Executing {task.task_type} task {task.task_id} for product {task.product_id}")
                    
#                     # Execute with timeout based on task type
#                     if task.task_type == "competitor_analysis":
#                         result = await asyncio.wait_for(
#                             process_product_analysis(
#                                 product_id=task.product_id,
#                                 user_id=task.user_id,
#                                 project_id=task.project_id
#                             ),
#                             timeout=self.timeout
#                         )
#                     else:  # standard_analysis
#                         result = await asyncio.wait_for(
#                             analyze_product(
#                                 product_id=task.product_id,
#                                 user_id=task.user_id
#                             ),
#                             timeout=self.timeout
#                         )
                    
#                     task.executed = True
#                     if result and not (isinstance(result, dict) and "error" in result):
#                         task.success = True
#                         logger.info(f"{task.task_type} task {task.task_id} completed successfully")
#                     else:
#                         task.success = False
#                         task.error = result.get("error", "Analysis failed with no result") if isinstance(result, dict) else "Analysis failed with no result"
#                         logger.error(f"{task.task_type} task {task.task_id} failed: {task.error}")
                    
#                 except Exception as e:
#                     task.executed = True
#                     task.success = False
#                     task.error = str(e)
#                     logger.error(f"Error executing {task.task_type} task {task.task_id}: {str(e)}")
                
#                 # Save task status to database
#                 try:
#                     await self._update_task_status(task)
#                 except Exception as e:
#                     logger.error(f"Error updating task status: {str(e)}")
                
#                 # Mark task as done in queue
#                 self.task_queue.task_done()
        
#         except Exception as e:
#             logger.error(f"Task processor error: {str(e)}")
#         finally:
#             self.running = False
    
#     async def _update_task_status(self, task: AnalysisTask):
#         """Update task status in database"""
#         tasks_collection = get_collection(MongoDBCollections.ANALYSIS_TASKS)
        
#         await tasks_collection.update_one(
#             {"task_id": task.task_id},
#             {
#                 "$set": {
#                     "executed": task.executed,
#                     "success": task.success,
#                     "error": task.error,
#                     "task_type": task.task_type,
#                     "product_id": task.product_id,
#                     "user_id": task.user_id,
#                     "project_id": task.project_id,
#                     "scheduled_time": task.scheduled_time,
#                     "completed_at": datetime.utcnow() if task.executed else None
#                 }
#             },
#             upsert=True
#         )
    
#     async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
#         """
#         Get the status of a scheduled task
        
#         Args:
#             task_id: ID of the task
            
#         Returns:
#             Task status or None if not found
#         """
#         # Check in-memory tasks first
#         if task_id in self.tasks:
#             task = self.tasks[task_id]
#             return {
#                 "task_id": task.task_id,
#                 "product_id": task.product_id,
#                 "user_id": task.user_id,
#                 "project_id": task.project_id,
#                 "task_type": task.task_type,
#                 "scheduled_time": task.scheduled_time,
#                 "executed": task.executed,
#                 "success": task.success,
#                 "error": task.error
#             }
        
#         # Check database
#         tasks_collection = get_collection(MongoDBCollections.ANALYSIS_TASKS)
#         task_doc = await tasks_collection.find_one({"task_id": task_id})
        
#         return task_doc


# # Singleton instance
# scheduler = AnalysisScheduler()