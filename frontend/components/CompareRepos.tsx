'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { GitCompare, Loader, KeyRound } from 'lucide-react'
import { compareRepositories, formatApiError } from '@/lib/api'
import { formatDurationDisplay } from '@/lib/format'

interface CompareReposProps {
  defaultUrl?: string
  githubToken?: string
}

export default function CompareRepos({ defaultUrl, githubToken = '' }: CompareReposProps) {
  const [urlA, setUrlA] = useState(defaultUrl || '')
  const [urlB, setUrlB] = useState('')
  const [compareToken, setCompareToken] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<any>(null)

  useEffect(() => {
    if (defaultUrl) setUrlA(defaultUrl)
  }, [defaultUrl])

  const handleCompare = async () => {
    if (!urlA.trim() || !urlB.trim()) return
    setLoading(true)
    setError(null)
    try {
      const token = compareToken.trim() || githubToken?.trim() || undefined
      const data = await compareRepositories(urlA.trim(), urlB.trim(), token)
      setResult(data)
    } catch (err) {
      setError(formatApiError(err))
    } finally {
      setLoading(false)
    }
  }

  const metrics = [
    { key: 'open_prs', label: 'Open PRs' },
    { key: 'stale_prs', label: 'Stale PRs' },
    { key: 'merge_rate', label: 'Merge rate (%)' },
    { key: 'avg_cycle_time', label: 'Avg cycle time' },
  ]

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="card card-hover mb-8">
      <div className="flex items-center gap-2 mb-4">
        <GitCompare className="w-5 h-5 text-purple-400" />
        <h3 className="text-lg font-bold">Compare Repositories</h3>
      </div>
      <p className="text-xs text-gray-400 mb-4">
        For private repos, use the same token as in Analyze above, or paste a token below (only sent to your backend).
      </p>
      <div className="grid md:grid-cols-2 gap-4 mb-4">
        <input
          type="text"
          value={urlA}
          onChange={(e) => setUrlA(e.target.value)}
          placeholder="Repository A URL"
          className="px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white text-sm"
        />
        <input
          type="text"
          value={urlB}
          onChange={(e) => setUrlB(e.target.value)}
          placeholder="Repository B URL"
          className="px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white text-sm"
        />
      </div>
      <div className="mb-4">
        <label className="block text-xs text-gray-400 mb-1 flex items-center gap-1">
          <KeyRound className="w-3 h-3" /> Token for compare (optional)
        </label>
        <input
          type="password"
          autoComplete="off"
          value={compareToken}
          onChange={(e) => setCompareToken(e.target.value)}
          placeholder="Optional — overrides Analyze token if set"
          className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white text-sm font-mono"
        />
      </div>
      <button
        type="button"
        onClick={handleCompare}
        disabled={loading || !urlA.trim() || !urlB.trim()}
        className="px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white rounded-lg text-sm font-medium flex items-center gap-2"
      >
        {loading ? <Loader className="w-4 h-4 animate-spin" /> : null}
        Compare
      </button>
      {error && <p className="text-red-400 text-sm mt-3">{error}</p>}
      {result && (
        <div className="mt-6 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-dark-700">
                <th className="py-2 text-left text-gray-400">Metric</th>
                <th className="py-2 text-left text-gray-400">
                  {result.repo_a.owner}/{result.repo_a.name}
                </th>
                <th className="py-2 text-left text-gray-400">
                  {result.repo_b.owner}/{result.repo_b.name}
                </th>
                <th className="py-2 text-left text-gray-400">Delta (B − A)</th>
              </tr>
            </thead>
            <tbody>
              {metrics.map(({ key, label }) => {
                const a = result.repo_a.kpi[key]
                const b = result.repo_b.kpi[key]
                const delta = result.comparison[`${key}_delta`]
                const displayA =
                  key === 'avg_cycle_time'
                    ? formatDurationDisplay(result.repo_a.kpi.avg_cycle_time_display, a)
                    : { value: a, unit: key === 'merge_rate' ? '%' : '' }
                const displayB =
                  key === 'avg_cycle_time'
                    ? formatDurationDisplay(result.repo_b.kpi.avg_cycle_time_display, b)
                    : { value: b, unit: key === 'merge_rate' ? '%' : '' }
                return (
                  <tr key={key} className="border-b border-dark-700/50">
                    <td className="py-2 text-gray-300">{label}</td>
                    <td className="py-2">
                      {displayA.value} {displayA.unit}
                    </td>
                    <td className="py-2">
                      {displayB.value} {displayB.unit}
                    </td>
                    <td className="py-2 text-gray-400">
                      {delta != null ? (delta > 0 ? `+${delta}` : delta) : '—'}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </motion.div>
  )
}
