import '../styles/AiAssistantPanel.css'

interface AiAssistantPanelProps {
  ticket: any
}

export default function AiAssistantPanel({ ticket }: AiAssistantPanelProps) {
  return (
    <div className="ai-assistant-panel">
      <h3>ИИ Ассистент</h3>
      {ticket.summary && (
        <div className="ai-section">
          <h4>Резюме</h4>
          <p>{ticket.summary}</p>
        </div>
      )}
      {ticket.auto_resolved && (
        <div className="ai-section">
          <h4>Автоматическое решение</h4>
          <p>Тикет был автоматически решен системой ИИ</p>
        </div>
      )}
      <div className="ai-section">
        <h4>Рекомендации</h4>
        <p>Проверьте классификацию и при необходимости скорректируйте</p>
      </div>
    </div>
  )
}

