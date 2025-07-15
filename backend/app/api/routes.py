import os
import logging
from typing import Optional
from fastapi import APIRouter, Query, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from io import BytesIO

# Service imports
from app.services.speech_utils.text_to_speech import TextToSpeechService
from app.services.crop_care_service import CropCareRAGService
from app.services.schemes_service import SchemesRAGService
from app.services.language_utils import LanguageService
from app.services.intent_recognizer import IntentRecognizer
from app.services.mandi_service import MandiPriceService
from app.services.weather_service import get_forecast, simplify_forecast_for_farmer
from app.services.speech_utils.speech_to_text import SpeechToTextService

# Import chat router
from app.api.chat_routes import create_chat_router

logger = logging.getLogger(__name__)
UPLOAD_DIR = "./temp"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def create_router() -> APIRouter:
    router = APIRouter()

    # Initialize services
    lang_service = LanguageService()
    intent_service = IntentRecognizer()
    rag_service = SchemesRAGService()
    crop_care_service = CropCareRAGService()
    mandi_service = MandiPriceService()
    stt_service = SpeechToTextService()
    tts_service = TextToSpeechService()

    # ---------------------------- Health Check ----------------------------
    @router.get("/ping")
    async def ping():
        return {"message": "pong"}

    # ---------------------------- Language ----------------------------
    @router.get("/detect-language")
    async def detect_language_route(text: str = Query(...)):
        lang = lang_service.detect_language(text)
        return {"detected_language": lang}

    @router.get("/translate-to-english")
    async def translate_to_english_route(text: str = Query(...)):
        source_lang = lang_service.detect_language(text)
        translated = text if source_lang == "en" else lang_service.translate_text(text, target_lang="en")
        return {"translated_text": translated, "original_language": source_lang}

    @router.get("/translate-from-english")
    async def translate_from_english_route(text: str = Query(...), target_lang: str = Query(...)):
        translated = lang_service.translate_text(text, target_lang)
        return {"translated_text": translated, "target_language": target_lang}

    # ---------------------------- Intent Detection ----------------------------
    @router.get("/detect-intent")
    async def detect_intent_route(query: str = Query(...)):
        intent = intent_service.detect_intent(query)
        return {"intent": intent}

    # ---------------------------- Government Schemes ----------------------------
    @router.get("/get-scheme-info")
    async def get_scheme_info_route(query: str = Query(...)):
        result = rag_service.run_rag_pipeline(query)
        return {"answer": result}

    # ---------------------------- Agriculture Info ----------------------------
    @router.get("/get-agriculture-info")
    async def get_agriculture_info_route(query: str = Query(...)):
        answer = crop_care_service.run_crop_care_pipeline(query)
        return {"answer": answer}


    # ---------------------------- Mandi Prices ----------------------------
    @router.get("/get-mandi-prices")
    async def get_mandi_prices_route(
        city: str = Query(..., description="City name in India"),
        crop: str = Query(..., description="Crop/commodity name")
    ):
        answer = mandi_service.search_prices(city, crop)
        return {"result": answer}

    # ---------------------------- Weather Forecast ----------------------------
    @router.get("/get-weather")
    async def get_weather_route(city: str):
        weather_data, forecast = get_forecast(city)
        if not weather_data:
            return {"error": forecast}
        simplified = simplify_forecast_for_farmer(city, forecast)
        return {"forecast": simplified}

    # ---------------------------- Speech-to-Text ----------------------------
    @router.post("/speech-to-text")
    async def speech_to_text_route(file: UploadFile = File(...), language: Optional[str] = None):
        try:
            file_location = os.path.abspath(os.path.join(UPLOAD_DIR, file.filename))
            with open(file_location, "wb") as buffer:
                buffer.write(await file.read())
            logger.info(f"File saved successfully at: {file_location}")
            transcription = stt_service.transcribe_audio(file_location, language)
            return {"transcription": transcription}
        except Exception as e:
            logger.error(f"Speech-to-text route error: {e}")
            raise HTTPException(status_code=500, detail="Speech-to-text transcription failed.")

    # ---------------------------- Text-to-Speech ----------------------------
    @router.get("/text-to-speech")
    async def text_to_speech_route(text: str = Query(...), slow: Optional[bool] = Query(False)):
        try:
            audio_path = tts_service.synthesize_speech(text, slow)
            with open(audio_path, "rb") as f:
                audio_bytes = f.read()
            return StreamingResponse(BytesIO(audio_bytes), media_type="audio/mpeg")
        except Exception as e:
            logger.error(f"Text-to-speech route error: {e}")
            raise HTTPException(status_code=500, detail="Text-to-speech generation failed.")

    # ---------------------------- Chat Routes ----------------------------
    router.include_router(create_chat_router(), tags=["Chat"])

    return router
