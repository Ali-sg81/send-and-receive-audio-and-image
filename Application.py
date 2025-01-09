import cv2
import socket
import threading
import sys
import os
import time
import pyaudio
import wave
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt

class CombinedApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(640, 480)
        self.move(800, 500)

        # Layout for stacking widgets
        layout = QVBoxLayout(self)

        # Button layout for mode selection
        button_layout = QVBoxLayout(self)
        self.client_button = QPushButton("Client Mode")
        self.client_button.clicked.connect(self.start_client)
        button_layout.addWidget(self.client_button)

        self.server_button = QPushButton("Server Mode")
        self.server_button.clicked.connect(self.start_server)
        button_layout.addWidget(self.server_button)
        layout.addLayout(button_layout)

        # Additional UI elements will be hidden initially
        self.webcam_label = QLabel() # Hidden initially
        self.webcam_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.webcam_label)
        self.webcam_label.hide()

        button_layout2 = QVBoxLayout()
        self.capture_button = QPushButton("Capture Image")  # Hidden initially
        self.capture_button.clicked.connect(self.capture_image)
        button_layout2.addWidget(self.capture_button)
        self.capture_button.setEnabled(False) 
        self.capture_button.hide()
        
        self.send_button = QPushButton("Send Image")  # Hidden initially
        self.send_button.clicked.connect(self.send_image)
        button_layout2.addWidget(self.send_button)
        self.send_button.setEnabled(False)
        self.send_button.hide()
        
        layout.addLayout(button_layout2)
        
        # Recording related variables
        button_layout3 = QVBoxLayout()
        self.record_button = QPushButton("Record Audio")
        self.record_button.clicked.connect(self.start_record)
        # self.record_button.setEnabled(False)  # Initially disabled
        button_layout3.addWidget(self.record_button)
        self.record_button.hide()  # Hidden initially
        self.recording = False
        self.recorded_audio = None
        
        self.send_button2 = QPushButton("Send Audio")  # Hidden initially
        self.send_button2.clicked.connect(self.send_audio)
        button_layout3.addWidget(self.send_button2)
        self.send_button2.setEnabled(False)
        self.send_button2.hide()
        
        layout.addLayout(button_layout3)

        # Initial message label
        self.message_label = QLabel("Select Mode:")
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.adjustSize()
        layout.addWidget(self.message_label)
        

        self.image = None
        self.server_ip = "192.168.170.116"
        self.server2 = "192.168.170.190"
        self.image_port = 9999  # Port for sending images
        self.audio_port = 9988  # Port for sending audio
        self.image_port2 = 4444  # Port for sending images
        self.audio_port2 = 4433  # Port for sending audio
        self.running = False  # Flag to control loop termination (client)
        self.image_dir = "captured_images"  # Local directory for saving images
        self.audio_dir = "recorded_audios"  # Local directory for saving audio
        self.received_image_dir = "received_image" # Local directory for resived images
        self.received_audio_dir = "received_audio" # Local directory for resived audio
        self.last_image = None
        self.server_public_ip = None 

        self.setLayout(layout)
        self.setWindowTitle("Client-Server Communication")
        self.show()

    def start_client(self):
        # Hide buttons
        # self.server_button.hide()
        self.message_label.hide()
        self.client_button.hide()

        # Show client mode UI elements
        self.webcam_label.show()
        self.capture_button.show()
        self.send_button.show()
        self.message_label.setText('To take picture press "capture image" button')
        self.message_label.show()
        self.record_button.show()
        self.send_button2.show()
        

        # Start client functionality
        self.capture_thread = threading.Thread(target=self.capture_and_display)
        self.capture_thread.start()
        self.running = True  # Set flag for capture loop

    def start_server(self):
        # Hide buttons
        self.server_button.hide()
        # self.client_button.hide()
        
        # Change message
        # self.server_public_ip = self.get_public_ip()
        # self.server_ip = self.get_local_ip()

        # Start server functionality
        self.server_thread = threading.Thread(target=self.run_server)
        self.server_thread.start()
        self.running = True  # Set flag for capture loop

    def closeEvent(self, event):  # Handle window closing
        if self.running:
            self.running = False
        event.accept()
        print("Window Closed!")

        # Delete all files in image directory 
        if os.path.exists(self.image_dir): 
            for filename in os.listdir(self.image_dir):
                filepath = os.path.join(self.image_dir, filename)
                os.remove(filepath)
            print("Image directory cleared!")

        # Delete all files in received image directory
        if os.path.exists(self.received_image_dir): 
            for filename in os.listdir(self.received_image_dir):
                filepath = os.path.join(self.received_image_dir, filename)
                os.remove(filepath)
            print("Received Image directory cleared!")
            
        # Delete all files in audio directory 
        if os.path.exists(self.audio_dir): 
            for filename in os.listdir(self.audio_dir):
                filepath = os.path.join(self.audio_dir, filename)
                os.remove(filepath)
            print("Audio directory cleared!")
            
        # Delete all files in resived audio directory 
        if os.path.exists(self.received_audio_dir): 
            for filename in os.listdir(self.received_audio_dir):
                filepath = os.path.join(self.received_audio_dir, filename)
                os.remove(filepath)
            print("Audio directory cleared!")

    #=====================================================================================
    #               Server code
    #=====================================================================================
    
    def run_server(self):
        
        HOST = self.server2
        image_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        image_server.bind((HOST, self.image_port2))
        image_server.listen()

        audio_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        audio_server.bind((HOST, self.audio_port2))
        audio_server.listen()

        print(f"Server listening on ports: {self.image_port2} (Image), {self.audio_port2} (Audio)")
        self.message_label.setText(f"Server listening on ports: {self.image_port2} (Image), {self.audio_port2} (Audio)")


        image_thread = threading.Thread(target=lambda: self.accept_clients(image_server, self.handle_image_client))
        audio_thread = threading.Thread(target=lambda: self.accept_clients(audio_server, self.handle_audio_client))

        image_thread.start()
        audio_thread.start()

        image_thread.join()
        audio_thread.join()

        image_server.close()
        audio_server.close()
    
    def handle_image_client(self,conn, addr):
        print(f"Image client connected by {addr}")
        while True:
            data_length = int(conn.recv(1024).decode())  # Receive image data length
            data = b''
            while len(data) < data_length:
                chunk = conn.recv(1024)
                if not chunk:
                    break
                data += chunk

            try:
                # Create directory if it doesn't exist
                if not os.path.exists(self.received_image_dir):
                    os.makedirs(self.received_image_dir)

                # Generate unique filename with timestamp
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                filename = f"{timestamp}.jpg"
                filepath = os.path.join(self.received_image_dir, filename)
                
                with open(filepath, "wb") as f:
                    f.write(data)
                print("Image received and saved successfully!")
                self.message_label.setText("Image received and saved successfully!")
            except Exception as e:
                print("Error saving image:", e)
            finally:
                conn.close()
                break  # Exit loop after receiving one image

    def handle_audio_client(self,conn, addr):
        print(f"Audio client connected by {addr}")
        while True:
            # Receive audio data in chunks
            data = b''
            while True:
                chunk = conn.recv(1024)
                if not chunk:  # Check for connection closure
                    break
                data += chunk

            try:
                # Create directory if it doesn't exist
                if not os.path.exists(self.received_audio_dir):
                    os.makedirs(self.received_audio_dir)

                # Generate unique filename with timestamp
                timestamp = time.strftime("%Y%m%d-%H%M%S")
                filename = f"{timestamp}.wav"
                filepath = os.path.join(self.received_audio_dir, filename)
                
                # Save audio data as a WAV file
                chunk_size = 1024
                sample_format = pyaudio.paInt16
                channels = 1
                rate = 44100
                audio = pyaudio.PyAudio()
                
                with wave.open(filepath, 'wb') as f:
                    f.setnchannels(channels)
                    f.setsampwidth(audio.get_sample_size(sample_format))
                    f.setframerate(rate)
                    f.writeframes(data)

                print("Audio received and saved successfully!")
                self.message_label.setText("Audio received and saved successfully!")
            except Exception as e:
                print("Error saving audio:", e)
            finally:
                conn.close()
                break  # Exit loop after receiving one audio stream
        
    def accept_clients(self, server_socket, handle_client_function):
        while self.running:
            conn, addr = server_socket.accept()
            handle_client_function(conn, addr)
    
    #=====================================================================================
    #               Image code
    #=====================================================================================
    def capture_and_display(self):
        cap = cv2.VideoCapture(0)

        while self.running:
            ret, frame = cap.read()
            first_time = True

            if ret:
                self.image = frame  # Update captured image
                self.update_webcam_label()  # Update webcam feed label
                if first_time is True:
                    self.capture_button.setEnabled(True)
                    first_time = False
                
            else:
                print("Error capturing image")

            if cv2.waitKey(1) == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

    def update_webcam_label(self):
        if self.image is not None:
            rgb_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB
            height, width, channel = rgb_image.shape
            bytes_per_line = 3 * width
            qimg = QImage(rgb_image.data, width, height, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap(qimg)
            self.webcam_label.minimumWidth = 10000
            self.webcam_label.minimumHeight = 10000
            self.webcam_label.setPixmap(pixmap.scaled(self.webcam_label.width(), self.webcam_label.height(), Qt.KeepAspectRatio))

    def capture_image(self):
        if self.image is not None:
            # Create directory if it doesn't exist
            if not os.path.exists(self.image_dir):
                os.makedirs(self.image_dir)

        # Generate unique filename with timestamp
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"{timestamp}.jpg"
        filepath = os.path.join(self.image_dir, filename)

        # Save image
        cv2.imwrite(filepath, self.image)
        print(f"Image saved to: {filepath}")
        self.message_label.setText(f"Image saved to: {filepath}")
        self.last_image = self.image
        self.send_button.setEnabled(True)  # Enable send button if capture successful
        self.server_button.setEnabled(True)   ##########################################################################
        print(f"last image changed")
            
    def send_image(self):
        if self.last_image is None:
            print("No image captured yet")
            return
        try:
            # Create TCP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            sock.connect((self.server_ip, self.image_port))

            # Send image data length (assuming server expects length first)
            image_data = cv2.imencode('.jpg', self.last_image)[1].tobytes()
            data_length = len(image_data)
            sock.sendall(str(data_length).encode())

            # Send image data
            sock.sendall(image_data)

            print("Image sent successfully!")
            self.message_label.setText(f"Image sent successfully!")
            sock.close()
            
        except Exception as e:
            self.message_label.setText(f"Error sending image: {e}")
            print("Error sending image:", e)
    
    #=====================================================================================
    #               Audio code
    #=====================================================================================
    def start_record(self):
        if self.recording:
            self.stop_record()
            return

        self.recording = True
        self.record_button.setText("Stop Recording")
        self.capture_thread = threading.Thread(target=self.record_audio)
        self.capture_thread.start()
        
    def stop_record(self):
        self.recording = False
        self.record_button.setText("Record Audio")
            
        
    def record_audio(self):
        # Audio recording parameters
        chunk_size = 1024
        sample_format = pyaudio.paInt16
        channels = 1
        rate = 44100

        p = pyaudio.PyAudio()

        stream = p.open(format=sample_format,
                        channels=channels,
                        rate=rate,
                        output=False,
                        input=True,
                        frames_per_buffer=chunk_size)

        frames = []
        while self.recording:
            data = stream.read(chunk_size)
            frames.append(data)

        stream.stop_stream()
        stream.close()
        p.terminate()
        self.recorded_audio = b''.join(frames)
        
        # Save recorded audio to a file
        if self.recorded_audio is not None:
            self.save_audio(self.recorded_audio)
            print("audio saved")
            
        self.send_button2.setEnabled(True)  # Enable send button after recording

    def save_audio(self, audio_data):
        print("in saving audio")
        # Create directory if it doesn't exist
        if not os.path.exists(self.audio_dir):
            os.makedirs(self.audio_dir)

        # Generate unique filename with timestamp
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        filename = f"{timestamp}.wav"
        filepath = os.path.join(self.audio_dir, filename)

        # Save audio data as a WAV file
        chunk_size = 1024
        sample_format = pyaudio.paInt16
        channels = 1
        rate = 44100
        audio = pyaudio.PyAudio()
        
        with wave.open(filepath, 'wb') as f:
            f.setnchannels(channels)
            f.setsampwidth(audio.get_sample_size(sample_format))
            f.setframerate(rate)
            f.writeframes(self.recorded_audio)

        print(f"Audio saved to: {filepath}")
        self.message_label.setText(f"Audio saved to: {filepath}")
        
    def send_audio(self):    
        if self.recorded_audio is None:
            print("There is no audio to send")
            return 
        
        try:
            # Create TCP socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.server_ip, self.audio_port))
            
            # Send audio data
            sock.sendall(self.recorded_audio)
            print("Audio sent successfully!")
            self.message_label.setText("Audio sent successfully!")
            sock.close()
        except Exception as e:
            print("Error sending audio:", e)
            self.message_label.setText(f"Error sending audio: {e}")


    #=====================================================================================
    #               IP code
    #=====================================================================================

    
    # def get_local_ip(self):
    #     s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #     s.connect(("8.8.8.8", 80))  # Connect to a public DNS server (Google DNS)
    #     return s.getsockname()[0]
    
    # def get_public_ip(self):
    #     response = requests.get("https://api.ipify.org?format=text")  # Replace with your preferred service
    #     if response.status_code == 200:
    #         return response.text.strip()
    #     else:
    #         print(f"Error getting public IP: {response.status_code}")
    #         return None
            
if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = CombinedApp()
    sys.exit(app.exec_())
