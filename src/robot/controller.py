 #!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Robot Controller for Orange Pi
Handles voice commands, camera input, and UART communication with STM32
"""

import os
import sys
import time
import json
import serial
import threading
import queue
import cv2
import numpy as np
from openai import OpenAI
import sounddevice as sd
import soundfile as sf
import tempfile
import base64
from typing import Optional, Tuple, Dict, Any

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class RobotController:
    def __init__(self, config_path: str = "config.json"):
        """Initialize the robot controller"""
        self.config = self._load_config(config_path)
        self.wake_word = "روبوک"  # Robot name in Persian
        self.command_queue = queue.Queue()
        self.is_listening = False
        self.is_processing = False
        
        # Initialize UART communication
        self.serial_port = serial.Serial(
            port=self.config['uart_port'],
            baudrate=self.config['uart_baudrate'],
            timeout=1
        )
        
        # Initialize camera
        self.camera = cv2.VideoCapture(self.config['camera_index'])
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # Initialize OpenAI client
        self.openai_client = OpenAI(api_key=self.config['openai_api_key'])
        
        # Initialize audio recording
        self.sample_rate = 16000
        self.channels = 1
        self.audio_queue = queue.Queue()
        
        # Initialize command handlers
        self.command_handlers = {
            'move': self._handle_movement,
            'look': self._handle_camera,
            'speak': self._handle_speech,
            'stop': self._handle_stop
        }
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # Default configuration
            config = {
                'uart_port': '/dev/ttyUSB0',
                'uart_baudrate': 115200,
                'camera_index': 0,
                'openai_api_key': os.getenv('OPENAI_API_KEY'),
                'robobook_api_url': 'http://localhost:5000/api/query',
                'wake_word_threshold': 0.8
            }
            # Save default config
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
            return config
    
    def start(self):
        """Start the robot controller"""
        print("Starting Robot Controller...")
        
        # Start listening thread
        self.is_listening = True
        self.listening_thread = threading.Thread(target=self._listen_for_commands)
        self.listening_thread.start()
        
        # Start processing thread
        self.is_processing = True
        self.processing_thread = threading.Thread(target=self._process_commands)
        self.processing_thread.start()
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop the robot controller"""
        print("Stopping Robot Controller...")
        self.is_listening = False
        self.is_processing = False
        
        if hasattr(self, 'listening_thread'):
            self.listening_thread.join()
        if hasattr(self, 'processing_thread'):
            self.processing_thread.join()
        
        self.serial_port.close()
        self.camera.release()
    
    def _listen_for_commands(self):
        """Listen for voice commands"""
        def audio_callback(indata, frames, time, status):
            if status:
                print(f"Audio callback status: {status}")
            self.audio_queue.put(indata.copy())
        
        with sd.InputStream(samplerate=self.sample_rate, channels=self.channels, callback=audio_callback):
            while self.is_listening:
                # Record audio in chunks
                audio_data = []
                for _ in range(50):  # Record for about 3 seconds
                    if not self.is_listening:
                        break
                    audio_data.append(self.audio_queue.get())
                    time.sleep(0.06)  # 60ms per chunk
                
                if not self.is_listening:
                    break
                
                # Convert audio to file
                audio_array = np.concatenate(audio_data)
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                    sf.write(temp_file.name, audio_array, self.sample_rate)
                    
                    # Transcribe audio
                    try:
                        with open(temp_file.name, 'rb') as f:
                            transcript = self.openai_client.audio.transcriptions.create(
                                model="whisper-1",
                                file=f,
                                language="fa"
                            )
                        
                        # Check for wake word
                        if self.wake_word in transcript.text:
                            print(f"Wake word detected! Command: {transcript.text}")
                            self.command_queue.put({
                                'type': 'voice_command',
                                'text': transcript.text
                            })
                    
                    except Exception as e:
                        print(f"Error processing audio: {e}")
                    
                    finally:
                        os.unlink(temp_file.name)
    
    def _process_commands(self):
        """Process commands from the queue"""
        while self.is_processing:
            try:
                command = self.command_queue.get(timeout=1)
                
                if command['type'] == 'voice_command':
                    self._process_voice_command(command['text'])
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error processing command: {e}")
    
    def _process_voice_command(self, text: str):
        """Process voice command and determine appropriate action"""
        try:
            # Check if command is about books
            if any(word in text for word in ['کتاب', 'کتابخانه', 'پیشنهاد', 'معرفی']):
                # Send to RoboBook backend
                response = self._send_to_robobook(text)
                if response:
                    self._handle_speech(response)
            
            # Check for movement commands
            elif any(word in text for word in ['برو', 'حرکت', 'بچرخ', 'توقف']):
                self._handle_movement(text)
            
            # Check for camera commands
            elif any(word in text for word in ['ببین', 'نگاه', 'دوربین']):
                self._handle_camera(text)
            
            else:
                print(f"Unknown command: {text}")
        
        except Exception as e:
            print(f"Error processing voice command: {e}")
    
    def _send_to_robobook(self, query: str) -> Optional[str]:
        """Send query to RoboBook backend"""
        try:
            response = requests.post(
                self.config['robobook_api_url'],
                json={'query': query}
            )
            if response.status_code == 200:
                data = response.json()
                return data.get('response')
            return None
        except Exception as e:
            print(f"Error sending to RoboBook: {e}")
            return None
    
    def _handle_movement(self, command: str):
        """Handle movement commands"""
        try:
            # Parse movement command
            if 'برو جلو' in command:
                self._send_uart_command('MOVE_FORWARD')
            elif 'برو عقب' in command:
                self._send_uart_command('MOVE_BACKWARD')
            elif 'بچرخ راست' in command:
                self._send_uart_command('TURN_RIGHT')
            elif 'بچرخ چپ' in command:
                self._send_uart_command('TURN_LEFT')
            elif 'توقف' in command:
                self._send_uart_command('STOP')
            else:
                print(f"Unknown movement command: {command}")
        except Exception as e:
            print(f"Error handling movement: {e}")
    
    def _handle_camera(self, command: str):
        """Handle camera commands"""
        try:
            # Capture frame
            ret, frame = self.camera.read()
            if not ret:
                print("Failed to capture frame")
                return
            
            # Process frame based on command
            if 'ببین' in command or 'نگاه' in command:
                # Save frame
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                filename = f"capture_{timestamp}.jpg"
                cv2.imwrite(filename, frame)
                print(f"Saved frame to {filename}")
            
            elif 'دنبال' in command:
                # Object detection could be added here
                pass
            
        except Exception as e:
            print(f"Error handling camera: {e}")
    
    def _handle_speech(self, text: str):
        """Handle speech output"""
        try:
            # Generate TTS
            response = self.openai_client.audio.speech.create(
                model="gpt-4o-mini-tts",
                voice="nova",
                input=text,
                response_format="mp3",
                speed=1.0
            )
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                response.stream_to_file(temp_file.name)
                
                # Play audio
                os.system(f"mpg123 {temp_file.name}")
                
                # Clean up
                os.unlink(temp_file.name)
        
        except Exception as e:
            print(f"Error handling speech: {e}")
    
    def _handle_stop(self):
        """Handle stop command"""
        self._send_uart_command('STOP')
    
    def _send_uart_command(self, command: str):
        """Send command to STM32 over UART"""
        try:
            # Format command
            cmd = f"{command}\r\n"
            self.serial_port.write(cmd.encode())
            
            # Wait for acknowledgment
            response = self.serial_port.readline().decode().strip()
            print(f"UART response: {response}")
            
        except Exception as e:
            print(f"Error sending UART command: {e}")

def main():
    """Main function"""
    controller = RobotController()
    try:
        controller.start()
    except KeyboardInterrupt:
        print("\nStopping robot controller...")
    finally:
        controller.stop()

if __name__ == "__main__":
    main()