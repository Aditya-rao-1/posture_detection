import cv2
import mediapipe as mp
import numpy as np
import time
from flask import Flask, Response, jsonify
from flask_cors import CORS
from flask import request
import os
import uuid  # REQUIRED for unique video names

app = Flask(__name__)
CORS(app)

# Mediapipe initialization
mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# Global state
cap = None
streaming = False
is_calibrated = False
calibration_frames = 0
calibration_shoulder_angles = []
calibration_neck_angles = []
shoulder_threshold = 0
neck_threshold = 0
last_alert_time = 0
alert_cooldown = 10
current_status = {"status": "Calibrating...", "alerts": []}

# Posture mode: "sitting" or "squat"
posture_mode = "sitting"

# Summary tracking
total_frames = 0
bad_posture_frames = 0
alert_counter = {}

# ---------------- Helper Functions ----------------

def calculate_angle(a, b, c):
    a, b, c = np.array(a), np.array(b), np.array(c)
    ba = a - b
    bc = c - b
    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
    angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
    return np.degrees(angle)

def draw_angle(frame, a, b, c, angle, color):
    cv2.line(frame, a, b, color, 2)
    cv2.line(frame, c, b, color, 2)
    cv2.putText(frame, f'{int(angle)}°', b, cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

# ---------------- Camera Functions ----------------

def start_camera():
    global cap, streaming, is_calibrated, calibration_frames
    if cap is None or not cap.isOpened():
        cap = cv2.VideoCapture(0)
    streaming = True
    is_calibrated = False
    calibration_frames = 0

def stop_camera():
    global cap, streaming
    streaming = False
    if cap is not None:
        cap.release()
        cv2.destroyAllWindows()

# ---------------- Video Stream Generator ----------------

def gen_frames():
    global cap, streaming, is_calibrated, calibration_frames
    global calibration_shoulder_angles, calibration_neck_angles
    global shoulder_threshold, neck_threshold, last_alert_time
    global current_status, posture_mode
    global total_frames, bad_posture_frames, alert_counter

    start_camera()

    while streaming and cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(image)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        h, w, _ = image.shape

        alerts = []

        if results.pose_landmarks:
            lm = results.pose_landmarks.landmark

            def get_coords(landmark): return (int(landmark.x * w), int(landmark.y * h))

            l_shoulder = get_coords(lm[mp_pose.PoseLandmark.LEFT_SHOULDER])
            r_shoulder = get_coords(lm[mp_pose.PoseLandmark.RIGHT_SHOULDER])
            l_hip = get_coords(lm[mp_pose.PoseLandmark.LEFT_HIP])
            r_hip = get_coords(lm[mp_pose.PoseLandmark.RIGHT_HIP])
            l_knee = get_coords(lm[mp_pose.PoseLandmark.LEFT_KNEE])
            l_ankle = get_coords(lm[mp_pose.PoseLandmark.LEFT_ANKLE])
            l_ear = get_coords(lm[mp_pose.PoseLandmark.LEFT_EAR])

            mid_shoulder = ((l_shoulder[0] + r_shoulder[0]) // 2, (l_shoulder[1] + r_shoulder[1]) // 2)
            mid_hip = ((l_hip[0] + r_hip[0]) // 2, (l_hip[1] + r_hip[1]) // 2)

            # Angle Calculations
            shoulder_angle = calculate_angle(l_shoulder, mid_shoulder, (mid_shoulder[0], 0))
            back_angle = calculate_angle(l_shoulder, l_hip, l_knee)

            # Neck angle
            neck_vector = np.array([l_ear[0] - l_shoulder[0], l_ear[1] - l_shoulder[1]])
            vertical_vector = np.array([0, -1])
            cos_angle = np.dot(neck_vector, vertical_vector) / (
                np.linalg.norm(neck_vector) * np.linalg.norm(vertical_vector) + 1e-6
            )
            neck_angle = np.degrees(np.arccos(np.clip(cos_angle, -1.0, 1.0)))

            knee_over_toe = abs(l_knee[0] - l_ankle[0]) > 20 and l_knee[1] > l_ankle[1]

            # Calibration
            if not is_calibrated and calibration_frames < 30:
                calibration_shoulder_angles.append(shoulder_angle)
                calibration_neck_angles.append(neck_angle)
                calibration_frames += 1
                current_status["status"] = f"Calibrating... {calibration_frames}/30"
                cv2.putText(image, current_status["status"], (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            elif not is_calibrated:
                shoulder_threshold = np.mean(calibration_shoulder_angles) - 10
                neck_threshold = np.mean(calibration_neck_angles) + 5
                is_calibrated = True
                print(f"✅ Calibration complete. Shoulder<{shoulder_threshold:.1f}°, Neck<{neck_threshold:.1f}°")

            # Draw Pose
            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

            # Draw angles
            draw_angle(image, l_shoulder, mid_shoulder, (mid_shoulder[0], 0), shoulder_angle, (255, 0, 0))
            draw_angle(image, l_shoulder, l_hip, l_knee, back_angle, (0, 255, 255))
            draw_angle(image, (l_shoulder[0], l_shoulder[1] - 50), l_shoulder, l_ear, neck_angle, (0, 255, 0))

            # Reference lines
            cv2.line(image, l_shoulder, (l_shoulder[0], h), (0, 255, 0), 2)
            cv2.line(image, l_shoulder, (w, l_shoulder[1]), (255, 0, 0), 2)
            cv2.line(image, l_shoulder, l_ear, (0, 255, 255), 2)

            # Posture alerts based on selected mode
            current_time = time.time()
            if is_calibrated:
                if posture_mode == "sitting":
                    if neck_angle > 30:
                        alerts.append("Neck bent forward (>30°)")
                    if back_angle < 150:
                        alerts.append("Back not straight (<150°)")
                elif posture_mode == "squat":
                    if back_angle < 150:
                        alerts.append("Back not straight (<150°)")
                    if knee_over_toe:
                        alerts.append("Knee over toe")

                # Update session stats
                total_frames += 1
                if alerts:
                    bad_posture_frames += 1
                    for alert in alerts:
                        alert_counter[alert] = alert_counter.get(alert, 0) + 1

                # Update current status
                if alerts:
                    current_status["status"] = "Poor Posture"
                    current_status["alerts"] = alerts
                    if current_time - last_alert_time > alert_cooldown:
                        last_alert_time = current_time
                        print("⚠️ Alerts:", alerts)
                else:
                    current_status["status"] = "Good Posture"
                    current_status["alerts"] = []
                    if current_time - last_alert_time > alert_cooldown:
                        print("✅ Good posture")
                        last_alert_time = current_time

                # Draw text
                y = 30
                color = (0, 255, 0) if current_status["status"] == "Good Posture" else (0, 0, 255)
                cv2.putText(image, current_status["status"], (10, y), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
                for alert in alerts:
                    y += 30
                    cv2.putText(image, f"- {alert}", (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

        ret, buffer = cv2.imencode('.jpg', image)
        if not ret:
            continue
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    stop_camera()

# ---------------- Flask Routes ----------------

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/stop_stream')
def stop_stream():
    stop_camera()
    return jsonify({"message": "Stream stopped"})

@app.route('/posture_status')
def posture_status():
    return jsonify(current_status)

@app.route('/set_mode/<mode>')
def set_mode(mode):
    global posture_mode
    if mode not in ["squat", "sitting"]:
        return jsonify({"error": "Invalid mode. Use 'squat' or 'sitting'."}), 400
    posture_mode = mode
    return jsonify({"message": f"Posture mode set to {mode}."})

@app.route('/posture_summary')
def posture_summary():
    return jsonify({
        "total_frames": total_frames,
        "bad_posture_frames": bad_posture_frames,
        "alert_breakdown": alert_counter
    })

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
from werkzeug.utils import secure_filename

@app.route('/upload_video', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        return jsonify({"error": "No video file provided"}), 400

    video = request.files['video']
    filename = secure_filename(video.filename)
    video_path = os.path.join('uploads', filename)

    os.makedirs('uploads', exist_ok=True)
    os.makedirs('outputs', exist_ok=True)

    unique_name = f"{uuid.uuid4().hex}.mp4"
    output_path = os.path.join('outputs', unique_name)

    video.save(video_path)

    # Process video
    cap = cv2.VideoCapture(video_path)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

    frame_index = 0
    summary = {
        "total_frames": 0,
        "bad_posture_frames": 0,
        "alert_breakdown": {}
    }
    frame_feedback = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(image_rgb)
        alerts = []

        if results.pose_landmarks:
            lm = results.pose_landmarks.landmark
            h, w, _ = frame.shape

            def get_coords(p): return (int(lm[p].x * w), int(lm[p].y * h))

            # Landmarks
            l_shoulder = get_coords(mp_pose.PoseLandmark.LEFT_SHOULDER)
            l_hip = get_coords(mp_pose.PoseLandmark.LEFT_HIP)
            l_knee = get_coords(mp_pose.PoseLandmark.LEFT_KNEE)
            l_ankle = get_coords(mp_pose.PoseLandmark.LEFT_ANKLE)
            l_ear = get_coords(mp_pose.PoseLandmark.LEFT_EAR)

            back_angle = calculate_angle(l_shoulder, l_hip, l_knee)
            neck_vector = np.array([l_ear[0] - l_shoulder[0], l_ear[1] - l_shoulder[1]])
            vertical_vector = np.array([0, -1])
            cos_angle = np.dot(neck_vector, vertical_vector) / (np.linalg.norm(neck_vector) * np.linalg.norm(vertical_vector) + 1e-6)
            neck_angle = np.degrees(np.arccos(np.clip(cos_angle, -1.0, 1.0)))
            knee_over_toe = abs(l_knee[0] - l_ankle[0]) > 20 and l_knee[1] > l_ankle[1]

            if neck_angle > 30:
                alerts.append("Neck bent forward (>30°)")
            if back_angle < 150:
                alerts.append("Back not straight (<150°)")
            if knee_over_toe:
                alerts.append("Knee over toe")

            mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        # Update summary
        summary["total_frames"] += 1
        if alerts:
            summary["bad_posture_frames"] += 1
            for a in alerts:
                summary["alert_breakdown"][a] = summary["alert_breakdown"].get(a, 0) + 1

        frame_feedback.append({
            "frame": frame_index,
            "alerts": alerts
        })
        frame_index += 1

        out.write(frame)

    cap.release()
    out.release()

    return jsonify({
        "summary": summary,
        "frame_feedback": frame_feedback,
        "video_url": f"http://localhost:5000/outputs/{unique_name}"
    })




from flask import send_from_directory
OUTPUT_FOLDER = os.path.join(os.getcwd(), 'outputs')
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER


@app.route('/outputs/<path:filename>')
def static_output(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)



if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ["PORT"]))


