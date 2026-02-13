import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';

export function AdminPortal() {
  const qc = useQueryClient();
  const queue = useQuery({ queryKey: ['queue'], queryFn: api.reviewQueue });
  const reports = useQuery({ queryKey: ['reports'], queryFn: api.reports });
  const syncConfig = useQuery({ queryKey: ['sync-config'], queryFn: api.syncConfig });
  const decide = useMutation({ mutationFn: ({ id, status }: { id: number; status: 'approved' | 'rejected' }) => api.decide(id, status), onSuccess: () => qc.invalidateQueries({ queryKey: ['queue'] }) });

  return <main>
    <h2>管理端：审核队列/举报处理/资源同步配置</h2>
    <h3>审核队列</h3>
    {(queue.data ?? []).map((item) => <div key={item.id}><span>{item.title}</span>
      <button onClick={() => decide.mutate({ id: item.id, status: 'approved' })}>通过</button>
      <button onClick={() => decide.mutate({ id: item.id, status: 'rejected' })}>拒绝</button>
    </div>)}
    <h3>举报处理</h3>
    {(reports.data ?? []).map((r) => <p key={r.id}>#{r.id} 内容{r.content_item_id}: {r.reason}</p>)}
    <h3>资源同步配置</h3>
    <p>enabled: {String(syncConfig.data?.enabled)} / interval: {syncConfig.data?.interval_minutes}m</p>
  </main>;
}
