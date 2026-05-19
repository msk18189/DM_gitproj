'use client'

import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts'
import { motion } from 'framer-motion'

interface ChartProps {
  title: string
  data: any[]
  type: 'line' | 'bar' | 'pie'
}

const COLORS = ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#00f2fe']

function EmptyChart({ title, message }: { title: string; message: string }) {
  return (
    <div className="card card-hover flex flex-col items-center justify-center h-[300px] text-gray-400">
      <p className="font-semibold text-gray-300 mb-1">{title}</p>
      <p className="text-sm">{message}</p>
    </div>
  )
}

export function MonthlyFlowChart({ data }: { data: any[] }) {
  const chartData = Array.isArray(data)
    ? data
    : Object.entries(data || {}).map(([month, flow]: [string, any]) => ({
        month,
        ...(typeof flow === 'object' ? flow : {}),
      }))

  if (!chartData.length) {
    return <EmptyChart title="Monthly PR Flow" message="No PR activity in the selected period." />
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="card card-hover"
    >
      <h3 className="text-lg font-bold mb-4">Monthly PR Flow</h3>
      <p className="text-xs text-gray-400 mb-3">
        Created, merged, and closed counts by month (when each event happened)
      </p>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="month" stroke="#9ca3af" tick={{ fontSize: 12 }} />
          <YAxis stroke="#9ca3af" allowDecimals={false} />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1f2937',
              border: '1px solid #374151',
              borderRadius: '8px',
            }}
          />
          <Legend />
          <Bar dataKey="created" name="Created" fill="#667eea" radius={[4, 4, 0, 0]} />
          <Bar dataKey="merged" name="Merged" fill="#10b981" radius={[4, 4, 0, 0]} />
          <Bar dataKey="closed" name="Closed (unmerged)" fill="#ef4444" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </motion.div>
  )
}

export function ThroughputChart({ data }: { data: any[] | Record<string, number> }) {
  const chartData = Array.isArray(data)
    ? data
    : Object.entries(data || {})
        .map(([week, count]) => ({ week, prs: count }))
        .sort((a, b) => a.week.localeCompare(b.week))

  if (!chartData.length) {
    return (
      <EmptyChart
        title="PR Throughput (Weekly)"
        message="No merged PRs in the last 8 weeks."
      />
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="card card-hover"
    >
      <h3 className="text-lg font-bold mb-4">PR Throughput (Weekly)</h3>
      <p className="text-xs text-gray-400 mb-3">Merged PRs per week (ISO week, Mon–Sun)</p>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis dataKey="week" stroke="#9ca3af" tick={{ fontSize: 11 }} />
          <YAxis stroke="#9ca3af" allowDecimals={false} />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1f2937',
              border: '1px solid #374151',
              borderRadius: '8px',
            }}
            formatter={(value: number) => [`${value} PRs`, 'Merged']}
          />
          <Line
            type="monotone"
            dataKey="prs"
            name="Merged PRs"
            stroke="#667eea"
            strokeWidth={2}
            dot={{ fill: '#667eea', r: 4 }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </motion.div>
  )
}

export function ContributorChart({ data }: { data: any[] }) {
  const chartData = (data || [])
    .slice()
    .sort((a, b) => (b.total_prs || 0) - (a.total_prs || 0))
    .map((c) => ({
      ...c,
      label:
        (c.username || 'unknown').length > 14
          ? `${c.username.slice(0, 12)}…`
          : c.username,
    }))

  if (!chartData.length) {
    return (
      <EmptyChart
        title="Contributor Activity"
        message="No contributor data yet. Re-analyze the repository to refresh."
      />
    )
  }

  const chartHeight = Math.max(300, chartData.length * 28 + 80)

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="card card-hover"
    >
      <h3 className="text-lg font-bold mb-4">Contributor Activity</h3>
      <p className="text-xs text-gray-400 mb-3">
        Top contributors by PRs opened vs merged (from fetched pull requests)
      </p>
      <ResponsiveContainer width="100%" height={chartHeight}>
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 8, right: 24, left: 8, bottom: 8 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" horizontal={false} />
          <XAxis type="number" stroke="#9ca3af" allowDecimals={false} />
          <YAxis
            type="category"
            dataKey="label"
            stroke="#9ca3af"
            width={100}
            tick={{ fontSize: 11 }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1f2937',
              border: '1px solid #374151',
              borderRadius: '8px',
            }}
            labelFormatter={(_, payload) =>
              payload?.[0]?.payload?.username || ''
            }
            formatter={(value: number, name: string) => [`${value} PRs`, name]}
          />
          <Legend />
          <Bar dataKey="total_prs" fill="#667eea" name="Total PRs" radius={[0, 4, 4, 0]} />
          <Bar dataKey="merged_prs" fill="#10b981" name="Merged" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </motion.div>
  )
}

export function ReviewTurnaroundChart({ data }: { data: any[] }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="card card-hover"
    >
      <h3 className="text-lg font-bold mb-4">Review Turnaround - Avg Wait for First Review</h3>
      <div className="space-y-3">
        {data.map((item, idx) => (
          <div key={idx} className="flex items-center gap-3">
            <div className="w-32 text-sm font-medium text-gray-300">{item.username}</div>
            <div className="flex-1 bg-dark-700 rounded h-6 relative overflow-hidden">
              <div
                className={`h-full rounded flex items-center justify-end pr-2 text-xs font-bold text-white ${
                  item.avg_wait_hours < 24
                    ? 'bg-green-600'
                    : item.avg_wait_hours < 48
                    ? 'bg-yellow-600'
                    : 'bg-red-600'
                }`}
                style={{ width: `${Math.min((item.avg_wait_hours / 100) * 100, 100)}%` }}
              >
                {item.avg_wait_hours > 10 && `${item.avg_wait_hours.toFixed(1)}h`}
              </div>
            </div>
            <div className="w-16 text-right text-sm font-semibold text-gray-300">
              {item.avg_wait_hours < 24
                ? `${item.avg_wait_hours.toFixed(1)}h`
                : `${(item.avg_wait_hours / 24).toFixed(1)}d`}
            </div>
          </div>
        ))}
      </div>
      <div className="mt-4 text-xs text-gray-400 flex gap-4">
        <span>🟢 &lt;24h</span>
        <span>🟡 24-48h</span>
        <span>🔴 &gt;48h</span>
      </div>
    </motion.div>
  )
}
