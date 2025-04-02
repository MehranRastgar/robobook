import os
from openai import OpenAI

class TranslationService:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = "gpt-4-turbo"  # Using GPT-4 for better translation quality

    def translate_to_farsi(self, text: str, book_title: str = None) -> str:
        """
        Translate the given text to Farsi using OpenAI's API
        
        Args:
            text (str): The text to translate
            book_title (str, optional): The title of the book for context
        """
        try:
            # Create system message with book context if available
            system_message = "You are a professional translator. Translate the following text to Farsi. Maintain the original meaning and tone. Do not include any prompts or instructions in the output. Keep names, places, dates, times, numbers, measurements, and prices in English format."
            
            if book_title:
                system_message += f"\nThis text is from the book '{book_title}'. Please maintain consistency with the book's style and terminology."

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": text}
                ],
                temperature=0.3,  # Lower temperature for more consistent translations
                max_tokens=2000
            )
            
            translated_text = response.choices[0].message.content.strip()
            
            # Clean up any remaining prompts
            prompt_indicators = [
                "لطفا متن را به فارسی ترجمه کنید:",
                "لطفا متن را به فارسی ترجمه کن:",
                "ترجمه به فارسی:",
                "Translation to Farsi:"
            ]
            
            for prompt in prompt_indicators:
                if translated_text.startswith(prompt):
                    translated_text = translated_text[len(prompt):].strip()
            
            return translated_text
            
        except Exception as e:
            print(f"Translation error: {str(e)}")
            raise Exception("Failed to translate text") 