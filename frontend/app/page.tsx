'use client'

import { useState, useCallback } from 'react'
import { motion } from 'framer-motion'
import RepositoryInput from '@/components/RepositoryInput'
import KPICard from '@/components/KPICard'
import DataTable from '@/components/DataTable'
import DashboardFilters, { DashboardFiltersState } from '@/components/DashboardFilters'
import PRRiskPanel from '@/components/PRRiskPanel'
import StalePRAlerts from '@/components/StalePRAlerts'
import CompareRepos from '@/components/CompareRepos'
import ExportButton from '@/components/ExportButton'
import {
  MonthlyFlowChart,
  ThroughputChart,
  ContributorChart,
  ReviewTurnaroundChart,
} from '@/components/Charts'
import {
  analyzeRepository,
  formatApiError,
  getKPI,
  getOldestPRs,
  getSlowestPRs,
  getContributorActivity,
  getMonthlyFlow,
  getThroughput,
  getAuthors,
  getPRRisk,
  getStaleAlerts,
} from '@/lib/api'
import { formatDurationDisplay, formatDurationFromDays } from '@/lib/format'
import { AlertCircle, Zap } from 'lucide-react'

const defaultFilters: DashboardFiltersState = {
  days: null,
  author: 'all',
  state: 'ALL',
}

export default function Home() {
  const [repoId, setRepoId] = useState<number | null>(null)
  const [repoUrl, setRepoUrl] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<any>(null)
  const [authors, setAuthors] = useState<string[]>([])
  const [filters, setFilters] = useState<DashboardFiltersState>(defaultFilters)

  const loadDashboardData = useCallback(
    async (id: number, activeFilters: DashboardFiltersState = defaultFilters) => {
      try {
        const [
          kpi,
          oldest,
          slowest,
          contributors,
          monthlyFlow,
          throughput,
          prRisk,
          staleAlerts,
          authorList,
        ] = await Promise.all([
          getKPI(id, activeFilters),
          getOldestPRs(id, 10, activeFilters),
          getSlowestPRs(id, 10, activeFilters),
          getContributorActivity(id, activeFilters),
          getMonthlyFlow(id, 6, activeFilters),
          getThroughput(id, 8, activeFilters),
          getPRRisk(id),
          getStaleAlerts(id),
          getAuthors(id),
        ])

        const reviewTurnaround = contributors.map((c: any) => ({
          username: c.username,
          avg_wait_hours: (c.avg_wait_for_review || 0) * 24,
        }))

        setAuthors(authorList)
        setData({
          kpi,
          oldest,
          slowest,
          contributors,
          monthlyFlow,
          throughput,
          reviewTurnaround,
          prRisk,
          staleAlerts,
        })
      } catch (err: unknown) {
        setError(formatApiError(err) || 'Failed to load dashboard data')
      }
    },
    []
  )

  const handleAnalyze = async (url: string) => {
    setIsLoading(true)
    setError(null)
    setRepoUrl(url)
    setFilters(defaultFilters)
    try {
      const result = await analyzeRepository(url)
      setRepoId(result.repo_id)
      await loadDashboardData(result.repo_id, defaultFilters)
    } catch (err: unknown) {
      setError(formatApiError(err))
    } finally {
      setIsLoading(false)
    }
  }

  const handleApplyFilters = () => {
    if (repoId) loadDashboardData(repoId, filters)
  }

  const cycleAvg = formatDurationDisplay(
    data?.kpi?.avg_cycle_time_display,
    data?.kpi?.avg_cycle_time
  )
  const cycleMedian = formatDurationDisplay(
    data?.kpi?.median_cycle_time_display,
    data?.kpi?.median_cycle_time
  )
  const waitReview = formatDurationDisplay(
    data?.kpi?.avg_wait_for_review_display,
    data?.kpi?.avg_wait_for_review
  )
  const reviewDuration = formatDurationDisplay(
    data?.kpi?.avg_review_duration_display,
    data?.kpi?.avg_review_duration
  )

  return (
    <div className="min-h-screen bg-dark-900">
      <motion.header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-dark-800 border-b border-dark-700 sticky top-0 z-50"
      >
        <div className="max-w-7xl mx-auto px-6 py-6 flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3">
              <Zap className="w-8 h-8 text-purple-400" />
              <h1 className="text-3xl font-bold gradient-text">PR Intelligence Dashboard</h1>
            </div>
            <p className="text-gray-400 mt-2">Analyze GitHub repository health and PR metrics</p>
          </div>
          {repoId && (
            <ExportButton repoId={repoId} filters={filters} />
          )}
        </div>
      </motion.header>

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

        {data && repoId && (
          <>
            <DashboardFilters
              authors={authors}
              filters={filters}
              onChange={setFilters}
              onApply={handleApplyFilters}
            />

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <KPICard title="Open PRs" value={data.kpi.open_prs} icon="📂" unit="currently open" />
              <KPICard title="Stale Open (>30D)" value={data.kpi.stale_prs} icon="⏳" unit="need attention" />
              <KPICard title="Avg Cycle Time" value={cycleAvg.value} icon="⏱️" unit={cycleAvg.unit} />
              <KPICard title="Median Cycle Time" value={cycleMedian.value} icon="📊" unit={cycleMedian.unit} />
              <KPICard title="Avg Wait for Review" value={waitReview.value} icon="⏳" unit={waitReview.unit} />
              <KPICard title="Avg Review Duration" value={reviewDuration.value} icon="👁️" unit={reviewDuration.unit} />
              <KPICard title="Merge Rate" value={data.kpi.merge_rate} icon="✅" unit="%" />
              <KPICard title="Avg Reviews / PR" value={data.kpi.avg_reviews_per_pr} icon="💬" unit="" />
            </div>

            <StalePRAlerts data={data.staleAlerts} />
            <PRRiskPanel data={data.prRisk} />

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

            <CompareRepos defaultUrl={repoUrl} />

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
                      return new Date(value).toLocaleDateString('en-US', {
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
                  {
                    key: 'cycle_time_display',
                    label: 'Cycle Time',
                    render: (_: unknown, row?: any) => {
                      const d = row?.cycle_time_display
                      if (d) return `${d.value} ${d.unit}`
                      return formatDurationFromDays(row?.cycle_time_days || 0).value + ' ' +
                        formatDurationFromDays(row?.cycle_time_days || 0).unit
                    },
                  },
                  { key: 'author', label: 'Author' },
                  {
                    key: 'merged_at',
                    label: 'Merged',
                    render: (value: string) => {
                      if (!value) return '-'
                      return new Date(value).toLocaleDateString('en-US', {
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
                {
                  key: 'avg_cycle_time_display',
                  label: 'Avg Cycle Time',
                  render: (_: unknown, row?: any) => {
                    const d = row?.avg_cycle_time_display
                    if (d) return `${d.value} ${d.unit}`
                    return `${row?.avg_cycle_time || 0} days`
                  },
                },
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
