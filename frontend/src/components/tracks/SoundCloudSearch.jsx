/**
 * Track Search component.
 * 
 * Allows users to search SoundCloud and Spotify directly and create tracks.
 */

import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import * as tracksService from '../../services/tracksService';
import * as standaloneTracksService from '../../services/standaloneTracksService';
import useAuthStore from '../../store/authStore';
import SpotifyEmbed from './SpotifyEmbed';

const SoundCloudSearch = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [platform, setPlatform] = useState('all'); // 'all', 'soundcloud', 'spotify'
  const [searching, setSearching] = useState(false);
  const [searchResults, setSearchResults] = useState([]);
  const [showResults, setShowResults] = useState(false);
  const [addingTrack, setAddingTrack] = useState(null);

  const handleSearch = async (e) => {
    e.preventDefault();
    
    if (!searchQuery.trim()) {
      setSearchResults([]);
      setShowResults(false);
      return;
    }

    setSearching(true);
    setShowResults(true);
    try {
      let response;
      if (platform === 'all') {
        response = await tracksService.searchTracks(searchQuery.trim(), 'all', 20);
      } else if (platform === 'spotify') {
        response = await tracksService.searchSpotify(searchQuery.trim(), 20);
      } else {
        response = await tracksService.searchSoundCloud(searchQuery.trim(), 20);
      }
      setSearchResults(response.data || []);
    } catch (error) {
      console.error('Failed to search tracks:', error);
      alert(error.response?.data?.detail || 'Failed to search tracks. Make sure you are logged in.');
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  };

  const handleCreateOrViewTrack = async (track) => {
    if (!isAuthenticated()) {
      alert('Please log in to create or view tracks');
      navigate('/login');
      return;
    }

    setAddingTrack(track.id);
    try {
      // Check if track already exists
      if (track.exists_in_db && track.track_id) {
        // Track exists, navigate to it
        navigate(`/tracks/${track.track_id}`);
        return;
      }
      
      // Create new track
      const trackData = {
        track_name: track.title || '',
        artist_name: track.artist_name || null,
        soundcloud_url: track.soundcloud_url || null,
        soundcloud_track_id: track.platform === 'soundcloud' && track.id ? String(track.id) : null,
        spotify_url: track.spotify_url || null,
        spotify_track_id: track.platform === 'spotify' && track.id ? track.id : null,
        thumbnail_url: track.thumbnail_url || null,
        duration_ms: track.duration_ms || null,
      };
      
      const response = await standaloneTracksService.createTrack(trackData);
      // Navigate to the new track's detail page
      navigate(`/tracks/${response.data.id}`);
    } catch (error) {
      console.error('Failed to create track:', error);
      if (error.response?.status === 409) {
        // Track already exists, try to find it and navigate
        alert('Track already exists. Searching...');
        // We could search for it, but for now just show error
      }
      alert(error.response?.data?.detail || 'Failed to create track');
    } finally {
      setAddingTrack(null);
    }
  };

  const formatDuration = (ms) => {
    if (!ms) return '';
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  return (
    <div className="bg-surface-800 rounded-xl border border-white/5 p-6 mb-6">
      <h2 className="text-xl font-semibold mb-4">Search Tracks</h2>
      <p className="text-sm text-gray-600 mb-4">
        Search SoundCloud and Spotify. Click on a track to view or add it to Deckd.
      </p>

      <form onSubmit={handleSearch} className="mb-4">
        <div className="flex gap-2 mb-3">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search for tracks, artists, or songs..."
            className="flex-1 px-4 py-2 bg-surface-700 border border-white/10 text-slate-100 placeholder-slate-500 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none text-sm"
          />
          <select
            value={platform}
            onChange={(e) => setPlatform(e.target.value)}
            className="px-4 py-2 bg-surface-700 border border-white/10 text-slate-300 rounded-xl focus:ring-2 focus:ring-primary-500 outline-none text-sm cursor-pointer"
          >
            <option value="all">All Platforms</option>
            <option value="soundcloud">SoundCloud</option>
            <option value="spotify">Spotify</option>
          </select>
          <button
            type="submit"
            disabled={searching || !searchQuery.trim()}
            className="px-6 py-2 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-md disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {searching ? 'Searching...' : 'Search'}
          </button>
        </div>
      </form>

      {/* Search Results */}
      {showResults && (
        <div>
          {searching ? (
            <div className="text-center py-8">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-orange-600"></div>
              <p className="mt-2 text-sm text-gray-600">Searching...</p>
            </div>
          ) : searchResults.length > 0 ? (
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {searchResults.map((track) => (
                <div
                  key={track.id}
                  className="bg-surface-700 border border-white/5 rounded-xl p-4 hover:bg-surface-600 transition-colors cursor-pointer"
                >
                  <div className="flex items-start gap-4">
                    {/* Thumbnail */}
                    {track.thumbnail_url && (
                      <img
                        src={track.thumbnail_url}
                        alt={track.title}
                        className="w-16 h-16 rounded object-cover"
                      />
                    )}
                    
                    {/* Track Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-0.5">
                        <h3 className="font-semibold text-slate-200 truncate">{track.title}</h3>
                        {track.platform === 'spotify' && (
                          <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-green-100 text-green-700 flex-shrink-0">Spotify</span>
                        )}
                        {track.platform === 'soundcloud' && (
                          <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-orange-100 text-orange-700 flex-shrink-0">SoundCloud</span>
                        )}
                        {track.exists_in_db && (
                          <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-medium bg-primary-100 text-primary-700 flex-shrink-0">In Deckd</span>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 mb-1 truncate">{track.artist_name}</p>
                      
                      <div className="flex items-center gap-3 text-xs text-gray-400">
                        {track.duration_ms > 0 && (
                          <span>{formatDuration(track.duration_ms)}</span>
                        )}
                        {track.playback_count > 0 && (
                          <span>{track.playback_count.toLocaleString()} plays</span>
                        )}
                        {track.likes_count > 0 && (
                          <span>{track.likes_count.toLocaleString()} likes</span>
                        )}
                      </div>

                      {/* Actions */}
                      <div className="flex items-center gap-2 mt-2">
                        {track.exists_in_db && track.track_id ? (
                          <Link
                            to={`/tracks/${track.track_id}`}
                            className="px-3 py-1.5 bg-primary-600 hover:bg-primary-700 text-white text-xs font-medium rounded-md transition-colors"
                          >
                            View Track
                          </Link>
                        ) : (
                          <button
                            onClick={() => handleCreateOrViewTrack(track)}
                            disabled={addingTrack === track.id || !isAuthenticated()}
                            className="px-3 py-1.5 bg-primary-600 hover:bg-primary-700 text-white text-xs font-medium rounded-md disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                          >
                            {addingTrack === track.id ? 'Adding...' : isAuthenticated() ? 'Add to Deckd' : 'Log in to Add'}
                          </button>
                        )}
                        {(track.soundcloud_url || track.spotify_url) && (
                          <a
                            href={track.soundcloud_url || track.spotify_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 text-xs font-medium rounded-md transition-colors"
                          >
                            Open in {track.platform === 'spotify' ? 'Spotify' : 'SoundCloud'}
                          </a>
                        )}
                      </div>
                      {track.platform === 'spotify' && track.id && (
                        <div className="mt-2">
                          <SpotifyEmbed spotifyTrackId={track.id} compact={true} />
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <p>No results found. Try a different search query.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SoundCloudSearch;
