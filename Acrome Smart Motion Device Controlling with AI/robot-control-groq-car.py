import sys
import requests
import os
import json
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QLabel, QTextEdit, QPushButton, QWidget, QMessageBox, QLineEdit,QDialog
from PyQt6.QtCore import Qt,QTimer
from PyQt6.QtGui import QFont
from groq import Groq
import time
import wave
import threading
import pyaudio
APIKEY = None
api_key_file = "api_key.txt"
def get_api_key_from_file():
   
    if os.path.exists(api_key_file):
        with open(api_key_file, 'r') as file:
            return file.read().strip()
    return None

def get_api_key_from_app():
    
    dialog = APIKeyDialog()
    dialog.exec()  
    return dialog.api_key

def get_groq_client():
    
    global APIKEY
    if not APIKEY:
        APIKEY = get_api_key_from_file()  
    if APIKEY is not None:
        return Groq(api_key=APIKEY)
    else:
        raise ValueError("API Key is missing!")
robotip = "http://127.0.0.1:5000/execute" # For Local.  You should change it.  You use your raspberry Pi Ip.

def init_robot(cm: int = 0):
    out = requests.post(robotip, json={"id": "0"})
    data = out.json()
    return data

def linear_movement(cm: int = 0, speed: int = 30):
    out = requests.post(robotip, json={"id": "1", "cm": cm, "speed": speed})
    data = out.json()
    return data

def turn_left(degree: int = 90, rotation_speed: int = 30):
    out = requests.post(robotip, json={"id": "2", "degree": degree, "rotation_speed": rotation_speed})
    data = out.json()
    return data
def turn_right(degree: int=90,rotation_speed: int=30):
    out = requests.post(robotip, json={"id": "3", "degree": degree, "rotation_speed": rotation_speed})
    data = out.json()
    return data
def radial_movement(radius: int, degree: int):
    out = requests.post(robotip, json={"id": "4", "radius": radius, "degree": degree})
    data = out.json()
    return data
def distance_movement(cm: int=15):
    out = requests.post(robotip,json={"id":"5","cm":cm})
    data = out.json()
    return data
def stop():
    out = requests.post(robotip,json={"id":"6"})
    data = out.json()
    return data
function_instructions = """
You are a robot control assistant. For each question, you should return a JSON object in the following format:
[
    {
        "function": "function_name",
        "parameters": {
            "parameter1": value1,
            "parameter2": value2
        }
    }
]

Available functions:
1. init_robot - Initializes the robot's position. No parameters.
2. linear_movement - Moves the robot a specified distance in cm. If user dont write speed you should use default value. (default value is:30)\n
    - Parameters: cm (int) - Distance to move in cm, speed (int)\n
3. turn_left - Turns the robot a specified degree counterclockwise (left). If the user doesn't write speed, you should use the default value (default value is: 30).\n
    - Parameters: degree (int) - Degree to turn, rotation_speed (int)\n
4. turn_right - Turns the robot a specified degree clockwise (right). If the user doesn't write speed, you should use the default value (default value is: 30).\n
    - Parameters: degree (int) - Degree to turn, rotation_speed (int)\n
5. radial_movement - Moves the robot along a circular path with a given radius and angle.\n
    - Parameters: radius (int), degree (int)\n
6. distance_movement -If you encounter an obstacle while moving straight ahead, let it follow the other function. Eg: For example, turn right function when approaching 20 cm\n
    - Parameters: cm(int)\n
7. stop - Stop the robot. No parameters.
NOTE: The first function have to be `init_robot`. Other functions will come after init_robot function.\n
NOTE: Understand the prompt given by the user\n
"""

def get_groq_response(prompt):
    client = get_groq_client()  # Client'ı alıyoruz
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}, {"role": "system", "content": function_instructions}]
    )

    try:
        content = response.choices[0].message.content
    except (AttributeError, json.JSONDecodeError) as e:
        QMessageBox.critical(None, "Error", f"Error parsing response: {e}")
        return None

    return content

