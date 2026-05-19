'use client'

import { motion } from 'framer-motion'
import { Filter } from 'lucide-react'

export interface DashboardFiltersState {
  days: number | null
  author: string
  state: string
}

interface DashboardFiltersProps {
  authors: string[]
  filters: DashboardFiltersState
  onChange: (filters: DashboardFiltersState) => void
  onApply: () => void
}

export default function DashboardFilters({
  authors,
  filters,
  onChange,
  onApply,
}: DashboardFiltersProps) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="card card-hover mb-8"
    >
      <div className="flex items-center gap-2 mb-4">
        <Filter className="w-5 h-5 text-purple-400" />
        <h3 className="text-lg font-bold">Filters</h3>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div>
          <label className="block text-xs text-gray-400 mb-1">Date range</label>
          <select
            value={filters.days ?? ''}
            onChange={(e) =>
              onChange({
                ...filters,
                days: e.target.value ? Number(e.target.value) : null,
              })
            }
            className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white text-sm"
          >
            <option value="">All time</option>
            <option value="30">Last 30 days</option>
            <option value="90">Last 90 days</option>
            <option value="180">Last 180 days</option>
          </select>
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">Author</label>
          <select
            value={filters.author}
            onChange={(e) => onChange({ ...filters, author: e.target.value })}
            className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white text-sm"
          >
            <option value="all">All authors</option>
            {authors.map((a) => (
              <option key={a} value={a}>
                {a}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label className="block text-xs text-gray-400 mb-1">PR state</label>
          <select
            value={filters.state}
            onChange={(e) => onChange({ ...filters, state: e.target.value })}
            className="w-full px-3 py-2 bg-dark-700 border border-dark-600 rounded-lg text-white text-sm"
          >
            <option value="ALL">All states</option>
            <option value="OPEN">Open</option>
            <option value="MERGED">Merged</option>
            <option value="CLOSED">Closed</option>
          </select>
        </div>
        <div className="flex items-end">
          <button
            type="button"
            onClick={onApply}
            className="w-full px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm font-medium transition"
          >
            Apply filters
          </button>
        </div>
      </div>
    </motion.div>
  )
}
