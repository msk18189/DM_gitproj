export interface DurationDisplay {
  value: number
  unit: string
  raw_hours?: number
}

export function formatDurationDisplay(
  display?: DurationDisplay | null,
  fallbackDays?: number
): { value: string | number; unit: string } {
  if (display && display.value > 0) {
    return { value: display.value, unit: display.unit }
  }
  if (fallbackDays !== undefined && fallbackDays > 0) {
    if (fallbackDays < 1) {
      const hrs = Math.round(fallbackDays * 24 * 10) / 10
      return { value: hrs === Math.floor(hrs) ? Math.floor(hrs) : hrs, unit: 'hrs' }
    }
    return { value: fallbackDays, unit: 'days' }
  }
  return { value: 0, unit: 'hrs' }
}

export function formatDurationFromDays(days: number): { value: string | number; unit: string } {
  if (days <= 0) return { value: 0, unit: 'hrs' }
  if (days < 1) {
    const hrs = Math.round(days * 24 * 10) / 10
    return { value: hrs === Math.floor(hrs) ? Math.floor(hrs) : hrs, unit: 'hrs' }
  }
  return { value: days, unit: 'days' }
}

export function severityColor(severity: string): string {
  switch (severity) {
    case 'high':
      return 'border-red-500/50 bg-red-900/20'
    case 'medium':
      return 'border-yellow-500/50 bg-yellow-900/20'
    default:
      return 'border-blue-500/50 bg-blue-900/20'
  }
}

export function riskColor(score: number): string {
  if (score >= 70) return 'text-red-400'
  if (score >= 40) return 'text-yellow-400'
  return 'text-green-400'
}
