import axios, { isAxiosError } from 'axios'

export const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
})

export function formatApiError(err: unknown): string {
  if (!isAxiosError(err)) {
    return err instanceof Error ? err.message : 'Failed to analyze repository'
  }
  if (err.code === 'ERR_NETWORK') {
    return `Cannot reach the API at ${API_BASE}. Start the backend with: cd backend && python main.py`
  }
  const detail = err.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail.map((d) => d.msg || d.message || String(d)).join(', ')
  }
  return err.message || 'Failed to analyze repository'
}

export const analyzeRepository = async (url: string) => {
  const response = await api.post('/api/analyze', {
    url,
  })
  return response.data
}

export const getKPI = async (repoId: number) => {
  const response = await api.get(`/api/kpi/${repoId}`)
  return response.data
}

export const getOldestPRs = async (repoId: number, limit: number = 10) => {
  const response = await api.get(`/api/oldest-prs/${repoId}`, {
    params: { limit },
  })
  return response.data
}

export const getSlowestPRs = async (repoId: number, limit: number = 10) => {
  const response = await api.get(`/api/slowest-prs/${repoId}`, {
    params: { limit },
  })
  return response.data
}

export const getContributorActivity = async (repoId: number) => {
  const response = await api.get(`/api/contributor-activity/${repoId}`)
  return response.data
}

export const getMonthlyFlow = async (repoId: number, months: number = 6) => {
  const response = await api.get(`/api/monthly-flow/${repoId}`, {
    params: { months },
  })
  return response.data
}

export const getThroughput = async (repoId: number, weeks: number = 8) => {
  const response = await api.get(`/api/throughput/${repoId}`, {
    params: { weeks },
  })
  return response.data
}
