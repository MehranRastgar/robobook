import pyttsx3
import time

def test_tts():
    print("Initializing pyttsx3 engine...")
    engine = pyttsx3.init()
    
    # Set properties
    rate = engine.getProperty('rate')
    print(f"Current rate: {rate}")
    engine.setProperty('rate', 150)  # Slower speed
    
    volume = engine.getProperty('volume')
    print(f"Current volume: {volume}")
    engine.setProperty('volume', 1.0)  # Max volume
    
    voices = engine.getProperty('voices')
    print(f"Available voices: {len(voices)}")
    for i, voice in enumerate(voices):
        print(f"Voice {i}: {voice.name}")
    
    # Select the first voice
    engine.setProperty('voice', voices[0].id)
    
    # English text for testing
    print("\nTesting English text...")
    english_text = "Hello, this is a test for text to speech."
    engine.say(english_text)
    engine.runAndWait()
    print("English test completed")
    
    # Persian text for testing
    print("\nTesting Persian text...")
    persian_text = "سلام، این یک آزمایش برای تبدیل متن به گفتار است."
    engine.say(persian_text)
    engine.runAndWait()
    print("Persian test completed")
    
    time.sleep(1)
    
    # Test with the second voice if available
    if len(voices) > 1:
        print("\nTesting with second voice...")
        engine.setProperty('voice', voices[1].id)
        
        print("Testing English text with second voice...")
        engine.say(english_text)
        engine.runAndWait()
        
        print("Testing Persian text with second voice...")
        engine.say(persian_text)
        engine.runAndWait()
        print("Second voice test completed")
    
    print("\nAll tests completed.")

if __name__ == "__main__":
    test_tts() 