def execute_function(response):
    for func_call in response:
        function = func_call["function"]
        parameters = func_call["parameters"]
        try:
            if function == "init_robot":
                init_robot()
            elif function == "linear_movement":
                linear_movement(parameters.get("cm", 0), parameters.get("speed", 30))
            elif function == "turn_left":
                turn_left(parameters.get("degree", 90), parameters.get("rotation_speed", 30))
            elif function=="turn_right":
                turn_right(parameters.get("degree", 90), parameters.get("rotation_speed", 30))
            elif function == "radial_movement":
                radial_movement(parameters.get("radius", 0), parameters.get("degree", 0))
            elif function== "distance_movement":
                distance_movement(parameters.get("cm",15))
            elif function =="stop":
                stop()
            else:
                raise ValueError("Unknown function")
        except Exception as e:
            QMessageBox.critical(None, "Error", f"Error during execution: {e}")
            return False
    return True





class RobotControlApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Robot Control Assistant")
        self.setMinimumSize(400, 600)
        self.setStyleSheet("background-color: #f0f0f0;")
        self.check_api_key()

        self.is_recording = False
        self.audio_file = "recorded_audio.wav"
        self.fs = 44100
        self.frames = []  
        self.recording_thread = None  
        self.recording_timer = None 
        
    
        

    def init_ui_qna(self):
        layout = QVBoxLayout()


        title_label = QLabel("Robot Control Assistant")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #333333;")
        layout.addWidget(title_label)

        self.qna_input = QTextEdit(self)
        self.qna_input.setPlaceholderText("Command me something about the robot...")
        self.qna_input.setStyleSheet("font-size: 14px; padding: 10px;")
        layout.addWidget(self.qna_input)

        self.voice_button = QPushButton("Start Voice Recording", self)
        self.voice_button.setStyleSheet("""background-color: #008CBA; color: white; font-size: 16px; padding: 10px; border-radius: 5px;""")
        self.voice_button.clicked.connect(self.toggle_recording)
        layout.addWidget(self.voice_button)

        self.response_display = QTextEdit(self)
        self.response_display.setPlaceholderText("Robot's response will appear here...")
        self.response_display.setReadOnly(True)
        self.response_display.setStyleSheet("font-size: 14px; padding: 10px; background-color: #e9e9e9;")
        layout.addWidget(self.response_display)

        self.response_time_label = QLabel("Response time: 0.00 seconds")
        self.response_time_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.response_time_label.setStyleSheet("font-size: 12px; color: #555555;")
        layout.addWidget(self.response_time_label)

        self.ask_button = QPushButton("Command", self)
        self.ask_button.setStyleSheet("""background-color: #008CBA; color: white; font-size: 16px; padding: 10px; border-radius: 5px;""")
        self.ask_button.clicked.connect(self.ask_robot)
        layout.addWidget(self.ask_button)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def toggle_recording(self):
        """Start/Stop Voice Record"""
        if self.is_recording:
            self.stop_recording()
            self.voice_button.setText("Start Recording")
        else:
            self.start_recording()
            self.voice_button.setText("Stop Recording")  


    def start_recording(self):
        """Start Recording"""
        self.is_recording = not self.is_recording  
        self.frames = []  
        self.stop_recording_event = threading.Event() 
        self.recording_thread = threading.Thread(target=self.record_audio)
        self.recording_thread.start()

    def record_audio(self):
        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=self.fs, input=True, frames_per_buffer=1024)

        while not self.stop_recording_event.is_set():  
            data = stream.read(512)
            self.frames.append(data)

        stream.stop_stream()
        stream.close()
        p.terminate()
  

    def audio_callback(self, indata, frames, time, status):
        """Add Frames to buffer"""
        if status:
            print(status, file=sys.stderr)
        if len(indata) > 0:
            self.frames.append(indata)  

    def stop_recording(self):
        """Stop Recording"""
        self.is_recording = not self.is_recording
        if self.recording_thread is not None:
            self.stop_recording_event.set()  

        if self.frames:
            with wave.open(self.audio_file, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
                wf.setframerate(self.fs)
                wf.writeframes(b''.join(self.frames))
        
        
        if self.recording_thread is not None:
            self.recording_thread.join()
            self.recording_thread = None
            self.convert_audio_to_text(self.audio_file)

    def ask_robot(self):
        
        self.response_display.setText("")
        self.response_time_label.setText("Response time: 0.00 seconds")
        user_input = self.qna_input.toPlainText().strip()
        if not user_input:
            QMessageBox.warning(self, "Warning", "Please enter a Command.")
            return

        start_time = time.time()
        prompt = f"User asked: {user_input}\nRespond appropriately."
        response = get_groq_response(prompt)
        response_json=json.loads(response)
        if response:
            elapsed_time = time.time() - start_time
            execute_function(response_json)
            self.response_time_label.setText(f"Response time: {elapsed_time:.2f} seconds")
            self.response_display.setText("Motion Device is running...")
        else:
            QMessageBox.warning(self, "Error", "Failed to get a response from the robot.")
        self.qna_input.clear()

    def convert_audio_to_text(self, wav_file):
        
        with open(wav_file, "rb") as file:
            client12 = get_groq_client()
            transcription = client12.audio.transcriptions.create(
                file=(wav_file, file.read()),
                model="whisper-large-v3-turbo",
                response_format="verbose_json",
            )
            self.qna_input.setText(transcription.text)

    def check_api_key(self):
        self.api_key = get_api_key_from_file()
        if self.api_key:
            self.show_qna_screen() 
        else:
            self.show_api_key_input_screen()

    def show_api_key_input_screen(self):
        self.setWindowTitle("API Key Input")
        self.init_ui_api_key()

    def show_qna_screen(self):
        self.setWindowTitle("Robot Control Assistant")
        self.init_ui_qna()


    def init_ui_api_key(self):
        layout = QVBoxLayout()

        # Başlık
        title_label = QLabel("Enter Your API Key")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #333333;")
        layout.addWidget(title_label)

        # API Key girişi
        self.api_key_input = QLineEdit(self)
        self.api_key_input.setPlaceholderText("Enter your API key here...")
        self.api_key_input.setStyleSheet("font-size: 14px; padding: 10px;")
        layout.addWidget(self.api_key_input)

        # Kaydetme butonu
        self.save_button = QPushButton("Save API Key", self)
        self.save_button.setStyleSheet("""background-color: #008CBA; color: white; font-size: 16px; padding: 10px; border-radius: 5px;""")
        self.save_button.clicked.connect(self.save_api_key)
        layout.addWidget(self.save_button)

        
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def save_api_key(self):
        api_key = self.api_key_input.text().strip()
        if not api_key:
            QMessageBox.warning(self, "Warning", "Please enter a valid API key.")
            return

        
        with open(api_key_file, 'w') as file:
            file.write(api_key)

        self.api_key = api_key
        QMessageBox.information(self, "Success", "API Key saved successfully!")
        self.show_qna_screen()  

class APIKeyDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enter API Key")
        self.setMinimumSize(400, 200)

        self.api_key_input = QLineEdit(self)
        self.api_key_input.setPlaceholderText("Enter your API key here...")

        self.save_button = QPushButton("Save API Key", self)
        self.save_button.clicked.connect(self.save_api_key)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Please enter your API key:"))
        layout.addWidget(self.api_key_input)
        layout.addWidget(self.save_button)
        self.setLayout(layout)

        self.api_key = None

    def save_api_key(self):
        
        self.api_key = self.api_key_input.text().strip()
        if self.api_key:
            self.accept()  
        else:
            QMessageBox.warning(self, "Warning", "Please enter a valid API key.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RobotControlApp()
    window.show()
    sys.exit(app.exec())
