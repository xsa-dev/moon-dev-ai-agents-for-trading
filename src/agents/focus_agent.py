"""
🌙 Moon Dev's Focus Agent
Built with love by Moon Dev 🚀

This agent randomly monitors speech samples and provides focus assessments.
"""
# System prompt for focus analysis
FOCUS_PROMPT = """
You are Moon Dev's Focus AI Agent. Analyze the following transcript and:
1. Rate focus level from 1-10 (10 being completely focused on coding)
2. Provide ONE encouraging sentence to maintain/improve focus or a great quote to inspire to focus

Consider:
- Coding discussion = high focus
- Trading analysis = high focus
- Random chat/topics = low focus
- Non-work discussion = low focus

RESPOND IN THIS EXACT FORMAT:
X/10
"Quote OR motivational sentence"
"""


import os
import time as time_lib
from datetime import datetime, timedelta, time
from google.cloud import speech_v1p1beta1 as speech
import pyaudio
import openai
from termcolor import cprint
from pathlib import Path
from dotenv import load_dotenv
from random import randint, uniform
import threading

# Configuration
MIN_INTERVAL_MINUTES = 3
MAX_INTERVAL_MINUTES = 8
RECORDING_DURATION = 30  # 1 minute recording
FOCUS_THRESHOLD = 8  # Minimum acceptable focus score
AUDIO_CHUNK_SIZE = 2048
SAMPLE_RATE = 16000

# Schedule settings
SCHEDULE_START = time(5, 0)  # 5:00 AM
SCHEDULE_END = time(13, 0)   # 1:00 PM

# Voice settings (copied from whale agent)
VOICE_MODEL = "tts-1"
VOICE_NAME = "echo" # Options: alloy, echo, fable, onyx, nova, shimmer
VOICE_SPEED = 1

# Create directories
AUDIO_DIR = Path("src/audio")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)



