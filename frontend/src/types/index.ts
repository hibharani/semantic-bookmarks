export interface User {
  id: string;
  email: string;
  created_at: string;
}

export interface Bookmark {
  id: string;
  user_id: string;
  url: string;
  title?: string;
  description?: string;
  content?: string;
  platform?: string;
  meta_data: Record<string, any>;
  tags: string[];
  is_public: boolean;
  created_at: string;
  updated_at: string;
  relevance_score?: number;  // For search results
}

export interface SearchQuery {
  query: string;
  limit?: number;
  mode?: 'smart';
  platform?: string;
  tags?: string[];
  date_from?: string;
  date_to?: string;
}

export interface SearchResult {
  bookmarks: Bookmark[];
  total: number;
  query: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
}

export interface BookmarkCreate {
  url: string;
  title?: string;
  description?: string;
  tags?: string[];
  is_public?: boolean;
}

export interface BookmarkUpdate {
  title?: string;
  description?: string;
  tags?: string[];
  is_public?: boolean;
}