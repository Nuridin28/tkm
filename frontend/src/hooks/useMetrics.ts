import { useQuery } from '@tanstack/react-query'
import { getMetrics } from '../services/api'

// Query keys
export const metricsKeys = {
  all: ['metrics'] as const,
  lists: () => [...metricsKeys.all, 'list'] as const,
  list: (params?: any) => [...metricsKeys.lists(), params] as const,
}

// Get metrics
export function useMetrics(params?: any) {
  return useQuery({
    queryKey: metricsKeys.list(params),
    queryFn: () => getMetrics(params),
    staleTime: 60000, // 1 минута - метрики обновляются реже
    gcTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
    refetchOnMount: false,
  })
}

