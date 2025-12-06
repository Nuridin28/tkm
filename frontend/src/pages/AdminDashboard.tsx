import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import { useTickets } from '../hooks/useTickets'
import { useMetrics } from '../hooks/useMetrics'
import { useDepartments } from '../hooks/useDepartments'
import { useTranslation } from 'react-i18next'
import TicketCard from '../components/TicketCard'
import TicketActions from '../components/TicketActions'
import MetricsCards from '../components/MetricsCards'
import RegisterUser from './RegisterUser'
import DepartmentManager from '../components/DepartmentManager'
import UserList from '../components/UserList'
import LanguageSwitcher from '../components/LanguageSwitcher'
import { LogOut, User, Ticket, Building, Settings, Plus, RefreshCw, Bot, BarChart3, Zap } from 'lucide-react'
import BotManager from '../components/BotManager'
import MonitoringPanel from '../components/MonitoringPanel'
import AutoResolvedTickets from '../components/AutoResolvedTickets'
import Logo from '../components/Logo'
import '../styles/AdminDashboard.css'

export default function AdminDashboard() {
  const { user, userProfile, signOut } = useAuth()
  const navigate = useNavigate()
  const { t } = useTranslation()
  const [showRegister, setShowRegister] = useState(false)
  const [activeTab, setActiveTab] = useState<'tickets' | 'auto-resolved' | 'users' | 'departments' | 'bots' | 'monitoring' | 'settings'>('tickets')

  const { data: tickets = [], isLoading: ticketsLoading, refetch: refetchTickets } = useTickets()
  const { data: metrics, isLoading: metricsLoading } = useMetrics()
  const { data: departments = [], isLoading: departmentsLoading } = useDepartments()

  const loading = ticketsLoading || metricsLoading || departmentsLoading

  const loadData = () => {
    refetchTickets()
  }

  const handleLogout = async () => {
    await signOut()
    navigate('/login')
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-blue-50">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <div className="text-gray-700 font-medium">{t('common.loading')}</div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-blue-50">
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-2 sm:px-4 lg:px-8">
          <div className="flex justify-between items-center h-16 min-h-[4rem]">
            <div className="flex items-center gap-2 sm:gap-4 lg:gap-6 flex-1 min-w-0">
              <div className="hidden sm:block">
                <Logo height={40} />
              </div>
              <h1 className="text-lg sm:text-xl lg:text-2xl font-bold text-[#0066CC] whitespace-nowrap">
                {t('admin.title')}
              </h1>
              <nav className="flex gap-0.5 sm:gap-1 overflow-x-auto scrollbar-hide flex-1 min-w-0">
                {[
                  { id: 'tickets', icon: Ticket, label: t('dashboard.tickets') },
                  { id: 'auto-resolved', icon: Zap, label: 'Авторешения' },
                  { id: 'users', icon: User, label: t('dashboard.users') },
                  { id: 'departments', icon: Building, label: t('dashboard.departments') },
                  { id: 'bots', icon: Bot, label: t('bots.title', 'Боты') },
                  { id: 'monitoring', icon: BarChart3, label: 'Мониторинг' },
                  { id: 'settings', icon: Settings, label: t('dashboard.settings') },
                ].map(({ id, icon: Icon, label }) => (
                  <button
                    key={id}
                    onClick={() => setActiveTab(id as any)}
                    className={`flex items-center gap-1 sm:gap-2 px-2 sm:px-3 lg:px-4 py-2 rounded-lg text-xs sm:text-sm font-medium transition-colors whitespace-nowrap flex-shrink-0 ${
                      activeTab === id
                        ? 'bg-blue-100 text-blue-700'
                        : 'text-gray-600 hover:bg-blue-50'
                    }`}
                    title={label}
                  >
                    <Icon className="w-3 h-3 sm:w-4 sm:h-4" />
                    <span className="hidden sm:inline">{label}</span>
                  </button>
                ))}
              </nav>
            </div>
            <div className="flex items-center gap-1 sm:gap-2 lg:gap-4 flex-shrink-0 ml-2">
              <div className="hidden sm:block">
                <LanguageSwitcher />
              </div>
              <button
                onClick={() => setShowRegister(true)}
                className="flex items-center gap-1 sm:gap-2 px-2 sm:px-3 lg:px-4 py-2 bg-[#0066CC] text-white rounded-lg text-xs sm:text-sm font-medium hover:bg-[#0052A3] transition-colors whitespace-nowrap"
                title={t('users.addUser')}
              >
                <Plus className="w-3 h-3 sm:w-4 sm:h-4" />
                <span className="hidden lg:inline">{t('users.addUser')}</span>
              </button>
              <div className="hidden md:flex items-center gap-2 text-gray-700">
                <User className="w-4 h-4" />
                <span className="text-xs lg:text-sm font-medium truncate max-w-[100px] lg:max-w-none">
                  {userProfile?.name || user?.email}
                </span>
              </div>
              <button
                onClick={handleLogout}
                className="flex items-center gap-1 sm:gap-2 px-2 sm:px-3 lg:px-4 py-2 text-xs sm:text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-colors whitespace-nowrap"
                title={t('auth.logout')}
              >
                <LogOut className="w-3 h-3 sm:w-4 sm:h-4" />
                <span className="hidden lg:inline">{t('auth.logout')}</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'tickets' && (
          <>
            {metrics && <MetricsCards metrics={metrics} />}
            <section className="mt-8">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-semibold text-gray-900">{t('dashboard.allTickets')}</h2>
                <button
                  onClick={loadData}
                  className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  <RefreshCw className="w-4 h-4" />
                  {t('dashboard.refresh')}
                </button>
              </div>
              {tickets.length === 0 ? (
                <div className="bg-white rounded-xl shadow-sm p-12 text-center">
                  <Ticket className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <p className="text-lg font-medium text-gray-900 mb-2">{t('dashboard.noTickets')}</p>
                  <p className="text-sm text-gray-500">{t('dashboard.noTickets')}</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {tickets.map((ticket: any) => (
                    <div key={ticket.id} className="flex flex-col">
                      <TicketCard
                        ticket={ticket}
                        onClick={() => navigate(`/tickets/${ticket.id}`)}
                      />
                      <div className="mt-2">
                        <TicketActions
                          ticket={ticket}
                          onUpdate={loadData}
                          departments={departments}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </>
        )}

        {activeTab === 'users' && (
          <section>
            <UserList />
          </section>
        )}

        {activeTab === 'departments' && (
          <section>
            <DepartmentManager />
          </section>
        )}

        {activeTab === 'bots' && (
          <section>
            <BotManager />
          </section>
        )}

        {activeTab === 'auto-resolved' && (
          <section>
            <AutoResolvedTickets />
          </section>
        )}

        {activeTab === 'monitoring' && (
          <section>
            <MonitoringPanel />
          </section>
        )}

        {activeTab === 'settings' && (
          <section>
            <div className="bg-white rounded-xl shadow-sm p-12 text-center">
              <Settings className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <p className="text-lg font-medium text-gray-900 mb-2">{t('dashboard.settings')}</p>
              <p className="text-sm text-gray-500">{t('dashboard.settings')}</p>
            </div>
          </section>
        )}
      </main>

      {showRegister && (
        <RegisterUser
          onClose={() => setShowRegister(false)}
          onSuccess={() => {
            setShowRegister(false)
          }}
        />
      )}
    </div>
  )
}
