import { useEffect, useState } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { useAuthStore } from '../store/authStore';
import Layout from '../components/Layout';
import { 
  ChartBarIcon, 
  DocumentMagnifyingGlassIcon, 
  Cog6ToothIcon,
  InformationCircleIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon,
  TagIcon,
  GlobeAltIcon
} from '@heroicons/react/24/outline';
import api from '../utils/api';

interface DiagnosticOverview {
  summary: {
    total_bookmarks: number;
    total_embeddings: number;
    embeddings_per_bookmark: number;
  };
  content_stats: {
    total_bookmarks: number;
    with_content: number;
    with_title: number;
    with_description: number;
    content_coverage: number;
    avg_content_length: number;
    max_content_length: number;
    min_content_length: number;
  };
  platforms: Array<{
    platform: string;
    count: number;
  }>;
  recent_activity: Array<{
    id: string;
    title: string;
    url: string;
    platform: string;
    created_at: string;
    embedding_count: number;
    content_length: number;
  }>;
}

interface BookmarkDetail {
  bookmark: {
    id: string;
    url: string;
    title: string;
    description?: string;
    content?: string;
    platform?: string;
    metadata: any;
    tags: string[];
    created_at: string;
    updated_at: string;
  };
  processing: {
    total_chunks: number;
    total_characters: number;
    avg_chunk_size: number;
    embedding_dimension: number;
  };
  embeddings: Array<{
    id: string;
    chunk_index: number;
    content_chunk: string;
    chunk_length: number;
    embedding_dimension: number;
  }>;
}

interface SystemInfo {
  configuration: {
    openai_api_key: string;
    database_url: string;
    redis_url: string;
    debug_mode: boolean;
  };
  database: {
    extensions: Array<{
      name: string;
      version: string;
    }>;
    search_indexes: Array<{
      name: string;
      definition: string;
    }>;
  };
}

