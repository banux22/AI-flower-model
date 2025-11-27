import os
import uuid
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import aiofiles
from PIL import Image
import io

from utils.image_processing import process_image, validate_image_format
from utils.validators import validate_file_size
from models import PredictionResponse, UploadResponse

app = FastAPI(title="Flower Recognition API", version="1.0.0")

os.makedirs("uploads", exist_ok=True)
os.makedirs("static", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="static")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload", response_model=UploadResponse)
async def upload_flower_image(
    file: UploadFile = File(..., description="Изображение цветка для распознавания"),
    use_camera: bool = Form(False, description="Флаг использования камеры")
):

    await validate_file_size(file, max_size_mb=10)
    await validate_image_format(file)
    
    file_extension = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
    filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join("uploads", filename)
    
    try:
        contents = await file.read()
        processed_image = await process_image(contents)

        async with aiofiles.open(file_path, "wb") as buffer:
            await buffer.write(processed_image)
        
        #здесь будет вызов модели
        #prediction = await predict_flower(processed_image)
        
        return UploadResponse(
            success=True,
            message="Изображение успешно загружено и обработано",
            filename=filename,
            file_path=f"/uploads/{filename}",
            # prediction=prediction  #раскомментировать когда будет готова модель
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обработки изображения: {str(e)}")

@app.post("/capture", response_model=UploadResponse)
async def capture_flower_image(
    image_data: str = Form(..., description="Base64 encoded image data from camera")
):
    try:
        if "," in image_data:
            image_data = image_data.split(",")[1]
        
        import base64
        image_bytes = base64.b64decode(image_data)
        await validate_image_format_from_bytes(image_bytes)
        processed_image = await process_image(image_bytes)
        filename = f"{uuid.uuid4()}.jpg"
        file_path = os.path.join("uploads", filename)
        
        async with aiofiles.open(file_path, "wb") as buffer:
            await buffer.write(processed_image)
        
        return UploadResponse(
            success=True,
            message="Фото с камеры успешно обработано",
            filename=filename,
            file_path=f"/uploads/{filename}",
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка обработки фото с камеры: {str(e)}")

@app.get("/uploads/{filename}")
async def get_uploaded_file(filename: str):
    file_path = os.path.join("uploads", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Файл не найден")
    
    async with aiofiles.open(file_path, "rb") as file:
        content = await file.read()
    
    return Response(content=content, media_type="image/jpeg")

#заглушка для модели, потом заменить на реализацию
async def predict_flower(image_data: bytes) -> PredictionResponse:
    #from your_ai_model import predict
    #result = predict(image_data)
    
    return PredictionResponse(
        flower_type="Роза",
        confidence=0.95,
        additional_info={
            "latin_name": "Rosa",
            "family": "Rosaceae",
            "blooming_season": "Лето"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
