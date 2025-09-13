import axios from 'axios';
import { AuthToken, LoginCredentials, RegisterData, User, Bookmark, BookmarkCreate, BookmarkUpdate, SearchQuery, SearchResult } from '../types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

const api = axios.create({
  baseURL: API_BASE_URL,
});

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/auth/login';
    }
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  login: (credentials: LoginCredentials): Promise<AuthToken> =>
    api.post('/auth/login', credentials).then(res => res.data),
  
  register: (userData: RegisterData): Promise<User> =>
    api.post('/auth/register', userData).then(res => res.data),
  
  getCurrentUser: (): Promise<User> =>
    api.get('/auth/me').then(res => res.data),
};

// Bookmarks API
export const bookmarksAPI = {
  create: (bookmarkData: BookmarkCreate): Promise<Bookmark> =>
    api.post('/bookmarks/', bookmarkData).then(res => res.data),
  
  getAll: (params?: { skip?: number; limit?: number; platform?: string }): Promise<Bookmark[]> =>
    api.get('/bookmarks/', { params }).then(res => res.data),
  
  getById: (id: string): Promise<Bookmark> =>
    api.get(`/bookmarks/${id}`).then(res => res.data),
  
  update: (id: string, data: BookmarkUpdate): Promise<Bookmark> =>
    api.put(`/bookmarks/${id}`, data).then(res => res.data),
  
  delete: (id: string): Promise<void> =>
    api.delete(`/bookmarks/${id}`).then(res => res.data),
};

// Search API
export const searchAPI = {
  search: (searchQuery: SearchQuery): Promise<SearchResult> =>
    api.post('/search/', searchQuery).then(res => res.data),
  
  getSuggestions: (query: string): Promise<{ suggestions: string[] }> =>
    api.get('/search/suggestions', { params: { q: query } }).then(res => res.data),
};

export default api;