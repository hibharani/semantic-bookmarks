import { useState, useRef, useEffect } from 'react';
import { MagnifyingGlassIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { useBookmarkStore } from '../store/bookmarkStore';
import { searchAPI } from '../utils/api';

/**
 * SearchBar Component
 * 
 * Advanced semantic search interface that supports natural language queries
 * with AI-powered relevance matching and intelligent search suggestions.
 * 
 * Search Logic:
 * - Smart adaptive threshold that adjusts based on best match quality
 *   - Excellent matches (>70%): Shows only similar quality results
 *   - Good matches (40-70%): Shows moderately relevant results  
 *   - Poor matches (<40%): Relaxed threshold to help users find content
 * 
 * Features:
 * - OpenAI embedding-based semantic search
 * - Real-time search suggestions with 300ms debouncing
 * - Keyboard shortcuts (Enter to search, Escape to close)
 * - Suggestion dropdown with click-to-search functionality
 */
export default function SearchBar() {
  // Search query state
  const [query, setQuery] = useState<string>('');
  
  // Search suggestions state management
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState<boolean>(false);
  
  // Zustand store for search operations and DOM references
  const { search, clearSearch, searchResults } = useBookmarkStore();
  const inputRef = useRef<HTMLInputElement>(null);
  
  /**
   * Search Suggestions Effect
   * 
   * Implements intelligent search suggestions with debouncing to enhance UX:
   * - Triggers after 3+ characters to avoid noise from short queries
   * - 300ms debounce prevents excessive API calls during typing
   * - Graceful error handling ensures suggestions don't break search
   * - Auto-clears suggestions for queries under 3 characters
   */
  useEffect(() => {
    const fetchSuggestions = async () => {
      if (query.length > 2) {
        try {
          // Fetch AI-generated search suggestions based on user's bookmarks
          const response = await searchAPI.getSuggestions(query);
          setSuggestions(response.suggestions);
          setShowSuggestions(true);
        } catch (error) {
          // Fail silently - suggestions are nice-to-have, not critical
          // Users can still search without suggestions
          setSuggestions([]);
        }
      } else {
        // Clear suggestions for short queries to reduce UI noise
        setSuggestions([]);
        setShowSuggestions(false);
      }
    };
    
    // Debounce API calls to prevent excessive requests during rapid typing
    // 300ms provides good balance between responsiveness and API efficiency
    const debounceTimeout = setTimeout(fetchSuggestions, 300);
    return () => clearTimeout(debounceTimeout);
  }, [query]);
  
  /**
   * Handle Search Execution
   * 
   * Executes semantic search with current query and selected mode.
   * Supports both direct calls and suggestion-triggered searches.
   * 
   * @param searchQuery - Optional query override (used by suggestion clicks)
   */
  const handleSearch = async (searchQuery?: string) => {
    const finalQuery = searchQuery || query;
    if (!finalQuery.trim()) return;
    
    try {
      // Execute semantic search through Zustand store (always uses smart mode)
      await search({ query: finalQuery, mode: 'smart' });
      
      // Clean up UI state after successful search
      setShowSuggestions(false);
      inputRef.current?.blur();
    } catch (error) {
      console.error('Search failed:', error);
      // TODO: Show user-friendly error message in UI
    }
  };
  
  /**
   * Clear Search and Reset State
   * 
   * Resets all search-related state and returns to bookmark listing view.
   * Maintains focus on input for immediate new search capability.
   */
  const handleClearSearch = () => {
    setQuery('');
    clearSearch(); // Clears search results in store, shows all bookmarks
    setShowSuggestions(false);
    inputRef.current?.focus(); // Keep focus for better UX
  };
  
  /**
   * Handle Suggestion Selection
   * 
   * When user clicks a suggestion, populate input and execute search.
   * 
   * @param suggestion - The selected suggestion text
   */
  const handleSuggestionClick = (suggestion: string) => {
    setQuery(suggestion);
    handleSearch(suggestion);
  };
  
  /**
   * Keyboard Event Handler
   * 
   * Provides keyboard shortcuts for better accessibility:
   * - Enter: Execute search with current query
   * - Escape: Close suggestions and blur input
   */
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSearch();
    } else if (e.key === 'Escape') {
      setShowSuggestions(false);
      inputRef.current?.blur();
    }
  };
  
  return (
    <div className="relative">
      {/* Main Search Input Container */}
      <div className="relative">
        {/* Search Icon - Left Side */}
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <MagnifyingGlassIcon className="h-5 w-5 text-gray-400" />
        </div>
        
        {/* Main Search Input Field */}
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => suggestions.length > 0 && setShowSuggestions(true)}
          className="block w-full pl-10 pr-12 py-3 border border-gray-300 rounded-lg leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-primary-500 focus:border-primary-500 text-sm"
          placeholder="Search your bookmarks with natural language..."
        />
        
        {/* Clear Button - Right Side (shows when there's content or active search) */}
        {(query || searchResults) && (
          <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
            <button
              onClick={handleClearSearch}
              className="text-gray-400 hover:text-gray-500 focus:outline-none"
              aria-label="Clear search"
            >
              <XMarkIcon className="h-5 w-5" />
            </button>
          </div>
        )}
      </div>
      
      {/* Search Suggestions Dropdown */}
      {showSuggestions && suggestions.length > 0 && (
        <div className="absolute z-10 mt-1 w-full bg-white shadow-lg max-h-60 rounded-md py-1 text-base ring-1 ring-black ring-opacity-5 overflow-auto focus:outline-none sm:text-sm">
          {suggestions.map((suggestion, index) => (
            <button
              key={index}
              onClick={() => handleSuggestionClick(suggestion)}
              className="w-full text-left px-4 py-2 text-sm text-gray-900 hover:bg-gray-100 focus:bg-gray-100 focus:outline-none"
              aria-label={`Search for "${suggestion}"`}
            >
              <div className="flex items-center">
                <MagnifyingGlassIcon className="h-4 w-4 text-gray-400 mr-2" />
                {suggestion}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}