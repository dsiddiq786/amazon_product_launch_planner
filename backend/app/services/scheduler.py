import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from app.database.mongodb import get_collection, MongoDBCollections
from app.services.analysis import analyze_product

logger = logging.getLogger(__name__)


class AnalysisTask:
    """Class to represent a product analysis task"""
    def __init__(self, product_id: str, user_id: str, project_id: str, 
                 scheduled_time: datetime, task_id: str):
        self.product_id = product_id
        self.user_id = user_id
        self.project_id = project_id
        self.scheduled_time = scheduled_time
        self.task_id = task_id
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
                           delay_seconds: int = 0) -> str:
        """
        Schedule a new product analysis task
        
        Args:
            product_id: ID of the product to analyze
            user_id: ID of the user who owns the product
            project_id: ID of the project the product belongs to
            delay_seconds: Delay in seconds before executing the task
            
        Returns:
            Task ID
        """
        # Generate a unique task ID using timestamp and product ID
        task_id = f"{int(datetime.utcnow().timestamp())}_{product_id}"
        
        # Calculate scheduled time
        scheduled_time = datetime.utcnow() + timedelta(seconds=delay_seconds)
        
        # Create task object
        task = AnalysisTask(
            product_id=product_id,
            user_id=user_id,
            project_id=project_id,
            scheduled_time=scheduled_time,
            task_id=task_id
        )
        
        # Store task
        self.tasks[task_id] = task
        
        # Add task to queue
        await self.task_queue.put(task)
        
        # Start processor if not running
        if not self.running:
            asyncio.create_task(self.task_processor())
        
        # Return task ID for later reference
        return task_id
    
    async def task_processor(self):
        """
        Background task processor that executes scheduled tasks
        """
        self.running = True
        
        try:
            while True:
                # Get task from queue with timeout
                try:
                    task = await asyncio.wait_for(self.task_queue.get(), timeout=60)
                except asyncio.TimeoutError:
                    # Check if any tasks need to be executed
                    now = datetime.utcnow()
                    pending_tasks = [t for t in self.tasks.values() 
                                    if not t.executed and t.scheduled_time <= now]
                    
                    if not pending_tasks:
                        # If no pending tasks and queue is empty, we can stop the processor
                        if self.task_queue.empty():
                            break
                        continue
                    
                    # Put the first pending task in the queue
                    await self.task_queue.put(pending_tasks[0])
                    continue
                
                # Check if it's time to execute the task
                now = datetime.utcnow()
                if task.scheduled_time > now:
                    # Put the task back in the queue and sleep
                    await self.task_queue.put(task)
                    await asyncio.sleep(1)
                    continue
                
                # Execute the task
                try:
                    logger.info(f"Executing analysis task {task.task_id} for product {task.product_id}")
                    
                    # Execute with timeout
                    result = await asyncio.wait_for(
                        analyze_product(
                            product_id=task.product_id,
                            user_id=task.user_id,
                            project_id=task.project_id
                        ),
                        timeout=self.timeout
                    )
                    
                    task.executed = True
                    if result:
                        task.success = True
                        logger.info(f"Analysis task {task.task_id} completed successfully")
                    else:
                        task.success = False
                        task.error = "Analysis failed with no result"
                        logger.error(f"Analysis task {task.task_id} failed: {task.error}")
                    
                except Exception as e:
                    task.executed = True
                    task.success = False
                    task.error = str(e)
                    logger.error(f"Error executing analysis task {task.task_id}: {str(e)}")
                
                # Save task status to database
                try:
                    await self._update_task_status(task)
                except Exception as e:
                    logger.error(f"Error updating task status: {str(e)}")
                
                # Mark task as done in queue
                self.task_queue.task_done()
        
        except Exception as e:
            logger.error(f"Task processor error: {str(e)}")
        finally:
            self.running = False
    
    async def _update_task_status(self, task: AnalysisTask):
        """Update task status in database"""
        tasks_collection = get_collection(MongoDBCollections.ANALYSIS_TASKS)
        
        await tasks_collection.update_one(
            {"task_id": task.task_id},
            {
                "$set": {
                    "executed": task.executed,
                    "success": task.success,
                    "error": task.error,
                    "completed_at": datetime.utcnow() if task.executed else None
                }
            },
            upsert=True
        )
    
    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a scheduled task
        
        Args:
            task_id: ID of the task
            
        Returns:
            Task status or None if not found
        """
        # Check in-memory tasks first
        if task_id in self.tasks:
            task = self.tasks[task_id]
            return {
                "task_id": task.task_id,
                "product_id": task.product_id,
                "user_id": task.user_id,
                "project_id": task.project_id,
                "scheduled_time": task.scheduled_time,
                "executed": task.executed,
                "success": task.success,
                "error": task.error
            }
        
        # Check database
        tasks_collection = get_collection(MongoDBCollections.ANALYSIS_TASKS)
        task_doc = await tasks_collection.find_one({"task_id": task_id})
        
        return task_doc


# Singleton instance
scheduler = AnalysisScheduler()