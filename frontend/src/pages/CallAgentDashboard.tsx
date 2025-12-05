import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { ingestTicket } from '../services/api'
import '../styles/Dashboard.css'

export default function CallAgentDashboard() {
  const { user, userProfile, signOut } = useAuth()
  const navigate = useNavigate()
  const [formData, setFormData] = useState({
    subject: '',
    text: '',
    client_email: '',
    client_phone: ''
  })
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setSuccess(false)

    try {
      await ingestTicket({
        source: 'call_agent',
        subject: formData.subject,
        text: formData.text,
        incoming_meta: {
          client_email: formData.client_email,
          client_phone: formData.client_phone
        }
      })
      setSuccess(true)
      setFormData({ subject: '', text: '', client_email: '', client_phone: '' })
      setTimeout(() => setSuccess(false), 3000)
    } catch (error) {
      console.error('Failed to create ticket:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = async () => {
    await signOut()
    navigate('/login')
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Панель оператора колл-центра</h1>
        <div className="header-actions">
          <span>{userProfile?.name || user?.email}</span>
          <button className="btn-logout" onClick={handleLogout}>Выйти</button>
        </div>
      </header>

      <main className="dashboard-content">
        <div className="call-agent-form-container">
          <h2>Создать обращение</h2>
          {success && (
            <div className="success-banner">
              ✅ Обращение успешно создано!
            </div>
          )}
          <form onSubmit={handleSubmit} className="call-agent-form">
            <div className="form-group">
              <label>Тема обращения *</label>
              <input
                type="text"
                value={formData.subject}
                onChange={(e) => setFormData({ ...formData, subject: e.target.value })}
                required
                placeholder="Краткое описание проблемы"
              />
            </div>

            <div className="form-group">
              <label>Описание *</label>
              <textarea
                value={formData.text}
                onChange={(e) => setFormData({ ...formData, text: e.target.value })}
                required
                rows={6}
                placeholder="Подробное описание обращения клиента"
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>Email клиента</label>
                <input
                  type="email"
                  value={formData.client_email}
                  onChange={(e) => setFormData({ ...formData, client_email: e.target.value })}
                  placeholder="client@example.com"
                />
              </div>

              <div className="form-group">
                <label>Телефон клиента</label>
                <input
                  type="tel"
                  value={formData.client_phone}
                  onChange={(e) => setFormData({ ...formData, client_phone: e.target.value })}
                  placeholder="+7 (XXX) XXX-XX-XX"
                />
              </div>
            </div>

            <button type="submit" disabled={loading} className="btn-primary btn-large">
              {loading ? 'Создание...' : 'Создать обращение'}
            </button>
          </form>
        </div>
      </main>
    </div>
  )
}

