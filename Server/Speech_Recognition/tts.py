import pygame
from gtts import gTTS
import os

# To play audio text-to-speech during execution


def speak(my_text):
    filename = '/tmp/temp.mp3'
    # cheri south indian accent-ta/te
    # cyka blyat accent- ru
    gTTS(text=my_text, lang='ru').save(filename)
    pygame.mixer.init()
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        continue
    os.remove(filename)


speak('сука блять')
