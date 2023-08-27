# Tello Drone Control with Hand Gestures and Facial Detection

This repository contains a Python script that demonstrates the control of a DJI Tello drone using hand gestures and facial detection. The script showcases the interaction between the Tello drone's APIs and computer vision techniques for recognizing gestures and faces. The code's complexity lies in its integration of real-time video processing and communication with the drone.

## Demo Video

Check out the [demo video](https://youtu.be/lXKtBHf08Sc) to see the Tello drone control using hand gestures and facial detection.

## Overview of Components and Functionalities

### 1. Importing Libraries
The script starts by importing the necessary libraries and modules, including those for communication, computer vision, and other functionalities.

### 2. Tello_Drone Class
The `Tello_Drone` class serves as the central component that encapsulates the drone's control and interaction functionalities.

### 3. Initialization
In the `__init__` method, attributes, constants, and parameters are initialized. This setup involves creating communication sockets, defining camera settings, loading the face detection cascade classifier, and more.

### 4. Methods for Communication
- `send_command`: Sends commands to the Tello drone and receives responses.
- `send_command_no_response`: Sends commands to the drone without expecting responses.
- `parse_data_string`: Converts received data from the drone into a dictionary format.
- `receive_tello_state`: Continuously receives state data from the drone.
- `receive_tello_video`: Receives and processes the drone's video stream.

### 5. Face and Gesture Detection
- `face_detector`: Detects the largest face in video frames using the Haar cascade classifier.
- `gesture_detector`: Uses the `HandTrackingModule` to detect hand gestures.

### 6. Drawing and Display
- `draw`: Combines video frames, recognized faces, detected hand gestures, and text information to create a comprehensive display window.
- The display window includes live video feed, drone status information, and identified face and hand gestures.

### 7. Start Method
- `start`: Initializes and starts the required threads for communication, video streaming, face detection, gesture detection, and display. Additionally, it initiates the drone's takeoff and initial commands.

### 8. Speed Calculation Method
- `get_speed`: Calculates speed values for drone movement based on the chosen mode and detected gestures.

### 9. Control Method
- `control`: The main control loop where the drone's movements are influenced by detected hand gestures. Logic is implemented to analyze gestures and execute corresponding drone movements like flips, spins, or hovering.

### 10. End Method
- `end`: Terminates threads, closes sockets, and releases resources in a graceful manner.

## Languages and Tools
<p align="left"> <a href="https://opencv.org/" target="_blank" rel="noreferrer"> <img src="https://www.vectorlogo.zone/logos/opencv/opencv-icon.svg" alt="opencv" width="40" height="40"/> </a> <a href="https://www.python.org" target="_blank" rel="noreferrer"> <img src="https://raw.githubusercontent.com/devicons/devicon/master/icons/python/python-original.svg" alt="python" width="40" height="40"/> </a> <a href="https://pytorch.org/" target="_blank" rel="noreferrer"> <img src="https://www.vectorlogo.zone/logos/pytorch/pytorch-icon.svg" alt="pytorch" width="40" height="40"/> </a> </p>



*Author: Avvienash Jaganathan*
