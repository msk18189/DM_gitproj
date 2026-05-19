'use client'

import { Download, FileText } from 'lucide-react'
import { getExportCsvUrl, getExportPdfUrl } from '@/lib/api'
import type { DashboardFiltersState } from '@/components/DashboardFilters'

interface ExportButtonProps {
  repoId: number
  filters: DashboardFiltersState
}

export default function ExportButton({ repoId, filters }: ExportButtonProps) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <button
        type="button"
        onClick={() => window.open(getExportCsvUrl(repoId, filters), '_blank')}
        className="flex items-center gap-2 px-4 py-2 bg-dark-700 hover:bg-dark-600 border border-dark-600 rounded-lg text-sm text-white transition"
      >
        <Download className="w-4 h-4" />
        Export CSV
      </button>
      <button
        type="button"
        onClick={() => window.open(getExportPdfUrl(repoId, filters), '_blank')}
        className="flex items-center gap-2 px-4 py-2 bg-dark-700 hover:bg-dark-600 border border-dark-600 rounded-lg text-sm text-white transition"
      >
        <FileText className="w-4 h-4" />
        Export PDF
      </button>
    </div>
  )
}
