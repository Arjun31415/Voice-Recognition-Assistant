import asyncio
import base64
import json
import logging
import time
import wave

import noisereduce as nr
import pyaudio
from flask import Flask
from flask_sockets import Sockets
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
from scipy.io import wavfile

from Speech_Recognition import try_transcription

app = Flask(__name__)
sockets = Sockets(app)
STARTED_TIME: int
HTTP_SERVER_PORT = 5000
audio_stream = []
CHANNELS: int
FORMAT = pyaudio.paInt16
SAMPLE_RATE: int
FRAMES_PER_BUFFER: int
SAMPLE_SIZE: int


def transcription(filename):
    app.logger.info(f"elapsed time: {(int(time.time())-STARTED_TIME)} ")
    if(int(time.time())-STARTED_TIME) % 5 == 0:
        text = try_transcription(filename, SAMPLE_RATE)
        app.logger.info("TRANSCRIPTION: %s\n" % text)
        return text
    return None


def save_audio_to_wav(audio, file):
    # frames = [audio]
    try:
        filename = file

        with wave.open(filename, mode="w") as f:
            try:
                f.setnchannels(CHANNELS)
                f.setsampwidth(SAMPLE_SIZE)
                f.setframerate(SAMPLE_RATE)
                f.writeframes(b''.join(audio))
            except KeyboardInterrupt:
                f.close()
        file = filename
        rate, data = wavfile.read(filename)
        reduced_noise = nr.reduce_noise(y=data, sr=rate)
        wavfile.write("mywav_reduced_noise.wav", rate, reduced_noise)
        return filename
    except KeyboardInterrupt:
        app.logger.info("Interrupted by user\n\n\n")
        return None


@sockets.route('/media')
def echo(ws):
    global CHANNELS, SAMPLE_RATE, FRAMES_PER_BUFFER, SAMPLE_SIZE, audio_stream
    app.logger.info("Connection accepted")
    # A lot of messages will be sent rapidly. We'll stop showing after the first one.
    has_seen_media = False
    message_count = 0
    ws.send("Hello")

    global STARTED_TIME
    STARTED_TIME = int(time.time())
    while not ws.closed:
        message = ws.receive()
        if message is None:
            # TODO: instead of continue do some transcript
            app.logger.info("No message received...")
            continue

        app.logger.info(f"Message received: {message[:10]}")

        # Messages are a JSON encoded string
        data = json.loads(message)
        app.logger.info("data received")

        # Using the event type you can determine what type of message you are receiving
        if data['event'] == "connected":
            app.logger.info("Connected Message received: %s", message)
        if data['event'] == "start":
            app.logger.info("Start Message received: %s", message)
        if data['event'] == "media":

            if not has_seen_media:
                app.logger.info("Media message: %s", message)
                payload = data['media']['payload']
                app.logger.info("Payload is: %s", payload)
                chunk = base64.b64decode(payload)
                app.logger.info("That's %d bytes", len(chunk))
                app.logger.info(
                    "Additional media messages from WebSocket are being suppressed....")
                has_seen_media = True
            payload = data['media']['payload']
            CHANNELS = data['media']['channels']
            SAMPLE_RATE = data['media']['sample_rate']
            FRAMES_PER_BUFFER = data['media']['frames']
            SAMPLE_SIZE = data['media']['sample_size']
            app.logger.info(f"Channels: {CHANNELS}")
            app.logger.info(f"Sample Rate: {SAMPLE_RATE}")
            app.logger.info(f"Frames per buffer: {FRAMES_PER_BUFFER}")
            app.logger.info(f"Sample Size: {SAMPLE_SIZE}")
            chunk = base64.b64decode(payload)
            audio_stream.append(chunk)
            save_audio_to_wav(audio_stream, "temp.wav")
            transcript = transcription("mywav_reduced_noise.wav")
            if transcript is not None:
                app.logger.info("Transcript: %s", transcript)
                app.logger.info("Sending Transcription\n")
                ws.send(transcript)

        if data['event'] == "closed":
            app.logger.info("Closed Message received: %s", message)
            break
        transcript = transcription("mywav_reduced_noise.wav")
        if transcript is not None:
            app.logger.info("Transcript: %s", transcript)
            app.logger.info("Sending Transcription\n")
            # ws.send({"transcription": transcript})
            ws.send(transcript)
        message_count += 1

    app.logger.info(
        "Connection closed. Received a total of {} messages".format(message_count))
    audio_stream = []


async def main():
    app.logger.setLevel(logging.DEBUG)
    server = pywsgi.WSGIServer(
        ('', HTTP_SERVER_PORT), app, handler_class=WebSocketHandler)
    print("Server listening on: http://localhost:" + str(HTTP_SERVER_PORT))

    await server.serve_forever()

if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    loop.run_until_complete(main())
