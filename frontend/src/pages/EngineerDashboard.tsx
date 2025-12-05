import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { getTickets } from '../services/api'
import TicketCard from '../components/TicketCard'
import '../styles/Dashboard.css'

export default function EngineerDashboard() {
  const { user, userProfile, signOut } = useAuth()
  const navigate = useNavigate()
  const [tickets, setTickets] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadTickets()
  }, [])

  const loadTickets = async () => {
    try {
      // Загрузить только тикеты, назначенные этому инженеру
      const data = await getTickets({ engineer_id: userProfile?.id }).catch(() => [])
      setTickets(data || [])
    } catch (error) {
      console.error('Failed to load tickets:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = async () => {
    await signOut()
    navigate('/login')
  }

  if (loading) {
    return (
      <div className="loading">
        <div>Загрузка заданий...</div>
      </div>
    )
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Панель инженера</h1>
        <div className="header-actions">
          <span>{userProfile?.name || user?.email}</span>
          <button className="btn-logout" onClick={handleLogout}>Выйти</button>
        </div>
      </header>

      <main className="dashboard-content">
        <section className="tickets-section">
          <h2>Мои выездные задания</h2>
          {tickets.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">🔧</div>
              <p>Нет назначенных заданий</p>
              <p className="empty-subtitle">
                Выездные задания будут отображаться здесь
              </p>
            </div>
          ) : (
            <div className="tickets-grid">
              {tickets.map((ticket) => (
                <TicketCard
                  key={ticket.id}
                  ticket={ticket}
                  onClick={() => navigate(`/tickets/${ticket.id}`)}
                />
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  )
}

