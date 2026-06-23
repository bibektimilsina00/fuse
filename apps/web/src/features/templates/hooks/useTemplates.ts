import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { templatesAPI, type ListTemplatesParams } from '../services/templatesAPI'
import type {
  PublishTemplateInput,
  TemplateDetail,
  TemplateListItem,
  TemplateListResponse,
  UpdateTemplateInput,
} from '../types/templatesTypes'

/** Marketplace grid — paginated, filterable. */
export function useTemplates(params: ListTemplatesParams = {}) {
  return useQuery<TemplateListResponse>({
    queryKey: ['templates', 'list', params],
    queryFn: () => templatesAPI.list(params),
    placeholderData: (prev) => prev,
  })
}

/** Distinct category counts for filter chips. */
export function useTemplateCategories() {
  return useQuery({
    queryKey: ['templates', 'categories'],
    queryFn: () => templatesAPI.categories(),
  })
}

/** Caller's own templates (drafts + published). */
export function useMyTemplates() {
  return useQuery<TemplateListItem[]>({
    queryKey: ['templates', 'mine'],
    queryFn: templatesAPI.mine,
  })
}

/** Detail page fetch by slug or UUID. */
export function useTemplateDetail(slugOrId: string | undefined | null) {
  return useQuery<TemplateDetail>({
    queryKey: ['templates', 'detail', slugOrId],
    queryFn: () => templatesAPI.detail(slugOrId!),
    enabled: Boolean(slugOrId),
  })
}

export function usePublishTemplate() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: PublishTemplateInput) => templatesAPI.publish(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['templates'] })
    },
  })
}

export function useUpdateTemplate() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (args: { id: string; data: UpdateTemplateInput }) =>
      templatesAPI.update(args.id, args.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['templates'] })
    },
  })
}

export function useDeleteTemplate() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => templatesAPI.delete(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['templates'] })
    },
  })
}

export function useInstallTemplate() {
  return useMutation({
    mutationFn: (slugOrId: string) => templatesAPI.install(slugOrId),
  })
}
