import io
from PIL import Image
from fastapi import HTTPException

async def process_image(image_data: bytes, target_size: int = 224) -> bytes:
    try:
        image = Image.open(io.BytesIO(image_data))
        
        if image.mode in ('RGBA', 'LA', 'P'):
            image = image.convert('RGB')
        
        width, height = image.size
        print(f"Original size: {width}x{height}")
        
        if width != height:
            size = min(width, height)
            left = (width - size) // 2
            top = (height - size) // 2
            right = left + size
            bottom = top + size
            
            print(f"Cropping to square: {size}x{size} from ({left},{top}) to ({right},{bottom})")
            image = image.crop((left, top, right, bottom))
        
        new_width, new_height = image.size
        if new_width != new_height:
            print(f"Warning: Image is still not square: {new_width}x{new_height}")
            size = min(new_width, new_height)
            image = image.resize((size, size), Image.Resampling.LANCZOS)
        
        print(f"Resizing to target size: {target_size}x{target_size}")
        image = image.resize((target_size, target_size), Image.Resampling.LANCZOS)
        
        final_width, final_height = image.size
        print(f"Final size: {final_width}x{final_height}")
        
        if final_width != target_size or final_height != target_size:
            raise ValueError(f"Final image size is not {target_size}x{target_size}")
        
        output_buffer = io.BytesIO()
        image.save(output_buffer, format="JPEG", quality=85)
        
        return output_buffer.getvalue()
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка обработки изображения: {str(e)}")

async def validate_image_format(file) -> bool:
    try:
        contents = await file.read()
        await file.seek(0)
        Image.open(io.BytesIO(contents))
        return True
        
    except Exception:
        raise HTTPException(status_code=400, detail="Файл не является валидным изображением")

async def validate_image_format_from_bytes(image_data: bytes) -> bool:
    try:
        Image.open(io.BytesIO(image_data))
        return True
    except Exception:
        raise HTTPException(status_code=400, detail="Невалидное изображение")