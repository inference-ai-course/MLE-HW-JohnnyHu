from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
import whisper
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig,pipeline
from gtts import gTTS
from pydub import AudioSegment
import io
import torch
import logging
import os
import tempfile
import pandas as pd
from IPython.display import display

log_file = "app.log"
logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

app = FastAPI()
 
@app.post("/chat/")
async def chat(file: UploadFile = File(...)):
    audio_bytes = await file.read()
    logging.info("audio file read completed......")
    user_text = transcribe_audio(audio_bytes)
    logging.info("user message: " + user_text)
    bot_text = generate_response(user_text)
    logging.info("bot response:" + bot_text)
    audio_path = synthesize_speech(bot_text)
    return FileResponse(audio_path, media_type="audio/wav")


asr_model = whisper.load_model("small")

def transcribe_audio(audio_bytes):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
        temp_file.write(audio_bytes)
        temp_file_path = temp_file.name
    
    try:
        result = asr_model.transcribe(temp_file_path)
    finally:
        os.remove(temp_file_path)
        
    return result["text"]

api_token = "**removed**"
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16
)
#model_id = "meta-llama/Meta-Llama-3.1-8B-Instruct"
model_id = "mistralai/Mistral-7B-Instruct-v0.1"
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    quantization_config=quantization_config,
    device_map="auto",
    token=api_token # Use your valid API token
)
tokenizer = AutoTokenizer.from_pretrained(
    model_id,
    token=api_token
)
llm = pipeline(
    "text-generation", 
    model=model,
    tokenizer=tokenizer,
    token=api_token,
    max_new_tokens=256) 
conversation_history = []
question_history = []

def generate_response(user_text):
    conversation_history.append({"role": "user", "text": user_text})
    # Construct prompt from history
    prompt = ""
    for turn in conversation_history[-5:]:
        prompt += f"{turn['role']}: {turn['text']}\n"
    outputs = llm(prompt, max_new_tokens=100)
    bot_response = outputs[0]["generated_text"]
    display(outputs)
    conversation_history.append({"role": "assistant", "text": bot_response})
    return clean_answer(bot_response)

def clean_answer(response):
    for turn in conversation_history[-5:]:
        response = response.replace(f"{turn['role']}: {turn['text']}\n", "")
    response = response.replace("assistant: ","").replace("user: ","").replace("Answer: ","").replace("AI: ","").replace("\n","")
    logging.info(response)
    return response



def synthesize_speech(text, filename="response.wav"):
    print(text)
    tts = gTTS(text)
    
    # Save the MP3 to an in-memory file
    mp3_fp = io.BytesIO()
    tts.write_to_fp(mp3_fp)
    mp3_fp.seek(0)
    
    # Convert MP3 to WAV
    sound = AudioSegment.from_file(mp3_fp, format="mp3")
    sound.export(filename, format="wav")
    
    return filename