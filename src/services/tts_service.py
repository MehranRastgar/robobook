import os
from typing import Optional
import openai
from dotenv import load_dotenv

load_dotenv()

class TTSService:
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.voice = "nova"  # Default voice
        self.model = "gpt-4o-mini-tts"  # Default model

    def text_to_speech(self, text: str, voice: Optional[str] = None) -> bytes:
        """Convert text to speech using OpenAI's TTS API."""
        try:
            response = openai.audio.speech.create(
                model=self.model,
                voice=voice or self.voice,
                input=text
            )
            return response.content
        except Exception as e:
            print(f"TTS error: {str(e)}")
            raise

    def save_audio(self, audio_data: bytes, filename: str) -> str:
        """Save audio data to a file."""
        try:
            with open(filename, 'wb') as f:
                f.write(audio_data)
            return filename
        except Exception as e:
            print(f"Error saving audio: {str(e)}")
            raise 