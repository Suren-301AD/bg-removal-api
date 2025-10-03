from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import io
import logging
import os
from PIL import Image

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Background Removal API",
    description="API for removing backgrounds from images using AI",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lazy import for rembg
_rembg_loaded = False
_rembg_remove = None

def get_rembg():
    """Lazy load rembg to avoid startup delays"""
    global _rembg_loaded, _rembg_remove
    if not _rembg_loaded:
        try:
            logger.info("Loading rembg library...")
            from rembg import remove as rembg_remove
            _rembg_remove = rembg_remove
            _rembg_loaded = True
            logger.info("rembg loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load rembg: {e}")
            raise HTTPException(status_code=500, detail="Background removal service unavailable")
    return _rembg_remove

@app.on_event("startup")
async def startup_event():
    logger.info("Background Removal API is starting up...")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Background Removal API is running!",
        "status": "healthy",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
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
    
    # Validate file size (50MB limit)
    content = await file.read()
    if len(content) > 50 * 1024 * 1024:  # 50MB
        raise HTTPException(
            status_code=413, 
            detail="File too large. Maximum size is 50MB"
        )
    
    if len(content) == 0:
        raise HTTPException(
            status_code=400,
            detail="Empty file uploaded"
        )
    
    try:
        logger.info("Starting background removal process...")
        
        # Get rembg function (lazy loaded)
        rembg_remove = get_rembg()
        
        # Validate image with PIL
        try:
            with Image.open(io.BytesIO(content)) as img:
                logger.info(f"Image validated: {img.format}, {img.size}, {img.mode}")
        except Exception as e:
            logger.error(f"Invalid image file: {e}")
            raise HTTPException(
                status_code=400,
                detail="Invalid image file. Please upload a valid image."
            )
        
        # Process the image with rembg - force raw bytes
        output_bytes = rembg_remove(content, force_return_bytes=True)
        
        logger.info("Background removal completed successfully")
        
        # Return the processed image
        return StreamingResponse(
            io.BytesIO(output_bytes), 
            media_type="image/png",
            headers={
                "Content-Disposition": f"attachment; filename=no_bg_{file.filename or 'image'}.png"
            }
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error processing image: {str(e)}"
        )

# Run the app directly
if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0"
    
    logger.info(f"Starting Background Removal API on {host}:{port}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
