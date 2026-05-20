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
import { AlertCircle, Info, Zap } from 'lucide-react'

const defaultFilters: DashboardFiltersState = {
  days: null,
  author: 'all',
  state: 'ALL',
}

export default function Home() {
  const [repoId, setRepoId] = useState<number | null>(null)
  const [repoUrl, setRepoUrl] = useState('')
  const [githubToken, setGithubToken] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [infoMessage, setInfoMessage] = useState<string | null>(null)
  const [data, setData] = useState<any>(null)
  const [emptyRepo, setEmptyRepo] = useState(false)
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

        const safeContributors = Array.isArray(contributors) ? contributors : []
        const reviewTurnaround = safeContributors.map((c: any) => ({
          username: c.username,
          avg_wait_hours: (c.avg_wait_for_review || 0) * 24,
        }))

        setAuthors(authorList ?? [])
        setData({
          kpi: kpi ?? {},
          oldest: Array.isArray(oldest) ? oldest : [],
          slowest: Array.isArray(slowest) ? slowest : [],
          contributors: safeContributors,
          monthlyFlow: Array.isArray(monthlyFlow) ? monthlyFlow : [],
          throughput: Array.isArray(throughput) ? throughput : [],
          reviewTurnaround: reviewTurnaround ?? [],
          prRisk: Array.isArray(prRisk) ? prRisk : [],
          staleAlerts: Array.isArray(staleAlerts) ? staleAlerts : [],
        })
      } catch (err: unknown) {
        setError(formatApiError(err) || 'Failed to load dashboard data')
      }
    },
    []
  )

  const handleAnalyze = async (url: string, token?: string) => {
    setIsLoading(true)
    setError(null)
    setInfoMessage(null)
    setEmptyRepo(false)
    setData(null)
    setRepoUrl(url)
    setFilters(defaultFilters)
    try {
      const result = await analyzeRepository(url, token)
      setRepoId(result.repo_id)

      if (result.total_prs === 0) {
        setEmptyRepo(true)
        setInfoMessage(
          result.message || 'No Pull Requests Found for this repository or file path.'
        )
        return
      }

      if (result.analytics_mode === 'file' && result.file_path) {
        setInfoMessage(
          `File analytics: showing PRs that modified ${result.file_path}` +
            (result.branch ? ` (branch: ${result.branch})` : '')
        )
      }

      await loadDashboardData(result.repo_id, defaultFilters)
    } catch (err: unknown) {
      setError(formatApiError(err))
      setRepoId(null)
    } finally {
      setIsLoading(false)
    }
  }

  const hasAnalyticsData =
    data &&
    (data.kpi?.open_prs > 0 ||
      data.oldest?.length > 0 ||
      data.slowest?.length > 0 ||
      data.contributors?.length > 0 ||
      (data.monthlyFlow?.some?.(
        (m: { created?: number; merged?: number; closed?: number }) =>
          (m.created || 0) + (m.merged || 0) + (m.closed || 0) > 0
      ) ?? false))

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
        <RepositoryInput
          githubToken={githubToken}
          onGithubTokenChange={setGithubToken}
          onAnalyze={handleAnalyze}
          isLoading={isLoading}
        />

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

        {infoMessage && !error && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className={`card mb-8 flex items-start gap-3 ${
              emptyRepo
                ? 'bg-amber-900/20 border-amber-700'
                : 'bg-blue-900/20 border-blue-700'
            }`}
          >
            <Info
              className={`w-5 h-5 flex-shrink-0 mt-0.5 ${
                emptyRepo ? 'text-amber-400' : 'text-blue-400'
              }`}
            />
            <div>
              <h3
                className={`font-semibold ${
                  emptyRepo ? 'text-amber-400' : 'text-blue-400'
                }`}
              >
                {emptyRepo ? 'No Pull Requests Found' : 'Notice'}
              </h3>
              <p
                className={`text-sm ${
                  emptyRepo ? 'text-amber-200' : 'text-blue-200'
                }`}
              >
                {infoMessage}
              </p>
            </div>
          </motion.div>
        )}

        {data && repoId && !hasAnalyticsData && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="card bg-dark-800 border-dark-600 mb-8 text-center py-12"
          >
            <p className="text-gray-300 font-medium">Insufficient Analytics Data</p>
            <p className="text-gray-500 text-sm mt-2">
              Not enough pull request history to render charts and KPIs for the current filters.
            </p>
          </motion.div>
        )}

        {data && repoId && hasAnalyticsData && (
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

            <CompareRepos defaultUrl={repoUrl} githubToken={githubToken} />
          </>
        )}
      </main>
    </div>
  )
}
