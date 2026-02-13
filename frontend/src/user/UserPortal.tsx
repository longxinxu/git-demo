import { useQuery, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';
import { ContentCard } from '../components/ContentCard';
import { SyncButton } from '../components/SyncButton';
import { UploadForm } from '../components/UploadForm';
import { useAppStore } from '../store/useAppStore';

export function UserPortal() {
  const qc = useQueryClient();
  const { keyword, category, setKeyword, setCategory } = useAppStore();
  const { data } = useQuery({ queryKey: ['dashboard'], queryFn: api.dashboard });
  const { data: learningPath } = useQuery({ queryKey: ['learningPath'], queryFn: api.learningPath });

  const filtered = (data?.contents ?? []).filter((it) =>
    it.status === 'approved' &&
    (category === '全部' || it.category === category) &&
    it.title.includes(keyword)
  );

  return <main>
    <h2>用户端：内容浏览/上传/收藏/学习路径</h2>
    <input placeholder='搜索标题' value={keyword} onChange={(e) => setKeyword(e.target.value)} />
    <select value={category} onChange={(e) => setCategory(e.target.value)}>
      <option>全部</option><option>工具教程</option><option>实战案例</option><option>skills</option>
    </select>
    {filtered.map((item) => <ContentCard key={item.id} item={item} onFavorite={async (id) => { await api.addFavorite(id); qc.invalidateQueries({ queryKey: ['favorites'] }); }} />)}
    <UploadForm />
    <SyncButton />
    <h3>学习路径</h3>
    {(learningPath?.path ?? []).map((step) => <p key={step.category}>{step.category}: {step.items.length} 项</p>)}
  </main>;
}
