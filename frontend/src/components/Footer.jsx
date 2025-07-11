import React from 'react'
import { Github, ExternalLink } from 'lucide-react'

const Footer = () => {
  return (
    <footer className="py-8 border-t border-gray-700 text-center text-sm text-gray-500 flex flex-col items-center gap-2">
      <div className="flex gap-4">
        <a
          href="https://github.com/Aditya-rao-1"
          target="_blank"
          rel="noopener noreferrer"
          className="hover:text-white transition-colors"
        >
          <Github size={50} />
        </a>
        <a
          href="https://adi-portfolio-beta.vercel.app/"
          target="_blank"
          rel="noopener noreferrer"
          className="hover:text-white transition-colors"
        >
          <ExternalLink size={50} />
        </a>
      </div>
      <p>&copy; {new Date().getFullYear()} Posture Assistant. All rights reserved.</p>
    </footer>
  )
}

export default Footer
