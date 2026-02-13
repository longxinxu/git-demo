import { create } from 'zustand';

type Role = 'user' | 'admin';

interface AppState {
  role: Role;
  keyword: string;
  category: string;
  setRole: (role: Role) => void;
  setKeyword: (keyword: string) => void;
  setCategory: (category: string) => void;
}

export const useAppStore = create<AppState>((set) => ({
  role: 'user',
  keyword: '',
  category: '全部',
  setRole: (role) => set({ role }),
  setKeyword: (keyword) => set({ keyword }),
  setCategory: (category) => set({ category })
}));
