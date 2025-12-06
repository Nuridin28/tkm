import { useEffect, useState } from 'react'
import '../styles/SLAClock.css'

interface SLAClockProps {
  ticket: any
}

export default function SLAClock({ ticket }: SLAClockProps) {
  const [timeRemaining, setTimeRemaining] = useState<string>('')

  useEffect(() => {
    const updateTimer = () => {
      if (!ticket.sla_accept_deadline) return

      const deadline = new Date(ticket.sla_accept_deadline)
      const now = new Date()
      const diff = deadline.getTime() - now.getTime()

      if (diff <= 0) {
        setTimeRemaining('Просрочено')
        return
      }

      const hours = Math.floor(diff / (1000 * 60 * 60))
      const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
      setTimeRemaining(`${hours}ч ${minutes}м`)
    }

    updateTimer()
    const interval = setInterval(updateTimer, 60000)

    return () => clearInterval(interval)
  }, [ticket.sla_accept_deadline])

  if (!ticket.sla_accept_deadline) {
    return null
  }

  return (
    <div className="sla-clock">
      <span className="sla-label">SLA принятия:</span>
      <span className={`sla-time ${timeRemaining === 'Просрочено' ? 'overdue' : ''}`}>
        {timeRemaining}
      </span>
    </div>
  )
}

