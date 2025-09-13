import { useEffect, useState } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { useAuthStore } from '../store/authStore';
import { useBookmarkStore } from '../store/bookmarkStore';
import Layout from '../components/Layout';
import SearchBar from '../components/SearchBar';
import BookmarkList from '../components/BookmarkList';

export default function Search() {
  const router = useRouter();
  const { user, isLoading: authLoading } = useAuthStore();
  const { searchResults, isLoading, search } = useBookmarkStore();
  const [hasSearched, setHasSearched] = useState(false);
  
  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/auth/login');
      return;
    }
  }, [user, authLoading, router]);

  // Handle URL query parameter for search
  useEffect(() => {
    if (router.query.q && typeof router.query.q === 'string' && user) {
      search({ query: router.query.q });
      setHasSearched(true);
    }
  }, [router.query.q, user, search]);
  
  if (authLoading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-500"></div>
      </div>
    );
  }
  
  return (
    <>
      <Head>
        <title>Search Bookmarks - Semantic Bookmarks</title>
        <meta name="description" content="Search your bookmarks with semantic search" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      
      <Layout>
        <div className="max-w-4xl mx-auto px-4 py-8">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-6">
              Search Bookmarks
            </h1>
            
            {/* Search Bar */}
            <SearchBar />
          </div>
          
          {/* Search Results Info */}
          {searchResults && (
            <div className="mb-4 text-sm text-gray-600">
              Found {searchResults.total} results for "{searchResults.query}"
            </div>
          )}
          
          {/* Loading State */}
          {isLoading && (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
            </div>
          )}
          
          {/* Search Results */}
          {!isLoading && searchResults && (
            <BookmarkList 
              bookmarks={searchResults.bookmarks} 
              showEmpty={true}
            />
          )}
          
          {/* Initial State - No Search Performed */}
          {!isLoading && !searchResults && !hasSearched && (
            <div className="text-center py-12">
              <div className="mx-auto h-12 w-12 text-gray-400 mb-4">
                <svg className="h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <h3 className="mt-2 text-sm font-medium text-gray-900">Search your bookmarks</h3>
              <p className="mt-1 text-sm text-gray-500">
                Enter a search query above to find your bookmarks using semantic search or keywords.
              </p>
            </div>
          )}
          
          {/* No Results State */}
          {!isLoading && searchResults && searchResults.bookmarks.length === 0 && (
            <div className="text-center py-12">
              <div className="mx-auto h-12 w-12 text-gray-400 mb-4">
                <svg className="h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 12h6m-6-4h6m2 5.291A7.962 7.962 0 0112 15c-2.034 0-3.9.785-5.291 2.09m-.709 8.91L8.515 20.485M12 21a9 9 0 100-18 9 9 0 000 18z" />
                </svg>
              </div>
              <h3 className="mt-2 text-sm font-medium text-gray-900">No bookmarks found</h3>
              <p className="mt-1 text-sm text-gray-500">
                No bookmarks match your search query. Try different keywords or browse all bookmarks.
              </p>
              <div className="mt-6">
                <button
                  onClick={() => router.push('/')}
                  className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                >
                  Browse All Bookmarks
                </button>
              </div>
            </div>
          )}
        </div>
      </Layout>
    </>
  );
}