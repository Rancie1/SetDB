/**
 * Track tag form component.
 *
 * Allows users to add track tags to sets by searching or entering a URL.
 * Track name and artist are automatically determined from the selected track.
 */

import { useState } from 'react';
import * as tracksService from '../../services/tracksService';
import * as standaloneTracksService from '../../services/standaloneTracksService';
import useAuthStore from '../../store/authStore';

const TrackTagForm = ({ setId, onSubmit, onCancel, setHasRecording = false }) => {
  const { isAuthenticated } = useAuthStore();

  const [searchQuery, setSearchQuery] = useState('');
  const [urlInput, setUrlInput] = useState('');
  const [platform, setPlatform] = useState('all');
  const [searching, setSearching] = useState(false);
  const [resolvingUrl, setResolvingUrl] = useState(false);
  const [searchResults, setSearchResults] = useState([]);
  const [showSearchResults, setShowSearchResults] = useState(false);
  const [selectedTrack, setSelectedTrack] = useState(null);
  const [timestampInput, setTimestampInput] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [addingTrack, setAddingTrack] = useState(null);

  const parseTimestamp = (timestampStr) => {
    if (!timestampStr || !timestampStr.trim()) return null;

    const trimmed = timestampStr.trim();
    if (trimmed.includes(':')) {
      const parts = trimmed.split(':');
      if (parts.length === 2) {
        const hours = parseInt(parts[0], 10) || 0;
        const minutes = parseInt(parts[1], 10) || 0;
        if (isNaN(hours) || isNaN(minutes) || hours < 0 || minutes < 0 || minutes >= 60) {
          return null;
        }
        return (hours * 60) + minutes;
      }
    }
    const decimal = parseFloat(trimmed);
    return isNaN(decimal) ? null : decimal;
  };

  const handleSearch = async (e) => {
    e.preventDefault();

    if (!searchQuery.trim()) {
      setSearchResults([]);
      setShowSearchResults(false);
      return;
    }

    setSearching(true);
    setShowSearchResults(true);
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
      alert(error.response?.data?.detail || 'Failed to search tracks');
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  };

  const handleResolveUrl = async () => {
    if (!urlInput.trim()) {
      alert('Please enter a SoundCloud or Spotify URL');
      return;
    }

    const url = urlInput.trim();
    const isSoundCloud = url.includes('soundcloud.com');
    const isSpotify = url.includes('spotify.com') || url.startsWith('spotify:track:');

    if (!isSoundCloud && !isSpotify) {
      alert('Please enter a valid SoundCloud or Spotify track URL');
      return;
    }

    setResolvingUrl(true);
    try {
      const response = await tracksService.resolveTrackUrl(url);
      const trackInfo = response.data;

      if (!trackInfo) {
        alert('Could not find track information from the URL. Please try searching instead.');
        return;
      }

      setSelectedTrack(trackInfo);
      setUrlInput('');
    } catch (error) {
      console.error('Failed to resolve URL:', error);
      alert(error.response?.data?.detail || 'Failed to resolve URL. Please try searching instead.');
    } finally {
      setResolvingUrl(false);
    }
  };

  const handleSelectResult = (result) => {
    setSelectedTrack(result);
    setShowSearchResults(false);
    setSearchQuery('');
  };

  const handleAddTrack = async () => {
    if (!selectedTrack) {
      alert('Please select a track from search results or enter a URL');
      return;
    }

    if (!isAuthenticated()) {
      alert('Please log in to add tracks');
      return;
    }

    setAddingTrack(selectedTrack.id);
    try {
      let trackId = null;

      if (selectedTrack.exists_in_db && selectedTrack.track_id) {
        trackId = selectedTrack.track_id;
      } else {
        const trackData = {
          track_name: selectedTrack.title || '',
          artist_name: selectedTrack.artist_name || null,
          soundcloud_url: selectedTrack.soundcloud_url || null,
          soundcloud_track_id: selectedTrack.platform === 'soundcloud' && selectedTrack.id ? String(selectedTrack.id) : null,
          spotify_url: selectedTrack.spotify_url || null,
          spotify_track_id: selectedTrack.platform === 'spotify' && selectedTrack.id ? selectedTrack.id : null,
          thumbnail_url: selectedTrack.thumbnail_url || null,
          duration_ms: selectedTrack.duration_ms || null,
          spotify_artist_ids: selectedTrack.platform === 'spotify' && selectedTrack.artist_ids?.length ? selectedTrack.artist_ids : null,
        };

        const createResponse = await standaloneTracksService.createTrack(trackData);
        trackId = createResponse.data.id;
      }

      const timestampMinutes = timestampInput ? parseTimestamp(timestampInput) : null;

      if (timestampInput && timestampMinutes === null) {
        alert('Invalid timestamp format. Please use HH:MM format (e.g., 1:30)');
        setAddingTrack(null);
        return;
      }

      await tracksService.addTrackTag(setId, {
        track_id: trackId,
        timestamp_minutes: timestampMinutes,
      });

      setSelectedTrack(null);
      setSearchQuery('');
      setUrlInput('');
      setTimestampInput('');
      setSearchResults([]);
      setShowSearchResults(false);
      if (onSubmit) onSubmit();
    } catch (error) {
      console.error('Failed to add track:', error);
      alert(error.response?.data?.detail || 'Failed to add track');
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
    <div className="bg-surface-800 rounded-xl border border-white/5 p-4">
      <h3 className="text-lg font-semibold mb-4 text-slate-100">Add Track Tag</h3>

      <div className="space-y-4">
        {/* Search Section */}
        <div>
          <label className="block text-sm font-medium text-slate-400 mb-1">Search Tracks</label>
          <div className="flex gap-2 mb-2">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search for tracks, artists, or songs..."
              className="flex-1 px-3 py-2 bg-surface-700 border border-white/10 text-slate-100 placeholder-slate-500 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none text-sm"
            />
            <select
              value={platform}
              onChange={(e) => setPlatform(e.target.value)}
              className="px-3 py-2 bg-surface-700 border border-white/10 text-slate-300 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none text-sm cursor-pointer"
            >
              <option value="all">All</option>
              <option value="soundcloud">SoundCloud</option>
              <option value="spotify">Spotify</option>
            </select>
            <button
              type="button"
              onClick={handleSearch}
              disabled={searching || !searchQuery.trim()}
              className="px-4 py-2 bg-primary-600 hover:bg-primary-500 text-white font-medium rounded-xl disabled:opacity-50 disabled:cursor-not-allowed transition-colors cursor-pointer text-sm"
            >
              {searching ? 'Searching...' : 'Search'}
            </button>
          </div>
        </div>

        {/* URL Input Section */}
        <div>
          <label className="block text-sm font-medium text-slate-400 mb-1">Or Enter Track URL</label>
          <div className="flex gap-2">
            <input
              type="text"
              value={urlInput}
              onChange={(e) => setUrlInput(e.target.value)}
              placeholder="https://soundcloud.com/artist/track or https://open.spotify.com/track/..."
              className="flex-1 px-3 py-2 bg-surface-700 border border-white/10 text-slate-100 placeholder-slate-500 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none text-sm"
            />
            <button
              type="button"
              onClick={handleResolveUrl}
              disabled={resolvingUrl || !urlInput.trim()}
              className="px-4 py-2 bg-primary-600 hover:bg-primary-500 text-white font-medium rounded-xl disabled:opacity-50 disabled:cursor-not-allowed transition-colors cursor-pointer text-sm"
            >
              {resolvingUrl ? 'Resolving...' : 'Resolve'}
            </button>
          </div>
        </div>

        {/* Search Results */}
        {showSearchResults && (
          <>
            {searching ? (
              <div className="text-center py-4 text-sm text-slate-500">Searching...</div>
            ) : searchResults.length > 0 ? (
              <div className="bg-surface-700 border border-white/10 rounded-xl max-h-60 overflow-y-auto">
                <div className="p-2 border-b border-white/5">
                  <p className="text-xs font-medium text-slate-500">Search Results</p>
                </div>
                <div className="divide-y divide-white/5">
                  {searchResults.map((result) => (
                    <button
                      key={result.id}
                      type="button"
                      onClick={() => handleSelectResult(result)}
                      className={`w-full text-left p-3 hover:bg-surface-600 transition-colors cursor-pointer ${
                        selectedTrack?.id === result.id ? 'bg-primary-600/20 border-l-2 border-primary-500' : ''
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1">
                          <p className="text-sm font-medium text-slate-200">{result.title}</p>
                          <p className="text-xs text-slate-500">{result.artist_name}</p>
                          {result.exists_in_db && (
                            <p className="text-xs text-green-400 mt-1">In Deckd</p>
                          )}
                        </div>
                        {selectedTrack?.id === result.id && (
                          <span className="text-xs text-primary-400 font-medium">Selected</span>
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-center py-4 text-sm text-slate-500">
                No results found. Try a different search query.
              </div>
            )}
          </>
        )}

        {/* Selected Track Display */}
        {selectedTrack && (
          <div className="bg-primary-600/10 border border-primary-500/20 rounded-xl p-4">
            <div className="flex items-start justify-between mb-2">
              <div className="flex-1">
                <p className="text-sm font-semibold text-slate-200">{selectedTrack.title}</p>
                <p className="text-xs text-slate-500">{selectedTrack.artist_name}</p>
                {selectedTrack.duration_ms && (
                  <p className="text-xs text-slate-500 mt-1">{formatDuration(selectedTrack.duration_ms)}</p>
                )}
              </div>
              <button
                type="button"
                onClick={() => setSelectedTrack(null)}
                className="text-slate-500 hover:text-slate-300 cursor-pointer"
              >
                ×
              </button>
            </div>
          </div>
        )}

        {/* Timestamp (for sets with recordings) */}
        {setHasRecording && (
          <div>
            <label className="block text-sm font-medium text-slate-400 mb-1">Timestamp (HH:MM)</label>
            <input
              type="text"
              value={timestampInput}
              onChange={(e) => setTimestampInput(e.target.value)}
              pattern="[0-9]+:[0-5][0-9]"
              className="w-full px-3 py-2 bg-surface-700 border border-white/10 text-slate-100 placeholder-slate-500 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none text-sm"
              placeholder="e.g., 1:30"
            />
            <p className="text-xs text-slate-600 mt-1">When in the recording this track starts (optional, format: HH:MM)</p>
          </div>
        )}

        {/* Form Actions */}
        <div className="flex gap-2">
          <button
            type="button"
            onClick={handleAddTrack}
            disabled={submitting || !selectedTrack || addingTrack}
            className="flex-1 px-4 py-2 bg-primary-600 hover:bg-primary-500 text-white font-medium rounded-xl disabled:opacity-50 disabled:cursor-not-allowed transition-colors cursor-pointer text-sm"
          >
            {addingTrack ? 'Adding...' : 'Add Track'}
          </button>
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 bg-surface-700 hover:bg-surface-600 text-slate-300 font-medium rounded-xl border border-white/5 transition-colors cursor-pointer text-sm"
            >
              Cancel
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default TrackTagForm;