export default function Diagnostics() {
  const router = useRouter();
  const { user, isLoading: authLoading } = useAuthStore();
  const [overview, setOverview] = useState<DiagnosticOverview | null>(null);
  const [systemInfo, setSystemInfo] = useState<SystemInfo | null>(null);
  const [selectedBookmark, setSelectedBookmark] = useState<BookmarkDetail | null>(null);
  const [searchTest, setSearchTest] = useState<any>(null);
  const [searchQuery, setSearchQuery] = useState('jules');
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'bookmarks' | 'search' | 'system'>('overview');

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/auth/login');
      return;
    }
    
    if (user) {
      loadDiagnosticData();
    }
  }, [user, authLoading, router]);

  const loadDiagnosticData = async () => {
    setIsLoading(true);
    try {
      const [overviewRes, systemRes] = await Promise.all([
        api.get('/diagnostics/overview'),
        api.get('/diagnostics/system-info')
      ]);
      
      setOverview(overviewRes.data);
      setSystemInfo(systemRes.data);
    } catch (error) {
      console.error('Failed to load diagnostic data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const loadBookmarkDetail = async (bookmarkId: string) => {
    try {
      const response = await api.get(`/diagnostics/bookmark/${bookmarkId}`);
      setSelectedBookmark(response.data);
    } catch (error) {
      console.error('Failed to load bookmark detail:', error);
    }
  };

  const testSearch = async () => {
    try {
      const response = await api.get(`/diagnostics/search-test?query=${encodeURIComponent(searchQuery)}`);
      setSearchTest(response.data);
    } catch (error) {
      console.error('Failed to test search:', error);
    }
  };

  if (authLoading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStatusColor = (value: number, threshold: number) => {
    return value >= threshold ? 'text-green-600' : 'text-yellow-600';
  };

  return (
    <>
      <Head>
        <title>Diagnostics - Semantic Bookmarks</title>
        <meta name="description" content="System diagnostics and indexing status" />
      </Head>
      
      <Layout>
        <div className="max-w-7xl mx-auto px-4 py-8">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">System Diagnostics</h1>
            <p className="text-gray-600">Monitor indexing status, content processing, and search functionality</p>
          </div>

          {/* Tabs */}
          <div className="border-b border-gray-200 mb-8">
            <nav className="-mb-px flex space-x-8">
              {[
                { id: 'overview', name: 'Overview', icon: ChartBarIcon },
                { id: 'bookmarks', name: 'Bookmarks', icon: DocumentMagnifyingGlassIcon },
                { id: 'search', name: 'Search Test', icon: GlobeAltIcon },
                { id: 'system', name: 'System Info', icon: Cog6ToothIcon }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`group inline-flex items-center py-2 px-1 border-b-2 font-medium text-sm ${
                    activeTab === tab.id
                      ? 'border-primary-500 text-primary-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <tab.icon className="h-5 w-5 mr-2" />
                  {tab.name}
                </button>
              ))}
            </nav>
          </div>

          {isLoading ? (
            <div className="flex justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
            </div>
          ) : (
            <>
              {/* Overview Tab */}
              {activeTab === 'overview' && overview && (
                <div className="space-y-6">
                  {/* Summary Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="bg-white p-6 rounded-lg shadow">
                      <div className="flex items-center">
                        <DocumentMagnifyingGlassIcon className="h-8 w-8 text-blue-500" />
                        <div className="ml-4">
                          <p className="text-2xl font-bold text-gray-900">{overview.summary.total_bookmarks}</p>
                          <p className="text-gray-600">Total Bookmarks</p>
                        </div>
                      </div>
                    </div>
                    
                    <div className="bg-white p-6 rounded-lg shadow">
                      <div className="flex items-center">
                        <ChartBarIcon className="h-8 w-8 text-green-500" />
                        <div className="ml-4">
                          <p className="text-2xl font-bold text-gray-900">{overview.summary.total_embeddings}</p>
                          <p className="text-gray-600">Vector Embeddings</p>
                        </div>
                      </div>
                    </div>
                    
                    <div className="bg-white p-6 rounded-lg shadow">
                      <div className="flex items-center">
                        <CheckCircleIcon className="h-8 w-8 text-purple-500" />
                        <div className="ml-4">
                          <p className="text-2xl font-bold text-gray-900">{overview.summary.embeddings_per_bookmark}</p>
                          <p className="text-gray-600">Avg Embeddings/Bookmark</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Content Statistics */}
                  <div className="bg-white p-6 rounded-lg shadow">
                    <h3 className="text-lg font-semibold mb-4">Content Processing Status</h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="text-center">
                        <p className={`text-2xl font-bold ${getStatusColor(overview.content_stats.content_coverage, 80)}`}>
                          {overview.content_stats.content_coverage}%
                        </p>
                        <p className="text-sm text-gray-600">Content Extracted</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl font-bold text-gray-900">
                          {formatBytes(overview.content_stats.avg_content_length)}
                        </p>
                        <p className="text-sm text-gray-600">Avg Content Size</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl font-bold text-gray-900">{overview.content_stats.with_title}</p>
                        <p className="text-sm text-gray-600">With Titles</p>
                      </div>
                      <div className="text-center">
                        <p className="text-2xl font-bold text-gray-900">{overview.content_stats.with_description}</p>
                        <p className="text-sm text-gray-600">With Descriptions</p>
                      </div>
                    </div>
                  </div>

                  {/* Platform Breakdown */}
                  <div className="bg-white p-6 rounded-lg shadow">
                    <h3 className="text-lg font-semibold mb-4">Platform Distribution</h3>
                    <div className="space-y-3">
                      {overview.platforms.map((platform) => (
                        <div key={platform.platform} className="flex items-center justify-between">
                          <div className="flex items-center">
                            <TagIcon className="h-4 w-4 text-gray-400 mr-2" />
                            <span className="capitalize">{platform.platform}</span>
                          </div>
                          <div className="flex items-center">
                            <span className="font-medium mr-2">{platform.count}</span>
                            <div className="w-20 bg-gray-200 rounded-full h-2">
                              <div 
                                className="bg-primary-500 h-2 rounded-full" 
                                style={{ width: `${(platform.count / overview.summary.total_bookmarks) * 100}%` }}
                              ></div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Bookmarks Tab */}
              {activeTab === 'bookmarks' && overview && (
                <div className="space-y-6">
                  <div className="bg-white rounded-lg shadow">
                    <div className="px-6 py-4 border-b border-gray-200">
                      <h3 className="text-lg font-semibold">Recent Bookmarks Processing</h3>
                    </div>
                    <div className="divide-y divide-gray-200">
                      {overview.recent_activity.map((bookmark) => (
                        <div key={bookmark.id} className="px-6 py-4 hover:bg-gray-50">
                          <div className="flex items-center justify-between">
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-gray-900 truncate">
                                {bookmark.title || 'Untitled'}
                              </p>
                              <p className="text-sm text-gray-500 truncate">{bookmark.url}</p>
                              <div className="flex items-center mt-1 space-x-4 text-xs text-gray-500">
                                <span className="flex items-center">
                                  <TagIcon className="h-3 w-3 mr-1" />
                                  {bookmark.platform || 'unknown'}
                                </span>
                                <span className="flex items-center">
                                  <ChartBarIcon className="h-3 w-3 mr-1" />
                                  {bookmark.embedding_count} embeddings
                                </span>
                                <span>{formatBytes(bookmark.content_length)} content</span>
                              </div>
                            </div>
                            <div className="flex items-center space-x-2">
                              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                                bookmark.embedding_count > 0 
                                  ? 'bg-green-100 text-green-800' 
                                  : 'bg-yellow-100 text-yellow-800'
                              }`}>
                                {bookmark.embedding_count > 0 ? 'Processed' : 'Pending'}
                              </span>
                              <button
                                onClick={() => loadBookmarkDetail(bookmark.id)}
                                className="text-primary-600 hover:text-primary-800 text-sm"
                              >
                                Details
                              </button>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Bookmark Detail Modal */}
                  {selectedBookmark && (
                    <div className="bg-white rounded-lg shadow">
                      <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
                        <h3 className="text-lg font-semibold">Bookmark Processing Details</h3>
                        <button
                          onClick={() => setSelectedBookmark(null)}
                          className="text-gray-400 hover:text-gray-600"
                        >
                          ×
                        </button>
                      </div>
                      <div className="px-6 py-4 space-y-4">
                        <div>
                          <h4 className="font-medium mb-2">Basic Information</h4>
                          <div className="bg-gray-50 p-3 rounded text-sm">
                            <p><strong>Title:</strong> {selectedBookmark.bookmark.title}</p>
                            <p><strong>URL:</strong> {selectedBookmark.bookmark.url}</p>
                            <p><strong>Platform:</strong> {selectedBookmark.bookmark.platform}</p>
                            <p><strong>Created:</strong> {new Date(selectedBookmark.bookmark.created_at).toLocaleString()}</p>
                          </div>
                        </div>
                        
                        <div>
                          <h4 className="font-medium mb-2">Processing Statistics</h4>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                            <div className="bg-gray-50 p-3 rounded">
                              <p className="font-medium">{selectedBookmark.processing.total_chunks}</p>
                              <p className="text-gray-600">Chunks</p>
                            </div>
                            <div className="bg-gray-50 p-3 rounded">
                              <p className="font-medium">{formatBytes(selectedBookmark.processing.total_characters)}</p>
                              <p className="text-gray-600">Content Size</p>
                            </div>
                            <div className="bg-gray-50 p-3 rounded">
                              <p className="font-medium">{selectedBookmark.processing.avg_chunk_size}</p>
                              <p className="text-gray-600">Avg Chunk Size</p>
                            </div>
                            <div className="bg-gray-50 p-3 rounded">
                              <p className="font-medium">{selectedBookmark.processing.embedding_dimension}</p>
                              <p className="text-gray-600">Vector Dimension</p>
                            </div>
                          </div>
                        </div>

                        <div>
                          <h4 className="font-medium mb-2">Content Chunks ({selectedBookmark.embeddings.length})</h4>
                          <div className="space-y-2 max-h-96 overflow-y-auto">
                            {selectedBookmark.embeddings.map((embedding) => (
                              <div key={embedding.id} className="bg-gray-50 p-3 rounded text-sm">
                                <div className="flex justify-between items-center mb-2">
                                  <span className="font-medium">Chunk {embedding.chunk_index + 1}</span>
                                  <span className="text-gray-500">{formatBytes(embedding.chunk_length)}</span>
                                </div>
                                <p className="text-gray-700 line-clamp-3">
                                  {embedding.content_chunk.substring(0, 200)}
                                  {embedding.content_chunk.length > 200 && '...'}
                                </p>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Search Test Tab */}
              {activeTab === 'search' && (
                <div className="space-y-6">
                  <div className="bg-white p-6 rounded-lg shadow">
                    <h3 className="text-lg font-semibold mb-4">Search Functionality Test</h3>
                    <div className="flex space-x-4 mb-4">
                      <input
                        type="text"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        placeholder="Enter search query..."
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-md"
                      />
                      <button
                        onClick={testSearch}
                        className="px-4 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700"
                      >
                        Test Search
                      </button>
                    </div>
                    
                    {searchTest && (
                      <div className="space-y-4">
                        <div>
                          <h4 className="font-medium mb-2">Hybrid Search Results</h4>
                          {searchTest.hybrid_search.error ? (
                            <div className="bg-red-50 p-3 rounded text-red-700">
                              Search failed: {searchTest.error}
                            </div>
                          ) : (
                            <div className="bg-gray-50 p-3 rounded">
                              <p className="text-sm text-gray-600 mb-2">
                                Found {searchTest.hybrid_search.total_results} results
                              </p>
                              {searchTest.hybrid_search.results.map((result: any) => (
                                <div key={result.id} className="border-l-2 border-primary-500 pl-3 mb-2">
                                  <p className="font-medium">{result.title}</p>
                                  <p className="text-sm text-gray-600">{result.platform}</p>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                        
                        <div>
                          <h4 className="font-medium mb-2">PostgreSQL Full-Text Search</h4>
                          <div className="bg-gray-50 p-3 rounded">
                            {searchTest.postgresql_search.map((result: any) => (
                              <div key={result.id} className="border-l-2 border-green-500 pl-3 mb-2">
                                <p className="font-medium">{result.title}</p>
                                <p className="text-sm text-gray-600">Rank: {result.rank.toFixed(4)}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* System Info Tab */}
              {activeTab === 'system' && systemInfo && (
                <div className="space-y-6">
                  <div className="bg-white p-6 rounded-lg shadow">
                    <h3 className="text-lg font-semibold mb-4">Configuration Status</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-3">
                        <div className="flex items-center justify-between">
                          <span>OpenAI API Key</span>
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            systemInfo.configuration.openai_api_key === 'configured'
                              ? 'bg-green-100 text-green-800'
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {systemInfo.configuration.openai_api_key}
                          </span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span>Debug Mode</span>
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            systemInfo.configuration.debug_mode
                              ? 'bg-yellow-100 text-yellow-800'
                              : 'bg-gray-100 text-gray-800'
                          }`}>
                            {systemInfo.configuration.debug_mode ? 'Enabled' : 'Disabled'}
                          </span>
                        </div>
                      </div>
                      <div className="space-y-3">
                        <div>
                          <span className="block text-sm font-medium">Database</span>
                          <span className="text-sm text-gray-600">{systemInfo.configuration.database_url}</span>
                        </div>
                        <div>
                          <span className="block text-sm font-medium">Redis</span>
                          <span className="text-sm text-gray-600">{systemInfo.configuration.redis_url}</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white p-6 rounded-lg shadow">
                    <h3 className="text-lg font-semibold mb-4">Database Extensions</h3>
                    <div className="space-y-2">
                      {systemInfo.database.extensions.map((ext) => (
                        <div key={ext.name} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                          <span className="font-medium">{ext.name}</span>
                          <span className="text-sm text-gray-600">v{ext.version}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="bg-white p-6 rounded-lg shadow">
                    <h3 className="text-lg font-semibold mb-4">Search Indexes</h3>
                    <div className="space-y-2">
                      {systemInfo.database.search_indexes.map((idx) => (
                        <div key={idx.name} className="p-3 bg-gray-50 rounded">
                          <p className="font-medium">{idx.name}</p>
                          <p className="text-sm text-gray-600 mt-1">{idx.definition}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </Layout>
    </>
  );
}