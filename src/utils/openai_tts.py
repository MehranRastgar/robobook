import os
import tempfile
import logging
import pygame

logger = logging.getLogger(__name__)

class OpenAITTS:
    def __init__(self, client, model="gpt-4o-mini-tts", voice="nova", speed=2.0):
        self.client = client
        self.model = model
        self.voice = voice
        self.speed = speed

    def is_available(self):
        # This method should be implemented to check if the TTS service is available
        return True

    def speak(self, text: str) -> bool:
        """Convert text to speech using OpenAI TTS with Persian language"""
        if not self.is_available():
            logger.warning("OpenAI TTS is not available")
            return False

        try:
            # Create a temporary file for the audio
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                temp_filename = temp_file.name
            
            # Use the current OpenAI API to generate speech
            response = self.client.audio.speech.create(
                model=self.model,
                voice=self.voice,
                input=text,
                speed=self.speed,
                response_format="mp3"
            )
            
            # Stream the response to the file
            response.stream_to_file(temp_filename)
            
            # Play the audio content
            pygame.mixer.init()
            pygame.mixer.music.load(temp_filename)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            pygame.mixer.quit()

            # Clean up the temporary file
            os.unlink(temp_filename)

            logger.info("Text-to-speech conversion successful with Persian language")
            return True
        except Exception as e:
            logger.error(f"Error in OpenAI TTS: {e}")
            return False
