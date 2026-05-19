'use client'

import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import RepositoryInput from '@/components/RepositoryInput'
import KPICard from '@/components/KPICard'
import DataTable from '@/components/DataTable'
import { MonthlyFlowChart, ThroughputChart, ContributorChart, ReviewTurnaroundChart } from '@/components/Charts'
import {
  analyzeRepository,
  formatApiError,
  getKPI,
  getOldestPRs,
  getSlowestPRs,
  getContributorActivity,
  getMonthlyFlow,
  getThroughput,
} from '@/lib/api'
import { AlertCircle, TrendingUp, Clock, GitMerge, Users, Zap } from 'lucide-react'

export default function Home() {
  const [repoId, setRepoId] = useState<number | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<any>(null)

  const handleAnalyze = async (url: string) => {
    setIsLoading(true)
    setError(null)
    try {
      const result = await analyzeRepository(url)
      setRepoId(result.repo_id)
      await loadDashboardData(result.repo_id)
    } catch (err: unknown) {
      setError(formatApiError(err))
    } finally {
      setIsLoading(false)
    }
  }

  const loadDashboardData = async (id: number) => {
    try {
      const [kpi, oldest, slowest, contributors, monthlyFlow, throughput] = await Promise.all([
        getKPI(id),
        getOldestPRs(id),
        getSlowestPRs(id),
        getContributorActivity(id),
        getMonthlyFlow(id),
        getThroughput(id),
      ])

      // Calculate review turnaround from contributor data
      const reviewTurnaround = contributors.map((c: any) => ({
        username: c.username,
        avg_wait_hours: (c.avg_wait_for_review || 0) * 24, // Convert days to hours
      }))

      setData({
        kpi,
        oldest,
        slowest,
        contributors,
        monthlyFlow,
        throughput,
        reviewTurnaround,
      })
    } catch (err: unknown) {
      setError(formatApiError(err) || 'Failed to load dashboard data')
    }
  }

  return (
    <div className="min-h-screen bg-dark-900">
      {/* Header */}
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-dark-800 border-b border-dark-700 sticky top-0 z-50"
      >
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center gap-3">
            <Zap className="w-8 h-8 text-purple-400" />
            <h1 className="text-3xl font-bold gradient-text">PR Intelligence Dashboard</h1>
          </div>
          <p className="text-gray-400 mt-2">Analyze GitHub repository health and PR metrics</p>
        </div>
      </motion.header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        <RepositoryInput onAnalyze={handleAnalyze} isLoading={isLoading} />

        {error && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="card bg-red-900/20 border-red-700 mb-8 flex items-start gap-3"
          >
            <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-red-400">Error</h3>
              <p className="text-red-300 text-sm">{error}</p>
            </div>
          </motion.div>
        )}

        {data && (
          <>
            {/* KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <KPICard
                title="Open PRs"
                value={data.kpi.open_prs}
                icon="📂"
                unit="all currently open"
              />
              <KPICard
                title="Stale Open (>30D)"
                value={data.kpi.stale_prs}
                icon="⏳"
                unit="need attention"
              />
              <KPICard
                title="Avg Cycle Time"
                value={data.kpi.avg_cycle_time}
                icon="⏱️"
                unit="d"
              />
              <KPICard
                title="Median Cycle Time"
                value={data.kpi.median_cycle_time}
                icon="📊"
                unit="d"
              />
              <KPICard
                title="Avg Wait for Review"
                value={data.kpi.avg_wait_for_review}
                icon="⏳"
                unit="d"
              />
              <KPICard
                title="Avg Review Duration"
                value={data.kpi.avg_review_duration}
                icon="👁️"
                unit="d"
              />
              <KPICard
                title="Merge Rate"
                value={data.kpi.merge_rate}
                icon="✅"
                unit="%"
              />
              <KPICard
                title="Avg Reviews / PR"
                value={data.kpi.avg_reviews_per_pr}
                icon="💬"
                unit=""
              />
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
              <MonthlyFlowChart data={data.monthlyFlow} />
              <ThroughputChart data={data.throughput} />
            </div>

            <div className="mb-8">
              <ContributorChart data={data.contributors} />
            </div>

            <div className="mb-8">
              <ReviewTurnaroundChart data={data.reviewTurnaround} />
            </div>

            {/* Tables with Timeline */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
              <DataTable
                title="Oldest Open PRs"
                columns={[
                  { key: 'number', label: '#' },
                  { key: 'title', label: 'Title' },
                  { key: 'age_days', label: 'Age (days)' },
                  { key: 'author', label: 'Author' },
                  {
                    key: 'created_at',
                    label: 'Created',
                    render: (value: string) => {
                      if (!value) return '-'
                      const date = new Date(value)
                      return date.toLocaleDateString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        year: '2-digit',
                      })
                    },
                  },
                ]}
                data={data.oldest}
              />
              <DataTable
                title="Slowest Merged PRs"
                columns={[
                  { key: 'number', label: '#' },
                  { key: 'title', label: 'Title' },
                  { key: 'cycle_time_days', label: 'Cycle Time (days)' },
                  { key: 'author', label: 'Author' },
                  {
                    key: 'merged_at',
                    label: 'Merged',
                    render: (value: string) => {
                      if (!value) return '-'
                      const date = new Date(value)
                      return date.toLocaleDateString('en-US', {
                        month: 'short',
                        day: 'numeric',
                        year: '2-digit',
                      })
                    },
                  },
                ]}
                data={data.slowest}
              />
            </div>

            <DataTable
              title="Contributor Activity"
              columns={[
                { key: 'username', label: 'Username' },
                { key: 'total_prs', label: 'Total PRs' },
                { key: 'merged_prs', label: 'Merged' },
                { key: 'avg_cycle_time', label: 'Avg Cycle Time (days)' },
                { key: 'merge_rate', label: 'Merge Rate (%)' },
              ]}
              data={data.contributors}
            />
          </>
        )}
      </main>
    </div>
  )
}
