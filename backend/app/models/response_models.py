from pydantic import BaseModel
from typing import Optional

class ChatResponse(BaseModel):
    response: str
    detected_module: str
    language: str
    audio_url: Optional[str] = None
    english_response: Optional[str] = None

