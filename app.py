from flask import Flask, render_template, Response, jsonify
import cv2
import smtplib
import threading
import pygame
import os
from datetime import datetime

app = Flask(__name__)
camera = cv2.VideoCapture(0)
motion_detected = False

# Initialize pygame mixer for playing audio
pygame.mixer.init()
beep_sound = pygame.mixer.Sound('beep.wav')  # Load your beep sound file

# Create a directory for saving recordings if it doesn't exist
if not os.path.exists('recordings'):
    os.makedirs('recordings')

def send_email_alert():
    """Sends an email alert when motion is detected."""
    sender = 'youremail@gmail.com'
    password = 'yourpassword'
    receiver = 'receiver@gmail.com'

    from email.mime.text import MIMEText
    msg = MIMEText('Motion detected from your smart camera.')
    msg['Subject'] = 'Motion Alert!'
    msg['From'] = sender
    msg['To'] = receiver

    try:
        # Set up the email server and send the email
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, receiver, msg.as_string())
        server.quit()
    except Exception as e:
        print(f"Failed to send email: {e}")

def generate_frames():
    """Generates video frames and detects motion."""
    global motion_detected
    first_frame = None
    video_writer = None

    while True:
        success, frame = camera.read()
        if not success:
            break

        # Convert to grayscale and blur to reduce noise
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if first_frame is None:
            first_frame = gray
            continue

        # Compute the difference between the current frame and the first frame
        delta = cv2.absdiff(first_frame, gray)
        thresh = cv2.threshold(delta, 30, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)

        # Find contours of moving objects
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        motion = False
        for contour in contours:
            if cv2.contourArea(contour) < 1200:
                continue
            motion = True
            (x, y, w, h) = cv2.boundingRect(contour)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # If motion is detected and not previously detected, trigger email, beep sound, and start recording
        if motion and not motion_detected:
            motion_detected = True
            threading.Thread(target=send_email_alert).start()
            beep_sound.play()  # Play the beep sound

            # Start saving the video recording
            filename = f"recordings/motion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.avi"
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            video_writer = cv2.VideoWriter(filename, fourcc, 20.0, (640, 480))

        # If motion is detected, continue recording
        if motion_detected and video_writer:
            video_writer.write(frame)

        # Stop recording if no motion is detected
        if not motion and motion_detected:
            motion_detected = False
            if video_writer:
                video_writer.release()
                video_writer = None

        # Encode the frame to send as response
        _, buffer = cv2.imencode('.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')

    # Release the video writer when done
    if video_writer:
        video_writer.release()

@app.route('/')
def index():
    """Renders the main page of the application."""
    return render_template('index.html')

@app.route('/video')
def video():
    """Streams the video frames."""
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/motion_status')
def motion_status():
    """Returns the motion detection status in JSON format."""
    return jsonify({'motion': motion_detected})

if __name__ == "__main__":
    app.run(debug=True)
