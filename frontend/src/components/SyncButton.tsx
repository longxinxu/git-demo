import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';

export function SyncButton() {
  const qc = useQueryClient();
  const mutation = useMutation({ mutationFn: api.triggerSync, onSuccess: () => qc.invalidateQueries({ queryKey: ['dashboard'] }) });
  return <button onClick={() => mutation.mutate()}>{mutation.isPending ? '同步中...' : '立即同步'}</button>;
}
