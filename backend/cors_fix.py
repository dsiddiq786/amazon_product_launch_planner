"""
CORS Fix for FastAPI backend

This script demonstrates how to properly configure CORS for the FastAPI backend.
Copy the relevant parts to your main.py file.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Create FastAPI app
app = FastAPI()

# Add CORS middleware with proper configuration
app.add_middleware(
    CORSMiddleware,
    # Allow all origins for development - restrict in production
    allow_origins=["*"],
    # Allow credentials like cookies
    allow_credentials=True,
    # Allow these HTTP methods
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    # Allow these headers
    allow_headers=["*"],
    # Allow browser to cache preflight requests for this duration in seconds
    max_age=86400,
    # Expose these headers to the browser
    expose_headers=["Content-Type", "X-Pagination", "Authorization"],
)

# Add a middleware to handle OPTIONS requests specifically
@app.middleware("http")
async def handle_options(request, call_next):
    if request.method == "OPTIONS":
        # For OPTIONS preflight requests, return a 200 OK response immediately
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
    response = await call_next(request)
    return response

# Example login endpoint implementation
@app.post("/api/auth/login")
async def login(username: str, password: str):
    # Your login logic here
    return {"token": "example_token", "user": {"email": username}}

# How to run this server:
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 