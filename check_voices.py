import pyttsx3

def main():
    print("Initializing pyttsx3 engine...")
    engine = pyttsx3.init()
    
    print("Getting available voices...")
    voices = engine.getProperty('voices')
    
    print(f"\nFound {len(voices)} voices:")
    for i, voice in enumerate(voices):
        print(f"{i}: {voice.name} ({voice.id})")
        print(f"   Languages: {voice.languages}")
        print(f"   Gender: {voice.gender}")
        print(f"   Age: {voice.age}")
        print()
    
    print("Done checking voices.")

if __name__ == "__main__":
    main() 