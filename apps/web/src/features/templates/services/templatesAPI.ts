import apiClient from '@/shared/utils/apiClient'
import type {
  InstallTemplateResponse,
  PublishTemplateInput,
  TemplateCategoryListResponse,
  TemplateDetail,
  TemplateListItem,
  TemplateListResponse,
  TemplateSort,
  UpdateTemplateInput,
} from '../types/templatesTypes'

export interface ListTemplatesParams {
  category?: string
  kind?: string
  q?: string
  sort?: TemplateSort
  limit?: number
  offset?: number
}

export const templatesAPI = {
  list: async (params: ListTemplatesParams = {}): Promise<TemplateListResponse> => {
    const res = await apiClient.get<TemplateListResponse>('/templates/', {
      params: {
        category: params.category || undefined,
        kind: params.kind || undefined,
        q: params.q || undefined,
        sort: params.sort,
        limit: params.limit,
        offset: params.offset,
      },
    })
    return res.data
  },

  categories: async (): Promise<TemplateCategoryListResponse> => {
    const res = await apiClient.get<TemplateCategoryListResponse>(
      '/templates/categories',
    )
    return res.data
  },

  mine: async (): Promise<TemplateListItem[]> => {
    const res = await apiClient.get<TemplateListItem[]>('/templates/mine')
    return res.data
  },

  detail: async (slugOrId: string): Promise<TemplateDetail> => {
    const res = await apiClient.get<TemplateDetail>(`/templates/${slugOrId}`)
    return res.data
  },

  publish: async (data: PublishTemplateInput): Promise<TemplateListItem> => {
    const res = await apiClient.post<TemplateListItem>('/templates/publish', data)
    return res.data
  },

  update: async (
    id: string,
    data: UpdateTemplateInput,
  ): Promise<TemplateListItem> => {
    const res = await apiClient.put<TemplateListItem>(`/templates/${id}`, data)
    return res.data
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/templates/${id}`)
  },

  install: async (slugOrId: string): Promise<InstallTemplateResponse> => {
    const res = await apiClient.post<InstallTemplateResponse>(
      `/templates/${slugOrId}/install`,
    )
    return res.data
  },

  purchase: async (slugOrId: string): Promise<void> => {
    // Endpoint returns 501 Not Implemented; the caller catches and shows
    // the "Coming soon" toast. Stripe wiring lands in a follow-up.
    await apiClient.post(`/templates/${slugOrId}/purchase`)
  },
}
