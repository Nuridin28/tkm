import { useQuery } from '@tanstack/react-query'
import { getMetrics } from '../services/api'

export const metricsKeys = {
  all: ['metrics'] as const,
  lists: () => [...metricsKeys.all, 'list'] as const,
  list: (params?: any) => [...metricsKeys.lists(), params] as const,
}

export function useMetrics(params?: any) {
  return useQuery({
    queryKey: metricsKeys.list(params),
    queryFn: () => getMetrics(params),
    staleTime: 30000,
    gcTime: 5 * 60 * 1000,
    refetchOnWindowFocus: true,
    refetchOnMount: true,
    refetchInterval: 30000,
  })
}

