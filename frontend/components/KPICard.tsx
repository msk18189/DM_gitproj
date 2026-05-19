'use client'

import { motion } from 'framer-motion'
import { ReactNode } from 'react'

interface KPICardProps {
  title: string
  value: string | number
  icon: ReactNode
  trend?: number
  unit?: string
}

export default function KPICard({ title, value, icon, trend, unit }: KPICardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="card card-hover"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-gray-400 text-xs font-medium uppercase tracking-wide">{title}</p>
          <div className="flex items-baseline gap-2 mt-3">
            <h3 className="text-2xl font-bold text-white">
              {typeof value === 'number' && value % 1 !== 0 ? value.toFixed(1) : value}
            </h3>
            {unit && <span className="text-gray-400 text-xs">{unit}</span>}
          </div>
          {trend !== undefined && (
            <p className={`text-xs mt-2 ${trend >= 0 ? 'text-green-400' : 'text-red-400'}`}>
              {trend >= 0 ? '↑' : '↓'} {Math.abs(trend)}%
            </p>
          )}
        </div>
        <div className="text-2xl opacity-60 ml-2">{icon}</div>
      </div>
    </motion.div>
  )
}
