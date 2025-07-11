import React from 'react'
import { useNavigate } from 'react-router-dom'
import Hero from './components/Hero'
import Footer from './components/Footer'

const App = () => {
  const navigate = useNavigate()

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-b from-gray-900 via-gray-950 to-black text-white">
      <Hero />

      <section className="py-20 px-6 max-w-6xl mx-auto grid md:grid-cols-2 gap-10">
        {/* Upload Section */}
        <div className="bg-gradient-to-br from-gray-800 to-gray-700 rounded-2xl p-8 shadow-2xl hover:shadow-blue-500/30 transition-all duration-300">
          <h2 className="text-3xl font-semibold mb-4">Upload & Analyze</h2>
          <p className="text-base text-gray-300 mb-6">
            Upload a posture image or video and let our AI analyze it for insights.
          </p>
          <button
            onClick={() => navigate('/upload-video')}
            className="bg-blue-600 hover:bg-blue-700 transition px-6 py-3 rounded-lg font-medium"
          >
            Upload
          </button>
        </div>

        {/* Webcam Section */}
        <div className="bg-gradient-to-br from-gray-800 to-gray-700 rounded-2xl p-8 shadow-2xl hover:shadow-green-500/30 transition-all duration-300">
          <h2 className="text-3xl font-semibold mb-4">Live Webcam Detection</h2>
          <p className="text-base text-gray-300 mb-6">
            Get instant feedback on your posture using real-time webcam tracking.
          </p>
          <button
            onClick={() => navigate('/webcam')}
            className="bg-green-600 hover:bg-green-700 transition px-6 py-3 rounded-lg font-medium"
          >
            Start Webcam
          </button>
        </div>
      </section>

      <Footer />
    </div>
  )
}

export default App
