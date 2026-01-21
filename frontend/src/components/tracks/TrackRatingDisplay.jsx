/**
 * Track Rating Display component.
 * 
 * Displays rating statistics and allows users to rate tracks.
 */

import { useState, useEffect } from 'react';
import * as trackRatingsService from '../../services/trackRatingsService';
import useAuthStore from '../../store/authStore';

const TrackRatingDisplay = ({ track, onRatingChange }) => {
  const { isAuthenticated, user } = useAuthStore();
  const [rating, setRating] = useState(track.user_rating || null);
  const [ratingStats, setRatingStats] = useState({
    average_rating: track.average_rating,
    total_ratings: track.rating_count || 0,
  });
  const [ratingLoading, setRatingLoading] = useState(false);

  const handleRatingClick = async (selectedRating) => {
    if (!isAuthenticated()) {
      alert('Please log in to rate tracks');
      return;
    }

    setRatingLoading(true);
    try {
      // Create or update rating (API handles upsert)
      await trackRatingsService.createTrackRating(track.id, selectedRating);
      setRating(selectedRating);
      
      // Reload stats
      if (onRatingChange) {
        await onRatingChange();
      }
    } catch (error) {
      console.error('Failed to rate track:', error);
      alert(error.response?.data?.detail || 'Failed to rate track');
    } finally {
      setRatingLoading(false);
    }
  };

  const renderStars = () => {
    const stars = [];
    for (let i = 0.5; i <= 5.0; i += 0.5) {
      const isHalf = i % 1 !== 0;
      const isFilled = rating && i <= rating;
      const isHalfFilled = isHalf && rating && Math.floor(rating) < i && rating >= i - 0.5;
      
      stars.push(
        <button
          key={i}
          onClick={() => handleRatingClick(i)}
          disabled={ratingLoading || !isAuthenticated()}
          className={`text-2xl transition-colors ${
            isFilled || isHalfFilled
              ? 'text-yellow-400'
              : 'text-gray-300 hover:text-yellow-200'
          } disabled:opacity-50 disabled:cursor-not-allowed`}
          title={`Rate ${i} stars`}
        >
          {isHalf ? '☆' : '★'}
        </button>
      );
    }
    return stars;
  };

  return (
    <div className="mb-6">
      <div className="flex items-center gap-4 mb-2">
        <div className="flex items-center gap-1">
          {isAuthenticated() ? (
            renderStars()
          ) : (
            <p className="text-gray-500 text-sm">Log in to rate this track</p>
          )}
        </div>
        
        {ratingStats.average_rating && (
          <div className="text-sm text-gray-600">
            <span className="font-semibold">{ratingStats.average_rating.toFixed(1)}</span>
            <span className="text-gray-500"> / 5.0</span>
            {ratingStats.total_ratings > 0 && (
              <span className="text-gray-500 ml-2">
                ({ratingStats.total_ratings} {ratingStats.total_ratings === 1 ? 'rating' : 'ratings'})
              </span>
            )}
          </div>
        )}
      </div>
      
      {rating && (
        <p className="text-sm text-gray-600">
          Your rating: {rating} stars
        </p>
      )}
    </div>
  );
};

export default TrackRatingDisplay;
