import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  getDepartments, 
  createDepartment, 
  updateDepartment, 
  deleteDepartment 
} from '../services/api'

// Query keys
export const departmentKeys = {
  all: ['departments'] as const,
  lists: () => [...departmentKeys.all, 'list'] as const,
  details: () => [...departmentKeys.all, 'detail'] as const,
  detail: (id: string) => [...departmentKeys.details(), id] as const,
}

// Get all departments
export function useDepartments() {
  return useQuery({
    queryKey: departmentKeys.lists(),
    queryFn: getDepartments,
    staleTime: 5 * 60 * 1000, // 5 минут - департаменты редко меняются
    gcTime: 10 * 60 * 1000, // 10 минут в кэше
    refetchOnWindowFocus: false,
    refetchOnMount: false,
  })
}

// Create department mutation
export function useCreateDepartment() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: createDepartment,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: departmentKeys.lists() })
    },
  })
}

// Update department mutation
export function useUpdateDepartment() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: ({ departmentId, data }: { departmentId: string; data: any }) =>
      updateDepartment(departmentId, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: departmentKeys.detail(variables.departmentId) })
      queryClient.invalidateQueries({ queryKey: departmentKeys.lists() })
    },
  })
}

// Delete department mutation
export function useDeleteDepartment() {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: deleteDepartment,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: departmentKeys.lists() })
    },
  })
}

