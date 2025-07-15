import os
import logging
import uuid
from fastapi import APIRouter, HTTPException
from app.models.request_models import ChatRequest
from app.models.response_models import ChatResponse
from app.services.language_utils import LanguageService
from app.services.intent_recognizer import IntentRecognizer
from app.services.weather_service import get_forecast, simplify_forecast_for_farmer
from app.services.mandi_service import MandiPriceService
from app.services.schemes_service import SchemesRAGService
from app.services.crop_care_service import CropCareRAGService
from app.services.location_crop_extractor import EntityExtractor
from app.services.speech_utils.text_to_speech import TextToSpeechService

logger = logging.getLogger(__name__)

def create_chat_router() -> APIRouter:
    router = APIRouter()

    # Initialize services
    lang_service = LanguageService()
    intent_service = IntentRecognizer()
    mandi_service = MandiPriceService()
    scheme_service = SchemesRAGService()
    cropcare_service = CropCareRAGService()
    entity_extractor = EntityExtractor()
    tts_service = TextToSpeechService()

    @router.post("/chat", response_model=ChatResponse)
    async def chat_endpoint(chat_request: ChatRequest):
        try:
            query_text = chat_request.query.strip()
            if not query_text:
                raise HTTPException(status_code=400, detail="Query cannot be empty")

            # 1. Detect user language
            detected_lang = lang_service.detect_language(query_text)
            logger.info(f"🌐 Detected language: {detected_lang}")

            # 2. Translate to English if needed
            translated_query = (
                lang_service.translate_text(query_text, target_lang="en")
                if detected_lang != "en"
                else query_text
            )
            logger.info(f"📝 Translated query: {translated_query}")

            # 3. Detect user intent
            intent = intent_service.detect_intent(translated_query)
            logger.info(f"🎯 Detected intent: {intent}")

            # 4. Route to appropriate module
            if intent == "weather":
                city = entity_extractor.extract_weather_city(translated_query)
                weather_data, forecast = get_forecast(city)
                response_text = (
                    simplify_forecast_for_farmer(city, forecast)
                    if weather_data
                    else forecast
                )

            elif intent == "mandi_prices":
                entities = entity_extractor.extract_mandi_entities(translated_query)
                crop = entities.get("crop", "")
                location = entities.get("location", "")
                response_text = mandi_service.search_prices(location, crop)

            elif intent == "schemes":
                response_text = scheme_service.run_rag_pipeline(translated_query)

            elif intent == "agriculture_info":
                response_text = cropcare_service.run_crop_care_pipeline(translated_query)

            else:
                response_text = "Sorry, I couldn't understand your request."

            # 5. Translate response back to original language (if not English)
            final_response_text = (
                lang_service.translate_text(response_text, target_lang=detected_lang)
                if detected_lang != "en"
                else response_text
            )

            # 6. Generate TTS audio
            audio_path = tts_service.synthesize_speech(final_response_text, slow=False)
            audio_filename = os.path.basename(audio_path)
            audio_url = f"http://localhost:8000/static/audio/{audio_filename}"

            return ChatResponse(
                response=final_response_text,
                detected_module=intent,
                language=detected_lang,
                audio_url=audio_url,
                english_response=response_text
            )

        except Exception as e:
            logger.error(f"Error in /chat route: {e}")
            raise HTTPException(status_code=500, detail="Internal Server Error")

    return router
