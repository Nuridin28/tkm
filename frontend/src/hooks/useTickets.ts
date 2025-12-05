import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getTickets, deleteTicket, assignTicket, updateTicket } from '../services/api'

// Query keys
export const ticketKeys = {
  all: ['tickets'] as const,
  lists: () => [...ticketKeys.all, 'list'] as const,
  list: (filters?: any) => [...ticketKeys.lists(), filters] as const,
  details: () => [...ticketKeys.all, 'detail'] as const,
  detail: (id: string) => [...ticketKeys.details(), id] as const,
}

// Get all tickets
export function useTickets(filters?: any) {
  return useQuery({
    queryKey: ticketKeys.list(filters),
    queryFn: () => getTickets(filters),
    staleTime: 30000, // 30 секунд - данные считаются свежими
    gcTime: 5 * 60 * 1000, // 5 минут - время хранения в кэше
    refetchOnWindowFocus: false, // Не обновлять при фокусе окна
    refetchOnMount: false, // Не обновлять при монтировании если данные свежие
  })
}

// Get single ticket
export function useTicket(id: string) {
  return useQuery({
    queryKey: ticketKeys.detail(id),
    queryFn: () => getTickets().then(tickets => tickets.find((t: any) => t.id === id)),
    enabled: !!id,
    staleTime: 30000,
    gcTime: 5 * 60 * 1000,
  })
}

// Delete ticket mutation
export function useDeleteTicket() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: deleteTicket,
    onSuccess: () => {
      // Инвалидировать все списки тикетов
      queryClient.invalidateQueries({ queryKey: ticketKeys.lists() })
    },
  })
}

// Assign ticket mutation
export function useAssignTicket() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ ticketId, data }: { ticketId: string; data: any }) => 
      assignTicket(ticketId, data),
    onSuccess: (_, variables) => {
      // Инвалидировать конкретный тикет и список
      queryClient.invalidateQueries({ queryKey: ticketKeys.detail(variables.ticketId) })
      queryClient.invalidateQueries({ queryKey: ticketKeys.lists() })
    },
  })
}

// Update ticket mutation
export function useUpdateTicket() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ ticketId, updates }: { ticketId: string; updates: any }) =>
      updateTicket(ticketId, updates),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ticketKeys.detail(variables.ticketId) })
      queryClient.invalidateQueries({ queryKey: ticketKeys.lists() })
    },
  })
}

