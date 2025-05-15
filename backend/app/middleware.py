import logging
import time
from fastapi import Request

logger = logging.getLogger(__name__)

async def log_requests(request: Request, call_next):
    """Middleware to log all incoming requests"""
    start_time = time.time()
    
    logger.info(f"Request: {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(f"Completed in {process_time:.2f}s")
    
    return response
