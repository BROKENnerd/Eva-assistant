import os
import sys
import json
import time
import asyncio
import logging
import subprocess
import random
import speech_recognition as sr
import edge_tts
from openai import OpenAI
from dotenv import load_dotenv
import webrtcvad

# 1. Path Fix to find modules folder
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.audio_engine import AudioEngine
from modules.tools import ToolManager

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("EVA")

client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")

class EVA_System:
    def __init__(self):
        self.audio = AudioEngine()
        
        # Two VAD Modes for Speed & Accuracy
        self.vad_sensitive = webrtcvad.Vad(1) # Listens for whispers
        self.vad_strict = webrtcvad.Vad(3)    # Detects loud human voice (for interrupt)
        
        self.tools = ToolManager()
        self.recognizer = sr.Recognizer()
        
        # --- FILLER SOUNDS SETUP ---
        self.fillers = ["hmm", "acha", "ruko", "umm", "let_me_see"]
        self._generate_filler_sounds()
        
        self.audio.start_stream()
        logger.info("⚡ EVA System Online (Natural + Turbo Mode)")

    def _generate_filler_sounds(self):
        """Generates filler audios on first run"""
        if not os.path.exists("fillers"):
            os.makedirs("fillers")

        filler_texts = {
            "hmm": "Hmm...",
            "acha": "Achaa...",
            "ruko": "Ek second...",
            "umm": "Umm...",
            "let_me_see": "Dekhti hoon..."
        }
        
        for name, text in filler_texts.items():
            path = f"fillers/{name}.mp3"
            if not os.path.exists(path):
                logger.info(f"Generating filler: {name}")
                asyncio.run(self._save_tts(text, path))

    async def _save_tts(self, text, filename):
        # Voice: Swara (Female). Change to 'hi-IN-MadhurNeural' for Male.
        communicate = edge_tts.Communicate(text, "hi-IN-SwaraNeural", rate="+5%")
        await communicate.save(filename)

    def play_filler(self):
        """Plays a random thinking sound"""
        sound = random.choice(self.fillers)
        subprocess.Popen(
            ["mpg123", "-q", f"fillers/{sound}.mp3"], 
            stdout=subprocess.DEVNULL, 
            stderr=subprocess.DEVNULL
        )

    def speak(self, text):
        logger.info(f"🤖 {text}")
        asyncio.run(self._save_tts(text, "response.mp3"))
        
        player = subprocess.Popen(["mpg123", "-q", "response.mp3"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        start = time.time()
        # --- SMART INTERRUPT LOOP ---
        while player.poll() is None:
            # Ignore mic for first 0.4s (Avoids self-echo)
            if time.time() - start < 0.4:
                time.sleep(0.05); continue
                
            frames = self.audio.get_frames()
            if not frames: time.sleep(0.02); continue

            speech_frames = 0
            for f in frames:
                # STRICT VAD: Only stops if you shout/speak clearly
                if self.vad_strict.is_speech(f, 16000): speech_frames += 1
            
            # If >60% of buffer is loud speech -> Stop
            if speech_frames > (len(frames) * 0.6):
                logger.info("🛑 Interrupted!")
                player.terminate()
                return
            time.sleep(0.02)

    def listen(self):
        print("\r🎧 Sun rahi hoon...", end="", flush=True)
        
        # Phase 1: Wait for any sound (Sensitive Mode)
        while True:
            frames = self.audio.get_frames()
            if frames:
                speech_count = 0
                for f in frames:
                    try:
                        if self.vad_sensitive.is_speech(f, 16000): speech_count += 1
                    except: pass
                
                if speech_count > (len(frames) * 0.2):
                    print("\r🔴 Recording... ", end="", flush=True)
                    break
            time.sleep(0.02)
        
        # Phase 2: Record until Silence (Turbo Timeout: 0.6s)
        collected_frames = []
        silence_chunks = 0
        while True:
            chunk = self.audio.get_frames()
            if not chunk: time.sleep(0.01); continue
            collected_frames.extend(chunk)
            
            is_speech = False
            for f in chunk:
                if self.vad_sensitive.is_speech(f, 16000): is_speech = True; break
            
            if is_speech: silence_chunks = 0
            else: silence_chunks += 1
            
            # 6 chunks * 100ms = 0.6 seconds of silence -> Stop
            if silence_chunks > 6: 
                print("\r⏳ Processing... ", end="", flush=True)
                break 
            time.sleep(0.1)

        # Phase 3: Transcribe
        import wave
        with wave.open("input.wav", 'wb') as wf:
            wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(16000); wf.writeframes(b''.join(collected_frames))
        
        try:
            with sr.AudioFile("input.wav") as source:
                # Google STT (Online Free) - High Accuracy
                return self.recognizer.recognize_google(self.recognizer.record(source), language="hi-IN")
        except: return None

    def think(self, text):
        self.play_filler() # "Hmm..."

        prompt = """
        You are EVA. Reply in Hinglish (Hindi+English).
        
        STYLE:
        - Natural, Witty, Short.
        - Use fillers: "Arre", "Haan", "Achaa", "Dekho".
        - Example: "Haan bilkul, kar diya maine." (Not "Yes I did it")
        
        TOOLS (JSON Only):
        - Create: {"tool": "create_file", "args": {"filename": "x", "content": "y"}}
        - Edit/Append: {"tool": "edit_file", "args": {"filename": "x", "content": "y", "mode": "append"}}
        - Read: {"tool": "read_file", "args": {"filename": "x"}}
        - Delete: {"tool": "delete_file", "args": {"filename": "x"}}
        """
        try:
            res = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "system", "content": prompt}, {"role": "user", "content": text}],
                stream=False
            )
            return res.choices[0].message.content
        except: return "Arre, internet slow hai shayad."

    def run(self):
        self.speak("Haan boliye, main ready hoon.")
        while True:
            try:
                text = self.listen()
                if not text: continue
                print(f"\n👤 You: {text}")

                if "force stop" in text.lower(): break
                
                reply = self.think(text)
                
                # Check for Tool Command
                if reply.strip().startswith("{") and "tool" in reply:
                    try:
                        cmd = json.loads(reply)
                        self.speak("Haan ek second...") # Acknowledge command
                        out = self.tools.execute(cmd["tool"], cmd.get("args", {}))
                        self.speak(out)
                    except: self.speak(reply)
                else:
                    self.speak(reply)
            except KeyboardInterrupt: break
        self.audio.stop_stream()

if __name__ == "__main__":
    EVA_System().run()
