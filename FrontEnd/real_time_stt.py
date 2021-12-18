from asyncio import futures
import json
from datetime import datetime
import base64
import asyncio
import pyaudio
import websockets
import wave
import logging
import speech_recognition as sr
import io
from scipy.io.wavfile import read, write
import time
r = sr.Recognizer()
mic = sr.Microphone(device_index=6)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SAMPLE_RATE = 16000
FRAMES_PER_BUFFER = 3200
CHANNELS = 1
FORMAT = pyaudio.paInt16

# API_KEY = '<your AssemblyAI Key goes here>'
# ASSEMBLYAI_ENDPOINT = f'wss://api.assemblyai.com/v2/realtime/ws?sample_rate={SAMPLE_RATE}'
ASSEMBLYAI_ENDPOINT = "wss://2746-27-5-10-110.ngrok.io/media"

# p = pyaudio.PyAudio()
# audio_stream = p.open(
#     frames_per_buffer=FRAMES_PER_BUFFER,
#     rate=SAMPLE_RATE,
#     format=pyaudio.paInt16,
#     channels=CHANNELS,
#     input=True,
# )
# p.close(audio_stream)
# print(f"Sample size: {p.get_sample_size(FORMAT)}")


def save_audio_to_wav(audio, p, append,  file):
    # frames = [audio]
    try:
        frames = []
        if not append:
            filename: str = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            filename += ".wav"
        else:
            filename = file
        # print(filename)

        # get the audio present in the file
        if append:
            with wave.open(filename, "rb") as f:
                n = f.getnframes()
                frame = f.readframes(n)
            # append it to frames
            frames.append(frame)
        # add the current audio
        frames.append(audio)
        with wave.open(filename, "wb") as f:
            f.setnchannels(CHANNELS)
            f.setsampwidth(p.get_sample_size(FORMAT))
            f.setframerate(SAMPLE_RATE)
            f.writeframes(b''.join(frames))
        file = filename
        return filename
    except KeyboardInterrupt:
        logger.info("\nInterrupted by user\n\n\n")
        f.close()


async def speech_to_text():
    """
    Asynchronous function used to perfrom real-time speech-to-text using AssemblyAI API
    """
    append: bool = False
    file: str = ""
    async with websockets.connect(
        ASSEMBLYAI_ENDPOINT,
        ping_interval=5,
        ping_timeout=20,
        # extra_headers=(('Authorization', API_KEY), ),
    ) as ws_connection:
        await asyncio.sleep(0.5)
        temp = await ws_connection.recv()
        logger.info("temp: %s", temp)
        logger.info('Websocket connection initialised')

        async def send_data():
            nonlocal append, file
            """
            Asynchronous function used for sending data
            """
            logger.info("Sending Data")
            # while True:

            with mic as source:
                # try:
                r.adjust_for_ambient_noise(source)
                r.energy_threshold = 4500
                r.dynamic_energy_threshold = True
                logger.info("Listening")
                try:
                    data = r.listen(source, phrase_time_limit=5, timeout=10)
                    logger.info(f"Transcription: {r.recognize_google(data)} ")

                    data = data.get_wav_data()
                    print(read(io.BytesIO(data)))
                    rate, data = read(io.BytesIO(data))
                except sr.WaitTimeoutError as e:
                    return {"timeout": True}
                # data = audio_stream.read(FRAMES_PER_BUFFER)

                # file = save_audio_to_wav(data, p, append, file)
                # append = True
                # logger.info(f"file name to be saved: {file} ")
                data = base64.b64encode(data).decode('utf-8')
                # print(f"Sample Size: { p.get_sample_size(FORMAT)}")
                await ws_connection.send(json.dumps(
                    {
                        'event': "media",
                        'media': {
                            "payload": str(data),
                            "channels": CHANNELS,
                            "sample_rate": rate,
                            "frames": FRAMES_PER_BUFFER,
                            "sample_size": 2
                        }
                    }
                ))
                # temp = ws_connection.recv()
                # print(temp)

                # except Exception as e:
                # print(e)
                # print(f'Something went wrong. Error code was {e.code}')
                # break
                # await asyncio.sleep(0.5)

            return True

        async def receive_data(start_time):
            """
            Asynchronous function used for receiving data
            """
            logger.info(f"start_time: {start_time}")
            prev_msg = None
            received_msg = None

            while True:
                # logger.info(f"elapsed: {int(time.time())-start_time }")
                prev_msg = received_msg
                received_msg = None
                try:
                    received_msg = await ws_connection.recv()
                    print(received_msg)
                    return received_msg
                    if(received_msg == "Finished"):
                        return prev_msg
                    # print(json.loads(received_msg)['text'])
                except asyncio.CancelledError as e:
                    return (received_msg if received_msg is not None else prev_msg)
                except Exception as e:
                    logger.error(f'Something went wrong.\n{e}')
                    break
            logger.info("recording over\n")
            await ws_connection.send(json.dumps(
                {
                    'event': "closed",
                }
            ))
            return received_msg
        data_received = None

        try:
            data_sent, data_received = await asyncio.gather(
                send_data(),
                asyncio.shield(
                    asyncio.wait_for(
                        receive_data(int(time.time())),
                        20)
                ),
                return_exceptions=True
            )
            logger.info(f"data received: {data_received} ")
        except futures.TimeoutError as e:
            await ws_connection.send(json.dumps(
                {
                    'event': "closed",
                }
            ))
            await ws_connection.close()
        finally:
            return data_received


def main():
    transcript = asyncio.run(speech_to_text())
    logger.info(f"Final Transcription: {transcript} ")


if __name__ == '__main__':
    main()
