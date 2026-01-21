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
  const [platform, setPlatform] = useState('all'); // 'all', 'soundcloud', 'spotify'
  const [searching, setSearching] = useState(false);
  const [resolvingUrl, setResolvingUrl] = useState(false);
  const [searchResults, setSearchResults] = useState([]);
  const [showSearchResults, setShowSearchResults] = useState(false);
  const [selectedTrack, setSelectedTrack] = useState(null);
  const [timestampInput, setTimestampInput] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [addingTrack, setAddingTrack] = useState(null);

  // Convert MM:SS format to decimal minutes
  const parseTimestamp = (timestampStr) => {
    if (!timestampStr || !timestampStr.trim()) return null;
    
    const trimmed = timestampStr.trim();
    // Handle MM:SS format
    if (trimmed.includes(':')) {
      const parts = trimmed.split(':');
      if (parts.length === 2) {
        const minutes = parseInt(parts[0], 10) || 0;
        const seconds = parseInt(parts[1], 10) || 0;
        if (isNaN(minutes) || isNaN(seconds) || minutes < 0 || seconds < 0 || seconds >= 60) {
          return null;
        }
        return minutes + (seconds / 60);
      }
    }
    // Handle decimal minutes as fallback
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

      // Set as selected track
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
      
      // Check if track already exists in database
      if (selectedTrack.exists_in_db && selectedTrack.track_id) {
        trackId = selectedTrack.track_id;
      } else {
        // Create new track in database
        const trackData = {
          track_name: selectedTrack.title || '',
          artist_name: selectedTrack.artist_name || null,
          soundcloud_url: selectedTrack.soundcloud_url || null,
          soundcloud_track_id: selectedTrack.platform === 'soundcloud' && selectedTrack.id ? String(selectedTrack.id) : null,
          spotify_url: selectedTrack.spotify_url || null,
          spotify_track_id: selectedTrack.platform === 'spotify' && selectedTrack.id ? selectedTrack.id : null,
          thumbnail_url: selectedTrack.thumbnail_url || null,
          duration_ms: selectedTrack.duration_ms || null,
        };
        
        const createResponse = await standaloneTracksService.createTrack(trackData);
        trackId = createResponse.data.id;
      }
      
      // Parse timestamp
      const timestampMinutes = timestampInput ? parseTimestamp(timestampInput) : null;
      
      if (timestampInput && timestampMinutes === null) {
        alert('Invalid timestamp format. Please use MM:SS format (e.g., 2:30)');
        setAddingTrack(null);
        return;
      }
      
      // Link track to set using track_id
      await tracksService.addTrackTag(setId, {
        track_id: trackId,
        timestamp_minutes: timestampMinutes,
      });
      
      // Reset form and close
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
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <h3 className="text-lg font-semibold mb-4">Add Track Tag</h3>
      
      <div className="space-y-4">
        {/* Search Section */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Search Tracks
          </label>
          <div className="flex gap-2 mb-2">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search for tracks, artists, or songs..."
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
            <select
              value={platform}
              onChange={(e) => setPlatform(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="all">All</option>
              <option value="soundcloud">SoundCloud</option>
              <option value="spotify">Spotify</option>
            </select>
            <button
              type="button"
              onClick={handleSearch}
              disabled={searching || !searchQuery.trim()}
              className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-md disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {searching ? 'Searching...' : '🔍 Search'}
            </button>
          </div>
        </div>

        {/* URL Input Section */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Or Enter Track URL
          </label>
          <div className="flex gap-2">
            <input
              type="text"
              value={urlInput}
              onChange={(e) => setUrlInput(e.target.value)}
              placeholder="https://soundcloud.com/artist/track or https://open.spotify.com/track/..."
              className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
            <button
              type="button"
              onClick={handleResolveUrl}
              disabled={resolvingUrl || !urlInput.trim()}
              className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-md disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {resolvingUrl ? 'Resolving...' : 'Resolve'}
            </button>
          </div>
        </div>

        {/* Search Results */}
        {showSearchResults && (
          <>
            {searching ? (
              <div className="text-center py-4 text-sm text-gray-500">
                Searching...
              </div>
            ) : searchResults.length > 0 ? (
              <div className="border border-gray-200 rounded-md max-h-60 overflow-y-auto">
                <div className="p-2 bg-gray-50 border-b border-gray-200">
                  <p className="text-xs font-medium text-gray-700">Search Results</p>
                </div>
                <div className="divide-y divide-gray-200">
                  {searchResults.map((result) => (
                    <button
                      key={result.id}
                      type="button"
                      onClick={() => handleSelectResult(result)}
                      className={`w-full text-left p-3 hover:bg-gray-50 transition-colors ${
                        selectedTrack?.id === result.id ? 'bg-primary-50 border-l-4 border-primary-500' : ''
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1">
                          <p className="text-sm font-medium text-gray-900">{result.title}</p>
                          <p className="text-xs text-gray-600">{result.artist_name}</p>
                          {result.exists_in_db && (
                            <p className="text-xs text-green-600 mt-1">✓ Already in database</p>
                          )}
                        </div>
                        {selectedTrack?.id === result.id && (
                          <span className="text-xs text-primary-600 font-medium">✓ Selected</span>
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-center py-4 text-sm text-gray-500">
                No results found. Try a different search query.
              </div>
            )}
          </>
        )}

        {/* Selected Track Display */}
        {selectedTrack && (
          <div className="bg-primary-50 border border-primary-200 rounded-md p-4">
            <div className="flex items-start justify-between mb-2">
              <div className="flex-1">
                <p className="text-sm font-semibold text-gray-900">{selectedTrack.title}</p>
                <p className="text-xs text-gray-600">{selectedTrack.artist_name}</p>
                {selectedTrack.duration_ms && (
                  <p className="text-xs text-gray-500 mt-1">⏱️ {formatDuration(selectedTrack.duration_ms)}</p>
                )}
              </div>
              <button
                type="button"
                onClick={() => setSelectedTrack(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                ×
              </button>
            </div>
          </div>
        )}

        {/* Timestamp (for sets with recordings) */}
        {setHasRecording && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Timestamp (MM:SS)
            </label>
            <input
              type="text"
              value={timestampInput}
              onChange={(e) => setTimestampInput(e.target.value)}
              pattern="[0-9]+:[0-5][0-9]"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              placeholder="e.g., 2:30"
            />
            <p className="text-xs text-gray-500 mt-1">When in the recording this track starts (optional, format: MM:SS)</p>
          </div>
        )}

        {/* Form Actions */}
        <div className="flex gap-2">
          <button
            type="button"
            onClick={handleAddTrack}
            disabled={submitting || !selectedTrack || addingTrack}
            className="flex-1 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-md disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {addingTrack ? 'Adding...' : 'Add Track'}
          </button>
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium rounded-md transition-colors"
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
