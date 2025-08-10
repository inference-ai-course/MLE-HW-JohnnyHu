import logging
import sounddevice as sd
from scipy.io.wavfile import write, read
import requests


# -----------------------------
# Logging Setup
# -----------------------------
log_file = "app.log"
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# -----------------------------
# Record Audio
# -----------------------------
def record_audio(file_path="output.wav", duration=5, sample_rate=44100):
    try:
        logging.info(f"Starting recording: duration={duration}s, sample_rate={sample_rate}")
        print("🎤 Recording... Speak now!")
        recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='int16')
        sd.wait()
        write(file_path, sample_rate, recording)
        logging.info(f"Recording saved to {file_path}")
        print(f"✅ Saved recording to {file_path}")
        return file_path
    except Exception as e:
        logging.error(f"Error in record_audio: {e}")
        print(f"❌ Error recording audio: {e}")
        return None

# -----------------------------
# Play Audio
# -----------------------------
def play_audio(file_path):
    try:
        logging.info(f"Playing audio from {file_path}")
        print(f"▶️ Playing response...")
        sample_rate, data = read(file_path)
        sd.play(data, sample_rate)
        sd.wait()
        logging.info("Playback finished.")
        print("✅ Playback finished.")
    except Exception as e:
        logging.error(f"Error in play_audio: {e}")
        print(f"❌ Error playing audio: {e}")

# -----------------------------
# Send WAV to FastAPI
# -----------------------------
def send_wav_to_fastapi(file_path, url="http://127.0.0.1:8000/chat/"):
    try:
        logging.info(f"Sending file {file_path} to {url}")
        with open(file_path, "rb") as f:
            files = {"file": (file_path, f, "audio/wav")}
            response = requests.post(url, files=files)

        if response.status_code == 200:
            # Save the received audio file
            response_audio_path = "response.wav"
            with open(response_audio_path, "wb") as f:
                f.write(response.content)
            logging.info(f"Response audio saved to {response_audio_path}")
            print(f"✅ Response audio saved to {response_audio_path}")
            play_audio(response_audio_path) # Play the response
        else:
            logging.warning(f"Failed to send file. Status: {response.status_code}, Response: {response.text}")
            print(f"❌ Failed with status code {response.status_code}")
            print("Response:", response.text)
    except Exception as e:
        logging.error(f"Error in send_wav_to_fastapi: {e}")
        print(f"⚠️ Error sending file: {e}")

# -----------------------------
# Main Workflow
# -----------------------------
if __name__ == "__main__":
    logging.info("Program started")
    while True:
        user_input = input("Press Enter to start recording, or type 'quit' to exit: ")
        if user_input.lower() == 'quit':
            break
        
        file_path = record_audio(duration=5)
        if file_path:
            send_wav_to_fastapi(file_path)
            
    logging.info("Program finished")
    print("👋 Goodbye!")