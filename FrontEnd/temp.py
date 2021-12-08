import speech_recognition as sr
for index, name in enumerate(sr.Microphone.list_microphone_names()):
    print("Microphone with name \"{1}\" found for `Microphone(device_index={0})`".format(
        index, name))
mic = sr.Microphone(device_index=6)
r = sr.Recognizer()


# print(mic.list_microphone_names())
with sr.Microphone(device_index=6) as source:
    r.adjust_for_ambient_noise(source)
    r.energy_threshold = 4103.52773393966
    r.dynamic_energy_threshold = True
    audio = r.listen(source, timeout=5, phrase_time_limit=5)
text = r.recognize_google(audio)
print(text)
