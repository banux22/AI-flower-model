from pydantic import BaseModel
from typing import Optional, Dict, Any

class PredictionResponse(BaseModel):
    flower_type: str
    confidence: float
    additional_info: Optional[Dict[str, Any]] = None

class UploadResponse(BaseModel):
    success: bool
    message: str
    filename: str
    file_path: str
    prediction: Optional[PredictionResponse] = None