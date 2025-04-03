#!/usr/bin/env python
"""
Database reset script.
This script drops all tables and recreates them from the SQLAlchemy models.
WARNING: This will delete all data in the database.
"""
import os
import sys
import argparse
from sqlalchemy_utils import database_exists, create_database, drop_database

# Add the parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config.settings import settings
from app.database.postgresql import Base, engine
from app.models.user import User
from app.models.project import Project
from app.models.plan import Plan, Subscription

def reset_database(confirm=False):
    """
    Reset the database by dropping all tables and recreating them.
    """
    if not confirm:
        confirmation = input(
            "WARNING: This will delete all data in the database. "
            "Type 'yes' to confirm: "
        )
        if confirmation.lower() != "yes":
            print("Operation cancelled.")
            return

    print(f"Using database URL: {settings.DATABASE_URL}")
    
    try:
        # Drop the database if it exists
        if database_exists(settings.DATABASE_URL):
            print("Dropping existing database...")
            drop_database(settings.DATABASE_URL)
        
        # Create a new database
        print("Creating new database...")
        create_database(settings.DATABASE_URL)
        
        # Create all tables
        print("Creating tables from SQLAlchemy models...")
        Base.metadata.create_all(bind=engine)
        
        print("Database reset completed successfully!")
    except Exception as e:
        print(f"Error resetting database: {e}")
        sys.exit(1)

def main():
    """Parse arguments and reset the database."""
    parser = argparse.ArgumentParser(description="Reset the database")
    parser.add_argument(
        "--yes", 
        action="store_true", 
        help="Skip confirmation prompt"
    )
    
    args = parser.parse_args()
    reset_database(confirm=args.yes)

if __name__ == "__main__":
    main() 