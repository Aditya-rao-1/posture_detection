import React from 'react'
import { Sparkles } from 'lucide-react'

const Hero = () => {
  return (
    <header className="text-center py-20 px-6">
      <div className="flex justify-center items-center mb-6">
        <Sparkles className="text-blue-400 mr-3" size={30} />
        <h1 className="text-5xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-blue-500 via-teal-400 to-green-400">
          Posture Assistant
        </h1>
      </div>
      <p className="max-w-2xl mx-auto text-lg text-gray-300">
        Improve your health and productivity by correcting your posture using AI-powered analysis
        and real-time feedback.
      </p>
    </header>
  )
}

export default Hero
