import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { ArrowLeft, Bot, MessageCircle, Ticket, Clock } from 'lucide-react'
import AIChat from '../components/AIChat'
import LanguageSwitcher from '../components/LanguageSwitcher'
import '../styles/PublicSupport.css'

export default function PublicSupport() {
  const { t } = useTranslation()
  const [showChat, setShowChat] = useState(false)
  const [contactInfo, setContactInfo] = useState({
    phone: '',
    email: ''
  })

  const handleStartChat = (e: React.FormEvent) => {
    e.preventDefault()
    if (contactInfo.phone || contactInfo.email) {
      setShowChat(true)
    }
  }

  const handleBack = () => {
    setShowChat(false)
  }

  if (showChat) {
    return (
      <div className="public-support">
      <div className="support-container">
        <div className="header-actions">
          <button onClick={handleBack} className="back-button">
            <ArrowLeft size={18} />
            {t('support.backToForm')}
          </button>
          <LanguageSwitcher />
        </div>
        <AIChat contactInfo={contactInfo} />
      </div>
      </div>
    )
  }

  return (
    <div className="public-support">
      <div className="support-container">
        <div className="header-actions">
          <LanguageSwitcher />
        </div>
        <div className="support-header">
          <h1>{t('support.title')}</h1>
          <p>{t('support.subtitle')}</p>
        </div>

        <form onSubmit={handleStartChat} className="contact-form">
          <div className="form-group">
            <label htmlFor="phone">{t('support.phone')} *</label>
            <input
              type="tel"
              id="phone"
              value={contactInfo.phone}
              onChange={(e) => setContactInfo({ ...contactInfo, phone: e.target.value })}
              placeholder={t('support.phonePlaceholder')}
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="email">{t('support.email')}</label>
            <input
              type="email"
              id="email"
              value={contactInfo.email}
              onChange={(e) => setContactInfo({ ...contactInfo, email: e.target.value })}
              placeholder={t('support.emailPlaceholder')}
            />
          </div>

          <button 
            type="submit" 
            className="start-chat-button"
            style={{ color: 'white', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' }}
          >
            {t('support.startChat')}
          </button>
        </form>

        <div className="info-section">
          <h3>{t('support.howItWorks')}</h3>
          <ul>
            <li>
              <Bot size={18} />
              <span>{t('support.howItWorks1')}</span>
            </li>
            <li>
              <MessageCircle size={18} />
              <span>{t('support.howItWorks2')}</span>
            </li>
            <li>
              <Ticket size={18} />
              <span>{t('support.howItWorks3')}</span>
            </li>
            <li>
              <Clock size={18} />
              <span>{t('support.howItWorks4')}</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  )
}

