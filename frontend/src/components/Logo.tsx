import { useState } from 'react'

interface LogoProps {
  className?: string
  height?: number
}

export default function Logo({ className = '', height = 40 }: LogoProps) {
  const [error, setError] = useState(false)

  if (error) {
    return (
      <div className={`flex items-center gap-2 ${className}`}>
        <div className="bg-[#0066CC] text-white px-3 py-1.5 rounded font-bold text-lg">
          КТ
        </div>
        <span className="text-[#0066CC] font-semibold">Казахтелеком</span>
      </div>
    )
  }

  return (
    <img
      src="/logo.png"
      alt="Казахтелеком"
      className={className}
      style={{ height: `${height}px` }}
      onError={() => setError(true)}
    />
  )
}

