// src/main.jsx or src/index.jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import App from './App'
import Webcam from './components/Webcam'
import './index.css' // assuming Tailwind is imported here
import Uploadvideo from './components/Uploadvideo'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <Router>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path='/upload-video' element={<Uploadvideo/>} />
        <Route path="/webcam" element={<Webcam />} />
      </Routes>
    </Router>
  </React.StrictMode>
)
