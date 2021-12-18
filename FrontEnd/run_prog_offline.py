import os
from time import sleep
from typing import Dict, Optional, Type, Union
import speech_recognition as sr
import pprint
from datetime import datetime


def save_audio_to_wav(audio: sr.AudioData):

    filename: str = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    filename += ".wav"
    print(filename)
    with open(filename, "wb") as f:
        f.write(audio.get_wav_data())


def recognize_speech_from_mic(recognizer: sr.Recognizer, microphone: sr.Microphone) -> Dict[str, Union[str, bool, None]]:
    """Transcribe speech from recorded from `microphone`.

    Returns a dictionary with three keys:
    "success": a boolean indicating whether or not the API request was
                successful
    "error":   `None` if no error occurred, otherwise a string containing
                an error message if the API could not be reached or
                speech was unrecognizable
    "transcription": `None` if speech could not be transcribed,
                    otherwise a string containing the transcribed text
    """
    # check that recognizer and microphone arguments are appropriate type
    if not isinstance(recognizer, sr.Recognizer):
        raise TypeError("`recognizer` must be `Recognizer` instance")

    if not isinstance(microphone, sr.Microphone):
        raise TypeError("`microphone` must be `Microphone` instance")

    # adjust the recognizer sensitivity to ambient noise and record audio
    # from the microphone
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)
        recognizer.energy_threshold = 13000
        recognizer.dynamic_energy_threshold = True
        try:
            print("\n\nSpeak Now!\n\n")
            audio = recognizer.listen(source, timeout=1)
        except sr.WaitTimeoutError as e:
            return {"timeout": True}
        # set up the response object
    save_audio_to_wav(audio)
    response: Dict[str, Union[str, bool, None]] = {}
    response["error"] = None
    # try recognizing the speech in the recording
    # if a RequestError or UnknownValueError exception is caught,
    #     update the response object accordingly
    try:
        response["transcription"] = recognizer.recognize_google(audio)
    except sr.RequestError:
        # API was unreachable or unresponsive
        response["success"] = False
        response["error"] = "API unavailable"
    except sr.UnknownValueError:
        # speech was unintelligible
        response["error"] = "Unable to recognize speech"

    return response


def main():
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    guess = recognize_speech_from_mic(recognizer, mic)
    pprint.pprint(guess)

    if "timeout" in guess:
        print("Timed out")
        return 2
    elif guess["error"]:
        print(f"{guess['error']}")
        return 1
    if("spotify" in guess["transcription"].lower()):
        print("spotify launching")
        os.system("/usr/bin/spotify &")
    elif(guess["transcription"].lower() == "brave"):
        print("launching Brave Browser")
        os.system("/usr/bin/brave &")
    elif(guess["transcription"].lower() == "code" or guess["transcription"].lower() == "vscode"):
        print("launching Vscode")
        os.system("/usr/bin/code &")
    elif(guess["transcription"].lower() == "quit"):
        print("Quitting Program")
        return 0
    else:
        print("unknown transcription")
        print(guess["transcription"])


if __name__ == "__main__":
    print(sr.Microphone.list_microphone_names())

    main()
    print("\n\n\Finished\n\n\n")
