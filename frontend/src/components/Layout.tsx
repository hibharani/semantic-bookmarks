import { ReactNode, useState, useEffect } from 'react';
import { useAuthStore } from '../store/authStore';
import { useRouter } from 'next/router';
import { 
  BookmarkIcon, 
  MagnifyingGlassIcon,
  UserCircleIcon,
  ArrowRightOnRectangleIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline';

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const { user, logout } = useAuthStore();
  const router = useRouter();
  const [hasMounted, setHasMounted] = useState(false);
  
  // Fix hydration issue - only render user-dependent content after mount
  useEffect(() => {
    setHasMounted(true);
  }, []);
  
  const handleLogout = () => {
    logout();
    router.push('/auth/login');
  };
  
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <div className="flex items-center">
              <BookmarkIcon className="h-8 w-8 text-primary-600" />
              <span className="ml-2 text-xl font-semibold text-gray-900">
                Semantic Bookmarks
              </span>
            </div>
            
            {/* Navigation Links */}
            <div className="hidden md:flex items-center space-x-8">
              <button
                onClick={() => router.push('/')}
                className={`flex items-center px-3 py-2 rounded-md text-sm font-medium ${
                  router.pathname === '/'
                    ? 'text-primary-600 bg-primary-50'
                    : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                }`}
              >
                <BookmarkIcon className="h-5 w-5 mr-1" />
                Bookmarks
              </button>
              
              <button
                onClick={() => router.push('/search')}
                className={`flex items-center px-3 py-2 rounded-md text-sm font-medium ${
                  router.pathname === '/search'
                    ? 'text-primary-600 bg-primary-50'
                    : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                }`}
              >
                <MagnifyingGlassIcon className="h-5 w-5 mr-1" />
                Search
              </button>
              
              <button
                onClick={() => router.push('/diagnostics')}
                className={`flex items-center px-3 py-2 rounded-md text-sm font-medium ${
                  router.pathname === '/diagnostics'
                    ? 'text-primary-600 bg-primary-50'
                    : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                }`}
              >
                <ChartBarIcon className="h-5 w-5 mr-1" />
                Diagnostics
              </button>
            </div>
            
            {/* User Menu */}
            <div className="flex items-center space-x-4">
              <div className="flex items-center text-sm text-gray-700">
                <UserCircleIcon className="h-5 w-5 mr-1" />
                {hasMounted ? user?.email : ''}
              </div>
              
              <button
                onClick={handleLogout}
                className="flex items-center px-3 py-2 rounded-md text-sm font-medium text-gray-500 hover:text-gray-700 hover:bg-gray-50"
              >
                <ArrowRightOnRectangleIcon className="h-5 w-5 mr-1" />
                Logout
              </button>
            </div>
          </div>
        </div>
      </nav>
      
      {/* Main Content */}
      <main className="flex-1">
        {children}
      </main>
    </div>
  );
}