class FocusAgent:
    def __init__(self):
        """Initialize the Focus Agent"""
        load_dotenv()
        
        # Initialize OpenAI
        openai_key = os.getenv("OPENAI_KEY")
        if not openai_key:
            raise ValueError("🚨 OPENAI_KEY not found in environment variables!")
        self.openai_client = openai.OpenAI(api_key=openai_key)
        
        # Initialize Google Speech client
        google_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not google_creds:
            raise ValueError("🚨 GOOGLE_APPLICATION_CREDENTIALS not found!")
        self.speech_client = speech.SpeechClient()
        
        cprint("🎯 Moon Dev's Focus Agent initialized!", "green")
        
        self.is_recording = False
        self.current_transcript = []
        
        self._check_schedule()
        
    def _check_schedule(self):
        """Check if current time is within scheduled hours"""
        current_time = datetime.now().time()
        if not (SCHEDULE_START <= current_time <= SCHEDULE_END):
            cprint(f"\n🌙 Moon Dev's Focus Agent is scheduled to run between {SCHEDULE_START.strftime('%I:%M %p')} and {SCHEDULE_END.strftime('%I:%M %p')}", "yellow")
            cprint("😴 Going to sleep until next scheduled time...", "yellow")
            raise SystemExit(0)
        
    def _get_random_interval(self):
        """Get random interval between MIN and MAX minutes"""
        return uniform(MIN_INTERVAL_MINUTES * 60, MAX_INTERVAL_MINUTES * 60)
        
    def record_audio(self):
        """Record audio for specified duration"""
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=SAMPLE_RATE,
            language_code="en-US",
        )
        streaming_config = speech.StreamingRecognitionConfig(config=config)
        
        def audio_generator():
            audio = pyaudio.PyAudio()
            stream = audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=SAMPLE_RATE,
                input=True,
                frames_per_buffer=AUDIO_CHUNK_SIZE
            )
            
            start_time = time_lib.time()
            try:
                while time_lib.time() - start_time < RECORDING_DURATION:
                    data = stream.read(AUDIO_CHUNK_SIZE, exception_on_overflow=False)
                    yield data
            finally:
                stream.stop_stream()
                stream.close()
                audio.terminate()
        
        try:
            self.is_recording = True
            self.current_transcript = []
            
            requests = (speech.StreamingRecognizeRequest(audio_content=chunk)
                      for chunk in audio_generator())
            
            responses = self.speech_client.streaming_recognize(
                config=streaming_config,
                requests=requests
            )
            
            for response in responses:
                if response.results:
                    for result in response.results:
                        if result.is_final:
                            self.current_transcript.append(result.alternatives[0].transcript)
                            
        except Exception as e:
            cprint(f"❌ Error recording audio: {str(e)}", "red")
        finally:
            self.is_recording = False
            
    def _announce(self, message, force_voice=False):
        """Announce message with optional voice"""
        try:
            cprint(f"\n🗣️ {message}", "cyan")
            
            if not force_voice:
                return
                
            # Generate unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            speech_file = AUDIO_DIR / f"focus_audio_{timestamp}.mp3"
            
            # Generate speech
            response = self.openai_client.audio.speech.create(
                model=VOICE_MODEL,
                voice=VOICE_NAME,
                speed=VOICE_SPEED,
                input=message
            )
            
            # Save and play audio
            with open(speech_file, 'wb') as f:
                for chunk in response.iter_bytes():
                    f.write(chunk)
            
            # Play audio based on OS
            if os.name == 'posix':
                os.system(f"afplay {speech_file}")
            else:
                os.system(f"start {speech_file}")
                time_lib.sleep(5)
            
            # Cleanup
            speech_file.unlink()
            
        except Exception as e:
            cprint(f"❌ Error in announcement: {str(e)}", "red")

    def analyze_focus(self, transcript):
        """Analyze focus level from transcript"""
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": FOCUS_PROMPT},
                    {"role": "user", "content": transcript}
                ],
                max_tokens=150
            )
            
            analysis = response.choices[0].message.content.strip()
            
            # Split into score and message
            score_line, message = analysis.split('\n', 1)
            score = float(score_line.split('/')[0])
            
            return score, message.strip()
            
        except Exception as e:
            cprint(f"❌ Error analyzing focus: {str(e)}", "red")
            return 0, "Error analyzing focus"

    def process_transcript(self, transcript):
        """Process transcript and provide focus assessment"""
        score, message = self.analyze_focus(transcript)
        
        # Determine if voice announcement needed
        needs_voice = score < FOCUS_THRESHOLD
        
        # Format message (now cleaner without labels)
        formatted_message = f"{score}/10\n{message}"
        
        # Announce
        self._announce(formatted_message, force_voice=needs_voice)
        
        return score

    def run(self):
        """Main loop for random focus monitoring"""
        cprint("\n🎯 Moon Dev's Focus Agent starting with random monitoring...", "cyan")
        cprint(f"⏰ Operating hours: {SCHEDULE_START.strftime('%I:%M %p')} - {SCHEDULE_END.strftime('%I:%M %p')}", "cyan")
        
        while True:
            try:
                # Check schedule before each monitoring cycle
                self._check_schedule()
                
                # Get random interval
                interval = self._get_random_interval()
                next_check = datetime.now() + timedelta(seconds=interval)
                
                # Print next check time
                cprint(f"\n⏰ Next focus check will be around {next_check.strftime('%I:%M %p')}", "cyan")
                
                # Use time_lib instead of time
                time_lib.sleep(interval)
                
                # Start recording
                cprint("\n🎤 Recording sample...", "cyan")
                self.record_audio()
                
                # Process recording if we got something
                if self.current_transcript:
                    full_transcript = ' '.join(self.current_transcript)
                    if full_transcript.strip():
                        self.process_transcript(full_transcript)
                    else:
                        cprint("⚠️ No speech detected in sample", "yellow")
                else:
                    cprint("⚠️ No transcript generated", "yellow")
                    
            except KeyboardInterrupt:
                raise
            except Exception as e:
                cprint(f"❌ Error in main loop: {str(e)}", "red")
                time_lib.sleep(5)  # Wait before retrying

if __name__ == "__main__":
    try:
        agent = FocusAgent()
        agent.run()
    except KeyboardInterrupt:
        cprint("\n👋 Focus Agent shutting down gracefully...", "yellow")
    except Exception as e:
        cprint(f"\n❌ Fatal error: {str(e)}", "red")
