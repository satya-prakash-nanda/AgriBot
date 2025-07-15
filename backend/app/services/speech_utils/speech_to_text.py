import logging
import os
import whisper
import subprocess
from typing import Optional
import tempfile
import uuid

logger = logging.getLogger(__name__)

class SpeechToTextService:
    def __init__(self, model_size: str = "small") -> None:
        try:
            self.setup_ffmpeg()
            self.model = whisper.load_model(model_size)
            logger.info(f"Whisper model '{model_size}' loaded successfully.")
        except Exception as e:
            logger.error(f"Error loading Whisper model: {e}")
            raise RuntimeError("SpeechToTextService initialization failed.") from e

    def setup_ffmpeg(self):
        """Add FFmpeg to PATH if needed and verify it's installed."""
        ffmpeg_dir = r"C:\ffmpeg\bin"  # 🧠 Update this for deployment if needed
        if os.path.exists(ffmpeg_dir):
            os.environ["PATH"] += os.pathsep + ffmpeg_dir

        try:
            result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                logger.info(f"✅ FFmpeg found: {result.stdout.splitlines()[0]}")
            else:
                logger.error(f"FFmpeg stderr: {result.stderr}")
                raise RuntimeError("FFmpeg is installed but not working.")
        except Exception as e:
            logger.error(f"❌ FFmpeg setup error: {e}")
            raise RuntimeError("FFmpeg setup failed.")

    def preprocess_audio(self, input_path: str) -> str:
        """Convert input to 16kHz mono WAV."""
        temp_wav = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4().hex}.wav")
        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-ar", "16000",
            "-ac", "1",
            "-c:a", "pcm_s16le",
            temp_wav,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            logger.error(f"❌ Audio conversion failed: {result.stderr}")
            raise RuntimeError("Audio conversion failed.")
        
        logger.info(f"✅ Audio converted to WAV: {temp_wav}")
        return temp_wav

    def transcribe_audio(self, file_path: str, language: Optional[str] = None) -> str:
        if not os.path.exists(file_path):
            logger.error(f"🚫 File not found: {file_path}")
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        should_convert = ext in [".webm", ".opus", ".m4a", ".aac", ".flac", ".ogg", ".wma", ".mp3"]

        try:
            target_path = self.preprocess_audio(file_path) if should_convert else file_path
            result = self.model.transcribe(target_path, language=language)
            transcription = result.get("text", "").strip()
            logger.info(f"✅ Transcription completed.")
            return transcription
        finally:
            if should_convert and os.path.exists(target_path):
                os.remove(target_path)
