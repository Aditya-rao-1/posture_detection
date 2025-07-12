import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { UploadCloud, DownloadCloud } from 'lucide-react';

const Uploadvideo = () => {
  const [videoFile, setVideoFile] = useState(null);
  const [summary, setSummary] = useState(null);
  const [frameFeedback, setFrameFeedback] = useState([]);
  const [processedVideoUrl, setProcessedVideoUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const onDrop = useCallback((acceptedFiles) => {
    const file = acceptedFiles[0];
    if (file) {
      setVideoFile(file);
      setSummary(null);
      setFrameFeedback([]);
      setProcessedVideoUrl(null);
      setError("");
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'video/*': [] }
  });

  const handleUpload = async () => {
    if (!videoFile) {
      setError("Please select a video file first.");
      return;
    }

    setLoading(true);
    setError("");

    const formData = new FormData();
    formData.append('video', videoFile);

    try {
      const res = await fetch('https://posture-detection-n5w9.onrender.com/upload_video', {
        method: 'POST',
        body: formData
      });

      if (!res.ok) throw new Error("Upload failed");

      const data = await res.json();
      setSummary(data.summary);
      setFrameFeedback(data.frame_feedback);
      setProcessedVideoUrl(data.video_url);
    } catch (err) {
      console.error(err);
      setError("Error uploading or processing video.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-800 text-white py-10 px-6">
      <div className="max-w-4xl mx-auto">
        <h2 className="text-4xl font-extrabold text-center mb-8 bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-purple-500">
          <UploadCloud className="inline-block mr-2" size={32} />
          Upload Video for Posture Analysis
        </h2>

        <div
          {...getRootProps()}
          className={`cursor-pointer border-2 border-dashed rounded-xl p-6 text-center transition-all ${
            isDragActive ? 'border-blue-500 bg-white/10' : 'border-white/20 bg-white/5'
          }`}
        >
          <input {...getInputProps()} />
          {videoFile ? (
            <p className="text-green-400 font-medium">Selected: {videoFile.name}</p>
          ) : (
            <p className="text-white/80">Drag & drop a video file here, or click to select one</p>
          )}
        </div>

        <div className="mt-4 flex justify-center">
          <button
            onClick={handleUpload}
            disabled={loading}
            className="px-6 py-2 mt-4 bg-blue-600 hover:bg-blue-700 rounded-xl shadow-lg transition font-semibold"
          >
            {loading ? "Uploading..." : "Upload & Analyze"}
          </button>
        </div>

        {error && <p className="text-red-400 text-center mt-4">{error}</p>}

        {processedVideoUrl && (
          <div className="mt-10 text-center">
            <h3 className="text-xl font-bold mb-2 flex justify-center items-center text-white">
              <DownloadCloud className="mr-2" /> Download Processed Video
            </h3>
            <a
              href={processedVideoUrl}
              download
              className="inline-block bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-lg shadow-md transition"
            >
              Download Video
            </a>
          </div>
        )}

        {summary && (
          <div className="mt-10 bg-white/10 backdrop-blur-md rounded-xl shadow-xl p-6">
            <h3 className="text-xl font-bold mb-2 text-white">📊 Posture Summary</h3>
            <p>Total Frames: <span className="text-blue-300 font-medium">{summary.total_frames}</span></p>
            <p>Bad Posture Frames: <span className="text-red-400 font-medium">{summary.bad_posture_frames}</span></p>
            <h4 className="mt-4 font-semibold text-white">Alert Breakdown:</h4>
            <ul className="list-disc list-inside text-red-300 mt-1">
              {Object.entries(summary.alert_breakdown).map(([alert, count]) => (
                <li key={alert}>{alert}: {count}</li>
              ))}
            </ul>
          </div>
        )}

        {frameFeedback.length > 0 && (
          <div className="mt-6 bg-white/10 backdrop-blur-md rounded-xl shadow-lg p-6 max-h-[300px] overflow-y-auto">
            <h3 className="text-xl font-bold mb-3 text-white">🎞️ Frame-by-Frame Feedback</h3>
            <ul className="space-y-2 text-sm">
              {frameFeedback.map(({ frame, alerts }) => (
                <li key={frame}>
                  <span className="font-semibold text-blue-300">Frame {frame}:</span>{" "}
                  <span className={alerts.length > 0 ? "text-red-300" : "text-green-400"}>
                    {alerts.length > 0 ? alerts.join(', ') : "Good posture"}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

export default Uploadvideo;
