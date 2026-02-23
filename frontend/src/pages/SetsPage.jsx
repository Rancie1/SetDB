/**
 * Sets page.
 * 
 * Single unified search across DB and SoundCloud.
 * When not searching, shows all sets in Deckd.
 * Clicking a SoundCloud result auto-imports it and navigates to the detail page.
 */

import { useEffect, useState, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import * as setsService from '../services/setsService';
import useAuthStore from '../store/authStore';

const SetsPage = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthStore();

  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);

  // DB browse state
  const [dbSets, setDbSets] = useState([]);
  const [dbLoading, setDbLoading] = useState(false);
  const [dbError, setDbError] = useState(null);
  const [sortBy, setSortBy] = useState('created_at');
  const [pagination, setPagination] = useState({
    page: 1, limit: 20, total: 0, pages: 0,
  });

  // Unified search results
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);

  // Set being imported
  const [importingId, setImportingId] = useState(null);

  const searchTimeout = useRef(null);

  useEffect(() => {
    if (!isSearching) {
      loadDbSets();
    }
  }, [pagination.page, sortBy, isSearching]);

  useEffect(() => {
    if (searchTimeout.current) clearTimeout(searchTimeout.current);

    if (!searchQuery.trim()) {
      setIsSearching(false);
      setSearchResults([]);
      return;
    }

    setIsSearching(true);
    setSearchLoading(true);

    searchTimeout.current = setTimeout(() => {
      performSearch(searchQuery.trim());
    }, 400);

    return () => {
      if (searchTimeout.current) clearTimeout(searchTimeout.current);
    };
  }, [searchQuery]);

  const loadDbSets = async () => {
    setDbLoading(true);
    setDbError(null);
    try {
      const response = await setsService.getSets(
        { sort: sortBy },
        pagination.page,
        pagination.limit
      );
      setDbSets(response.data.items || []);
      setPagination(prev => ({
        ...prev,
        total: response.data.total || 0,
        pages: response.data.pages || 0,
      }));
    } catch (err) {
      console.error('Failed to load sets:', err);
      setDbError(err.response?.data?.detail || 'Failed to load sets');
      setDbSets([]);
    } finally {
      setDbLoading(false);
    }
  };

  const performSearch = async (query) => {
    setSearchLoading(true);
    try {
      const [dbResponse, scResponse] = await Promise.all([
        setsService.getSets({ search: query }, 1, 10),
        setsService.searchSoundCloudSets(query, 15).catch(() => ({ data: [] })),
      ]);

      const dbItems = (dbResponse.data.items || []).map(s => ({
        ...s,
        _source: 'db',
        _dbId: s.id,
      }));

      const scItems = (scResponse.data || []).map(s => ({
        ...s,
        _source: 'soundcloud',
        _dbId: null,
        _scId: s.id,
      }));

      // Deduplicate: skip SoundCloud results that match a DB set by URL
      const dbUrls = new Set(dbItems.map(s => s.source_url).filter(Boolean));
      const deduped = scItems.filter(s => !dbUrls.has(s.soundcloud_url));

      setSearchResults([...dbItems, ...deduped]);
    } catch (err) {
      console.error('Search failed:', err);
      setSearchResults([]);
    } finally {
      setSearchLoading(false);
    }
  };

  const handleSetClick = async (set) => {
    if (set._dbId) {
      navigate(`/sets/${set._dbId}`);
      return;
    }

    // Auto-import from SoundCloud
    if (!isAuthenticated()) {
      navigate('/login');
      return;
    }

    if (!set.soundcloud_url) return;

    setImportingId(set._scId);
    try {
      const response = await setsService.importSetFromSoundCloud(set.soundcloud_url);
      navigate(`/sets/${response.data.id}`);
    } catch (err) {
      console.error('Failed to import set:', err);
      alert(err.response?.data?.detail || 'Failed to import set');
    } finally {
      setImportingId(null);
    }
  };

  const handleSortChange = (newSort) => {
    setSortBy(newSort);
    setPagination(prev => ({ ...prev, page: 1 }));
  };

  const handleClear = () => {
    setSearchQuery('');
    setIsSearching(false);
    setSearchResults([]);
  };

  const formatDuration = (ms) => {
    if (!ms) return '';
    const totalMinutes = Math.floor(ms / 60000);
    const hours = Math.floor(totalMinutes / 60);
    const mins = totalMinutes % 60;
    if (hours > 0) return `${hours}h ${mins}m`;
    return `${mins}m`;
  };

  const formatDurationMinutes = (minutes) => {
    if (!minutes) return '';
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours > 0) return `${hours}h ${mins}m`;
    return `${mins}m`;
  };

  // Unified set card renderer
  const renderSetCard = (set, index) => {
    const isDb = set._source === 'db';
    const isImporting = importingId === set._scId;

    if (isDb) {
      return (
        <Link
          key={`db-${set._dbId}-${index}`}
          to={`/sets/${set._dbId}`}
          className="block bg-white rounded-lg border border-gray-200 overflow-hidden hover:shadow-md hover:border-primary-200 transition-all"
        >
          <div className="flex">
            {/* Thumbnail */}
            <div className="w-40 h-28 flex-shrink-0 bg-gray-200 relative overflow-hidden">
              {set.thumbnail_url ? (
                <img
                  src={set.thumbnail_url}
                  alt={set.title}
                  className="w-full h-full object-cover"
                  onError={(e) => { e.target.style.display = 'none'; }}
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-gray-400 text-2xl">
                  🎧
                </div>
              )}
              {set.source_type && (
                <span className={`absolute top-1 right-1 px-1.5 py-0.5 rounded text-[10px] font-medium ${
                  set.source_type === 'youtube' ? 'bg-red-100 text-red-700' :
                  set.source_type === 'soundcloud' ? 'bg-orange-100 text-orange-700' :
                  set.source_type === 'live' ? 'bg-purple-100 text-purple-700' :
                  'bg-gray-100 text-gray-600'
                }`}>
                  {set.source_type === 'youtube' ? 'YouTube' :
                   set.source_type === 'soundcloud' ? 'SoundCloud' :
                   set.source_type === 'live' ? 'Live' : set.source_type}
                </span>
              )}
            </div>
            {/* Info */}
            <div className="flex-1 p-3 min-w-0">
              <h3 className="font-semibold text-gray-900 truncate mb-0.5">{set.title}</h3>
              <p className="text-sm text-gray-600 truncate">{set.dj_name}</p>
              <div className="flex items-center gap-3 mt-2 text-xs text-gray-400">
                {set.duration_minutes > 0 && (
                  <span>{formatDurationMinutes(set.duration_minutes)}</span>
                )}
                {set.source_type === 'live' && set.recording_url && (
                  <span className="text-purple-500">Has Recording</span>
                )}
              </div>
            </div>
          </div>
        </Link>
      );
    }

    // SoundCloud result (not yet imported)
    return (
      <button
        key={`sc-${set._scId}-${index}`}
        onClick={() => handleSetClick(set)}
        disabled={isImporting}
        className="w-full text-left bg-white rounded-lg border border-gray-200 overflow-hidden hover:shadow-md hover:border-primary-200 transition-all disabled:opacity-60"
      >
        <div className="flex">
          {/* Thumbnail */}
          <div className="w-40 h-28 flex-shrink-0 bg-gray-200 relative overflow-hidden">
            {set.thumbnail_url ? (
              <img
                src={set.thumbnail_url}
                alt={set.title}
                className="w-full h-full object-cover"
                onError={(e) => { e.target.style.display = 'none'; }}
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-gray-400 text-2xl">
                🎧
              </div>
            )}
            <span className="absolute top-1 right-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-orange-100 text-orange-700">
              SoundCloud
            </span>
          </div>
          {/* Info */}
          <div className="flex-1 p-3 min-w-0">
            <div className="flex items-center gap-2 mb-0.5">
              <h3 className="font-semibold text-gray-900 truncate">{set.title}</h3>
              {isImporting && (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-500 flex-shrink-0"></div>
              )}
            </div>
            <p className="text-sm text-gray-600 truncate">{set.dj_name}</p>
            <div className="flex items-center gap-3 mt-2 text-xs text-gray-400">
              {set.duration_ms > 0 && (
                <span>{formatDuration(set.duration_ms)}</span>
              )}
              {set.playback_count > 0 && (
                <span>{set.playback_count.toLocaleString()} plays</span>
              )}
              {set.likes_count > 0 && (
                <span>{set.likes_count.toLocaleString()} likes</span>
              )}
            </div>
          </div>
        </div>
      </button>
    );
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Sets</h1>
        <p className="text-gray-600">
          Search across Deckd and SoundCloud for DJ sets and mixes — or browse what's already here.
        </p>
      </div>

      {/* Search Bar */}
      <div className="mb-6">
        <div className="relative">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search for any DJ set, mix, or artist..."
            className="w-full px-4 py-3 pl-11 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 text-lg"
          />
          <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
            <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          {searchQuery && (
            <button
              onClick={handleClear}
              className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-400 hover:text-gray-600"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
        {isSearching && !searchLoading && searchResults.length > 0 && (
          <p className="text-xs text-gray-500 mt-2">
            {searchResults.length} results from Deckd and SoundCloud
          </p>
        )}
      </div>

      {/* Search Results */}
      {isSearching ? (
        <div>
          {searchLoading ? (
            <div className="space-y-3">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="bg-gray-100 animate-pulse rounded-lg h-28"></div>
              ))}
            </div>
          ) : searchResults.length === 0 ? (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
              <p className="text-gray-600 mb-1">No sets found</p>
              <p className="text-gray-400 text-sm">Try a different search term</p>
            </div>
          ) : (
            <div className="space-y-3">
              {searchResults.map((set, i) => renderSetCard(set, i))}
            </div>
          )}
        </div>
      ) : (
        /* Browse Mode */
        <div>
          {/* Sort Options */}
          <div className="flex items-center gap-3 flex-wrap mb-6">
            <span className="text-sm font-medium text-gray-700">Sort by:</span>
            {[
              { value: 'created_at', label: 'Newest' },
              { value: 'title', label: 'Title' },
              { value: 'dj_name', label: 'DJ Name' },
            ].map((option) => (
              <button
                key={option.value}
                onClick={() => handleSortChange(option.value)}
                className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                  sortBy === option.value
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>

          {/* Count */}
          {pagination.total > 0 && (
            <p className="text-sm text-gray-500 mb-4">
              {dbSets.length} of {pagination.total} sets
            </p>
          )}

          {/* Sets List */}
          {dbLoading ? (
            <div className="space-y-3">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="bg-gray-100 animate-pulse rounded-lg h-28"></div>
              ))}
            </div>
          ) : dbError ? (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
              {dbError}
            </div>
          ) : dbSets.length === 0 ? (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
              <p className="text-gray-600 mb-1">No sets yet</p>
              <p className="text-gray-400 text-sm">
                Search above to find and import sets from SoundCloud
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {dbSets.map((set, i) => renderSetCard({
                ...set,
                _source: 'db',
                _dbId: set.id,
              }, i))}
            </div>
          )}

          {/* Pagination */}
          {pagination.pages > 1 && (
            <div className="flex items-center justify-center space-x-2 mt-6">
              <button
                onClick={() => setPagination(prev => ({ ...prev, page: prev.page - 1 }))}
                disabled={pagination.page === 1}
                className="px-4 py-2 border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
              >
                Previous
              </button>
              <span className="px-4 py-2 text-sm text-gray-600">
                Page {pagination.page} of {pagination.pages}
              </span>
              <button
                onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
                disabled={pagination.page >= pagination.pages}
                className="px-4 py-2 border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
              >
                Next
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SetsPage;
