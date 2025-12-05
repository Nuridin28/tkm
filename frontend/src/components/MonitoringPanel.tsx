import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Target, TrendingUp, Clock, AlertTriangle, RefreshCw } from 'lucide-react'
import { getMonitoringMetrics } from '../services/api'
import '../styles/MonitoringPanel.css'

interface MonitoringMetrics {
  classification_accuracy: {
    total_classifications: number
    correct_classifications: number
    accuracy_percentage: number
    by_category: Record<string, number>
    by_department: Record<string, number>
  }
  auto_resolve_stats: {
    total_auto_resolved: number
    total_tickets: number
    auto_resolve_rate: number
    avg_confidence: number
    by_category: Record<string, number>
  }
  response_time_stats: {
    avg_response_time_seconds: number
    median_response_time_seconds: number
    p95_response_time_seconds: number
    by_source: Record<string, number>
    by_department: Record<string, number>
  }
  routing_error_stats: {
    total_routing_errors: number
    error_rate: number
    by_error_type: Record<string, number>
    by_department: Record<string, number>
  }
  period_from: string
  period_to: string
}

export default function MonitoringPanel() {
  const { t } = useTranslation()
  const [metrics, setMetrics] = useState<MonitoringMetrics | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadMetrics()
  }, [])

  const loadMetrics = async () => {
    try {
      setLoading(true)
      const data = await getMonitoringMetrics()
      setMetrics(data)
    } catch (error) {
      console.error('Failed to load monitoring metrics:', error)
    } finally {
      setLoading(false)
    }
  }

  const formatTime = (seconds: number) => {
    if (!seconds || seconds === 0) return '0с'
    if (seconds < 60) return `${seconds.toFixed(0)}с`
    if (seconds < 3600) return `${(seconds / 60).toFixed(1)}мин`
    return `${(seconds / 3600).toFixed(1)}ч`
  }

  if (loading) {
    return (
      <div className="monitoring-panel">
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">{t('common.loading')}</p>
        </div>
      </div>
    )
  }

  if (!metrics) {
    return (
      <div className="monitoring-panel">
        <div className="text-center py-8">
          <p className="text-gray-600">Нет данных для отображения</p>
        </div>
      </div>
    )
  }

  return (
    <div className="monitoring-panel">
      <div className="monitoring-header">
        <div>
          <h2>Панель мониторинга AI</h2>
          <p className="text-sm text-gray-500 mt-1">
            Период: {new Date(metrics.period_from).toLocaleDateString('ru-RU')} - {new Date(metrics.period_to).toLocaleDateString('ru-RU')}
          </p>
        </div>
        <button onClick={loadMetrics} className="refresh-button" disabled={loading}>
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          {t('dashboard.refresh')}
        </button>
      </div>

      <div className="metrics-grid">
        {/* Точность классификации */}
        <div className="metric-card">
          <div className="metric-header">
            <Target className="metric-icon" />
            <h3>Точность классификации</h3>
          </div>
          <div className={`metric-value ${metrics.classification_accuracy.accuracy_percentage >= 80 ? 'good' : metrics.classification_accuracy.accuracy_percentage >= 60 ? 'medium' : 'bad'}`}>
            {metrics.classification_accuracy.accuracy_percentage.toFixed(1)}%
          </div>
          <div className="metric-details">
            <p className="metric-stat">
              Правильно: <strong>{metrics.classification_accuracy.correct_classifications}</strong> / 
              <strong> {metrics.classification_accuracy.total_classifications}</strong>
            </p>
            {Object.keys(metrics.classification_accuracy.by_category).length > 0 && (
              <div className="breakdown">
                <strong className="breakdown-title">По категориям:</strong>
                {Object.entries(metrics.classification_accuracy.by_category).map(([cat, acc]) => (
                  <div key={cat} className="breakdown-item">
                    <span className="breakdown-label">{cat}:</span>
                    <span className="breakdown-value">{acc.toFixed(1)}%</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Автоматические решения */}
        <div className="metric-card">
          <div className="metric-header">
            <TrendingUp className="metric-icon" />
            <h3>Автоматические решения</h3>
          </div>
          <div className={`metric-value ${metrics.auto_resolve_stats.auto_resolve_rate >= 30 ? 'good' : metrics.auto_resolve_stats.auto_resolve_rate >= 15 ? 'medium' : 'bad'}`}>
            {metrics.auto_resolve_stats.auto_resolve_rate.toFixed(1)}%
          </div>
          <div className="metric-details">
            <p className="metric-stat">
              Авторешено: <strong>{metrics.auto_resolve_stats.total_auto_resolved}</strong> / 
              <strong> {metrics.auto_resolve_stats.total_tickets}</strong>
            </p>
            <p className="metric-stat">
              Средняя уверенность: <strong>{(metrics.auto_resolve_stats.avg_confidence * 100).toFixed(1)}%</strong>
            </p>
            {Object.keys(metrics.auto_resolve_stats.by_category).length > 0 && (
              <div className="breakdown">
                <strong className="breakdown-title">По категориям:</strong>
                {Object.entries(metrics.auto_resolve_stats.by_category).map(([cat, count]) => (
                  <div key={cat} className="breakdown-item">
                    <span className="breakdown-label">{cat}:</span>
                    <span className="breakdown-value">{count}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Время ответа */}
        <div className="metric-card">
          <div className="metric-header">
            <Clock className="metric-icon" />
            <h3>Время ответа</h3>
          </div>
          <div className="metric-value">
            {formatTime(metrics.response_time_stats.avg_response_time_seconds)}
          </div>
          <div className="metric-details">
            <p className="metric-stat">
              Медиана: <strong>{formatTime(metrics.response_time_stats.median_response_time_seconds)}</strong>
            </p>
            <p className="metric-stat">
              P95: <strong>{formatTime(metrics.response_time_stats.p95_response_time_seconds)}</strong>
            </p>
            {Object.keys(metrics.response_time_stats.by_source).length > 0 && (
              <div className="breakdown">
                <strong className="breakdown-title">По источникам:</strong>
                {Object.entries(metrics.response_time_stats.by_source).map(([source, time]) => (
                  <div key={source} className="breakdown-item">
                    <span className="breakdown-label">{source}:</span>
                    <span className="breakdown-value">{formatTime(time)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Ошибки маршрутизации */}
        <div className="metric-card">
          <div className="metric-header">
            <AlertTriangle className="metric-icon" />
            <h3>Ошибки маршрутизации</h3>
          </div>
          <div className={`metric-value ${metrics.routing_error_stats.error_rate < 5 ? 'good' : metrics.routing_error_stats.error_rate < 10 ? 'medium' : 'bad'}`}>
            {metrics.routing_error_stats.error_rate.toFixed(2)}%
          </div>
          <div className="metric-details">
            <p className="metric-stat">
              Всего ошибок: <strong>{metrics.routing_error_stats.total_routing_errors}</strong>
            </p>
            {Object.keys(metrics.routing_error_stats.by_error_type).length > 0 && (
              <div className="breakdown">
                <strong className="breakdown-title">По типам:</strong>
                {Object.entries(metrics.routing_error_stats.by_error_type).map(([type, count]) => (
                  <div key={type} className="breakdown-item">
                    <span className="breakdown-label">{type}:</span>
                    <span className="breakdown-value">{count}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

