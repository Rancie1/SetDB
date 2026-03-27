/**
 * Track tag component.
 * 
 * Displays a single track tag with SoundCloud link, timestamp, and confirmation buttons.
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import * as tracksService from '../../services/tracksService';
import * as trackRatingsService from '../../services/trackRatingsService';
import useAuthStore from '../../store/authStore';
import ArtistLink from '../shared/ArtistLink';

const TrackTag = ({ track, onDelete, canDelete, onConfirmationChange, setHasRecording, onRatingChange }) => {
  const { isAuthenticated, user } = useAuthStore();
  const [confirming, setConfirming] = useState(false);
  const [rating, setRating] = useState(track.user_rating || null);
  const [ratingLoading, setRatingLoading] = useState(false);
  const [showRatingSelector, setShowRatingSelector] = useState(false);
  
  useEffect(() => {
    setRating(track.user_rating || null);
  }, [track.user_rating]);
  
  const displayName = track.artist_name
    ? `${track.track_name} - ${track.artist_name}`
    : track.track_name;

  const formatTimestamp = (minutes) => {
    if (!minutes && minutes !== 0) return null;
    const totalMinutes = Math.round(minutes);
    const hours = Math.floor(totalMinutes / 60);
    const mins = totalMinutes % 60;
    return `${hours}:${mins.toString().padStart(2, '0')}`;
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
    <div className="p-3 bg-surface-800 rounded-xl border border-white/5 hover:border-primary-500/20 transition-colors">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            {track.track_entity_id ? (
              <Link
                to={`/tracks/${track.track_entity_id}`}
                className="text-sm font-medium text-slate-200 hover:text-primary-400 transition-colors"
              >
                {track.track_name}
              </Link>
            ) : (
              <p className="text-sm font-medium text-slate-200">{track.track_name}</p>
            )}
            {(track.timestamp_minutes != null && track.timestamp_minutes !== undefined) && setHasRecording && (
              <span className="text-xs text-slate-500 bg-surface-700 px-2 py-0.5 rounded">
                {formatTimestamp(track.timestamp_minutes)}
              </span>
            )}
          </div>
          {track.artist_name && (
            <p className="text-xs text-slate-500 mb-2">
              <ArtistLink name={track.artist_name} />
            </p>
          )}

          {/* Rating and Confirmation Stats */}
          <div className="flex items-center gap-3 text-xs text-slate-500 mt-2 flex-wrap">
            {track.average_rating && (
              <span className="text-accent-400">{track.average_rating.toFixed(1)} ({track.rating_count || 0})</span>
            )}
            {track.confirmation_count > 0 && (
              <span className="text-green-400">{track.confirmation_count} confirmed</span>
            )}
            {track.denial_count > 0 && (
              <span className="text-red-400">{track.denial_count} denied</span>
            )}
          </div>

          {/* Track Rating */}
          {isAuthenticated && (
            <div className="mt-2">
              {rating ? (
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-500">
                    Your rating: <span className="font-semibold text-accent-400">{rating.toFixed(1)}</span>
                  </span>
                  <button
                    onClick={() => setShowRatingSelector(!showRatingSelector)}
                    className="text-xs text-primary-400 hover:text-primary-300 cursor-pointer"
                  >
                    Change
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => setShowRatingSelector(!showRatingSelector)}
                  className="text-xs text-primary-400 hover:text-primary-300 cursor-pointer"
                >
                  Rate this track
                </button>
              )}

              {showRatingSelector && (
                <div className="mt-2 flex items-center gap-1 flex-wrap">
                  {[0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0].map((starValue) => (
                    <button
                      key={starValue}
                      onClick={async () => {
                        if (!isAuthenticated) {
                          alert('Please log in to rate tracks');
                          return;
                        }
                        setRatingLoading(true);
                        try {
                          await trackRatingsService.createTrackRating(track.id, starValue);
                          setRating(starValue);
                          setShowRatingSelector(false);
                          if (onRatingChange) {
                            await onRatingChange();
                          }
                        } catch (error) {
                          console.error('Failed to rate track:', error);
                          alert(error.response?.data?.detail || 'Failed to rate track');
                        } finally {
                          setRatingLoading(false);
                        }
                      }}
                      disabled={ratingLoading}
                      className={`text-sm px-1 py-0.5 rounded cursor-pointer ${
                        rating && starValue <= rating
                          ? 'text-accent-400 font-bold'
                          : 'text-slate-600 hover:text-accent-400'
                      } disabled:opacity-50`}
                      title={`${starValue} stars`}
                    >
                      {starValue % 1 === 0 ? '★' : '☆'}
                    </button>
                  ))}
                  <button
                    onClick={() => setShowRatingSelector(false)}
                    className="text-xs text-slate-500 ml-2 cursor-pointer"
                  >
                    Cancel
                  </button>
                </div>
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
              className="inline-flex items-center px-3 py-1.5 bg-orange-500/20 hover:bg-orange-500/30 text-orange-300 border border-orange-500/30 text-xs font-medium rounded-lg transition-colors"
            >
              SC
            </a>
          )}

          {isAuthenticated && (
            <div className="flex items-center gap-1">
              <button
                onClick={() => handleConfirm(true)}
                disabled={confirming}
                className={`px-2 py-1 text-xs font-medium rounded transition-colors cursor-pointer ${
                  isConfirmed
                    ? 'bg-green-500/30 text-green-300 border border-green-500/40'
                    : 'bg-surface-700 text-slate-400 hover:bg-green-500/20 hover:text-green-400 border border-white/5'
                } disabled:opacity-50`}
                title="Confirm this track is correct"
              >
                ✓
              </button>
              <button
                onClick={() => handleConfirm(false)}
                disabled={confirming}
                className={`px-2 py-1 text-xs font-medium rounded transition-colors cursor-pointer ${
                  isDenied
                    ? 'bg-red-500/30 text-red-300 border border-red-500/40'
                    : 'bg-surface-700 text-slate-400 hover:bg-red-500/20 hover:text-red-400 border border-white/5'
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
              className="ml-2 text-red-400 hover:text-red-300 text-sm font-medium px-2 py-1 rounded hover:bg-red-500/10 transition-colors cursor-pointer"
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
