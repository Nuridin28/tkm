import { useQuery } from '@tanstack/react-query'
import { getMetrics } from '../services/api'

// Query keys
export const metricsKeys = {
  all: ['metrics'] as const,
  lists: () => [...metricsKeys.all, 'list'] as const,
  list: (params?: any) => [...metricsKeys.lists(), params] as const,
}

// Get metrics with auto-refresh
export function useMetrics(params?: any) {
  return useQuery({
    queryKey: metricsKeys.list(params),
    queryFn: () => getMetrics(params),
    staleTime: 30000, // 30 секунд - данные считаются свежими
    gcTime: 5 * 60 * 1000,
    refetchOnWindowFocus: true, // Обновлять при фокусе окна
    refetchOnMount: true, // Обновлять при монтировании
    refetchInterval: 30000, // Автообновление каждые 30 секунд
  })
}

