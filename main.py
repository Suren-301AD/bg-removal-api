from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
from rembg import remove
from PIL import Image
import io
import os

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Background Removal API is running!"}

@app.post("/remove-background")
async def remove_background(file: UploadFile = File(...)):
    input_bytes = await file.read()
    output_bytes = remove(input_bytes)

    return StreamingResponse(io.BytesIO(output_bytes), media_type="image/png")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)