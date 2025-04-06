from datetime import datetime
import re
import traceback
from vosk import Model, KaldiRecognizer
import os
import json
import sys
import pyaudio

prev_entry_datetime = None
writing = True
writing_start_magick_words = re.compile("^команда (начни|начать|возобнови|включи)(ть)? запись$")
writing_stop_magick_words = re.compile("^команда (прекрати|останови|выключи)(ть)? запись$")

def log_time():
    print("### " + datetime.now().strftime("(%H:%M:%S)"))

log_time()
model = Model(sys.argv[1])
print("KaldiRecognizer...")
rec = KaldiRecognizer(model, 16000)

def add_to_txt(text):
    #if os.access(file_path, os.W_OK):
    #  print(f"Write permission is granted for file: {file_path}")
    if writing == True:
        with open(datetime.today().strftime("../../%m-%Y.txt"), "a", encoding="utf-8") as f:
            f.writelines(text + f"\n")
            f.flush()

def listen_input():
    try:
        global prev_entry_datetime
        global writing
        print("pyaudio...")
        p = pyaudio.PyAudio()
        print("open stream...")
        stream = p.open(
            format=pyaudio.paInt16, 
            channels=1, 
            rate=16000, 
            input=True, 
            frames_per_buffer=8192
        )
        stream.start_stream()
        print("listening...")
        log_time()
        while True:
            data = stream.read(4096)
            if len(data) == 0:
                break
            text = rec.Result() if rec.AcceptWaveform(data) else rec.PartialResult()
            data = json.loads(text)
            if 'partial' in data.keys():
                continue
            if 'text' in data.keys():
                text = data['text']
                if text == "":
                    continue
                log_time()
                print(text)
                if writing_stop_magick_words.match(text):
                    writing = False
                    print("### запись остановлена")
                    continue
                elif writing_start_magick_words.match(text):
                    writing = True
                    print("### запись возобновлена")
                    continue
                #[2025-04-05T7:28:00+03:00]
                if prev_entry_datetime == None: 
                    add_to_txt(datetime.now().strftime("[%Y-%m-%dT%H:%M:%S+03:00]"))
                else:
                    delta = datetime.now() - prev_entry_datetime
                    if delta.total_seconds() > 1800:
                        add_to_txt(f"\n\n")
                    if delta.total_seconds() > 300:
                        add_to_txt(f"\n")
                    if delta.total_seconds() > 20:
                        add_to_txt(datetime.now().strftime("[%Y-%m-%dT%H:%M:%S+03:00]"))
                add_to_txt(text)
                prev_entry_datetime = datetime.now()
    except Exception:
        print(traceback.format_exc())

while True:
   listen_input()
