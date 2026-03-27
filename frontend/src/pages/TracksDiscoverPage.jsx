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
    spotify: 'bg-green-500/20 text-green-300 border border-green-500/30',
    soundcloud: 'bg-orange-500/20 text-orange-300 border border-orange-500/30',
  };
  return (
    <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium ${styles[platform] || 'bg-white/5 text-slate-400 border border-white/10'}`}>
      {platform === 'spotify' ? 'Spotify' : platform === 'soundcloud' ? 'SoundCloud' : platform}
    </span>
  );
};

const TracksDiscoverPage = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthStore();

  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [dbTracks, setDbTracks] = useState([]);
  const [dbLoading, setDbLoading] = useState(false);
  const [dbError, setDbError] = useState(null);
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('desc');
  const [pagination, setPagination] = useState({ page: 1, limit: 20, total: 0, pages: 0 });
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [importingId, setImportingId] = useState(null);
  const searchTimeout = useRef(null);

  useEffect(() => {
    if (!isSearching) loadDbTracks();
  }, [pagination.page, sortBy, sortOrder, isSearching]);

  useEffect(() => {
    if (searchTimeout.current) clearTimeout(searchTimeout.current);
    if (!searchQuery.trim()) { setIsSearching(false); setSearchResults([]); return; }
    setIsSearching(true);
    setSearchLoading(true);
    searchTimeout.current = setTimeout(() => performSearch(searchQuery.trim()), 400);
    return () => { if (searchTimeout.current) clearTimeout(searchTimeout.current); };
  }, [searchQuery]);

  const loadDbTracks = async () => {
    setDbLoading(true); setDbError(null);
    try {
      const response = await tracksService.discoverTracks({ sort: sortBy, order: sortOrder }, pagination.page, pagination.limit);
      setDbTracks(response.data.items || []);
      setPagination(prev => ({ ...prev, total: response.data.total || 0, pages: response.data.pages || 0 }));
    } catch (err) {
      setDbError(err.response?.data?.detail || 'Failed to load tracks');
      setDbTracks([]);
    } finally { setDbLoading(false); }
  };

  const performSearch = async (query) => {
    setSearchLoading(true);
    try {
      const [dbResponse, platformResponse] = await Promise.all([
        tracksService.discoverTracks({ search: query }, 1, 10),
        tracksService.searchTracks(query, 'all', 15).catch(() => ({ data: [] })),
      ]);
      const dbItems = (dbResponse.data.items || []).map(t => ({
        ...t, _source: 'db', _name: t.track_name, _artist: t.artist_name,
        _platform: t.spotify_url ? 'spotify' : t.soundcloud_url ? 'soundcloud' : null,
        _thumbnail: t.thumbnail_url, _dbId: t.id,
      }));
      const platformItems = (platformResponse.data || []).map(t => ({
        ...t, _source: 'external', _name: t.title, _artist: t.artist_name,
        _platform: t.platform, _thumbnail: t.thumbnail_url,
        _dbId: t.exists_in_db ? t.track_id : null,
        _externalId: t.id, _artistIds: t.artist_ids || [],
      }));
      const dbIds = new Set(dbItems.map(t => t._dbId).filter(Boolean));
      const deduped = platformItems.filter(t => !(t._dbId && dbIds.has(t._dbId)));
      const spotifyResults = deduped.filter(t => t._platform === 'spotify');
      const soundcloudResults = deduped.filter(t => t._platform === 'soundcloud');
      setSearchResults([...spotifyResults, ...soundcloudResults, ...dbItems]);
    } catch (err) { setSearchResults([]); }
    finally { setSearchLoading(false); }
  };

  const handleTrackClick = async (track) => {
    if (track._dbId) { navigate(`/tracks/${track._dbId}`); return; }
    if (!isAuthenticated()) { navigate('/login'); return; }
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
    } finally { setImportingId(null); }
  };

  const handleSortChange = (newSort) => {
    if (sortBy === newSort) { setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc'); }
    else { setSortBy(newSort); setSortOrder('desc'); }
    setPagination(prev => ({ ...prev, page: 1 }));
  };

  const handleClear = () => { setSearchQuery(''); setIsSearching(false); setSearchResults([]); };

  const formatDuration = (ms) => {
    if (!ms) return '';
    const seconds = Math.floor(ms / 1000);
    return `${Math.floor(seconds / 60)}:${(seconds % 60).toString().padStart(2, '0')}`;
  };

  const renderTrackCard = (track, index) => {
    const isDb = track._source === 'db';
    const { _name: name, _artist: artist, _platform: platform, _thumbnail: thumbnail, _dbId: dbId } = track;
    const isImporting = importingId === (track._externalId || track.id);
    const cardClass = "bg-surface-800 rounded-xl border border-white/5 p-4 hover:border-primary-500/30 hover:bg-surface-700 transition-colors cursor-pointer";

    const cardContent = (
      <div className="flex items-center gap-4">
        {thumbnail && <img src={thumbnail} alt={name} className="w-12 h-12 rounded-lg object-cover flex-shrink-0" />}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-0.5">
            <h3 className="font-semibold text-slate-100 truncate text-sm">{name}</h3>
            {platform && <PlatformTag platform={platform} />}
          </div>
          {artist && <p className="text-xs text-slate-400 truncate">{artist}</p>}
          <div className="flex items-center gap-3 mt-1 text-xs text-slate-500">
            {isDb && track.average_rating > 0 && (
              <span className="text-accent-400 font-medium">{track.average_rating.toFixed(1)}{track.rating_count > 0 && ` (${track.rating_count})`}</span>
            )}
            {isDb && track.linked_sets_count > 0 && <span>In {track.linked_sets_count} set{track.linked_sets_count !== 1 ? 's' : ''}</span>}
            {!isDb && track.duration_ms > 0 && <span>{formatDuration(track.duration_ms)}</span>}
          </div>
        </div>
        {isImporting && <div className="flex-shrink-0 animate-spin rounded-full h-5 w-5 border-b-2 border-primary-400"></div>}
        {isDb && (track.spotify_track_id || track.spotify_url) && (
          <div className="flex-shrink-0 w-[300px] hidden lg:block" onClick={(e) => e.stopPropagation()}>
            <SpotifyEmbed spotifyTrackId={track.spotify_track_id} spotifyUrl={track.spotify_url} compact={true} />
          </div>
        )}
      </div>
    );

    if (dbId) {
      return <Link key={`${track._source}-${dbId}-${index}`} to={`/tracks/${dbId}`} className={`block ${cardClass}`}>{cardContent}</Link>;
    }
    return (
      <button key={`${track._source}-${track._externalId || track.id}-${index}`}
        onClick={() => handleTrackClick(track)} disabled={isImporting}
        className={`w-full text-left ${cardClass} disabled:opacity-60`}>
        {cardContent}
      </button>
    );
  };

  const Skeleton = ({ h = 'h-20' }) => (
    <div className="space-y-3">
      {[1,2,3,4,5].map(i => <div key={i} className={`bg-surface-700 animate-pulse rounded-xl ${h}`}></div>)}
    </div>
  );

  const EmptyState = ({ title, subtitle }) => (
    <div className="bg-surface-800 border border-white/5 rounded-xl p-8 text-center">
      <p className="text-slate-400 mb-1">{title}</p>
      <p className="text-slate-500 text-sm">{subtitle}</p>
    </div>
  );

  const Pagination = ({ page, pages, onChange }) => pages > 1 && (
    <div className="flex items-center justify-center gap-2 mt-6">
      <button onClick={() => onChange(page - 1)} disabled={page === 1}
        className="px-4 py-2 bg-surface-800 border border-white/5 rounded-lg text-sm text-slate-300 hover:text-white hover:bg-surface-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors cursor-pointer">
        Previous
      </button>
      <span className="px-4 py-2 text-sm text-slate-500">{page} / {pages}</span>
      <button onClick={() => onChange(page + 1)} disabled={page >= pages}
        className="px-4 py-2 bg-surface-800 border border-white/5 rounded-lg text-sm text-slate-300 hover:text-white hover:bg-surface-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors cursor-pointer">
        Next
      </button>
    </div>
  );

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2 text-slate-100">Tracks</h1>
        <p className="text-slate-400">Search across Deckd, SoundCloud, and Spotify — or browse what's already here.</p>
      </div>

      {/* Search Bar */}
      <div className="mb-6">
        <div className="relative">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search for any track or artist..."
            className="w-full px-4 py-3 pl-11 bg-surface-800 border border-white/10 text-slate-100 placeholder-slate-500 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none text-sm"
          />
          <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
            <svg className="w-5 h-5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          {searchQuery && (
            <button onClick={handleClear} className="absolute inset-y-0 right-0 flex items-center pr-3 text-slate-500 hover:text-slate-300 cursor-pointer">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
        {isSearching && !searchLoading && searchResults.length > 0 && (
          <p className="text-xs text-slate-500 mt-2">{searchResults.length} results from Deckd, SoundCloud, and Spotify</p>
        )}
      </div>

      {isSearching ? (
        <div>
          {searchLoading ? <Skeleton /> : searchResults.length === 0
            ? <EmptyState title="No tracks found" subtitle="Try a different search term" />
            : <div className="space-y-2">{searchResults.map((track, i) => renderTrackCard(track, i))}</div>
          }
        </div>
      ) : (
        <div>
          {/* Sort Options */}
          <div className="flex items-center gap-3 flex-wrap mb-6">
            <span className="text-sm text-slate-500">Sort by:</span>
            {[
              { value: 'created_at', label: 'Newest' },
              { value: 'track_name', label: 'Name' },
              { value: 'artist_name', label: 'Artist' },
              { value: 'average_rating', label: 'Rating' },
              { value: 'rating_count', label: 'Most Rated' },
            ].map((option) => (
              <button key={option.value} onClick={() => handleSortChange(option.value)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors cursor-pointer ${
                  sortBy === option.value ? 'bg-primary-600 text-white' : 'bg-surface-700 text-slate-400 hover:bg-surface-600 hover:text-slate-200'
                }`}>
                {option.label}
                {sortBy === option.value && <span className="ml-1">{sortOrder === 'asc' ? '↑' : '↓'}</span>}
              </button>
            ))}
          </div>

          {pagination.total > 0 && (
            <p className="text-sm text-slate-500 mb-4">{dbTracks.length} of {pagination.total} tracks</p>
          )}

          {dbLoading ? <Skeleton />
            : dbError ? (
              <div className="bg-red-500/10 border border-red-500/20 text-red-400 px-4 py-3 rounded-xl">{dbError}</div>
            ) : dbTracks.length === 0 ? (
              <EmptyState title="No tracks yet" subtitle="Search above to find and add tracks from SoundCloud and Spotify" />
            ) : (
              <div className="space-y-2">
                {dbTracks.map((track, i) => renderTrackCard({
                  ...track, _source: 'db', _name: track.track_name, _artist: track.artist_name,
                  _platform: track.spotify_url ? 'spotify' : track.soundcloud_url ? 'soundcloud' : null,
                  _thumbnail: track.thumbnail_url, _dbId: track.id,
                }, i))}
              </div>
            )
          }

          <Pagination page={pagination.page} pages={pagination.pages}
            onChange={(p) => setPagination(prev => ({ ...prev, page: p }))} />
        </div>
      )}
    </div>
  );
};

export default TracksDiscoverPage;
