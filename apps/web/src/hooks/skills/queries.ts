import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { z } from 'zod'
import { requestJson } from '@/lib/api/client'
import { skillKeys } from './keys'

export const SkillMetaSchema = z.object({
  id: z.string().uuid(),
  name: z.string(),
  description: z.string(),
  icon: z.string(),
  color: z.string(),
})

export const SkillSchema = SkillMetaSchema.extend({
  content: z.string(),
  created_at: z.string(),
  updated_at: z.string(),
})

export type SkillMeta = z.infer<typeof SkillMetaSchema>
export type Skill = z.infer<typeof SkillSchema>

const SkillMetaListSchema = z.array(SkillMetaSchema)

export function useSkills() {
  return useQuery({
    queryKey: skillKeys.lists(),
    queryFn: ({ signal }) =>
      requestJson(SkillMetaListSchema, { url: '/skills/', method: 'GET', signal }),
    staleTime: 1000 * 60 * 5,
  })
}

export function useSkill(id: string) {
  return useQuery({
    queryKey: skillKeys.detail(id),
    queryFn: ({ signal }) =>
      requestJson(SkillSchema, { url: `/skills/${id}`, method: 'GET', signal }),
    enabled: !!id,
  })
}

export function useCreateSkill() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: { name: string; description?: string; icon?: string; color?: string; content: string }) =>
      requestJson(SkillSchema, { url: '/skills/', method: 'POST', data }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: skillKeys.lists() })
    },
  })
}

export function useUpdateSkill() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      id,
      ...data
    }: { id: string; name?: string; description?: string; icon?: string; color?: string; content?: string }) =>
      requestJson(SkillSchema, { url: `/skills/${id}`, method: 'PUT', data }),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: skillKeys.lists() })
      queryClient.invalidateQueries({ queryKey: skillKeys.detail(id) })
    },
  })
}

export function useDeleteSkill() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) =>
      requestJson(z.any(), { url: `/skills/${id}`, method: 'DELETE' }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: skillKeys.lists() })
    },
  })
}
