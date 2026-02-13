import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';
import { api } from '../api/client';

export function UploadForm() {
  const qc = useQueryClient();
  const [form, setForm] = useState({ title: '', category: '工具教程', summary: '', body: '' });
  const mutation = useMutation({
    mutationFn: api.createContent,
    onSuccess: () => {
      setForm({ title: '', category: '工具教程', summary: '', body: '' });
      qc.invalidateQueries({ queryKey: ['dashboard'] });
    }
  });
  return <form onSubmit={(e) => { e.preventDefault(); mutation.mutate(form); }}>
    <h3>上传你的内容</h3>
    <input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder='标题' required />
    <input value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} placeholder='分类' required />
    <input value={form.summary} onChange={(e) => setForm({ ...form, summary: e.target.value })} placeholder='摘要' required />
    <textarea value={form.body} onChange={(e) => setForm({ ...form, body: e.target.value })} placeholder='正文' required />
    <button type='submit'>{mutation.isPending ? '提交中...' : '提交内容'}</button>
  </form>;
}
