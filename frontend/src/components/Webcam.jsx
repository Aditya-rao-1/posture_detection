import React, { useEffect, useState } from 'react';
import { Video, AlertTriangle, CheckCircle, BarChart3 } from 'lucide-react';

const Webcam = () => {
  const [status, setStatus] = useState('');
  const [alerts, setAlerts] = useState([]);
  const [mode, setMode] = useState('sitting');
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    const interval = setInterval(() => {
      fetch('https://posture-detection-n5w9.onrender.com/posture_status')
        .then(res => res.json())
        .then(data => {
          setStatus(data.status);
          setAlerts(data.alerts || []);
        })
        .catch(err => console.error("Failed to fetch posture status:", err));
    }, 1000);

    return () => {
      clearInterval(interval);
      fetch('https://posture-detection-n5w9.onrender.com/stop_stream').catch(err => console.error("Failed to stop stream:", err));
    };
  }, []);

  const handleModeChange = (newMode) => {
    fetch(`https://posture-detection-n5w9.onrender.com/set_mode/${newMode}`)
      .then(res => res.json())
      .then(data => {
        setMode(newMode);
        console.log("Mode switched:", data.message);
      })
      .catch(err => console.error("Failed to set mode:", err));
  };

  const fetchSummary = () => {
    fetch('https://posture-detection-n5w9.onrender.com/posture_summary')
      .then(res => res.json())
      .then(data => {
        setSummary(data);
      })
      .catch(err => console.error("Failed to fetch summary:", err));
  };

  const statusColor = alerts.length > 0 ? 'border-red-500 ' : 'border-green-500';

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gradient-to-br from-gray-900 via-gray-950 to-black text-white p-6">
      <h1 className="text-4xl font-extrabold mb-6 bg-clip-text text-transparent bg-gradient-to-r from-teal-400 to-blue-500">
        <Video className="inline-block mr-2" size={32} />
        Live Posture Detection
      </h1>

      {/* Video feed */}
      <div className={`rounded-xl overflow-hidden border-4 shadow-xl transition-all duration-500 ${statusColor}`}>
        <img
          src="https://posture-detection-n5w9.onrender.com/video_feed"
          alt="Live Feed"
          className="w-[640px] h-[480px] object-cover"
        />
      </div>

      {/* Controls */}
      <div className="flex flex-wrap justify-center gap-4 mt-8">
        <button
          onClick={() => handleModeChange('sitting')}
          className={`px-6 py-3 rounded-xl font-semibold transition-all ${
            mode === 'sitting' ? 'bg-blue-600 shadow-lg' : 'bg-gray-700 hover:bg-gray-600'
          }`}
        >
          Sitting Mode
        </button>
        <button
          onClick={() => handleModeChange('squat')}
          className={`px-6 py-3 rounded-xl font-semibold transition-all ${
            mode === 'squat' ? 'bg-blue-600 shadow-lg' : 'bg-gray-700 hover:bg-gray-600'
          }`}
        >
          Squat Mode
        </button>
        <button
          onClick={fetchSummary}
          className="px-6 py-3 rounded-xl bg-purple-600 hover:bg-purple-700 font-semibold shadow-lg flex items-center gap-2"
        >
          <BarChart3 size={20} /> Get Summary
        </button>
      </div>

      {/* Status and alerts */}
      <div className="mt-8 p-6 rounded-xl bg-white/10 backdrop-blur-lg shadow-xl w-full max-w-xl">
        <h2 className="text-2xl font-semibold mb-3 flex items-center gap-2">
          {alerts.length > 0 ? <AlertTriangle className="text-red-400" /> : <CheckCircle className="text-green-400" />}
          {status}
        </h2>
        {alerts.length > 0 ? (
          <ul className="list-disc list-inside text-red-300">
            {alerts.map((alert, i) => (
              <li key={i}>{alert}</li>
            ))}
          </ul>
        ) : (
          <p className="text-green-400">No posture issues detected.</p>
        )}
      </div>

      {/* Summary Display */}
      {summary && (
        <div className="mt-6 p-6 rounded-xl bg-white/10 backdrop-blur-lg shadow-xl w-full max-w-xl">
          <h3 className="text-xl font-bold text-white mb-3">📊 Posture Summary</h3>
          <p className="mb-1">Total Frames: <span className="font-medium text-blue-300">{summary.total_frames}</span></p>
          <p className="mb-3">Bad Posture Frames: <span className="font-medium text-red-400">{summary.bad_posture_frames}</span></p>
          <p className="font-semibold text-red-300 mb-2">Alert Breakdown:</p>
          <ul className="list-disc list-inside text-red-200">
            {Object.entries(summary.alert_breakdown).map(([alert, count]) => (
              <li key={alert}>
                {alert}: {count}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default Webcam;
