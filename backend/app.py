import cv2
import mediapipe as mp
import numpy as np
import time
import uuid
import os
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# Global state
is_calibrated = False
calibration_frames = 0
calibration_shoulder_angles = []
calibration_neck_angles = []
shoulder_threshold = 0
neck_threshold = 0

posture_mode = "sitting"
last_alert_time = 0
alert_cooldown = 10

total_frames = 0
bad_posture_frames = 0
alert_counter = {}

def calculate_angle(a, b, c):
    a, b, c = np.array(a), np.array(b), np.array(c)
    ba = a - b
    bc = c - b
    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
    angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
    return np.degrees(angle)

@app.route('/process_frame', methods=['POST'])
def process_frame():
    global is_calibrated, calibration_frames
    global calibration_shoulder_angles, calibration_neck_angles
    global shoulder_threshold, neck_threshold
    global posture_mode, total_frames, bad_posture_frames, alert_counter, last_alert_time

    file = request.files.get('frame')
    if not file:
        return jsonify({"error": "No frame provided"}), 400

    data = np.frombuffer(file.read(), np.uint8)
    frame = cv2.imdecode(data, cv2.IMREAD_COLOR)
    h, w, _ = frame.shape

    image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(image_rgb)
    alerts = []

    if results.pose_landmarks:
        lm = results.pose_landmarks.landmark

        def coords(p): return (int(lm[p].x * w), int(lm[p].y * h))

        l_shoulder = coords(mp_pose.PoseLandmark.LEFT_SHOULDER)
        r_shoulder = coords(mp_pose.PoseLandmark.RIGHT_SHOULDER)
        l_hip = coords(mp_pose.PoseLandmark.LEFT_HIP)
        l_knee = coords(mp_pose.PoseLandmark.LEFT_KNEE)
        l_ankle = coords(mp_pose.PoseLandmark.LEFT_ANKLE)
        l_ear = coords(mp_pose.PoseLandmark.LEFT_EAR)

        mid_shoulder = ((l_shoulder[0] + r_shoulder[0]) // 2, (l_shoulder[1] + r_shoulder[1]) // 2)
        shoulder_angle = calculate_angle(l_shoulder, mid_shoulder, (mid_shoulder[0], 0))
        back_angle = calculate_angle(l_shoulder, l_hip, l_knee)

        neck_vec = np.array([l_ear[0] - l_shoulder[0], l_ear[1] - l_shoulder[1]])
        vert_vec = np.array([0, -1])
        cosn = np.dot(neck_vec, vert_vec) / (np.linalg.norm(neck_vec) * np.linalg.norm(vert_vec) + 1e-6)
        neck_angle = np.degrees(np.arccos(np.clip(cosn, -1.0, 1.0)))
        knee_over_toe = abs(l_knee[0] - l_ankle[0]) > 20 and l_knee[1] > l_ankle[1]

        if not is_calibrated:
            if calibration_frames < 30:
                calibration_shoulder_angles.append(shoulder_angle)
                calibration_neck_angles.append(neck_angle)
                calibration_frames += 1
                return jsonify({"status": f"Calibrating... {calibration_frames}/30", "alerts": []})
            else:
                shoulder_threshold = np.mean(calibration_shoulder_angles) - 10
                neck_threshold = np.mean(calibration_neck_angles) + 5
                is_calibrated = True
                print(f"✅ Calibration complete. Shoulder < {shoulder_threshold:.1f}, Neck < {neck_threshold:.1f}")

        if posture_mode == "sitting":
            if neck_angle > 30:
                alerts.append("Neck bent forward (>30°)")
            if back_angle < 150:
                alerts.append("Back not straight (<150°)")
        else:
            if back_angle < 150:
                alerts.append("Back not straight (<150°)")
            if knee_over_toe:
                alerts.append("Knee over toe")

        total_frames += 1
        if alerts:
            bad_posture_frames += 1
            for a in alerts:
                alert_counter[a] = alert_counter.get(a, 0) + 1

        # Draw pose landmarks and status
        mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)

        status_text = "Poor Posture" if alerts else "Good Posture"
        color = (0, 0, 255) if alerts else (0, 255, 0)
        cv2.putText(frame, status_text, (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, color, 3)

        # Convert back to bytes for client if needed
        _, img_encoded = cv2.imencode('.jpg', frame)
        return jsonify({"status": status_text, "alerts": alerts})
    else:
        return jsonify({"status": "No person detected", "alerts": []})

@app.route('/set_mode/<mode>')
def set_mode(mode):
    global posture_mode
    if mode not in ["sitting", "squat"]:
        return jsonify({"error": "Invalid mode"}), 400
    posture_mode = mode
    return jsonify({"message": f"Mode set to {mode}."})

@app.route('/posture_summary')
def posture_summary():
    return jsonify({
        "total_frames": total_frames,
        "bad_posture_frames": bad_posture_frames,
        "alert_breakdown": alert_counter
    })

# Video upload logic preserved and enhanced
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

@app.route('/upload_video', methods=['POST'])
def upload_video():
    video = request.files.get('video')
    if not video:
        return jsonify({"error": "No video provided"}), 400

    filename = uuid.uuid4().hex + "_" + video.filename
    upload_path = os.path.join(UPLOAD_FOLDER, filename)
    video.save(upload_path)

    cap = cv2.VideoCapture(upload_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    output_name = uuid.uuid4().hex + ".mp4"
    output_path = os.path.join(OUTPUT_FOLDER, output_name)
    out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

    frame_index = 0
    summary = {"total_frames": 0, "bad_posture_frames": 0, "alert_breakdown": {}}
    frame_feedback = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        summary["total_frames"] += 1

        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(image_rgb)
        alerts = []

        if results.pose_landmarks:
            lm = results.pose_landmarks.landmark
            def coords(p): return (int(lm[p].x * w), int(lm[p].y * h))
            l_shoulder = coords(mp_pose.PoseLandmark.LEFT_SHOULDER)
            l_hip = coords(mp_pose.PoseLandmark.LEFT_HIP)
            l_knee = coords(mp_pose.PoseLandmark.LEFT_KNEE)
            l_ankle = coords(mp_pose.PoseLandmark.LEFT_ANKLE)
            l_ear = coords(mp_pose.PoseLandmark.LEFT_EAR)

            back_angle = calculate_angle(l_shoulder, l_hip, l_knee)
            neck_vec = np.array([l_ear[0] - l_shoulder[0], l_ear[1] - l_shoulder[1]])
            vert_vec = np.array([0, -1])
            cosn = np.dot(neck_vec, vert_vec) / (np.linalg.norm(neck_vec) * np.linalg.norm(vert_vec) + 1e-6)
            neck_angle = np.degrees(np.arccos(np.clip(cosn, -1.0, 1.0)))
            knee_over_toe = abs(l_knee[0] - l_ankle[0]) > 20 and l_knee[1] > l_ankle[1]

            if neck_angle > 30:
                alerts.append("Neck bent forward (>30°)")
            if back_angle < 150:
                alerts.append("Back not straight (<150°)")
            if knee_over_toe:
                alerts.append("Knee over toe")

        if alerts:
            summary["bad_posture_frames"] += 1
            for a in alerts:
                summary["alert_breakdown"][a] = summary["alert_breakdown"].get(a, 0) + 1

        status_text = "Poor Posture" if alerts else "Good Posture"
        color = (0, 0, 255) if alerts else (0, 255, 0)

        mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        cv2.putText(frame, status_text, (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, color, 3)

        frame_feedback.append({"frame": frame_index, "alerts": alerts})
        frame_index += 1
        out.write(frame)

    cap.release()
    out.release()
    return jsonify({
        "summary": summary,
        "frame_feedback": frame_feedback,
        "video_url": f"{request.host_url}outputs/{output_name}"
    })

@app.route('/outputs/<path:filename>')
def serve_output(filename):
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
