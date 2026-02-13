export type ContentStatus = 'pending' | 'approved' | 'rejected' | 'archived';

export interface ContentItem {
  id: number;
  title: string;
  category: string;
  summary: string;
  body: string;
  quality_score: number;
  status: ContentStatus;
  source: string;
  created_at: string;
  last_reviewed_at?: string | null;
}

export interface ResourceUpdate { id: number; title: string; url: string; summary: string; fetched_at: string; }
export interface DashboardStats { total: number; approved: number; pending: number; last_sync: string; }
export interface DashboardResponse { contents: ContentItem[]; updates: ResourceUpdate[]; stats: DashboardStats; }
export interface SyncConfig { enabled: boolean; interval_minutes: number; updated_at?: string | null; }
export interface LearningPathStep { category: string; items: ContentItem[]; }
