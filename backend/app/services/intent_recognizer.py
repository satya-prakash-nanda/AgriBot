# backend/app/services/intent_recognizer.py

import os
import logging
from langchain_groq import ChatGroq

logger = logging.getLogger(__name__)


class IntentRecognizer:
    def __init__(self) -> None:
        """
        Initializes the Groq LLM for intent detection.
        """
        try:
            self.llm = ChatGroq(
                api_key=os.getenv("GROQ_API_KEY"),
                model_name="llama3-8b-8192"
            )
            logger.info("✅ Groq LLM initialized for intent recognition.")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Groq LLM: {e}")
            raise

    def detect_intent(self, user_query: str) -> str:
        """
        Detects the intent from a user query.
        Possible intents are:
            - weather: For any weather, rainfall, temperature, climate, or forecast queries.
            - mandi_prices: For questions about crop prices, market rates, or commodity prices.
            - schemes: For government schemes, subsidies, farmer support, or benefits.
            - agriculture_info: For crop care, farming techniques, aquaculture, pest control, machinery, or general agricultural advice.

        Returns the intent name as a lowercase string, or 'unknown' if unclear.
        """

        prompt = (
            "You are an AI assistant classifying user queries for an Indian agricultural chatbot.\n"
            "You must identify the **single best intent** from the following options:\n"
            "- weather: weather forecasts, temperature, rainfall, climate updates.\n"
            "- mandi_prices: crop prices, market rates, mandi rates.\n"
            "- schemes: government schemes, subsidies, financial benefits.\n"
            "- agriculture_info: crop care, farming advice, aquaculture, pest control, agricultural machinery, and farming techniques.\n\n"
            "Reply with only the intent word: 'weather', 'mandi_prices', 'schemes', or 'agriculture_info'. No explanation.\n\n"
            f"User Query: \"{user_query}\"\n"
            "Intent:"
        )

        try:
            response = self.llm.invoke(prompt)
            intent = getattr(response, 'content', str(response)).strip().lower()
            logger.info(f"🔍 Groq detected intent: {intent}")

            valid_intents = ["weather", "mandi_prices", "schemes", "agriculture_info"]
            if intent not in valid_intents:
                logger.warning(f"⚠️ Invalid intent detected: {intent}, returning 'unknown'")
                return "unknown"

            return intent

        except Exception as e:
            logger.error(f"❌ Groq API error during intent detection: {e}")
            return "unknown"
