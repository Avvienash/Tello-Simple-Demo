#Name : Winter Drone Project

# import libraries
import threading
import socket
import sys
import time
import cv2
import numpy as np
import av
import subprocess
import select
import cv2
from cvzone.HandTrackingModule import HandDetector  
import os
import datetime
import pyttsx3
import win32com.client




class Tello_Drone:
    
    def __init__(self):
        
        #TO Clear pott: netstat -ano | findstr :9000   
        command = 'netstat -ano | findstr :9000'
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        command = 'netstat -ano | findstr :8889'
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        command = 'netstat -ano | findstr :11111'
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        
        #Setup 
        self.tello_address = ('192.168.10.1', 8889)
        self.tello_state_address = ('192.168.10.1', 8890)
        
        # Create a UDP socket for send and receive responses
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('', 9000))
        self.sock.setblocking(0)
        
        self.state_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.state_socket.bind(('0.0.0.0', 8890))
        
        #Threads
        self.state_thread = None
        self.vs_thread = None
        self.fd_thread  = None
        self.d_thread = None
        self.gd_thread = None
        self.sp_thread = None
        
        # FPS
        self.vs_thread_prev_time = 0
        self.vs_thread_curr_time = 0
        self.d_thread_prev_time = 0
        self.d_thread_curr_time = 0

        
        # Video Stream
        self.udp_link_vs = "udp://@0.0.0.0:11111"
        self.timeout_vs = (5, None)
        self.fifo_size = 5000000
         
        # Define vaiable
        self.STATE = {}
        self.FACE = (None,None,None,None)
        self.hand = (None,None,None,None)
        self.FRAME = None
        self.CANVAS = np.zeros((760, 1500,3), dtype=np.uint8)
        self.ON = False
        self.fingerup= [None, None, None, None, None]
        self.display_text = ""
        
        # Define constants
        
        # video Stream
        self.vs_scale = 1
        self.image_height = 720//self.vs_scale
        self.image_width = 960//self.vs_scale
        
        # draw constants
        self.canvas_background_colour = (135,107,23)
        self.state_background_colour = (197,204,100)
        self.text_color = (255, 255, 255)  # White color (BGR format)
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.8
        self.font_thickness = 2
        self.line_spacing = 50
        

        
        # Face Detection Setup
        self.face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')   
        
        # hand detector setup
        self.hand_detector = HandDetector(maxHands=1,detectionCon=0.85)
        
        #Speech Sythesis Setup
        self.speaker = win32com.client.Dispatch("SAPI.SpVoice")
        self.speech = ""
        self.speaker.Rate = 0
        self.speaker.Speak("Starting ")

            
    def speak(self):
        
        while self.ON:
            
            if self.speech == "":
                time.sleep(0.1)
                continue
            
            
            temp = self.speech
            self.speech = ""
            self.speaker.Speak(temp)
            self.speaker.Rate = 0
            
            
            
        

    # Function to send commands to Tello and receive responses
    def send_command(self,command):
        msg = command.encode(encoding="utf-8")

        sent = self.sock.sendto(msg, self.tello_address)
        ready = select.select([self.sock], [], [], 30)
        if ready[0]:
            data, server = self.sock.recvfrom(4096)
        
        try:   
            response = data.decode(encoding="utf-8")
        except:
            print(command + ": Decode Error" )
            return "error"
        
        print(command + ": " + str(response))
        return response  
    
    # Function to send commands to Tello and dont receive responses
    def send_command_no_response(self,command):
        msg = command.encode(encoding="utf-8")
        sent = self.sock.sendto(msg, self.tello_address)
        print(command)
    
    # Function to convert to Dictionary
    def parse_data_string(self,data_string):
        data_dict = {}
        
        # Split the data string into key-value pairs
        data_pairs = data_string.strip().split(';')
        data_pairs = data_pairs[0:-1]
        # Process each key-value pair
        for pair in data_pairs:
            # Split the pair into key and value
            key, value = pair.split(':')
            key = key.strip()
            value = value.strip()
            
            # Check if the value is an integer or float
            if value.isdigit():
                data_dict[key] = int(value)
            elif '.' in value:
                data_dict[key] = float(value)
            else:
                data_dict[key] = value
        
        return data_dict
    
    
    def receive_tello_state(self):
        while self.ON:
            data, _ = self.state_socket.recvfrom(1024)
            self.STATE = self.parse_data_string(data.decode('utf-8'))


            
    
    def receive_tello_video(self):
        
        container = av.open(f"{self.udp_link_vs}?fifo_size={self.fifo_size}", timeout=self.timeout_vs)
        
        while self.ON:
            
            
            for frame in container.decode(video=0):
                
                self.vs_thread_prev_time = self.vs_thread_curr_time
                self.vs_thread_curr_time = time.time()
        
                try:
                    temp = np.array(frame.to_image())
                    temp = cv2.resize(temp, (self.image_width, self.image_height))
                    self.FRAME = cv2.cvtColor(temp, cv2.COLOR_RGB2BGR)
                    
                    if self.ON == False:
                        break
                except av.AVError:
                    print("AVError")
                    self.vs_thread_prev_time = time.time()
                    self.vs_thread_curr_time = time.time()
                    
            container.close()

    def face_detector(self):
        
        while self.ON:

            if (self.FRAME is not None):

                gray = cv2.cvtColor(self.FRAME, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
                
                # Find the largest face
                largest_face = (None,None,None,None)
                largest_area = 0
                for (x, y, w, h) in faces:
                    area = w * h
                    if area > largest_area:
                        largest_area = area
                        largest_face = (x, y, w, h)
                
                self.FACE = largest_face
                
    def gesture_detector(self):
        
        while self.ON:
            
            
            if (self.FRAME is not None):
                hand = self.hand_detector.findHands(self.FRAME, draw=False)
                if hand:
                    lmlist = hand[0] 
                    if lmlist:
                        self.fingerup = self.hand_detector.fingersUp(lmlist)
                        self.hand = lmlist['bbox']
                        continue
            
            self.hand = (None,None,None,None)
            self.fingerup = [None, None, None, None, None]
                
    def draw(self):
        while self.ON:
            
            #FPS
            self.d_thread_prev_time = self.d_thread_curr_time
            self.d_thread_curr_time = time.time()
            
            
            # background Colour
            self.CANVAS[:,:,:] = self.canvas_background_colour
            
            # Text:
            self.CANVAS[20:740,1000:1480,:] = self.state_background_colour

            # Set text positions
            start_x = 1020
            start_y = 60

            # Calculate FPS for vs
            if self.vs_thread_curr_time != self.vs_thread_prev_time:
                vs_fps = round( 1 / (self.vs_thread_curr_time - self.vs_thread_prev_time))
            else:
                vs_fps = 0

            # Calculate FPS for d
            if self.d_thread_curr_time != self.d_thread_prev_time:
                d_fps = round( 1 / (self.d_thread_curr_time - self.d_thread_prev_time) )
            else:
                d_fps = 0

            # Set text content
            text_lines = [
                "Battery: " + str(self.STATE['bat']) + " %",
                "Height: " + str(self.STATE['h']) + " cm",
                "Face: " + str(self.FACE),
                "Hand: " + str(self.fingerup),
                "FPS (VS): " + str(vs_fps) + " FPS",
                "FPS (Vis): " + str(d_fps) + " FPS"
            ]

            # Loop through text lines and print on the canvas
            for i, line in enumerate(text_lines):
                text_position = (start_x, start_y + i * self.line_spacing)
                cv2.putText(self.CANVAS, line, text_position, self.font, self.font_scale, self.text_color, self.font_thickness)

            cv2.putText(self.CANVAS, self.display_text, (1010,600), self.font, 3, (0, 0, 0), 8)
            
            temp = np.copy(self.FRAME)
            
            if self.FACE[0] is not None:
                (x, y, w, h) = self.FACE
                cv2.rectangle(temp, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.circle(temp, (x+w//2, y + h//2), 5, (0, 0, 255), -1)
                cv2.line(temp,(x+w//2, y + h//2), (self.image_width//2,self.image_height//2),(0, 255, 0), 2)
                
            if self.hand[0] is not None:
                (x, y, w, h) = self.hand
                cv2.rectangle(temp, (x, y), (x + w, y + h), (255,0, 0), 2)
                cv2.circle(temp, (x+w//2, y + h//2), 8, (255, 0, 0), -1)
        
            self.CANVAS[20:(20+self.image_height),20:(20+self.image_width),:] = temp
            cv2.imshow('Tello EDU',self.CANVAS)
            cv2.waitKey(1)
        
        
    def start(self):
        
       
        self.ON = True
        self.display_text = "STARTING"
        
        # Create and start the thread for speech synthesis
        self.sp_thread = threading.Thread(target=self.speak)
        self.sp_thread.daemon = True
        self.sp_thread.start()
        
        
        
         ## Connect to tello
        response = self.send_command("command")
        if response == "error":
            print("Exiting")
            return False
        
        # Create and start the thread to receive Tello state data
        self.state_thread = threading.Thread(target=self.receive_tello_state)
        self.state_thread.daemon = True
        self.state_thread.start()
        
        
        ## Connect to tello vs
        response = self.send_command("streamon")
        if response == "error":
            print("Exiting")
            return False
        
        
        # Create and start the thread to receive Tello state data
        print("Start VS Thread")
        self.vs_thread = threading.Thread(target=self.receive_tello_video)
        self.vs_thread.daemon = True
        self.vs_thread.start()
        
        print("Wait for Video (10s)")
        self.speech = "Waiting for Video"
        time.sleep(10)
        
        
        # Create and start the thread to receive face detection
        print("Start Face Detecting Thread")
        self.fd_thread = threading.Thread(target=self.face_detector)
        self.fd_thread.daemon = True
        self.fd_thread.start()
        
        print("Start Hand Detecting Thread")
        self.gd_thread = threading.Thread(target=self.gesture_detector)
        self.gd_thread.daemon = True
        self.gd_thread.start()
        
        
        # Create and start the thread to receive face detection
        print("Start Draw Thread")
        self.d_thread = threading.Thread(target=self.draw)
        self.d_thread.daemon = True
        self.d_thread.start()
        
        print(self.STATE['bat'])
        if self.STATE['bat'] < 50:
            print("Low Battery. Abort")
            return False
        
        self.speech = "Taking off"
        response = self.send_command("takeoff")
        if response == "error":
            print("Exiting")
            return False
        
        self.speech = "getting to height"
        response = self.send_command("up 10")
        if response == "error":
            print("Exiting")
            return False
        
        return True
        
    def get_speed(self,mode):
        
        if mode == "hand_follow":
            
            
            if self.fingerup == [1,1,1,1,1]:
                
                (x, y, w, h) = self.hand

                target_x = (x+w/2) - (self.image_width/2)
                target_y = (self.image_height/2) - (y+h/2) - 30
                target_z =  300 - h
                
                up_speed = np.clip( np.floor(np.sign(target_y)*(target_y*2/self.image_width)**2 * 150) , -50, 50)
                yaw_speed = 0
                side_speed = np.clip( np.floor(np.sign(target_x)*(target_x*2/self.image_width)**2 * 45 ), -50, 50)
                front_speed = np.clip( np.floor(np.sign(target_z)*(target_z*2/self.image_width)**2 * 250) , -50, 70)
                
                return side_speed, front_speed, up_speed, yaw_speed
                    
            
            if self.fingerup == [0,0,0,0,0]:
                
                (x, y, w, h) = self.hand
                target_x = (x+w/2) - (self.image_width/2)
                yaw_speed = np.clip( np.floor(np.sign(target_x)*(target_x*2/self.image_width)**2 * 200 ), -60, 60)
                    
                return 0, 0, 0, yaw_speed
            
            
            return 0,0,0,0
                
        
        if (self.FACE[0] == None):
            target_x = 0
            target_z = None
            target_y = None

        else:
            (x, y, w, h) = self.FACE

            target_x = (x+w/2) - (self.image_width/2)
            target_y = (self.image_height/2) - (y+h/2)
            target_z = 250-h
            
            
            
            
        
        match mode:
            case "yaw":
                fixed_h = 145
                up_speed = np.floor( (np.clip(fixed_h-self.STATE['h'],-50,50))/50 * 100)
                yaw_speed = np.clip( np.floor(np.sign(target_x)*(target_x*2/self.image_width)**2 * 250 ), -100, 100)
                side_speed = 0
                front_speed = 0
                
            case "yaw_y":
                if target_y != None:
                    up_speed = np.clip( np.floor(np.sign(target_y)*(target_y*2/self.image_width)**2 * 500) , -60, 30)
                else:
                    up_speed = 0
                yaw_speed = np.clip( np.floor(np.sign(target_x)*(target_x*2/self.image_width)**2 * 250 ), -100, 100)
                side_speed = 0
                front_speed = 0
                
            case "xy":
                if target_y != None:
                    up_speed = np.clip( np.floor(np.sign(target_y)*(target_y*2/self.image_width)**2 * 500) , -60, 30)
                else:
                    up_speed = 0
                yaw_speed = 0
                side_speed = np.clip( np.floor(np.sign(target_x)*(target_x*2/self.image_width)**2 * 60 ), -50, 50)
                front_speed = 0
                
            case "yaw_xy":
                if target_y != None:
                    up_speed = np.clip( np.floor(np.sign(target_y)*(target_y*2/self.image_width)**2 * 500) , -60, 30)
                else:
                    up_speed = 0
                yaw_speed = np.clip( np.floor(np.sign(target_x)*(target_x*2/self.image_width)**2 * 250 ), -100, 100)
                side_speed = np.clip( np.floor(np.sign(target_x)*(target_x*2/self.image_width)**2 * 60 ), -50, 50)
                front_speed = 0
                
            case "yaw_yz":
                if target_y != None:
                    target_y = target_y - 70
                    up_speed = np.clip( np.floor(np.sign(target_y)*(target_y*2/self.image_width)**2 * 300) , -60, 30)
                else:
                    up_speed = 0
                yaw_speed = np.clip( np.floor(np.sign(target_x)*(target_x*2/self.image_width)**2 * 250 ), -100, 100)
                side_speed = 0
                if target_z != None:
                    front_speed = np.clip( np.floor(np.sign(target_z)*(target_z*2/self.image_width)**2 * 500) , -20, 20)
                else:
                    front_speed = 0
            
            
            
            case default:
                print("ERROR: Invalid Mode")
                up_speed = 0
                yaw_speed = 0
                side_speed = 0
                front_speed = 0
                
            
        
        return side_speed, front_speed, up_speed, yaw_speed
        
        
    def control(self,mode):
        
        try:
            time_start_gesture = time.time()

            
            self.speech = "Ready"            
            while True:
                               
                (side_speed, front_speed, up_speed, yaw_speed) = self.get_speed(mode)
                
                if self.STATE['h'] > 190 or self.STATE['h'] < 30 :
                    up_speed = 0

                # Hand Commands:
                match self.fingerup:
                    
                    case [0,1,1,1,1]: # FLIP
                        text = "FLIP in " + str(6 - round(time.time() -time_start_gesture) )
                        self.display_text = text
                        up_speed = 0
                        yaw_speed= 0
                        self.speaker.Rate = 8
                        self.speech = str(6 - round(time.time() -time_start_gesture) )
                        
                        if (time.time() -time_start_gesture)> 5 :
                            self.display_text = "FLIP NOW"
                            self.speech = "Flip"
                            self.send_command("stop")
                            time.sleep(1)
                            self.send_command("flip f")
                            time.sleep(3)
                            time_start_gesture = time.time()
                            continue
                        
                    case [0,1,1,1,0]: # spin
                        text = "SPIN in " + str(3 - round(time.time() -time_start_gesture) )
                        self.display_text = text
                        up_speed = 0
                        yaw_speed= 0
                        self.speaker.Rate = 8
                        self.speech = str(3 - round(time.time() -time_start_gesture) )
                        
                        if (time.time() -time_start_gesture)> 2:
                            self.display_text = "SPIN NOW"
                            self.speech = "Spining 360 degrees"
                            self.send_command("stop")
                            time.sleep(1)
                            self.send_command("cw 360")
                            time.sleep(4)
                            time_start_gesture = time.time()
                            continue
                    
                    case [0,1,1,0,0]: # pic
                        text = "PIC in " + str(3 - round(time.time() -time_start_gesture) )
                        self.display_text = text
                        up_speed = 0
                        yaw_speed= 0
                        self.speaker.Rate = 8
                        self.speech = str(3 - round(time.time() -time_start_gesture) )
                        
                        if (time.time() -time_start_gesture)> 2 :
                            self.display_text = "SMILE"
                            self.speech = "Picture"
                            self.send_command("stop")
                            # Generate a unique filename using current timestamp
                            timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
                            image_filename = f'image_{timestamp}.jpg'
                            image_path = os.path.join("images", image_filename)
                            
                            cv2.imwrite(image_path, self.FRAME)
                            time.sleep(1)
                            time_start_gesture = time.time()
                            continue
                        
                    case [0,1,0,0,0]: # landing
                        self.display_text = "EMERGENCY"
                        up_speed = 0
                        yaw_speed= 0
                        
                        if (time.time() -time_start_gesture)> 0.4 :
                            self.display_text = "STOP"
                            time_start_gesture = time.time()
                            self.speech = "Stop"
                            break
                    
                    case default:
                        time_start_gesture = time.time()
                        self.display_text = "ON"
                    
                

                    
                    
                self.send_command_no_response(f"rc {side_speed} {front_speed} {up_speed} {yaw_speed}")    
                time.sleep(0.001)

        except KeyboardInterrupt:
            print("keyboard interupt")           
            
        
        response = self.send_command("land")
        if response == "error":
            print("Exiting")
            return
        
        return

    def end(self):
        
        
        self.speaker.Speak("Mission Complete")
        self.ON = False
        print("Joining state thread...")
        self.state_thread.join()
        print("Joining video stream thread...")
        self.vs_thread.join()
        print("Joining face detector thread...")
        self.fd_thread.join()
        print("Joining draw thread...")
        self.d_thread.join()
        print("Joining speech thread...")
        self.sp_thread.join()
        
        print("Closing socket...")
        self.sock.close()
        print("Closing state socket...")
        self.state_socket.close()
        
        print("Closing OpenCV windows...")
        cv2.destroyAllWindows()
        
        print("battery level: ")
        print(self.STATE['bat'])



tt = Tello_Drone()

if tt.start():
    tt.control("hand_follow")
tt.end()

sys.exit(0)
            
        
        

         
        
        

                
                
