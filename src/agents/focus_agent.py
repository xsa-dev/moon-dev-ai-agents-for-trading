"""
🌙 Moon Dev's Focus Agent
Built with love by Moon Dev 🚀

This agent randomly monitors speech samples and provides focus assessments.
"""




# System prompt for focus analysis
FOCUS_PROMPT = """
You are Moon Dev's Focus AI Agent. Analyze the following transcript and:
1. Rate focus level from 1-10 (10 being completely focused on coding)
2. Provide ONE encouraging sentence to maintain/improve focus or a great quote to inspire to focus or keep pushing through hard times

Consider:
- Coding discussion = high focus
- Trading analysis = high focus
- Random chat/topics = low focus
- Non-work discussion = low focus

BE VERY STRICT WITH YOUR RATING, LIKE A DRILL SERGEANT. DONT GO EASY ON ME. I HAVE TO BE VERY FOCUSED, AND YOUR JOB IS TO MAKE ME VERY FOCUSED.

RESPOND IN THIS EXACT FORMAT:
X/10
"Quote OR motivational sentence"
"""

# Model override settings
# Set to "0" to use config.py's AI_MODEL setting
# Available models:
# - "deepseek-chat" (DeepSeek's V3 model - fast & efficient)
# - "deepseek-reasoner" (DeepSeek's R1 reasoning model)
# - "0" (Use config.py's AI_MODEL setting)
MODEL_OVERRIDE = "deepseek-chat"  # Set to "0" to disable override
DEEPSEEK_BASE_URL = "https://api.deepseek.com"  # Base URL for DeepSeek API

import os
import time as time_lib
from datetime import datetime, timedelta, time
from google.cloud import speech_v1p1beta1 as speech
import pyaudio
import openai
from anthropic import Anthropic
from termcolor import cprint
from pathlib import Path
from dotenv import load_dotenv
from random import randint, uniform
import threading
import pandas as pd
import tempfile
from src.config import *

# Configuration
MIN_INTERVAL_MINUTES = 4
MAX_INTERVAL_MINUTES = 11
RECORDING_DURATION = 30  # seconds
FOCUS_THRESHOLD = 8  # Minimum acceptable focus score
AUDIO_CHUNK_SIZE = 2048
SAMPLE_RATE = 16000

# Schedule settings
SCHEDULE_START = time(5, 0)  # 5:00 AM
SCHEDULE_END = time(13, 0)   # 1:00 PM

# Voice settings (copied from whale agent)
VOICE_MODEL = "tts-1"
VOICE_NAME = "onyx" # Options: alloy, echo, fable, onyx, nova, shimmer
VOICE_SPEED = 1

# Create directories
AUDIO_DIR = Path("src/audio")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


