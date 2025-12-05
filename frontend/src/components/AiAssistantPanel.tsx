import { useState, useEffect } from 'react'
import { getAIRecommendations, submitClassificationFeedback } from '../services/api'
import { Bot, Check, X, Edit, Loader, MessageSquare, Lightbulb } from 'lucide-react'
import '../styles/AiAssistantPanel.css'

interface AiAssistantPanelProps {
  ticket: any
  onClassificationUpdate?: () => void
}

export default function AiAssistantPanel({ ticket, onClassificationUpdate }: AiAssistantPanelProps) {
  const [recommendations, setRecommendations] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [showEditForm, setShowEditForm] = useState(false)
  const [editedClassification, setEditedClassification] = useState({
    category: ticket.category || '',
    department_id: ticket.department_id || '',
    priority: ticket.priority || ''
  })

  useEffect(() => {
    loadRecommendations()
  }, [ticket.id])

  const loadRecommendations = async () => {
    setLoading(true)
    try {
      const data = await getAIRecommendations(ticket.id)
      setRecommendations(data)
    } catch (error) {
      console.error('Failed to load recommendations:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleApproveClassification = async () => {
    setSubmitting(true)
    try {
      const result = await submitClassificationFeedback(ticket.id, {
        is_correct: true,
        category: ticket.category,
        department_id: ticket.department_id,
        priority: ticket.priority,
        notes: 'Классификация подтверждена'
      })
      if (onClassificationUpdate) {
        onClassificationUpdate()
      }
      alert('Классификация подтверждена. Тикет автоматически назначен в департамент и статус изменен на "В разработке".')
    } catch (error) {
      console.error('Failed to approve classification:', error)
      alert('Ошибка при подтверждении классификации')
    } finally {
      setSubmitting(false)
    }
  }

  const handleChangeClassification = async () => {
    setSubmitting(true)
    try {
      await submitClassificationFeedback(ticket.id, {
        is_correct: false,
        category: editedClassification.category,
        department_id: editedClassification.department_id,
        priority: editedClassification.priority,
        notes: 'Классификация изменена оператором'
      })
      if (onClassificationUpdate) {
        onClassificationUpdate()
      }
      setShowEditForm(false)
      alert('Классификация изменена')
    } catch (error) {
      console.error('Failed to change classification:', error)
      alert('Ошибка при изменении классификации')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="ai-assistant-panel">
      <div className="ai-header">
        <Bot className="ai-icon" />
        <h3>ИИ Ассистент</h3>
      </div>

      {ticket.summary && (
        <div className="ai-section">
          <h4>Резюме</h4>
          <p>{ticket.summary}</p>
        </div>
      )}

      {loading ? (
        <div className="ai-loading">
          <Loader className="spinner" />
          <span>Загрузка рекомендаций...</span>
        </div>
      ) : recommendations ? (
        <>
          <div className="ai-section">
            <div className="ai-section-header">
              <MessageSquare className="section-icon" />
              <h4>Что ответить пользователю</h4>
            </div>
            <div className="recommendation-box">
              <p>{recommendations.user_response}</p>
              {recommendations.confidence && (
                <div className="confidence-badge">
                  Уверенность: {(recommendations.confidence * 100).toFixed(0)}%
                </div>
              )}
            </div>
          </div>

          {recommendations.support_solutions && recommendations.support_solutions.length > 0 && (
            <div className="ai-section">
              <div className="ai-section-header">
                <Lightbulb className="section-icon" />
                <h4>Решения для техподдержки</h4>
              </div>
              <ul className="solutions-list">
                {recommendations.support_solutions.map((solution: string, index: number) => (
                  <li key={index}>{solution}</li>
                ))}
              </ul>
            </div>
          )}
        </>
      ) : (
        <div className="ai-section">
          <p className="no-recommendations">Рекомендации не доступны</p>
        </div>
      )}

      {/* Classification Approval */}
      <div className="ai-section classification-section">
        <h4>Классификация</h4>
        <div className="classification-info">
          <div className="classification-item">
            <span className="label">Категория:</span>
            <span className="value">{ticket.category || 'Не указана'}</span>
          </div>
          <div className="classification-item">
            <span className="label">Приоритет:</span>
            <span className="value">{ticket.priority || 'Не указан'}</span>
          </div>
        </div>

        {!showEditForm ? (
          <div className="classification-actions">
            <button
              onClick={handleApproveClassification}
              disabled={submitting}
              className="btn-approve"
            >
              <Check className="btn-icon" />
              Подтвердить
            </button>
            <button
              onClick={() => setShowEditForm(true)}
              disabled={submitting}
              className="btn-change"
            >
              <Edit className="btn-icon" />
              Изменить
            </button>
          </div>
        ) : (
          <div className="edit-classification-form">
            <div className="form-group">
              <label>Категория:</label>
              <select
                value={editedClassification.category}
                onChange={(e) => setEditedClassification({ ...editedClassification, category: e.target.value })}
              >
                <option value="">Выберите категорию</option>
                <option value="network">Network</option>
                <option value="telephony">Telephony</option>
                <option value="tv">TV</option>
                <option value="billing">Billing</option>
                <option value="equipment">Equipment</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div className="form-group">
              <label>Приоритет:</label>
              <select
                value={editedClassification.priority}
                onChange={(e) => setEditedClassification({ ...editedClassification, priority: e.target.value })}
              >
                <option value="">Выберите приоритет</option>
                <option value="critical">Critical</option>
                <option value="high">High</option>
                <option value="medium">Medium</option>
                <option value="low">Low</option>
              </select>
            </div>
            <div className="form-actions">
              <button
                onClick={handleChangeClassification}
                disabled={submitting}
                className="btn-save"
              >
                {submitting ? <Loader className="spinner" /> : <Check className="btn-icon" />}
                Сохранить
              </button>
              <button
                onClick={() => {
                  setShowEditForm(false)
                  setEditedClassification({
                    category: ticket.category || '',
                    department_id: ticket.department_id || '',
                    priority: ticket.priority || ''
                  })
                }}
                disabled={submitting}
                className="btn-cancel"
              >
                <X className="btn-icon" />
                Отмена
              </button>
            </div>
          </div>
        )}
      </div>

      {ticket.auto_resolved && (
        <div className="ai-section auto-resolved">
          <h4>Автоматическое решение</h4>
          <p>Тикет был автоматически решен системой ИИ</p>
        </div>
      )}
    </div>
  )
}
