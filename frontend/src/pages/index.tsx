import { useEffect, useState } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import { useAuthStore } from '../store/authStore';
import { useBookmarkStore } from '../store/bookmarkStore';
import Layout from '../components/Layout';
import SearchBar from '../components/SearchBar';
import BookmarkList from '../components/BookmarkList';
import AddBookmarkModal from '../components/AddBookmarkModal';
import { PlusIcon } from '@heroicons/react/24/outline';

export default function Home() {
  const router = useRouter();
  const { user, isLoading: authLoading } = useAuthStore();
  const { bookmarks, searchResults, fetchBookmarks, isLoading } = useBookmarkStore();
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  
  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/auth/login');
      return;
    }
    
    if (user) {
      fetchBookmarks();
    }
  }, [user, authLoading, router, fetchBookmarks]);
  
  if (authLoading || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-500"></div>
      </div>
    );
  }
  
  const displayBookmarks = searchResults?.bookmarks || bookmarks;
  
  return (
    <>
      <Head>
        <title>Semantic Bookmarks</title>
        <meta name="description" content="Smart bookmarking with semantic search" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      
      <Layout>
        <div className="max-w-4xl mx-auto px-4 py-8">
          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center justify-between mb-6">
              <h1 className="text-3xl font-bold text-gray-900">
                My Bookmarks
              </h1>
              
              <button
                onClick={() => setIsAddModalOpen(true)}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                <PlusIcon className="h-5 w-5 mr-2" />
                Add Bookmark
              </button>
            </div>
            
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
          
          {/* Bookmark List */}
          {!isLoading && (
            <BookmarkList 
              bookmarks={displayBookmarks} 
              showEmpty={!searchResults}
            />
          )}
        </div>
        
        {/* Add Bookmark Modal */}
        <AddBookmarkModal
          isOpen={isAddModalOpen}
          onClose={() => setIsAddModalOpen(false)}
        />
      </Layout>
    </>
  );
}