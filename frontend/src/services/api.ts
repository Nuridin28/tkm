import axios from 'axios'
import { createClient } from '@supabase/supabase-js'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || ''
const SUPABASE_KEY = import.meta.env.VITE_SUPABASE_KEY || ''

const supabase = createClient(SUPABASE_URL, SUPABASE_KEY)

const api = axios.create({
  baseURL: API_BASE_URL,
})

api.interceptors.request.use(async (config) => {
  const { data: { session } } = await supabase.auth.getSession()
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      console.error('API Error:', error.response.status, error.response.data)
    } else if (error.request) {
      console.error('API Error: No response from server', error.request)
    } else {
      console.error('API Error:', error.message)
    }
    return Promise.reject(error)
  }
)

export const getTickets = async (params?: any) => {
  const response = await api.get('/api/tickets', { params })
  return response.data
}

export const getAutoResolvedTickets = async (params?: { limit?: number; offset?: number }) => {
  const response = await api.get('/api/tickets/auto-resolved', { params })
  return response.data
}

export const getTicket = async (id: string) => {
  const response = await api.get(`/api/tickets/${id}`)
  return response.data
}

export const updateTicket = async (id: string, updates: any) => {
  const response = await api.patch(`/api/tickets/${id}`, updates)
  return response.data
}

export const acceptTicket = async (id: string) => {
  const response = await api.post(`/api/tickets/${id}/accept`)
  return response.data
}

export const completeRemote = async (id: string) => {
  const response = await api.post(`/api/tickets/${id}/complete_remote`)
  return response.data
}

export const requestOnSite = async (id: string) => {
  const response = await api.post(`/api/tickets/${id}/request_on_site`)
  return response.data
}

export const getMessages = async (ticketId: string) => {
  const response = await api.get(`/api/tickets/${ticketId}/messages`)
  return response.data
}

export const getMetrics = async (params?: any) => {
  const response = await api.get('/api/admin/metrics', { params })
  return response.data
}

export const processWithAI = async (ticketId: string) => {
  const response = await api.post('/api/ai/process', { ticket_id: ticketId })
  return response.data
}

export const searchKB = async (query: string, k: number = 5) => {
  const response = await api.post('/api/ai/search', { query, k })
  return response.data
}

export const ingestTicket = async (data: any) => {
  const response = await api.post('/api/ingest', data)
  return response.data
}

export const createUser = async (data: {
  email: string
  password: string
  name: string
  role: string
  department_id?: string
}) => {
  const response = await api.post('/api/admin/users', data)
  return response.data
}

export const deleteTicket = async (ticketId: string) => {
  const response = await api.delete(`/api/tickets/${ticketId}`)
  return response.data
}

export const assignTicket = async (ticketId: string, data: {
  assigned_to?: string
  department_id?: string
}) => {
  const response = await api.post(`/api/tickets/${ticketId}/assign`, data)
  return response.data
}

export const getDepartments = async () => {
  const response = await api.get('/api/admin/departments')
  return response.data
}

export const createDepartment = async (data: {
  name: string
  description?: string
}) => {
  const response = await api.post('/api/admin/departments', data)
  return response.data
}

export const updateDepartment = async (departmentId: string, data: {
  name: string
  description?: string
}) => {
  const response = await api.put(`/api/admin/departments/${departmentId}`, data)
  return response.data
}

export const deleteDepartment = async (departmentId: string) => {
  const response = await api.delete(`/api/admin/departments/${departmentId}`)
  return response.data
}

export const getUsers = async () => {
  const response = await api.get('/api/admin/users')
  return response.data
}

export const deleteUser = async (userId: string) => {
  const response = await api.delete(`/api/admin/users/${userId}`)
  return response.data
}

const publicApi = axios.create({
  baseURL: API_BASE_URL,
})

export const sendChatMessage = async (data: {
  message: string
  conversation_history: Array<{ role: string; content: string; timestamp?: string }>
  contact_info?: { phone?: string; email?: string }
}) => {
  const response = await publicApi.post('/api/public/chat', data)
  return response.data
}

export const createTicketFromChat = async (ticketDraft: any) => {
  const response = await publicApi.post('/api/public/chat/create-ticket', ticketDraft)
  return response.data
}

export const getBots = async () => {
  const response = await api.get('/api/admin/bots')
  return response.data
}

export const getBotStatus = async (botType: string) => {
  const response = await api.get(`/api/admin/bots/${botType}/status`)
  return response.data
}

export const startBot = async (botType: string) => {
  const response = await api.post(`/api/admin/bots/${botType}/start`)
  return response.data
}

export const stopBot = async (botType: string) => {
  const response = await api.post(`/api/admin/bots/${botType}/stop`)
  return response.data
}

export const restartBot = async (botType: string) => {
  const response = await api.post(`/api/admin/bots/${botType}/restart`)
  return response.data
}

export const getMonitoringMetrics = async (fromDate?: string, toDate?: string) => {
  const params = new URLSearchParams()
  if (fromDate) params.append('from_date', fromDate)
  if (toDate) params.append('to_date', toDate)

  const response = await api.get(`/api/admin/monitoring/metrics?${params.toString()}`)
  return response.data
}

export const getAIRecommendations = async (ticketId: string) => {
  const response = await api.get(`/api/tickets/${ticketId}/ai-recommendations`)
  return response.data
}

export const getChatHistory = async (ticketId: string) => {
  const response = await api.get(`/api/tickets/${ticketId}/chat-history`)
  return response.data
}

export const submitClassificationFeedback = async (ticketId: string, feedback: {
  is_correct?: boolean
  category?: string
  department_id?: string
  priority?: string
  notes?: string
}) => {
  const response = await api.post(`/api/tickets/${ticketId}/classify-feedback`, feedback)
  return response.data
}

