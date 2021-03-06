import pyaudio
import base64
import json
import logging
import asyncio
from datetime import datetime
import time
import wave
from flask import Flask
from flask_sockets import Sockets
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
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
    # if((int(time.time())-STARTED_TIME) % 2 == 0):
    text = try_transcription(filename, SAMPLE_RATE)
    app.logger.info("TRANSCRIPTION: %s\n" % text)
    return text
    return None


def save_audio_to_wav(audio_stream, file):
    # frames = [audio]
    try:
        filename = file
        # print(filename)

        with wave.open(filename, "wb") as f:
            try:
                f.setnchannels(CHANNELS)
                f.setsampwidth(SAMPLE_SIZE)
                f.setframerate(SAMPLE_RATE)
                f.writeframes(b''.join(audio_stream))
            except KeyboardInterrupt:
                f.close()
        file = filename
        return filename
    except KeyboardInterrupt:
        app.logger.info("\nInterrupted by user\n\n\n")


@sockets.route('/media')
def echo(ws):
    global CHANNELS, SAMPLE_RATE, FRAMES_PER_BUFFER, SAMPLE_SIZE, audio_stream
    app.logger.info("Connection accepted")
    # A lot of messages will be sent rapidly. We'll stop showing after the first one.
    has_seen_media = False
    message_count = 0
    ws.send("Hello")
    while not ws.closed:
        message = ws.receive()
        global STARTED_TIME
        STARTED_TIME = int(time.time())
        if message is None:
            # TODO: instead of continue do some transcript
            app.logger.info("No message received...")
            if not message_count:
                continue
            else:
                if transcript is not None:
                    app.logger.info(f"Transcript: {transcript}")
                    app.logger.info(f"Sending Transcription\n")
                    # ws.send({"transcription": transcript})
                try:
                    ws.send(transcript)
                except Exception:
                    continue
        app.logger.info(f"Message received: {message[:10]}")

        # Messages are a JSON encoded string
        data = json.loads(message)
        app.logger.info(f"data received")

        # Using the event type you can determine what type of message you are receiving
        if data['event'] == "connected":
            app.logger.info("Connected Message received: {}".format(message))
        if data['event'] == "start":
            app.logger.info("Start Message received: {}".format(message))
        if data['event'] == "media":

            if not has_seen_media:
                app.logger.info("Media message: {}".format(message))
                payload = data['media']['payload']
                app.logger.info("Payload is: {}".format(payload))
                chunk = base64.b64decode(payload)
                app.logger.info("That's {} bytes".format(len(chunk)))
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
            transcript = transcription("temp.wav")
            if transcript is not None:
                app.logger.info(f"Transcript: {transcript}")
                app.logger.info(f"Sending Transcription\n")
                # ws.send({"transcription": transcript})
                ws.send(transcript)

        if data['event'] == "closed":
            app.logger.info("Closed Message received: {}".format(message))
            break
        transcript = transcription("temp.wav")
        if transcript is not None:
            app.logger.info(f"Transcript: {transcript}")
            app.logger.info(f"Sending Transcription\n")
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
