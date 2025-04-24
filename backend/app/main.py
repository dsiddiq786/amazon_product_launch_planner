from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
import logging
import time
import asyncio
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi

from app.config.settings import settings
from app.database.mongodb import connect_to_mongodb, close_mongodb_connection
from app.routers import auth, users, projects, plans, prompts, products, recipes
from app.services.scheduler import scheduler

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    docs_url=None,  # Disable default docs URL
    redoc_url=None,  # Disable default redoc URL
    openapi_url=None,  # Disable default OpenAPI URL
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add GZip compression middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add request ID middleware
@app.middleware("http")
async def add_request_id_middleware(request, call_next):
    """
    Middleware to add a unique request ID and log request timing
    """
    import uuid
    request_id = str(uuid.uuid4())
    
    # Add request ID to request state
    request.state.request_id = request_id
    
    # Log request start
    start_time = time.time()
    logger.info(f"Request {request_id} started: {request.method} {request.url.path}")
    
    # Process request
    try:
        response = await call_next(request)
        
        # Log request completion
        process_time = (time.time() - start_time) * 1000
        logger.info(f"Request {request_id} completed in {process_time:.2f}ms")
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        return response
    except Exception as e:
        logger.error(f"Request {request_id} failed: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )


# Add rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request, call_next):
    """
    Simple rate limiting middleware based on client IP
    """
    from fastapi import Request, HTTPException
    from collections import defaultdict
    
    # Simple in-memory rate limiting (not suitable for distributed systems)
    # For production, use Redis or similar
    if not hasattr(app, "rate_limit_counter"):
        app.rate_limit_counter = defaultdict(int)
        app.rate_limit_last_reset = defaultdict(float)
    
    client_ip = request.client.host
    
    # Reset counter if period has passed
    current_time = time.time()
    if current_time - app.rate_limit_last_reset.get(client_ip, 0) > settings.RATE_LIMIT_PERIOD_SECONDS:
        app.rate_limit_counter[client_ip] = 0
        app.rate_limit_last_reset[client_ip] = current_time
    
    # Check rate limit
    if app.rate_limit_counter[client_ip] >= settings.RATE_LIMIT_REQUESTS:
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests"},
        )
    
    # Increment counter
    app.rate_limit_counter[client_ip] += 1
    
    # Process request
    response = await call_next(request)
    return response


# Include routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(users.router, prefix=settings.API_V1_STR)
app.include_router(projects.router, prefix=settings.API_V1_STR)
app.include_router(plans.router, prefix=settings.API_V1_STR)
app.include_router(prompts.router, prefix=settings.API_V1_STR)
app.include_router(products.router, prefix=settings.API_V1_STR)
app.include_router(recipes.router, prefix=settings.API_V1_STR)


# Custom OpenAPI and documentation endpoints
@app.get("/api/v1/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """
    Custom Swagger UI endpoint
    """
    return get_swagger_ui_html(
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        title=f"{settings.PROJECT_NAME} - Swagger UI",
        oauth2_redirect_url=None,
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.9.0/swagger-ui.css",
    )


@app.get("/api/v1/redoc", include_in_schema=False)
async def custom_redoc_html():
    """
    Custom ReDoc endpoint
    """
    return get_redoc_html(
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        title=f"{settings.PROJECT_NAME} - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.0.0/bundles/redoc.standalone.js",
    )


@app.get(f"{settings.API_V1_STR}/openapi.json", include_in_schema=False)
async def get_openapi_endpoint():
    """
    Custom OpenAPI endpoint
    """
    return get_openapi(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        routes=app.routes,
    )


# Root endpoint
@app.get("/")
async def root():
    """
    Root endpoint
    """
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "version": settings.VERSION,
        "docs_url": f"{settings.API_V1_STR}/docs",
        "redoc_url": f"{settings.API_V1_STR}/redoc",
    }


# Health check endpoint
@app.get("/api/v1/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "ok",
        "version": settings.VERSION,
    }


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """
    Perform actions when the application starts
    """
    logger.info(f"Starting {settings.PROJECT_NAME} API, version {settings.VERSION}")
    
    # Connect to MongoDB
    await connect_to_mongodb()
    
    # Initialize SQLAlchemy models
    from app.database.postgresql import Base, engine
    Base.metadata.create_all(bind=engine)
    
    # Start the analysis task processor
    logger.info("Starting analysis task processor")
    # Initialize the scheduler and start the task processor
    asyncio.create_task(scheduler.task_processor())
    
    # Additional startup tasks can be added here
    logger.info("Startup completed")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Perform actions when the application shuts down
    """
    logger.info("Shutting down application")
    
    # Close MongoDB connection
    await close_mongodb_connection()
    
    # Additional cleanup tasks can be added here
    logger.info("Shutdown completed") 