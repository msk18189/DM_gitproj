'use client'

import { motion } from 'framer-motion'
import { Brain } from 'lucide-react'
import { riskColor } from '@/lib/format'

interface PRRiskItem {
  number: number
  title: string
  author: string
  risk_score: number
  bottleneck_probability: number
  predicted_delay_days: number | null
  predicted_delay_display?: { value: number; unit: string }
  predicted_review_wait_hours: number | null
  score_source?: string
  _panel_note?: string
}

export default function PRRiskPanel({ data }: { data: PRRiskItem[] }) {
  if (!data?.length) {
    return (
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="card card-hover mb-8">
        <div className="flex items-center gap-2 mb-2">
          <Brain className="w-5 h-5 text-purple-400" />
          <h3 className="text-lg font-bold">PR Risk & Delay Predictions</h3>
        </div>
        <p className="text-gray-400 text-sm">No open PRs with ML predictions yet.</p>
      </motion.div>
    )
  }

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="card card-hover mb-8">
      <div className="flex items-center gap-2 mb-4">
        <Brain className="w-5 h-5 text-purple-400" />
        <h3 className="text-lg font-bold">PR Risk & Delay Predictions</h3>
      </div>
      <p className="text-xs text-gray-400 mb-4">
        {data[0]?._panel_note ||
          (data[0]?.score_source === 'heuristic'
            ? 'Rule-based risk estimates from PR age, reviews, and size (same signals as stale alerts). Train ML models for full predictions.'
            : 'ML-powered risk scores for open PRs — higher risk may need attention')}
      </p>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-dark-700">
              <th className="px-3 py-2 text-left text-xs text-gray-400">#</th>
              <th className="px-3 py-2 text-left text-xs text-gray-400">Title</th>
              <th className="px-3 py-2 text-left text-xs text-gray-400">Author</th>
              <th className="px-3 py-2 text-left text-xs text-gray-400">Risk</th>
              <th className="px-3 py-2 text-left text-xs text-gray-400">Bottleneck</th>
              <th className="px-3 py-2 text-left text-xs text-gray-400">Est. delay</th>
              <th className="px-3 py-2 text-left text-xs text-gray-400">Est. review wait</th>
            </tr>
          </thead>
          <tbody>
            {data.map((pr) => (
              <tr key={pr.number} className="border-b border-dark-700/50 hover:bg-dark-700/50">
                <td className="px-3 py-2 text-sm">{pr.number}</td>
                <td className="px-3 py-2 text-sm max-w-xs truncate">{pr.title}</td>
                <td className="px-3 py-2 text-sm">{pr.author}</td>
                <td className={`px-3 py-2 text-sm font-bold ${riskColor(pr.risk_score)}`}>
                  {pr.risk_score}%
                </td>
                <td className="px-3 py-2 text-sm">{pr.bottleneck_probability}%</td>
                <td className="px-3 py-2 text-sm">
                  {pr.predicted_delay_display
                    ? `${pr.predicted_delay_display.value} ${pr.predicted_delay_display.unit}`
                    : pr.predicted_delay_days != null
                    ? `${pr.predicted_delay_days} days`
                    : '—'}
                </td>
                <td className="px-3 py-2 text-sm">
                  {pr.review_count === 0
                    ? pr.predicted_review_wait_hours != null
                      ? `No reviews yet (${pr.predicted_review_wait_hours}h open)`
                      : 'No reviews yet'
                    : pr.predicted_review_wait_display
                    ? `${pr.predicted_review_wait_display.value} ${pr.predicted_review_wait_display.unit}`
                    : pr.predicted_review_wait_hours != null
                    ? `${pr.predicted_review_wait_hours} hrs`
                    : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </motion.div>
  )
}
