/**
 * Tracks Discover page component.
 * 
 * Allows users to browse and discover tracks across all sets.
 */

import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import * as tracksService from '../services/tracksService';
import SoundCloudSearch from '../components/tracks/SoundCloudSearch';

const TracksDiscoverPage = () => {
  const [tracks, setTracks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [artistFilter, setArtistFilter] = useState('');
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('desc');
  const [pagination, setPagination] = useState({
    page: 1,
    limit: 20,
    total: 0,
    pages: 0,
  });

  useEffect(() => {
    loadTracks();
  }, [pagination.page, sortBy, sortOrder]);

  const loadTracks = async () => {
    setLoading(true);
    setError(null);
    try {
      const filters = {
        search: searchQuery || undefined,
        artist_name: artistFilter || undefined,
        sort: sortBy,
        order: sortOrder,
      };
      const response = await tracksService.discoverTracks(filters, pagination.page, pagination.limit);
      setTracks(response.data.items || []);
      setPagination(prev => ({
        ...prev,
        total: response.data.total || 0,
        pages: response.data.pages || 0,
      }));
    } catch (err) {
      console.error('Failed to load tracks:', err);
      setError(err.response?.data?.detail || 'Failed to load tracks');
      setTracks([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setPagination(prev => ({ ...prev, page: 1 }));
    loadTracks();
  };

  const handleClear = () => {
    setSearchQuery('');
    setArtistFilter('');
    setPagination(prev => ({ ...prev, page: 1 }));
    setTimeout(() => loadTracks(), 0);
  };

  const handleSortChange = (newSort) => {
    if (sortBy === newSort) {
      // Toggle order if clicking same sort
      setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(newSort);
      setSortOrder('desc');
    }
    setPagination(prev => ({ ...prev, page: 1 }));
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Discover Tracks</h1>
        <p className="text-gray-600">
          Browse and discover tracks from all sets, or search SoundCloud directly.
        </p>
      </div>

      {/* SoundCloud Direct Search */}
      <div className="mb-6">
        <SoundCloudSearch />
      </div>

      {/* Search and Filters */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
        <form onSubmit={handleSearch} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Search Tracks
              </label>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by track name or artist..."
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Filter by Artist
              </label>
              <input
                type="text"
                value={artistFilter}
                onChange={(e) => setArtistFilter(e.target.value)}
                placeholder="Artist name..."
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
            </div>
          </div>
          <div className="flex items-center gap-4">
            <button
              type="submit"
              className="bg-primary-600 hover:bg-primary-700 text-white font-medium px-6 py-2 rounded-md"
            >
              Search
            </button>
            {(searchQuery || artistFilter) && (
              <button
                type="button"
                onClick={handleClear}
                className="bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium px-4 py-2 rounded-md"
              >
                Clear
              </button>
            )}
          </div>
        </form>
      </div>

      {/* Sort Options */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
        <div className="flex items-center gap-4 flex-wrap">
          <span className="text-sm font-medium text-gray-700">Sort by:</span>
          {[
            { value: 'created_at', label: 'Newest' },
            { value: 'track_name', label: 'Track Name' },
            { value: 'artist_name', label: 'Artist' },
            { value: 'average_rating', label: 'Rating' },
            { value: 'rating_count', label: 'Most Rated' },
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
              {sortBy === option.value && (
                <span className="ml-1">{sortOrder === 'asc' ? '↑' : '↓'}</span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Tracks List */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">
            {searchQuery || artistFilter ? 'Search Results' : 'All Tracks'}
          </h2>
          {pagination.total > 0 && (
            <p className="text-sm text-gray-600">
              Showing {tracks.length} of {pagination.total} tracks
            </p>
          )}
        </div>

        {loading ? (
          <div className="space-y-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="bg-gray-100 animate-pulse rounded-lg h-24"></div>
            ))}
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
            {error}
          </div>
        ) : tracks.length === 0 ? (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
            <p className="text-gray-600 mb-2">No tracks found</p>
            <p className="text-gray-400 text-sm">
              {searchQuery || artistFilter
                ? 'Try adjusting your search or filters'
                : 'Tracks will appear here once they are tagged in sets'}
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {tracks.map((track) => (
              <Link
                key={track.id}
                to={`/tracks/${track.id}`}
                className="block bg-white rounded-lg border border-gray-200 p-4 hover:shadow-md hover:border-primary-300 transition-all cursor-pointer"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900 hover:text-primary-600 transition-colors">
                        {track.track_name}
                      </h3>
                      {track.average_rating && (
                        <div className="flex items-center gap-1 text-sm text-yellow-600">
                          <span>⭐</span>
                          <span className="font-medium">{track.average_rating.toFixed(1)}</span>
                          {track.rating_count > 0 && (
                            <span className="text-gray-500">
                              ({track.rating_count})
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                    {track.artist_name && (
                      <p className="text-gray-600 mb-2">{track.artist_name}</p>
                    )}
                    <div className="flex items-center gap-4 text-sm text-gray-500">
                      {track.linked_sets_count > 0 && (
                        <span className="text-gray-600">
                          📀 In {track.linked_sets_count} set{track.linked_sets_count !== 1 ? 's' : ''}
                        </span>
                      )}
                      {track.soundcloud_url && (
                        <a
                          href={track.soundcloud_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          onClick={(e) => e.stopPropagation()}
                          className="text-orange-600 hover:text-orange-700 font-medium"
                        >
                          🎵 SoundCloud
                        </a>
                      )}
                      {track.spotify_url && (
                        <a
                          href={track.spotify_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          onClick={(e) => e.stopPropagation()}
                          className="text-green-600 hover:text-green-700 font-medium"
                        >
                          🎵 Spotify
                        </a>
                      )}
                    </div>
                    {track.user_rating && (
                      <div className="mt-2 text-xs text-gray-600">
                        Your rating: <span className="font-semibold text-yellow-600">⭐ {track.user_rating.toFixed(1)}</span>
                      </div>
                    )}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>

      {/* Pagination */}
      {pagination.pages > 1 && (
        <div className="flex items-center justify-center space-x-2">
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
  );
};

export default TracksDiscoverPage;
