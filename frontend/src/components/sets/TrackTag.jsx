/**
 * Track tag component.
 * 
 * Displays a single track tag with SoundCloud link, timestamp, and confirmation buttons.
 */

import { useState } from 'react';
import * as tracksService from '../../services/tracksService';
import useAuthStore from '../../store/authStore';

const TrackTag = ({ track, onDelete, canDelete, onConfirmationChange, setHasRecording }) => {
  const { isAuthenticated, user } = useAuthStore();
  const [confirming, setConfirming] = useState(false);
  
  const displayName = track.artist_name
    ? `${track.track_name} - ${track.artist_name}`
    : track.track_name;

  const formatTimestamp = (minutes) => {
    if (!minutes && minutes !== 0) return null;
    const mins = Math.floor(minutes);
    const secs = Math.round((minutes - mins) * 60);
    if (secs === 0) {
      return `${mins}:00`;
    }
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleConfirm = async (isConfirmed) => {
    if (!isAuthenticated) {
      alert('Please log in to confirm tracks');
      return;
    }

    if (confirming) {
      return; // Prevent double-clicks
    }

    setConfirming(true);
    try {
      // Check current user confirmation status
      // Handle both boolean true/false, string "true"/"false", and null/undefined from API
      const currentConfirmation = track.user_confirmation;
      const isCurrentlyConfirmed = currentConfirmation === true || currentConfirmation === "true";
      const isCurrentlyDenied = currentConfirmation === false || currentConfirmation === "false";
      
      // If user clicks confirm button
      if (isConfirmed) {
        // If already confirmed, remove it (toggle off)
        if (isCurrentlyConfirmed) {
          await tracksService.removeTrackConfirmation(track.set_id, track.id);
        } else {
          // Add or update to confirmed
          await tracksService.confirmTrack(track.set_id, track.id, { is_confirmed: true });
        }
      } else {
        // If user clicks deny button
        // If already denied, remove it (toggle off)
        if (isCurrentlyDenied) {
          await tracksService.removeTrackConfirmation(track.set_id, track.id);
        } else {
          // Add or update to denied
          await tracksService.confirmTrack(track.set_id, track.id, { is_confirmed: false });
        }
      }
      
      // Always reload tracks to get updated confirmation status
      if (onConfirmationChange) {
        await onConfirmationChange();
      }
    } catch (error) {
      console.error('Failed to confirm track:', error);
      console.error('Error details:', error.response?.data);
      alert(error.response?.data?.detail || 'Failed to confirm track');
    } finally {
      setConfirming(false);
    }
  };

  // Handle both boolean true/false, string "true"/"false", and null/undefined from API
  const userConfirmation = track.user_confirmation;
  const isConfirmed = userConfirmation === true || userConfirmation === "true";
  const isDenied = userConfirmation === false || userConfirmation === "false";

  return (
    <div className="p-3 bg-gray-50 rounded-lg border border-gray-200 hover:bg-gray-100 transition-colors">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <p className="text-sm font-medium text-gray-900">{track.track_name}</p>
            {track.timestamp_minutes != null && setHasRecording && (
              <span className="text-xs text-gray-500 bg-gray-200 px-2 py-0.5 rounded">
                {formatTimestamp(track.timestamp_minutes)}
              </span>
            )}
          </div>
          {track.artist_name && (
            <p className="text-xs text-gray-600 mb-2">{track.artist_name}</p>
          )}
          
          {/* Confirmation Stats */}
          {(track.confirmation_count > 0 || track.denial_count > 0) && (
            <div className="flex items-center gap-3 text-xs text-gray-500 mt-2">
              {track.confirmation_count > 0 && (
                <span className="text-green-600">✓ {track.confirmation_count} confirmed</span>
              )}
              {track.denial_count > 0 && (
                <span className="text-red-600">✗ {track.denial_count} denied</span>
              )}
            </div>
          )}
        </div>
        
        <div className="flex items-center gap-2">
          {track.soundcloud_url && (
            <a
              href={track.soundcloud_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center px-3 py-1.5 bg-orange-600 hover:bg-orange-700 text-white text-xs font-medium rounded-md transition-colors"
            >
              <span className="mr-1.5">🎵</span>
              SoundCloud
            </a>
          )}
          
          {isAuthenticated && (
            <div className="flex items-center gap-1">
              <button
                onClick={() => handleConfirm(true)}
                disabled={confirming}
                className={`px-2 py-1 text-xs font-medium rounded transition-colors ${
                  isConfirmed
                    ? 'bg-green-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-green-100'
                } disabled:opacity-50`}
                title="Confirm this track is correct"
              >
                ✓
              </button>
              <button
                onClick={() => handleConfirm(false)}
                disabled={confirming}
                className={`px-2 py-1 text-xs font-medium rounded transition-colors ${
                  isDenied
                    ? 'bg-red-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-red-100'
                } disabled:opacity-50`}
                title="Deny this track is incorrect"
              >
                ✗
              </button>
            </div>
          )}
          
          {canDelete && onDelete && (
            <button
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                onDelete(track.id);
              }}
              className="ml-2 text-red-600 hover:text-red-700 text-sm font-medium px-2 py-1 rounded hover:bg-red-50 transition-colors"
              title="Remove track tag"
            >
              ×
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default TrackTag;
