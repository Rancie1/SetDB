/**
 * Track tag form component.
 * 
 * Allows users to add track tags to sets, with SoundCloud search integration.
 */

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import * as tracksService from '../../services/tracksService';

const TrackTagForm = ({ setId, onSubmit, onCancel, setHasRecording = false }) => {
  const { register, handleSubmit, setValue, watch, reset } = useForm({
    defaultValues: {
      track_name: '',
      artist_name: '',
      soundcloud_url: '',
      timestamp_input: '',
    }
  });
  
  const [searching, setSearching] = useState(false);
  const [searchResults, setSearchResults] = useState([]);
  const [showSearchResults, setShowSearchResults] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const trackName = watch('track_name');
  const artistName = watch('artist_name');

  const handleSearch = async (e) => {
    e.preventDefault();
    const query = trackName || artistName || '';
    
    if (!query.trim()) {
      setSearchResults([]);
      setShowSearchResults(false);
      return;
    }

    setSearching(true);
    try {
      const response = await tracksService.searchSoundCloud(query, 10);
      setSearchResults(response.data || []);
      setShowSearchResults(true);
    } catch (error) {
      console.error('Failed to search SoundCloud:', error);
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  };

  const handleSelectResult = (result) => {
    setValue('track_name', result.title);
    setValue('artist_name', result.artist_name);
    setValue('soundcloud_url', result.soundcloud_url);
    setShowSearchResults(false);
  };

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

  const handleFormSubmit = async (data) => {
    if (!data.track_name.trim()) {
      alert('Please enter a track name');
      return;
    }

    // Parse timestamp from MM:SS format to decimal minutes
    const timestampMinutes = data.timestamp_input ? parseTimestamp(data.timestamp_input) : null;
    
    if (data.timestamp_input && timestampMinutes === null) {
      alert('Invalid timestamp format. Please use MM:SS format (e.g., 2:30)');
      return;
    }

    setSubmitting(true);
    try {
      await tracksService.addTrackTag(setId, {
        track_name: data.track_name.trim(),
        artist_name: data.artist_name?.trim() || null,
        soundcloud_url: data.soundcloud_url?.trim() || null,
        timestamp_minutes: timestampMinutes,
      });
      reset();
      setSearchResults([]);
      setShowSearchResults(false);
      if (onSubmit) onSubmit();
    } catch (error) {
      console.error('Failed to add track tag:', error);
      alert(error.response?.data?.detail || 'Failed to add track tag');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <h3 className="text-lg font-semibold mb-4">Add Track Tag</h3>
      
      <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
        {/* Track Name */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Track Name *
          </label>
          <input
            {...register('track_name')}
            type="text"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            placeholder="Enter track name"
            required
          />
        </div>

        {/* Artist Name */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Artist Name
          </label>
          <input
            {...register('artist_name')}
            type="text"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            placeholder="Enter artist name (optional)"
          />
        </div>

        {/* Timestamp (for sets with recordings) */}
        {setHasRecording && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Timestamp (MM:SS)
            </label>
            <input
              {...register('timestamp_input')}
              type="text"
              pattern="[0-9]+:[0-5][0-9]"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              placeholder="e.g., 2:30"
            />
            <p className="text-xs text-gray-500 mt-1">When in the recording this track starts (optional, format: MM:SS)</p>
          </div>
        )}

        {/* SoundCloud URL */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            SoundCloud URL
          </label>
          <input
            {...register('soundcloud_url')}
            type="url"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            placeholder="https://soundcloud.com/artist/track (optional)"
          />
        </div>

        {/* Search SoundCloud Button */}
        <div>
          <button
            type="button"
            onClick={handleSearch}
            disabled={searching || (!trackName && !artistName)}
            className="w-full px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white font-medium rounded-md disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {searching ? 'Searching...' : '🔍 Search on SoundCloud'}
          </button>
        </div>

        {/* Search Results */}
        {showSearchResults && searchResults.length > 0 && (
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
                  className="w-full text-left p-3 hover:bg-gray-50 transition-colors"
                >
                  <p className="text-sm font-medium text-gray-900">{result.title}</p>
                  <p className="text-xs text-gray-600">{result.artist_name}</p>
                </button>
              ))}
            </div>
          </div>
        )}

        {showSearchResults && searchResults.length === 0 && !searching && (
          <div className="text-center py-4 text-sm text-gray-500">
            No results found on SoundCloud
          </div>
        )}

        {/* Form Actions */}
        <div className="flex gap-2">
          <button
            type="submit"
            disabled={submitting}
            className="flex-1 px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-md disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {submitting ? 'Adding...' : 'Add Track'}
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
      </form>
    </div>
  );
};

export default TrackTagForm;
