# 🧍‍♂️ Posture Detection App

A full-stack application for real-time and video-based posture analysis using **MediaPipe**, **Flask**, and **React**. This system detects poor posture like neck bending, back slouching, or incorrect squats, and provides feedback and summaries based on live webcam input or uploaded videos.

🌐 **Live App**: [**https://posture-detection-omega.vercel.app/**](https://posture-detection-omega.vercel.app/)

## 🔍 Features

* 🎥 **Live Webcam Posture Detection**
* 📼 **Video Upload & Analysis**
* 🔁 **Dynamic Mode Switching** (e.g., Sitting vs. Squatting)
* 📊 **Summary Report** with Alert Breakdown
* 🌐 **RESTful API** with endpoints for frame processing, mode setting, and summary

---

## 📦 Tech Stack

### Backend (Flask + OpenCV + MediaPipe)

* Pose estimation using MediaPipe
* Flask API for real-time and batch processing
* Video processing with OpenCV
* Cross-Origin Resource Sharing (CORS) support

### Frontend (React + Tailwind CSS)

* Live webcam streaming and posture alerts
* Video upload interface with download link for processed video
* Beautiful, responsive UI with real-time updates

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/posture-detection-app.git
cd posture-detection-app
```

### 2. Backend Setup

#### 🔧 Install Requirements

```bash
cd backend
pip install -r requirements.txt
```

> `requirements.txt` should include:
> `flask`, `flask-cors`, `opencv-python`, `mediapipe`, `numpy`

#### ▶️ Run Flask Server

```bash
python app.py
```

By default, the server runs at `http://localhost:5000`.

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

This will start the React app at `http://localhost:3000`.

---

## 📡 API Endpoints

### `/process_frame` `[POST]`

* Accepts a webcam image (`multipart/form-data`)
* Returns posture status and alerts

### `/upload_video` `[POST]`

* Accepts a video file
* Returns a processed video URL and summary of posture alerts

### `/posture_summary` `[GET]`

* Returns aggregate summary of posture data

### `/set_mode/<mode>` `[GET]`

* Switch between `sitting` and `squat` detection modes

---

## 🖥️ UI Components

### Live Detection (Webcam.jsx)

* Captures video frames every second
* Sends to backend for processing
* Displays posture alerts and live feedback

### Video Upload (UploadVideo.jsx)

* Drag-and-drop or select video files
* Submits to backend for batch posture analysis
* Returns downloadable video with feedback overlay

---


## 📈 Sample Posture Feedback

```json
{
  "total_frames": 120,
  "bad_posture_frames": 45,
  "alert_breakdown": {
    "Neck bent forward (>30°)": 30,
    "Back not straight (<150°)": 20
  }
}
```



## 🧪 Testing

* Upload short videos (\~10-30 seconds) for quicker feedback
* Try different lighting/backgrounds for better MediaPipe accuracy
* Use `set_mode/squat` to analyze squat form

---


## 🙌 Acknowledgements

* [Google MediaPipe](https://mediapipe.dev/)
* [OpenCV](https://opencv.org/)
* [Flask](https://flask.palletsprojects.com/)
* [Tailwind CSS](https://tailwindcss.com/)


