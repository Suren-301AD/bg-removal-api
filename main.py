from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from rembg import remove
import io
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Background Removal API",
    description="API for removing backgrounds from images using AI",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    logger.info("Background Removal API is starting up...")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Background Removal API is running!",
        "status": "healthy",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "healthy", "service": "background-removal-api"}

@app.post("/remove-background")
async def remove_background(file: UploadFile = File(...)):
    """
    Remove background from uploaded image
    
    - **file**: Image file to process (JPG, PNG, etc.)
    
    Returns the processed image with transparent background as PNG
    """
    logger.info(f"Processing file: {file.filename}, content_type: {file.content_type}")
    
    # Validate file type
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=400, 
            detail="File must be an image (JPG, PNG, etc.)"
        )
    
    # Validate file size (10MB limit)
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(
            status_code=413, 
            detail="File too large. Maximum size is 10MB"
        )
    
    if len(content) == 0:
        raise HTTPException(
            status_code=400,
            detail="Empty file uploaded"
        )
    
    try:
        logger.info("Starting background removal process...")
        
        # Process the image with rembg
        output_bytes = remove(content)
        
        logger.info("Background removal completed successfully")
        
        # Return the processed image
        return StreamingResponse(
            io.BytesIO(output_bytes), 
            media_type="image/png",
            headers={
                "Content-Disposition": f"attachment; filename=no_bg_{file.filename or 'image'}.png"
            }
        )
        
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing image: {str(e)}"
        )

@app.get("/docs")
async def get_docs():
    """Redirect to API documentation"""
    return {"message": "Visit /docs for API documentation"}

# This is important for Render deployment
if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment (Render provides this)
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    
    logger.info(f"Starting server on {host}:{port}")
    logger.info(f"Environment PORT: {os.environ.get('PORT', 'Not set')}")
    
    try:
        uvicorn.run(
            app,  # Pass app object directly instead of string
            host=host,
            port=port,
            log_level="info",
            access_log=True
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise