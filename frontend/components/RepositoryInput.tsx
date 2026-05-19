'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Github, Loader } from 'lucide-react'

interface RepositoryInputProps {
  onAnalyze: (url: string) => Promise<void>
  isLoading: boolean
}

export default function RepositoryInput({ onAnalyze, isLoading }: RepositoryInputProps) {
  const [url, setUrl] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (url.trim()) {
      await onAnalyze(url)
    }
  }

  return (
    <motion.form
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      onSubmit={handleSubmit}
      className="card card-hover mb-8"
    >
      <div className="flex items-center gap-3 mb-6">
        <Github className="w-6 h-6 text-purple-400" />
        <h2 className="text-xl font-bold">Analyze Repository</h2>
      </div>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Repository URL
          </label>
          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://github.com/owner/repository"
            className="w-full px-4 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 transition"
            disabled={isLoading}
          />
          <p className="text-xs text-gray-400 mt-1">GitHub token is configured in backend</p>
        </div>

        <button
          type="submit"
          disabled={isLoading || !url.trim()}
          className="w-full px-4 py-2 bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium rounded-lg transition flex items-center justify-center gap-2"
        >
          {isLoading ? (
            <>
              <Loader className="w-4 h-4 animate-spin" />
              Analyzing...
            </>
          ) : (
            'Analyze Repository'
          )}
        </button>
      </div>
    </motion.form>
  )
}
