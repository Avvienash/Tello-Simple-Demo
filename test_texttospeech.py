import pyttsx3
import threading
import time

engine = pyttsx3.init()
talk = True
on = True

# def t():
#     while on:
#      engine.runAndWait()
#      time.sleep(1)

# thread = threading.Thread(target=t)
# thread.daemon = True
# thread.start()


for i in range(100):
    time.sleep(1)
    print(i)
    engine.say(str(i))
    engine.runAndWait()
