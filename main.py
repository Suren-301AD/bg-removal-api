from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from rembg import remove
from PIL import Image
import io

app = FastAPI(
    title="Background Removal API",
    description="API for removing backgrounds from images",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {"message": "Background Removal API is running!", "status": "healthy"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/remove-background")
async def remove_background(file: UploadFile = File(...)):
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Validate file size (10MB limit)
    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 10MB)")
    
    try:
        input_bytes = await file.read()
        output_bytes = remove(input_bytes)
        
        return StreamingResponse(
            io.BytesIO(output_bytes), 
            media_type="image/png",
            headers={"Content-Disposition": "attachment; filename=removed_bg.png"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)