from enum import Enum
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.database import Database
from pymongo.collection import Collection

from app.config.settings import settings

# MongoDB Client
client = AsyncIOMotorClient(settings.MONGODB_URL)
database = client[settings.MONGODB_DB]


class MongoDBCollections(str, Enum):
    """MongoDB collection names"""
    PRODUCTS = "products"
    PROMPTS = "prompts"
    ANALYSIS = "analysis"
    LOGS = "logs"
    RECIPES = "recipes"
    MASTER_RECIPES = "master_recipes"
    ANALYSIS_TASKS = "analysis_tasks"


def get_collection(collection: MongoDBCollections) -> Collection:
    """
    Get a MongoDB collection.
    
    Args:
        collection: Name of the collection to retrieve
        
    Returns:
        Collection object for the specified collection
    """
    return database[collection]


async def connect_to_mongodb() -> None:
    """
    Connect to MongoDB and validate the connection.
    This function is called during application startup.
    """
    try:
        # Ping the MongoDB server to verify connection
        await client.admin.command('ping')
        print("✅ Successfully connected to MongoDB")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        raise


async def close_mongodb_connection() -> None:
    """
    Close MongoDB connection.
    This function is called during application shutdown.
    """
    client.close()
    print("MongoDB connection closed") 