import { useState } from 'react';
import { format } from 'date-fns';
import { Bookmark } from '../types';
import { useBookmarkStore } from '../store/bookmarkStore';
import {
  LinkIcon,
  TagIcon,
  CalendarIcon,
  TrashIcon,
  PencilIcon,
  ArrowTopRightOnSquareIcon
} from '@heroicons/react/24/outline';

interface BookmarkListProps {
  bookmarks: Bookmark[];
  showEmpty?: boolean;
}

export default function BookmarkList({ bookmarks, showEmpty = true }: BookmarkListProps) {
  const { deleteBookmark } = useBookmarkStore();
  const [deletingId, setDeletingId] = useState<string | null>(null);
  
  const handleDelete = async (id: string) => {
    if (confirm('Are you sure you want to delete this bookmark?')) {
      setDeletingId(id);
      try {
        await deleteBookmark(id);
      } catch (error) {
        console.error('Failed to delete bookmark:', error);
      }
      setDeletingId(null);
    }
  };
  
  const getPlatformColor = (platform?: string) => {
    switch (platform) {
      case 'youtube':
        return 'bg-red-100 text-red-800';
      case 'twitter':
        return 'bg-blue-100 text-blue-800';
      case 'pdf':
        return 'bg-orange-100 text-orange-800';
      case 'github':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };
  
  const truncateContent = (content: string, maxLength: number = 200) => {
    if (content.length <= maxLength) return content;
    return content.substring(0, maxLength) + '...';
  };
  
  if (bookmarks.length === 0 && showEmpty) {
    return (
      <div className="text-center py-12">
        <LinkIcon className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-900">No bookmarks</h3>
        <p className="mt-1 text-sm text-gray-500">
          Get started by adding your first bookmark.
        </p>
      </div>
    );
  }
  
  return (
    <div className="space-y-4">
      {bookmarks.map((bookmark) => (
        <div
          key={bookmark.id}
          className="bg-white shadow rounded-lg p-6 hover:shadow-md transition-shadow"
        >
          <div className="flex items-start justify-between">
            <div className="flex-1 min-w-0">
              {/* Title and URL */}
              <div className="flex items-center space-x-2 mb-2">
                <h3 className="text-lg font-medium text-gray-900 truncate">
                  {bookmark.title || 'Untitled'}
                </h3>
                {bookmark.platform && (
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getPlatformColor(bookmark.platform)}`}>
                    {bookmark.platform}
                  </span>
                )}
              </div>
              
              <a
                href={bookmark.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-primary-600 hover:text-primary-800 flex items-center space-x-1 mb-3"
              >
                <span className="truncate">{bookmark.url}</span>
                <ArrowTopRightOnSquareIcon className="h-4 w-4 flex-shrink-0" />
              </a>
              
              {/* Description */}
              {bookmark.description && (
                <p className="text-gray-600 text-sm mb-3">
                  {truncateContent(bookmark.description)}
                </p>
              )}
              
              {/* Content Preview */}
              {bookmark.content && (
                <p className="text-gray-500 text-sm mb-3 bg-gray-50 p-3 rounded">
                  {truncateContent(bookmark.content, 150)}
                </p>
              )}
              
              {/* Tags */}
              {bookmark.tags && bookmark.tags.length > 0 && (
                <div className="flex items-center space-x-1 mb-3">
                  <TagIcon className="h-4 w-4 text-gray-400" />
                  <div className="flex flex-wrap gap-1">
                    {bookmark.tags.map((tag, index) => (
                      <span
                        key={index}
                        className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-primary-100 text-primary-800"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              
              {/* Metadata */}
              <div className="flex items-center text-xs text-gray-500 space-x-4">
                <div className="flex items-center space-x-1">
                  <CalendarIcon className="h-4 w-4" />
                  <span>{format(new Date(bookmark.created_at), 'MMM d, yyyy')}</span>
                </div>
                
                {/* Relevance Score (only for search results) */}
                {bookmark.relevance_score !== undefined && bookmark.relevance_score !== null && bookmark.relevance_score > 0 && (
                  <div className="flex items-center space-x-1">
                    <div className="h-2 w-2 rounded-full bg-primary-500"></div>
                    <span className="text-primary-600 font-medium">
                      {Math.round(bookmark.relevance_score)}% match
                    </span>
                  </div>
                )}
                
                {bookmark.meta_data?.view_count && (
                  <span>{bookmark.meta_data.view_count.toLocaleString()} views</span>
                )}
                
                {bookmark.meta_data?.duration && (
                  <span>{Math.floor(bookmark.meta_data.duration / 60)} min</span>
                )}
              </div>
            </div>
            
            {/* Actions */}
            <div className="flex items-center space-x-2 ml-4">
              <button
                onClick={() => {/* TODO: Implement edit */}}
                className="text-gray-400 hover:text-gray-600"
                title="Edit bookmark"
              >
                <PencilIcon className="h-5 w-5" />
              </button>
              
              <button
                onClick={() => handleDelete(bookmark.id)}
                disabled={deletingId === bookmark.id}
                className="text-red-400 hover:text-red-600 disabled:opacity-50"
                title="Delete bookmark"
              >
                <TrashIcon className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}