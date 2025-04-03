#!/usr/bin/env python
import os
import sys
import argparse
import subprocess

def run_migrations(action="upgrade", revision="head"):
    """Run Alembic migrations."""
    if action == "create":
        message = input("Enter migration message: ")
        cmd = f"alembic revision --autogenerate -m \"{message}\""
    elif action == "upgrade":
        cmd = f"alembic upgrade {revision}"
    elif action == "downgrade":
        cmd = f"alembic downgrade {revision}"
    elif action == "history":
        cmd = "alembic history"
    elif action == "current":
        cmd = "alembic current"
    else:
        print(f"Unknown action: {action}")
        return

    print(f"Running: {cmd}")
    subprocess.run(cmd, shell=True)

def main():
    """Parse arguments and run migrations."""
    parser = argparse.ArgumentParser(description="Database migration helper")
    parser.add_argument(
        "action", 
        choices=["upgrade", "downgrade", "create", "history", "current"], 
        help="Migration action to perform"
    )
    parser.add_argument(
        "--revision", 
        default="head", 
        help="Revision to migrate to (default: head)"
    )
    
    args = parser.parse_args()
    run_migrations(args.action, args.revision)

if __name__ == "__main__":
    main() 