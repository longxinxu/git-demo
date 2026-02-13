import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AdminPortal } from './admin/AdminPortal';
import { UserPortal } from './user/UserPortal';
import { useAppStore } from './store/useAppStore';

const qc = new QueryClient();

export default function App() {
  const { role, setRole } = useAppStore();
  return <QueryClientProvider client={qc}>
    <header>
      <h1>AI Coding 学习平台</h1>
      <button onClick={() => setRole('user')}>用户端</button>
      <button onClick={() => setRole('admin')}>管理端</button>
    </header>
    {role === 'user' ? <UserPortal /> : <AdminPortal />}
  </QueryClientProvider>;
}
