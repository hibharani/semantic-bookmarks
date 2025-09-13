import { create } from 'zustand';
import { Bookmark, BookmarkCreate, BookmarkUpdate, SearchQuery, SearchResult } from '../types';
import { bookmarksAPI, searchAPI } from '../utils/api';

interface BookmarkState {
  bookmarks: Bookmark[];
  searchResults: SearchResult | null;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  fetchBookmarks: (params?: { skip?: number; limit?: number; platform?: string }) => Promise<void>;
  createBookmark: (data: BookmarkCreate) => Promise<Bookmark>;
  updateBookmark: (id: string, data: BookmarkUpdate) => Promise<Bookmark>;
  deleteBookmark: (id: string) => Promise<void>;
  search: (query: SearchQuery) => Promise<SearchResult>;
  clearError: () => void;
  clearSearch: () => void;
}

export const useBookmarkStore = create<BookmarkState>()((set, get) => ({
  bookmarks: [],
  searchResults: null,
  isLoading: false,
  error: null,
  
  fetchBookmarks: async (params) => {
    set({ isLoading: true, error: null });
    try {
      const bookmarks = await bookmarksAPI.getAll(params);
      set({ bookmarks, isLoading: false });
    } catch (error: any) {
      set({ 
        error: error.response?.data?.detail || 'Failed to fetch bookmarks',
        isLoading: false 
      });
    }
  },
  
  createBookmark: async (data: BookmarkCreate) => {
    set({ isLoading: true, error: null });
    try {
      const bookmark = await bookmarksAPI.create(data);
      set(state => ({
        bookmarks: [bookmark, ...state.bookmarks],
        isLoading: false
      }));
      return bookmark;
    } catch (error: any) {
      set({ 
        error: error.response?.data?.detail || 'Failed to create bookmark',
        isLoading: false 
      });
      throw error;
    }
  },
  
  updateBookmark: async (id: string, data: BookmarkUpdate) => {
    set({ isLoading: true, error: null });
    try {
      const updatedBookmark = await bookmarksAPI.update(id, data);
      set(state => ({
        bookmarks: state.bookmarks.map(b => 
          b.id === id ? updatedBookmark : b
        ),
        isLoading: false
      }));
      return updatedBookmark;
    } catch (error: any) {
      set({ 
        error: error.response?.data?.detail || 'Failed to update bookmark',
        isLoading: false 
      });
      throw error;
    }
  },
  
  deleteBookmark: async (id: string) => {
    set({ isLoading: true, error: null });
    try {
      await bookmarksAPI.delete(id);
      set(state => ({
        bookmarks: state.bookmarks.filter(b => b.id !== id),
        isLoading: false
      }));
    } catch (error: any) {
      set({ 
        error: error.response?.data?.detail || 'Failed to delete bookmark',
        isLoading: false 
      });
      throw error;
    }
  },
  
  search: async (query: SearchQuery) => {
    set({ isLoading: true, error: null });
    try {
      const results = await searchAPI.search(query);
      set({ searchResults: results, isLoading: false });
      return results;
    } catch (error: any) {
      set({ 
        error: error.response?.data?.detail || 'Search failed',
        isLoading: false 
      });
      throw error;
    }
  },
  
  clearError: () => set({ error: null }),
  clearSearch: () => set({ searchResults: null }),
}));