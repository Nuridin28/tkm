import { useState, useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { Bot, Play, Square, RotateCw, MessageCircle, Phone } from 'lucide-react'
import { getBots, startBot, stopBot, restartBot } from '../services/api'
import '../styles/BotManager.css'

interface BotStatus {
  type: string
  status: string
  pid?: number
  running: boolean
  memory_mb?: number
  cpu_percent?: number
  started_at?: number
  error?: string
}

export default function BotManager() {
  const { t } = useTranslation()
  const [bots, setBots] = useState<BotStatus[]>([])
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState<string | null>(null)
  const [lastUpdate, setLastUpdate] = useState<number>(Date.now())
  const hasRunningBotsRef = useRef(false)

  const loadBots = async (showLoading = true) => {
    try {
      if (showLoading) {
        setLoading(true)
      }
      const data = await getBots()
      setBots(data)
      setLastUpdate(Date.now())
    } catch (error) {
      console.error('Failed to load bots:', error)
    } finally {
      if (showLoading) {
        setLoading(false)
      }
    }
  }

  useEffect(() => {
    loadBots()
  }, [])

  useEffect(() => {
    hasRunningBotsRef.current = bots.some(bot => bot.running)
  }, [bots])

  useEffect(() => {
    const statsInterval = setInterval(() => {
      if (hasRunningBotsRef.current) {
        loadBots(false)
      }
    }, 3000)

    return () => clearInterval(statsInterval)
  }, [])

  const handleStart = async (botType: string) => {
    try {
      setActionLoading(botType)
      await startBot(botType)
      setTimeout(() => loadBots(false), 1000)
    } catch (error: any) {
      alert(error.response?.data?.detail || `Failed to start ${botType} bot`)
    } finally {
      setActionLoading(null)
    }
  }

  const handleStop = async (botType: string) => {
    try {
      setActionLoading(botType)
      await stopBot(botType)
      setTimeout(() => loadBots(false), 1000)
    } catch (error: any) {
      alert(error.response?.data?.detail || `Failed to stop ${botType} bot`)
    } finally {
      setActionLoading(null)
    }
  }

  const handleRestart = async (botType: string) => {
    try {
      setActionLoading(botType)
      await restartBot(botType)
      setTimeout(() => loadBots(false), 1000)
    } catch (error: any) {
      alert(error.response?.data?.detail || `Failed to restart ${botType} bot`)
    } finally {
      setActionLoading(null)
    }
  }

  const getBotIcon = (type: string) => {
    switch (type) {
      case 'telegram':
        return <MessageCircle className="w-5 h-5" />
      case 'whatsapp':
        return <Phone className="w-5 h-5" />
      default:
        return <Bot className="w-5 h-5" />
    }
  }

  const getBotName = (type: string) => {
    switch (type) {
      case 'telegram':
        return 'Telegram Bot'
      case 'whatsapp':
        return 'WhatsApp Bot'
      default:
        return type
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'bg-green-100 text-green-800'
      case 'stopped':
        return 'bg-gray-100 text-gray-800'
      case 'error':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  if (loading) {
    return (
      <div className="bot-manager">
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-2 text-gray-600">{t('common.loading')}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="bot-manager">
      <div className="bot-manager-header">
        <div>
          <h2>{t('bots.title', 'Управление ботами')}</h2>
          {lastUpdate && (
            <p className="text-xs text-gray-500 mt-1">
              Обновлено: {new Date(lastUpdate).toLocaleTimeString('ru-RU')}
            </p>
          )}
        </div>
        <button
          onClick={() => loadBots(true)}
          className="refresh-button"
          disabled={loading}
        >
          <RotateCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          {t('dashboard.refresh')}
        </button>
      </div>

      <div className="bots-grid">
        {bots.map((bot) => (
          <div key={bot.type} className="bot-card">
            <div className="bot-card-header">
              <div className="bot-info">
                {getBotIcon(bot.type)}
                <div>
                  <h3>{getBotName(bot.type)}</h3>
                  <span className={`status-badge ${getStatusColor(bot.status)}`}>
                    {bot.status === 'running' ? t('bots.running', 'Запущен') :
                     bot.status === 'stopped' ? t('bots.stopped', 'Остановлен') :
                     t('bots.error', 'Ошибка')}
                  </span>
                </div>
              </div>
            </div>

            {bot.running && (
              <div className="bot-stats">
                {bot.pid && (
                  <div className="stat-item-full">
                    <span className="stat-label">PID:</span>
                    <span className="stat-value">{bot.pid}</span>
                  </div>
                )}
                {bot.memory_mb && (
                  <div className="stat-item-full">
                    <span className="stat-label">{t('bots.memory', 'Память')}:</span>
                    <span className="stat-value">{bot.memory_mb} MB</span>
                  </div>
                )}
                {bot.cpu_percent !== undefined && (
                  <div className="stat-item-full">
                    <span className="stat-label">CPU:</span>
                    <span className="stat-value">{bot.cpu_percent.toFixed(1)}%</span>
                  </div>
                )}
              </div>
            )}

            {bot.error && (
              <div className="bot-error">
                <span className="error-text">{bot.error}</span>
              </div>
            )}

            <div className="bot-actions">
              {bot.running ? (
                <>
                  <button
                    onClick={() => handleStop(bot.type)}
                    disabled={actionLoading === bot.type}
                    className="action-button stop-button"
                  >
                    <Square className="w-4 h-4" />
                    {t('bots.stop', 'Остановить')}
                  </button>
                  <button
                    onClick={() => handleRestart(bot.type)}
                    disabled={actionLoading === bot.type}
                    className="action-button restart-button"
                  >
                    <RotateCw className={`w-4 h-4 ${actionLoading === bot.type ? 'animate-spin' : ''}`} />
                    {t('bots.restart', 'Перезапустить')}
                  </button>
                </>
              ) : (
                <button
                  onClick={() => handleStart(bot.type)}
                  disabled={actionLoading === bot.type}
                  className="action-button start-button"
                >
                  <Play className="w-4 h-4" />
                  {t('bots.start', 'Запустить')}
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

