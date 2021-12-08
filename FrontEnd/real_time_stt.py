import json
from datetime import datetime
import base64
import asyncio
import pyaudio
import websockets
import wave
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SAMPLE_RATE = 16000
FRAMES_PER_BUFFER = 3200
CHANNELS = 1
FORMAT = pyaudio.paInt16

# API_KEY = '<your AssemblyAI Key goes here>'
# ASSEMBLYAI_ENDPOINT = f'wss://api.assemblyai.com/v2/realtime/ws?sample_rate={SAMPLE_RATE}'
ASSEMBLYAI_ENDPOINT = "wss://27a9-115-97-254-132.ngrok.io/media"

p = pyaudio.PyAudio()
audio_stream = p.open(
    frames_per_buffer=FRAMES_PER_BUFFER,
    rate=SAMPLE_RATE,
    format=pyaudio.paInt16,
    channels=CHANNELS,
    input=True,
)


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
            while True:
                # try:
                data = audio_stream.read(
                    FRAMES_PER_BUFFER, exception_on_overflow=False)

                file = save_audio_to_wav(data, p, append, file)
                append = True
                logger.info(f"file name to be saved: {file} ")
                data = base64.b64encode(data).decode('utf-8')
                await ws_connection.send(json.dumps(
                    {
                        'event': "media",
                        'media': {
                            "payload": str(data),
                            "channels": CHANNELS,
                            "sample_rate": SAMPLE_RATE,
                            "frames": FRAMES_PER_BUFFER,
                            "sample_size": p.get_sample_size(FORMAT)
                        }
                    }
                ))
                # except Exception as e:
                # print(e)
                # print(f'Something went wrong. Error code was {e.code}')
                # break
                # await asyncio.sleep(0.5)
            return True

        async def receive_data():
            """
            Asynchronous function used for receiving data
            """
            while True:
                try:
                    received_msg = await ws_connection.recv()
                    print(json.loads(received_msg)['text'])
                except Exception as e:
                    logger.error(
                        f'Something went wrong. Error code was {e.code}')
                    break

        data_sent, data_received = await asyncio.gather(send_data(), receive_data())


def main():
    asyncio.run(speech_to_text())


if __name__ == '__main__':
    main()
