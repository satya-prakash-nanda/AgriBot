import os
import uuid
import logging
from gtts import gTTS

logger = logging.getLogger(__name__)

class TextToSpeechService:
    def __init__(self):
        logger.info("✅ TextToSpeechService initialized (gTTS)")

    def synthesize_speech(self, text: str, slow: bool = False) -> str:
        """
        Converts text to speech using gTTS and saves as an MP3 in /static/audio/.

        :param text: The text to convert.
        :param slow: Speak slowly (default: False).
        :return: Public URL to the generated MP3 file (e.g. /static/audio/xyz.mp3).
        """
        try:
            # ✅ Save in static/audio directory
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            audio_dir = os.path.join(base_dir, "static", "audio")
            os.makedirs(audio_dir, exist_ok=True)

            # ✅ Generate unique filename
            filename = f"{uuid.uuid4().hex}.mp3"
            output_path = os.path.join(audio_dir, filename)

            logger.info(f"🔉 Generating speech for: {text[:60]}...")
            tts = gTTS(text=text, lang='hi', slow=slow)  # Use lang='hi' or auto-detect if needed
            tts.save(output_path)
            logger.info(f"✅ TTS audio saved at: {output_path}")

            # ✅ Return public URL path (not absolute path)
            return f"/static/audio/{filename}"

        except Exception as e:
            logger.error(f"❌ TTS generation failed: {e}")
            raise RuntimeError("Text-to-Speech generation failed.") from e
