import React, { useEffect, useRef, useState } from 'react';

const Webcam = () => {
  const videoRef = useRef(null);
  const [status, setStatus] = useState('Waiting...');
  const [alerts, setAlerts] = useState([]);
  const [summary, setSummary] = useState(null);
  const [mode, setMode] = useState('sitting');

  // Start webcam
  useEffect(() => {
    navigator.mediaDevices.getUserMedia({ video: true })
      .then((stream) => {
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      })
      .catch((err) => {
        console.error("Webcam access error:", err);
      });

    const interval = setInterval(() => {
      captureAndSendFrame();
    }, 1000);

    return () => {
      clearInterval(interval);
      fetch('https://posture-detection-n5w9.onrender.com/stop_stream');
    };
  }, []);

  // Capture frame and send to backend
  const captureAndSendFrame = async () => {
    const canvas = document.createElement('canvas');
    const video = videoRef.current;
    if (!video) return;

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0);

    const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg'));

    const formData = new FormData();
    formData.append('frame', blob, 'frame.jpg');

    fetch('https://posture-detection-n5w9.onrender.com/process_frame', {
      method: 'POST',
      body: formData
    })
    .then(res => res.json())
    .then(data => {
      setStatus(data.status);
      setAlerts(data.alerts || []);
    })
    .catch(err => console.error("Processing error:", err));
  };

  const fetchSummary = () => {
    fetch('https://posture-detection-n5w9.onrender.com/posture_summary')
      .then(res => res.json())
      .then(data => {
        setSummary(data);
      })
      .catch(err => console.error("Failed to fetch summary:", err));
  };

  const changeMode = (newMode) => {
    fetch(`https://posture-detection-n5w9.onrender.com/set_mode/${newMode}`)
      .then(res => res.json())
      .then(() => setMode(newMode))
      .catch(err => console.error("Mode switch failed:", err));
  };

  return (
    <div className="min-h-screen bg-black text-white flex flex-col items-center p-6">
      <h1 className="text-4xl font-bold text-cyan-400 mb-4">Live Posture Detection</h1>

      <div className={`rounded-xl overflow-hidden border-4 ${alerts.length ? 'border-red-500' : 'border-green-500'}`}>
        <video ref={videoRef} autoPlay playsInline className="w-[640px] h-[480px] object-cover" />
      </div>

      <div className="flex gap-4 mt-6">
        <button onClick={() => changeMode('sitting')} className={`px-4 py-2 rounded ${mode === 'sitting' ? 'bg-blue-600' : 'bg-gray-700'}`}>Sitting Mode</button>
        <button onClick={() => changeMode('squat')} className={`px-4 py-2 rounded ${mode === 'squat' ? 'bg-blue-600' : 'bg-gray-700'}`}>Squat Mode</button>
        <button onClick={fetchSummary} className="px-4 py-2 bg-purple-600 rounded">Get Summary</button>
      </div>

      <div className="mt-6 text-center">
        <h2 className="text-xl font-semibold mb-2">Status: {status}</h2>
        {alerts.length > 0 ? (
          <ul className="text-red-400">
            {alerts.map((alert, idx) => <li key={idx}>{alert}</li>)}
          </ul>
        ) : (
          <p className="text-green-400">Good posture detected.</p>
        )}
      </div>

      {summary && (
        <div className="mt-6 bg-white/10 p-4 rounded-xl max-w-xl w-full">
          <h3 className="text-lg font-bold">Posture Summary</h3>
          <p>Total Frames: {summary.total_frames}</p>
          <p>Bad Posture Frames: {summary.bad_posture_frames}</p>
          <ul>
            {Object.entries(summary.alert_breakdown).map(([k, v]) => (
              <li key={k}>{k}: {v}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default Webcam;
