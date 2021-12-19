import torch
import soundfile as sf
import librosa
import numpy as np
from scipy.io import wavfile
from IPython.display import Audio
from os.path import dirname, join as pjoin
from os import getcwd
from transformers import Wav2Vec2ForCTC, Wav2Vec2Tokenizer, Wav2Vec2CTCTokenizer, Wav2Vec2Processor
tokenizer = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base-960h")
model = Wav2Vec2ForCTC.from_pretrained("facebook/wav2vec2-base-960h")


class STT:
    pass


def try_transcription(filename, rate: int):
    data = wavfile.read(filename)
    framerate = data[0]
    print(framerate)
    sounddata = data[1]
    time = np.arange(0, len(sounddata))/framerate
    input_audio, _ = librosa.load(filename, sr=16000)
    print(type(input_audio))
    input_values = tokenizer(input_audio, return_tensors="pt").input_values
    logits = model(input_values).logits
    predicted_ids = torch.argmax(logits, dim=-1)
    transcription = tokenizer.batch_decode(predicted_ids)[0]
    print("\n\n\n\n")
    print(transcription)
    print("\n\n\n")
    with open("transcript.txt", "w") as f:
        f.write(transcription)
    return transcription


# print(getcwd())
# data_dir = pjoin(getcwd(), "")
# if("Server" not in data_dir):
#     data_dir = pjoin(getcwd(), "Server")

# file_name = pjoin(data_dir, 'temp.wav')
# data = wavfile.read(file_name)

# framerate = data[0]
# print(framerate)
# sounddata = data[1]
# time = np.arange(0, len(sounddata))/framerate
# input_audio, _ = librosa.load(file_name, sr=16000)
# print(type(input_audio))
# input_values = tokenizer(input_audio, return_tensors="pt").input_values
# logits = model(input_values).logits
# predicted_ids = torch.argmax(logits, dim=-1)
# transcription = tokenizer.batch_decode(predicted_ids)[0]
# print(transcription)

try_transcription("mywav_reduced_noise.wav", 16000)
