import os
from typing import List, Dict, Optional
import openai
from dotenv import load_dotenv
import json

load_dotenv()

class TextProcessor:
    def __init__(self):
        self.chunk_size = 1000  # characters per chunk
        self.overlap = 100  # overlap between chunks
        openai.api_key = os.getenv("OPENAI_API_KEY")

    def chunk_text(self, text: str) -> List[Dict[str, str]]:
        """Split text into overlapping chunks."""
        try:
            chunks = []
            start = 0
            text_length = len(text)

            while start < text_length:
                end = start + self.chunk_size
                if end > text_length:
                    end = text_length

                chunk = text[start:end]
                chunks.append({
                    "text": chunk,
                    "start": start,
                    "end": end
                })

                start = end - self.overlap

            return chunks
        except Exception as e:
            print(f"Error in chunk_text: {str(e)}")
            raise

    def translate_to_farsi(self, text: str) -> str:
        """Translate text to Farsi using OpenAI API."""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional translator. Translate the following text to Farsi. Maintain the original meaning and tone."},
                    {"role": "user", "content": text}
                ],
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Translation error: {str(e)}")
            return text  # Return original text if translation fails

    def process_book(self, text: str) -> List[Dict[str, str]]:
        """Process book text into chunks and translate to Farsi."""
        try:
            chunks = self.chunk_text(text)
            processed_chunks = []

            for chunk in chunks:
                translated_text = self.translate_to_farsi(chunk["text"])
                processed_chunks.append({
                    "original_text": chunk["text"],
                    "translated_text": translated_text,
                    "start": chunk["start"],
                    "end": chunk["end"]
                })

            return processed_chunks
        except Exception as e:
            print(f"Error in process_book: {str(e)}")
            raise

    def get_page_content(self, chunks: List[Dict[str, str]], page_number: int, items_per_page: int = 1) -> Dict:
        """Get content for a specific page."""
        try:
            # Ensure chunks is a list
            if isinstance(chunks, str):
                chunks = json.loads(chunks)
            elif not isinstance(chunks, list):
                raise ValueError("Chunks must be a list or a JSON string")

            start_idx = (page_number - 1) * items_per_page
            end_idx = start_idx + items_per_page
            
            if start_idx >= len(chunks):
                return {
                    "error": "Page number out of range",
                    "current_page": page_number,
                    "total_pages": (len(chunks) + items_per_page - 1) // items_per_page
                }

            page_chunks = chunks[start_idx:end_idx]
            return {
                "chunks": page_chunks,
                "current_page": page_number,
                "total_pages": (len(chunks) + items_per_page - 1) // items_per_page
            }
        except Exception as e:
            print(f"Error in get_page_content: {str(e)}")
            raise 