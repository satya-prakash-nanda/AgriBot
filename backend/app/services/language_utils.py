import logging
import os
from google.cloud import translate_v3 as translate
from google.api_core.exceptions import GoogleAPICallError

logger = logging.getLogger(__name__)


class LanguageService:
    def __init__(self, project_id: str = None, location: str = "global") -> None:
        """
        Initialize the Google Cloud Translation Service.
        Expects the environment variable GOOGLE_APPLICATION_CREDENTIALS to point to the JSON key file.
        """
        try:
            # Read project_id from argument or environment variable
            self.project_id = project_id or os.getenv("GOOGLE_PROJECT_ID")
            if not self.project_id:
                raise ValueError("❌ GOOGLE_PROJECT_ID not set in environment or arguments.")
            
            # Initialize the translation client
            self.client = translate.TranslationServiceClient()
            self.parent = f"projects/{self.project_id}/locations/{location}"

            logger.info("✅ LanguageService initialized with Google Cloud Translate.")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Google Cloud Translate: {e}")
            raise

    def detect_language(self, text: str) -> str:
        """
        Detect the input language using Google Cloud Translate.
        Returns the language code as a lowercase string (e.g., 'en', 'hi').
        """
        try:
            response = self.client.detect_language(
                content=text,
                parent=self.parent
            )
            lang_code = response.languages[0].language_code.lower()
            print(f"🔍 Language detected: {lang_code}")
            return lang_code
        except GoogleAPICallError as e:
            print(f"Language detection error: {e}")
            return "en"

    def translate_text(self, text: str, target_lang: str = "en") -> str:
        """
        Translate text to the target language using Google Cloud Translate.
        """
        try:
            response = self.client.translate_text(
                parent=self.parent,
                contents=[text],
                mime_type="text/plain",
                target_language_code=target_lang,
            )
            translated_text = response.translations[0].translated_text
            print(f"🔤 Translated to {target_lang}: {translated_text}")
            return translated_text
        except GoogleAPICallError as e:
            print(f"Translation error: {e}")
            return text
