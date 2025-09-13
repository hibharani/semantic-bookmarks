import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User, LoginCredentials, RegisterData } from '../types';
import { authAPI } from '../utils/api';

interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  login: (credentials: LoginCredentials) => Promise<void>;
  register: (userData: RegisterData) => Promise<void>;
  logout: () => void;
  getCurrentUser: () => Promise<void>;
  clearError: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isLoading: false,
      error: null,
      
      login: async (credentials: LoginCredentials) => {
        set({ isLoading: true, error: null });
        try {
          const authToken = await authAPI.login(credentials);
          localStorage.setItem('access_token', authToken.access_token);
          set({ token: authToken.access_token });
          
          // Get user info
          await get().getCurrentUser();
        } catch (error: any) {
          set({ 
            error: error.response?.data?.detail || 'Login failed',
            isLoading: false 
          });
          throw error;
        }
      },
      
      register: async (userData: RegisterData) => {
        set({ isLoading: true, error: null });
        try {
          const user = await authAPI.register(userData);
          set({ user, isLoading: false });
        } catch (error: any) {
          set({ 
            error: error.response?.data?.detail || 'Registration failed',
            isLoading: false 
          });
          throw error;
        }
      },
      
      logout: () => {
        localStorage.removeItem('access_token');
        set({ user: null, token: null, error: null });
      },
      
      getCurrentUser: async () => {
        const token = localStorage.getItem('access_token');
        if (!token) return;
        
        set({ isLoading: true });
        try {
          const user = await authAPI.getCurrentUser();
          set({ user, token, isLoading: false });
        } catch (error: any) {
          set({ 
            error: error.response?.data?.detail || 'Failed to get user',
            isLoading: false 
          });
          // If token is invalid, clear it
          if (error.response?.status === 401) {
            get().logout();
          }
        }
      },
      
      clearError: () => set({ error: null }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ 
        token: state.token,
        user: state.user 
      }),
    }
  )
);