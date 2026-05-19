'use client'

import { Download } from 'lucide-react'
import { getExportUrl } from '@/lib/api'
import type { DashboardFiltersState } from '@/components/DashboardFilters'

interface ExportButtonProps {
  repoId: number
  filters: DashboardFiltersState
}

export default function ExportButton({ repoId, filters }: ExportButtonProps) {
  const handleExport = () => {
    const url = getExportUrl(repoId, filters)
    window.open(url, '_blank')
  }

  return (
    <button
      type="button"
      onClick={handleExport}
      className="flex items-center gap-2 px-4 py-2 bg-dark-700 hover:bg-dark-600 border border-dark-600 rounded-lg text-sm text-white transition"
    >
      <Download className="w-4 h-4" />
      Export CSV
    </button>
  )
}
