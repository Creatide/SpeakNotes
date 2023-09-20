#!python3.10

import os
import io

import speech_recognition as sr
import torch
import whisper

from datetime import datetime, timedelta
from queue import Queue
from tempfile import NamedTemporaryFile
from time import sleep
from sys import platform

from utils import Utilities


class ASR:
    def __init__(self) -> None:
        self.pytorch_device = torch.device(
            "cuda:0" if torch.cuda.is_available() else "cpu"
        )
        # Use only CPU
        # self.pytorch_device = torch.device('cpu')

        if self.pytorch_device.type == "cuda":
            torch.cuda.empty_cache()

        self.data_folder = "./data"
        self.audio_folder = os.path.join(self.data_folder, "audio")
        self.models_folder = os.path.join(self.data_folder, "models")
        self.whisper_folder = os.path.join(self.models_folder, "whisper")

        # Whisper Settings --------------------------------------------------- #
        self.whisper_all_models = [
            "tiny.en",
            "tiny",
            "base.en",
            "base",
            "small.en",
            "small",
            "medium.en",
            "medium",
            "large-v2",
        ]
        self.whisper_model_name = None
        self.whisper_model_path = None
        self.whisper_model = None

        # Recognizer Settings -------------------------------------------------- #
        # https://github.com/Uberi/speech_recognition/blob/master/reference/library-reference.rst
        self.recognizer = sr.Recognizer()
        self.stop_listening = None
        self.running = False
        self.is_paused = False
        self.recognizer.energy_threshold = 1000
        self.recognizer.dynamic_energy_threshold = False
        self.mic_devices = self.get_mic_devices()
        self.mic_device = None
        self.mic_device_selected = False
        self.sample_rate = 16000
        self.channels = 1
        self.record_timeout = 2
        self.phrase_timeout = 2
        self.transcription = [""]

        self.session_id = 0
        self.audio_file_counter = 0

    def get_transcription(self, join_text=False):
        return self.transcription if not join_text else " ".join(self.transcription)

    def recognition(self) -> None:

        phrase_time = None
        last_sample = bytes()
        data_queue = Queue()
        temp_file = NamedTemporaryFile().name
        self.stop_listening = None

        with self.mic_device:
            self.recognizer.adjust_for_ambient_noise(self.mic_device)

        # https://github.com/davabase/whisper_real_time
        def record_callback(_, audio: sr.AudioData) -> None:
            if not self.is_paused:
                data = audio.get_raw_data()
                data_queue.put(data)

                now = datetime.utcnow()

                if not data_queue.empty() and not self.is_paused:

                    nonlocal phrase_time
                    nonlocal last_sample
                    phrase_complete = False

                    if phrase_time and now - phrase_time > timedelta(
                        seconds=self.phrase_timeout
                    ):
                        last_sample = bytes()
                        phrase_complete = True

                    phrase_time = now

                    while not data_queue.empty():
                        data = data_queue.get()
                        last_sample += data

                    audio_data = sr.AudioData(
                        last_sample,
                        self.mic_device.SAMPLE_RATE,
                        self.mic_device.SAMPLE_WIDTH,
                    )
                    wav_data = io.BytesIO(audio_data.get_wav_data())

                    with open(temp_file, "w+b") as f:
                        f.write(wav_data.read())

                    result = self.whisper_model.transcribe(
                        temp_file,
                        fp16=torch.cuda.is_available(),
                        task="transcribe",
                        # task="translate",
                        # language="fi",
                    )
                    text = result["text"].strip()

                    if phrase_complete:
                        self.transcription.append(text)
                    else:
                        self.transcription[-1] = text

                    sleep(0.25)

                # Clear queue if paused
                elif self.is_paused:
                    data_queue.queue.clear()

        # Start listening in the background
        self.stop_listening = self.recognizer.listen_in_background(
            self.mic_device, record_callback, phrase_time_limit=self.record_timeout
        )

    def start(self) -> None:
        print(f"Model loaded: {self.whisper_model_path}\n")
        print(f"Microphone device selected: {self.mic_device}\n")
        self.recognition()

    def stop(self) -> None:
        self.stop_listening(wait_for_stop=False)
        self.stop_listening = None

    def pause(self) -> None:
        self.is_paused = True

    def resume(self) -> None:
        self.is_paused = False

    def reset(self) -> None:
        self.transcription = [""]

    # Get Microphone Devices ------------------------------------------------- #
    def get_mic_devices(self) -> dict:
        mic_devices = []
        for index, name in enumerate(sr.Microphone.list_microphone_names()):
            print(f'Microphone with name "{name}" found')
            mic_devices.append(name)
        return mic_devices

    # Set Michrophone Device ------------------------------------------------- #
    def set_mic_device(self, mic_name=""):
        if self.mic_devices:
            if "linux" in platform:
                if not mic_name or mic_name == "list":
                    print("Available microphone devices are: ")
                    for index, name in enumerate(sr.Microphone.list_microphone_names()):
                        print(f'Microphone with name "{name}" found')
                    return
                else:
                    for index, name in enumerate(sr.Microphone.list_microphone_names()):
                        if mic_name in name:
                            self.mic_device = sr.Microphone(
                                sample_rate=self.sample_rate, device_index=index
                            )
                            break
            else:
                self.mic_device = sr.Microphone(sample_rate=self.sample_rate)
        else:
            print("No microphone devices found")

    # Set Whisper Audio Model ------------------------------------------------ #
    def load_whisper_model(self, model_name=""):
        try:
            torch.cuda.empty_cache()
            if model_name in self.whisper_all_models:
                self.whisper_model_name = model_name
                self.whisper_model_path = os.path.join(
                    self.whisper_folder, self.whisper_model_name + ".pt"
                )
                # Download model if not found
                if not os.path.exists(self.whisper_model_path):
                    self.download_whisper_models(model_name=self.whisper_model_name)
                # Load model
                self.whisper_model = whisper.load_model(
                    self.whisper_model_path, download_root=self.models_folder
                )
                return model_name
            else:
                print(f"Model {model_name} not found")
                return None

        except Exception as e:
            print(f"Error loading model {model_name}: {e}")
            return None
            # Try to load lighter model
            # index = Utilities().find_index_by_name(model_name, self.whisper_all_models)
            # if index is not None and index - 2 >= 0:
            #     print(f"Trying to load model {self.whisper_all_models[index - 2]}")
            #     return self.load_whisper_model(self.whisper_all_models[index - 2])
            # else:
            #     print(f"Error loading model {model_name}: {e}")
            #     return None

    # Download Whisper Models ------------------------------------------------ #
    def download_whisper_models(
        self, model_name="", model_path=None, download_all=False
    ) -> None:
        if not model_path:
            model_path = os.path.join(self.models_folder, "whisper")
        # All whisper models
        # https://github.com/openai/whisper/discussions/63#discussioncomment-4423519
        from whisper import _download, _MODELS

        if download_all:
            print("Downloading all models")
            for model in self.whisper_all_models:
                _download(_MODELS[model], model_path, False)
        elif model_name in self.whisper_all_models:
            print(f"Downloading model {model_name}")
            _download(_MODELS[model_name], model_path, False)
