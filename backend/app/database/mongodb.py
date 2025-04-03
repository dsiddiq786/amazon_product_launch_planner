from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.database import Database
from pymongo.collection import Collection

from app.config.settings import settings

# MongoDB Client
client = AsyncIOMotorClient(settings.MONGODB_URL)
database = client[settings.MONGODB_DB]


class MongoDBCollections:
    """MongoDB Collections for the application."""
    SCRAPED_DATA = "scraped_data"
    PROMPTS = "prompts"
    LOGS = "logs"
    RECIPES = "recipes"
    ANALYSIS = "analysis"
    MASTER_RECIPES = "master_recipes"
    ANALYSIS_TASKS = "analysis_tasks"


def get_collection(collection_name: str) -> Collection:
    """
    Get a MongoDB collection.
    
    Args:
        collection_name: Name of the collection to retrieve
        
    Returns:
        Collection object for the specified collection
    """
    return database[collection_name]


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