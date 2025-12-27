import subprocess
import threading
import collections
import time
import os
import signal
import logging

# Logging config
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AudioEngine")

class AudioEngine:
    def __init__(self):
        self.running = False
        self.process = None
        self.buffer = collections.deque(maxlen=200) # Buffer last ~2-3 seconds
        self.lock = threading.Lock()
        
        # 16000Hz * 30ms = 960 bytes (Standard frame size for VAD)
        self.frame_size = 960 

    def start_stream(self):
        if self.running: return
        # Using sox to convert 48k capture to 16k clean audio (No Gain/Boost applied here to save CPU)
        cmd = (
            "arecord -D plughw:3,0 -c 1 -r 48000 -f S32_LE -t raw -q 2>/dev/null | "
            "sox -t raw -r 48000 -e signed -b 32 -c 1 - "
            "-t raw -r 16000 -e signed -b 16 - "
        )

        self.process = subprocess.Popen(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, preexec_fn=os.setsid
        )
        
        self.running = True
        self.thread = threading.Thread(target=self._read_stream, daemon=True)
        self.thread.start()

    def _read_stream(self):
        """Background thread to read audio chunks"""
        while self.running and self.process.poll() is None:
            try:
                data = self.process.stdout.read(self.frame_size)
                if not data: break
                
                if len(data) == self.frame_size:
                    with self.lock:
                        self.buffer.append(data)
            except: break

    def get_frames(self):
        """Main thread calls this to get latest audio"""
        with self.lock:
            frames = list(self.buffer)
            self.buffer.clear()
        return frames

    def stop_stream(self):
        self.running = False
        if self.process:
            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            except: pass
