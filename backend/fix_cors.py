"""
CORS Fix for FastAPI Backend

This standalone script can be used to run your existing FastAPI app with correct CORS settings.
Place this file in your FastAPI project directory and run it instead of your main.py.

=== INSTRUCTIONS FOR USE ===

1. Keep this file in your "new_planner/backend" directory
2. Open a command prompt or terminal
3. Navigate to your backend directory:
   cd path/to/new_planner/backend

4. Run this script instead of your normal FastAPI startup:
   python fix_cors.py

5. The script will:
   - Import your original FastAPI app
   - Add proper CORS middleware to handle preflight requests
   - Run the server with fixed CORS settings

6. After running this script, your Chrome extension should be able to
   connect to the API without CORS errors.

IMPORTANT: Make sure your API is running before trying to log in with the extension.

If you need permanent CORS fixes, update your main FastAPI app with the CORS 
middleware settings from this script.

Usage:
python fix_cors.py

This will wrap your existing FastAPI app with proper CORS middleware.
"""

import sys
import importlib.util
import os
from pathlib import Path

# Try to load the FastAPI app from main.py
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from app.main import app as original_app
    print("Successfully imported original FastAPI app from app.main")
except ImportError as e:
    print(f"Error importing app: {e}")
    print("Make sure to place this file in your FastAPI project directory.")
    sys.exit(1)

# Add CORS middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

# Remove existing CORS middleware if present
original_middlewares = original_app.user_middleware
new_middlewares = []

for middleware in original_middlewares:
    # Keep all middlewares except CORS
    if middleware.cls.__name__ != "CORSMiddleware":
        new_middlewares.append(middleware)
    else:
        print("Removed existing CORSMiddleware")

# Create new app with all the same routes but new middleware setup
app = FastAPI(
    title=original_app.title,
    description=original_app.description,
    version=original_app.version,
    openapi_url=original_app.openapi_url,
    docs_url=original_app.docs_url,
    redoc_url=original_app.redoc_url,
)

# Copy all routes from original app
for route in original_app.routes:
    app.routes.append(route)

# Apply all non-CORS middlewares
for middleware in new_middlewares:
    app.add_middleware(middleware.cls, **middleware.options)

# Apply fixed CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,  # Allow cookies
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
    max_age=86400,  # Cache preflight for 24 hours
    expose_headers=["Content-Type", "X-Pagination", "Authorization"],
)

# Special handler for OPTIONS requests
@app.middleware("http")
async def options_middleware(request: Request, call_next):
    if request.method == "OPTIONS":
        print(f"Handling OPTIONS request to {request.url.path}")
        return JSONResponse(
            content={"detail": "OK"},
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Max-Age": "86400",
            },
        )
    return await call_next(request)

# Copy all event handlers from original app
for event_type, handlers in original_app.router.on_startup:
    for handler in handlers:
        app.router.on_startup.append(handler)

for event_type, handlers in original_app.router.on_shutdown:
    for handler in handlers:
        app.router.on_shutdown.append(handler)

# Add logging for requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"Request: {request.method} {request.url.path}")
    print(f"Headers: {request.headers}")
    response = await call_next(request)
    print(f"Response: {response.status_code}")
    return response

# Run server if executed directly
if __name__ == "__main__":
    import uvicorn
    print("Starting FastAPI server with fixed CORS settings...")
    uvicorn.run(app, host="0.0.0.0", port=8000) 