# EVA Assistant (Extraterrestrial/Virtual Assistant) 🌱

**"Directive?"**

EVA is a lightweight, voice-controlled AI assistant inspired by the sleek and reactive nature of EVE from the movie *WALL-E*. Designed to be more than just a chatbot, EVA acts as a hands-on system companion capable of listening, speaking, and autonomously modifying its own files.

### 🤖 Core Features
* **DeepSeek Powered:** Built for efficiency and low cost (default), with optional support for **OpenAI**.
* **Full Duplex Voice:** Uses advanced Speech-to-Text and Text-to-Speech for seamless conversation.
* **System Access:** Can read, write, and modify specific local files it is given access to.
* **Reactive Personality:** Features humor and reactive behaviors, making interactions feel "alive" rather than robotic.

### 🛠️ Hardware Requirements
* Raspberry Pi 4B (2GB+) / PC
* Microphone (e.g., INMP441)
* Speakers

setup.sh (One-Click Installer)
​Agar aap git repo mein ye file bhi daal denge, to future mein install karna bahut aasaan ho jayega.
​File banayein: nano setup.sh
​Paste karein:
#!/bin/bash

echo "🔵 Installing System Tools (SoX, MPG123)..."
sudo apt update
sudo apt install python3-pip sox libsox-fmt-all mpg123 flac -y

echo "🔵 Installing Python Libraries..."
pip install -r requirements.txt

echo "✅ Setup Complete! Run with: python main.py"
________-----_____
execute it
chmod +x setup.sh




