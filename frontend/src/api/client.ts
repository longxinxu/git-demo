import type { ContentItem, DashboardResponse, LearningPathStep, SyncConfig } from '../types/api';

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, { headers: { 'Content-Type': 'application/json' }, ...init });
  if (!res.ok) throw new Error(await res.text());
  return res.json() as Promise<T>;
}

export const api = {
  dashboard: () => request<DashboardResponse>('/api/dashboard'),
  listContents: (status?: string) => request<ContentItem[]>(`/api/contents${status ? `?status=${status}` : ''}`),
  createContent: (payload: { title: string; category: string; summary: string; body: string }) =>
    request<{ id: number; item: ContentItem }>('/api/contents', { method: 'POST', body: JSON.stringify(payload) }),
  triggerSync: () => request<{ message: string; reviewed: number }>('/api/admin/trigger-sync', { method: 'POST' }),
  listFavorites: (userId = 1) => request<ContentItem[]>(`/api/favorites?user_id=${userId}`),
  addFavorite: (contentId: number, userId = 1) => request('/api/favorites/' + contentId, { method: 'POST', body: JSON.stringify({ user_id: userId }) }),
  removeFavorite: (contentId: number, userId = 1) => request('/api/favorites/' + contentId + `?user_id=${userId}`, { method: 'DELETE' }),
  learningPath: () => request<{ path: LearningPathStep[]; generated_at: string }>('/api/learning-path'),
  reviewQueue: () => request<ContentItem[]>('/api/admin/review-queue'),
  decide: (contentId: number, status: 'approved' | 'rejected') => request('/api/admin/reviews/' + contentId, { method: 'POST', body: JSON.stringify({ status, score: status === 'approved' ? 90 : 40 }) }),
  reports: () => request<{ id: number; reason: string; content_item_id: number; created_at: string }[]>('/api/admin/reports'),
  syncConfig: () => request<SyncConfig>('/api/admin/sync-config'),
  setSyncConfig: (payload: SyncConfig) => request<SyncConfig>('/api/admin/sync-config', { method: 'PUT', body: JSON.stringify(payload) })
};
