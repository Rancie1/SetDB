/**
 * Tracks page.
 * 
 * Single unified search across DB, SoundCloud, and Spotify.
 * When not searching, shows all tracks in Deckd.
 * Clicking any result auto-imports it and navigates to the detail page.
 */

import { useEffect, useState, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import * as tracksService from '../services/tracksService';
import * as standaloneTracksService from '../services/standaloneTracksService';
import SpotifyEmbed from '../components/tracks/SpotifyEmbed';
import useAuthStore from '../store/authStore';

const PlatformTag = ({ platform }) => {
  if (!platform) return null;
  const styles = {
    spotify: 'bg-green-100 text-green-700',
    soundcloud: 'bg-orange-100 text-orange-700',
  };
  return (
    <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium ${styles[platform] || 'bg-gray-100 text-gray-600'}`}>
      {platform === 'spotify' ? 'Spotify' : platform === 'soundcloud' ? 'SoundCloud' : platform}
    </span>
  );
};

const TracksDiscoverPage = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthStore();

  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);

  // DB browse state (shown when not searching)
  const [dbTracks, setDbTracks] = useState([]);
  const [dbLoading, setDbLoading] = useState(false);
  const [dbError, setDbError] = useState(null);
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('desc');
  const [pagination, setPagination] = useState({
    page: 1, limit: 20, total: 0, pages: 0,
  });

  // Unified search results (shown when searching)
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);

  // Track being imported
  const [importingId, setImportingId] = useState(null);

  // Debounce ref
  const searchTimeout = useRef(null);

  // Load DB tracks on mount and when sort/page changes
  useEffect(() => {
    if (!isSearching) {
      loadDbTracks();
    }
  }, [pagination.page, sortBy, sortOrder, isSearching]);

  // Debounced search as user types
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

  const loadDbTracks = async () => {
    setDbLoading(true);
    setDbError(null);
    try {
      const response = await tracksService.discoverTracks(
        { sort: sortBy, order: sortOrder },
        pagination.page,
        pagination.limit
      );
      setDbTracks(response.data.items || []);
      setPagination(prev => ({
        ...prev,
        total: response.data.total || 0,
        pages: response.data.pages || 0,
      }));
    } catch (err) {
      console.error('Failed to load tracks:', err);
      setDbError(err.response?.data?.detail || 'Failed to load tracks');
      setDbTracks([]);
    } finally {
      setDbLoading(false);
    }
  };

  const performSearch = async (query) => {
    setSearchLoading(true);
    try {
      // Search all platforms at once (DB + SoundCloud + Spotify)
      const [dbResponse, platformResponse] = await Promise.all([
        tracksService.discoverTracks({ search: query }, 1, 10),
        tracksService.searchTracks(query, 'all', 15).catch(() => ({ data: [] })),
      ]);

      const dbItems = (dbResponse.data.items || []).map(t => ({
        ...t,
        _source: 'db',
        _name: t.track_name,
        _artist: t.artist_name,
        _platform: t.spotify_url ? 'spotify' : t.soundcloud_url ? 'soundcloud' : null,
        _thumbnail: t.thumbnail_url,
        _dbId: t.id,
      }));

      const platformItems = (platformResponse.data || []).map(t => ({
        ...t,
        _source: 'external',
        _name: t.title,
        _artist: t.artist_name,
        _platform: t.platform,
        _thumbnail: t.thumbnail_url,
        _dbId: t.exists_in_db ? t.track_id : null,
        _externalId: t.id,
        _artistIds: t.artist_ids || [],
      }));

      // Deduplicate: if an external result already exists in DB results, skip it
      const dbIds = new Set(dbItems.map(t => t._dbId).filter(Boolean));
      const deduped = platformItems.filter(t => {
        if (t._dbId && dbIds.has(t._dbId)) return false;
        return true;
      });

      // Spotify first, then SoundCloud, then DB tracks
      const spotifyResults = deduped.filter(t => t._platform === 'spotify');
      const soundcloudResults = deduped.filter(t => t._platform === 'soundcloud');
      setSearchResults([...spotifyResults, ...soundcloudResults, ...dbItems]);
    } catch (err) {
      console.error('Search failed:', err);
      setSearchResults([]);
    } finally {
      setSearchLoading(false);
    }
  };

  const handleTrackClick = async (track) => {
    // If it's already in the DB, just navigate
    if (track._dbId) {
      navigate(`/tracks/${track._dbId}`);
      return;
    }

    // Auto-import then navigate
    if (!isAuthenticated()) {
      navigate('/login');
      return;
    }

    setImportingId(track._externalId || track.id);
    try {
      const trackData = {
        track_name: track._name || '',
        artist_name: track._artist || null,
        soundcloud_url: track.soundcloud_url || null,
        soundcloud_track_id: track._platform === 'soundcloud' && track._externalId ? String(track._externalId) : null,
        spotify_url: track.spotify_url || null,
        spotify_track_id: track._platform === 'spotify' && track._externalId ? track._externalId : null,
        thumbnail_url: track._thumbnail || null,
        duration_ms: track.duration_ms || null,
        spotify_artist_ids: track._artistIds?.length ? track._artistIds : null,
      };
      const response = await standaloneTracksService.createTrack(trackData);
      navigate(`/tracks/${response.data.id}`);
    } catch (err) {
      if (err.response?.status === 409 && err.response?.data?.track_id) {
        navigate(`/tracks/${err.response.data.track_id}`);
      } else if (err.response?.status === 409) {
        alert('Track already exists.');
      } else {
        alert(err.response?.data?.detail || 'Failed to add track');
      }
    } finally {
      setImportingId(null);
    }
  };

  const handleSortChange = (newSort) => {
    if (sortBy === newSort) {
      setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(newSort);
      setSortOrder('desc');
    }
    setPagination(prev => ({ ...prev, page: 1 }));
  };

  const handleClear = () => {
    setSearchQuery('');
    setIsSearching(false);
    setSearchResults([]);
  };

  const formatDuration = (ms) => {
    if (!ms) return '';
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  // Unified track card renderer
  const renderTrackCard = (track, index) => {
    const isDb = track._source === 'db';
    const name = track._name;
    const artist = track._artist;
    const platform = track._platform;
    const thumbnail = track._thumbnail;
    const dbId = track._dbId;
    const isImporting = importingId === (track._externalId || track.id);

    const cardContent = (
      <div className="flex items-center gap-4">
        {thumbnail && (
          <img src={thumbnail} alt={name} className="w-12 h-12 rounded object-cover flex-shrink-0" />
        )}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-0.5">
            <h3 className="font-semibold text-gray-900 truncate">{name}</h3>
            {platform && <PlatformTag platform={platform} />}
          </div>
          {artist && <p className="text-sm text-gray-600 truncate">{artist}</p>}
          <div className="flex items-center gap-3 mt-1 text-xs text-gray-400">
            {isDb && track.average_rating > 0 && (
              <span className="text-yellow-600 font-medium">
                ⭐ {track.average_rating.toFixed(1)}
                {track.rating_count > 0 && ` (${track.rating_count})`}
              </span>
            )}
            {isDb && track.linked_sets_count > 0 && (
              <span>In {track.linked_sets_count} set{track.linked_sets_count !== 1 ? 's' : ''}</span>
            )}
            {!isDb && track.duration_ms > 0 && (
              <span>{formatDuration(track.duration_ms)}</span>
            )}
            {isDb && track.user_rating > 0 && (
              <span className="text-yellow-500">Your: ⭐ {track.user_rating.toFixed(1)}</span>
            )}
          </div>
        </div>
        {isImporting && (
          <div className="flex-shrink-0">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-primary-500"></div>
          </div>
        )}
        {isDb && (track.spotify_track_id || track.spotify_url) && (
          <div className="flex-shrink-0 w-[300px] hidden lg:block" onClick={(e) => e.stopPropagation()}>
            <SpotifyEmbed spotifyTrackId={track.spotify_track_id} spotifyUrl={track.spotify_url} compact={true} />
          </div>
        )}
      </div>
    );

    if (dbId) {
      return (
        <Link
          key={`${track._source}-${dbId}-${index}`}
          to={`/tracks/${dbId}`}
          className="block bg-white rounded-lg border border-gray-200 p-4 hover:shadow-sm hover:border-primary-200 transition-all"
        >
          {cardContent}
        </Link>
      );
    }

    return (
      <button
        key={`${track._source}-${track._externalId || track.id}-${index}`}
        onClick={() => handleTrackClick(track)}
        disabled={isImporting}
        className="w-full text-left bg-white rounded-lg border border-gray-200 p-4 hover:shadow-sm hover:border-primary-200 transition-all disabled:opacity-60"
      >
        {cardContent}
      </button>
    );
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Tracks</h1>
        <p className="text-gray-600">
          Search across Deckd, SoundCloud, and Spotify — or browse what's already here.
        </p>
      </div>

      {/* Search Bar */}
      <div className="mb-6">
        <div className="relative">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search for any track or artist..."
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
            {searchResults.length} results from Deckd, SoundCloud, and Spotify
          </p>
        )}
      </div>

      {/* Search Results */}
      {isSearching ? (
        <div>
          {searchLoading ? (
            <div className="space-y-3">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="bg-gray-100 animate-pulse rounded-lg h-20"></div>
              ))}
            </div>
          ) : searchResults.length === 0 ? (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
              <p className="text-gray-600 mb-1">No tracks found</p>
              <p className="text-gray-400 text-sm">Try a different search term</p>
            </div>
          ) : (
            <div className="space-y-3">
              {searchResults.map((track, i) => renderTrackCard(track, i))}
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
              { value: 'track_name', label: 'Name' },
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

          {/* Track Count */}
          {pagination.total > 0 && (
            <p className="text-sm text-gray-500 mb-4">
              {dbTracks.length} of {pagination.total} tracks
            </p>
          )}

          {/* Tracks List */}
          {dbLoading ? (
            <div className="space-y-3">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="bg-gray-100 animate-pulse rounded-lg h-20"></div>
              ))}
            </div>
          ) : dbError ? (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
              {dbError}
            </div>
          ) : dbTracks.length === 0 ? (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
              <p className="text-gray-600 mb-1">No tracks yet</p>
              <p className="text-gray-400 text-sm">
                Search above to find and add tracks from SoundCloud and Spotify
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {dbTracks.map((track, i) => renderTrackCard({
                ...track,
                _source: 'db',
                _name: track.track_name,
                _artist: track.artist_name,
                _platform: track.spotify_url ? 'spotify' : track.soundcloud_url ? 'soundcloud' : null,
                _thumbnail: track.thumbnail_url,
                _dbId: track.id,
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

export default TracksDiscoverPage;
