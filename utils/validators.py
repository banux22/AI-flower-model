from fastapi import HTTPException

async def validate_file_size(file, max_size_mb: int = 10):
    max_size_bytes = max_size_mb * 1024 * 1024
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > max_size_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"Файл слишком большой. Максимальный размер: {max_size_mb}MB"
        )
    
    return True