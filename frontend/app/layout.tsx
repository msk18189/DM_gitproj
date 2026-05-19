import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'GitHub PR Intelligence Dashboard',
  description: 'Analyze GitHub PR activity and repository health',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="bg-dark-900 text-gray-100">{children}</body>
    </html>
  )
}