class FocusAgent:
    def __init__(self):
        """Initialize the Focus Agent"""
        load_dotenv()
        
        # Initialize OpenAI for voice and DeepSeek
        openai_key = os.getenv("OPENAI_KEY")
        if not openai_key:
            raise ValueError("🚨 OPENAI_KEY not found in environment variables!")
        self.openai_client = openai.OpenAI(api_key=openai_key)
        
        # Initialize Anthropic for Claude models
        anthropic_key = os.getenv("ANTHROPIC_KEY")
        if not anthropic_key:
            raise ValueError("🚨 ANTHROPIC_KEY not found in environment variables!")
        self.anthropic_client = Anthropic(api_key=anthropic_key)
        
        # Set active model - use override if set, otherwise use config
        self.active_model = MODEL_OVERRIDE if MODEL_OVERRIDE != "0" else AI_MODEL
        
        # Initialize DeepSeek client if needed
        if "deepseek" in self.active_model.lower():
            deepseek_key = os.getenv("DEEPSEEK_KEY")
            if deepseek_key:
                self.deepseek_client = openai.OpenAI(
                    api_key=deepseek_key,
                    base_url=DEEPSEEK_BASE_URL
                )
                cprint("🚀 Moon Dev's Focus Agent using DeepSeek override!", "green")
            else:
                self.deepseek_client = None
                cprint("⚠️ DEEPSEEK_KEY not found - DeepSeek model will not be available", "yellow")
        else:
            self.deepseek_client = None
            cprint(f"🎯 Moon Dev's Focus Agent using Claude model: {self.active_model}!", "green")
        
        # Initialize Google Speech client
        google_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not google_creds:
            raise ValueError("🚨 GOOGLE_APPLICATION_CREDENTIALS not found!")
        self.speech_client = speech.SpeechClient()
        
        cprint("🎯 Moon Dev's Focus Agent initialized!", "green")
        
        self.is_recording = False
        self.current_transcript = []
        
        # Add data directory path
        self.data_dir = Path("/Users/md/Dropbox/dev/github/moon-dev-ai-agents-for-trading/src/data")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.focus_log_path = self.data_dir / "focus_history.csv"
        
        # Initialize focus history DataFrame if file doesn't exist
        if not self.focus_log_path.exists():
            self._create_focus_log()
            
        cprint("📊 Focus history will be logged to: " + str(self.focus_log_path), "green")
        
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
                
            # Generate speech directly to memory and play
            response = self.openai_client.audio.speech.create(
                model=VOICE_MODEL,
                voice=VOICE_NAME,
                speed=VOICE_SPEED,
                input=message
            )
            
            # Create temporary file in system temp directory
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
                for chunk in response.iter_bytes():
                    temp_file.write(chunk)
                temp_path = temp_file.name

            # Play audio based on OS
            if os.name == 'posix':
                os.system(f"afplay {temp_path}")
            else:
                os.system(f"start {temp_path}")
                time_lib.sleep(5)
            
            # Cleanup temp file
            os.unlink(temp_path)
            
        except Exception as e:
            cprint(f"❌ Error in announcement: {str(e)}", "red")

    def analyze_focus(self, transcript):
        """Analyze focus level from transcript"""
        try:
            # Use either DeepSeek or Claude
            if "deepseek" in self.active_model.lower():
                if not self.deepseek_client:
                    raise ValueError("🚨 DeepSeek client not initialized - check DEEPSEEK_KEY")
                client = self.deepseek_client
                model = "deepseek-chat"
                cprint(f"🤖 Using DeepSeek model: {model}", "cyan")
                
                # Make DeepSeek API call
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": FOCUS_PROMPT},
                        {"role": "user", "content": transcript}
                    ],
                    max_tokens=AI_MAX_TOKENS,
                    temperature=AI_TEMPERATURE,
                    stream=False
                )
                analysis = response.choices[0].message.content.strip()
                
            else:
                # Use Claude with Anthropic client
                cprint(f"🤖 Using Claude model: {self.active_model}", "cyan")
                
                # Make Anthropic API call
                response = self.anthropic_client.messages.create(
                    model=self.active_model,
                    max_tokens=AI_MAX_TOKENS,
                    temperature=AI_TEMPERATURE,
                    system=FOCUS_PROMPT,
                    messages=[
                        {"role": "user", "content": transcript}
                    ]
                )
                analysis = response.content[0].text
            
            cprint(f"\n📝 Raw model response:\n{analysis}", "magenta")
            
            # Split into score and message
            score_line, message = analysis.split('\n', 1)
            score = float(score_line.split('/')[0])
            
            return score, message.strip()
            
        except Exception as e:
            cprint(f"❌ Error analyzing focus: {str(e)}", "red")
            return 0, "Error analyzing focus"

    def _create_focus_log(self):
        """Create empty focus history CSV"""
        df = pd.DataFrame(columns=['timestamp', 'focus_score', 'quote'])
        df.to_csv(self.focus_log_path, index=False)
        cprint("🌟 Moon Dev's Focus History log created!", "green")

    def _log_focus_data(self, score, quote):
        """Log focus data to CSV"""
        try:
            # Create new row
            new_data = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'focus_score': score,
                'quote': quote.strip('"')  # Remove quotation marks
            }
            
            # Read existing CSV
            df = pd.read_csv(self.focus_log_path)
            
            # Append new data
            df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
            
            # Save back to CSV
            df.to_csv(self.focus_log_path, index=False)
            
            cprint("📝 Focus data logged successfully!", "green")
            
        except Exception as e:
            cprint(f"❌ Error logging focus data: {str(e)}", "red")

    def process_transcript(self, transcript):
        """Process transcript and provide focus assessment"""
        score, message = self.analyze_focus(transcript)
        
        # Log the data
        self._log_focus_data(score, message)
        
        # Determine if voice announcement needed
        needs_voice = score < FOCUS_THRESHOLD
        
        # Format message
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
