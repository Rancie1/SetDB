/**
 * Rating display component.
 * 
 * Shows rating stars and allows users to rate sets.
 */

import { useState, useEffect } from 'react';
import * as ratingsService from '../../services/ratingsService';
import useAuthStore from '../../store/authStore';

const RatingDisplay = ({ setId, ratingStats, userRating, onRatingChange }) => {
  const { isAuthenticated } = useAuthStore();
  const [hoveredRating, setHoveredRating] = useState(null);
  const [loading, setLoading] = useState(false);
  const [currentRating, setCurrentRating] = useState(userRating?.rating || null);

  useEffect(() => {
    setCurrentRating(userRating?.rating || null);
  }, [userRating]);

  const handleRatingClick = async (rating) => {
    if (!isAuthenticated) {
      window.location.href = '/login';
      return;
    }

    // If clicking the same rating, remove it
    if (currentRating === rating) {
      if (userRating?.id) {
        setLoading(true);
        try {
          await ratingsService.deleteRating(userRating.id);
          setCurrentRating(null);
          onRatingChange && onRatingChange(null);
        } catch (err) {
          console.error('Failed to delete rating:', err);
        } finally {
          setLoading(false);
        }
      }
      return;
    }

    setLoading(true);
    try {
      if (userRating?.id) {
        // Update existing rating
        await ratingsService.updateRating(userRating.id, { rating });
      } else {
        // Create new rating
        await ratingsService.createRating({ set_id: setId, rating });
      }
      setCurrentRating(rating);
      onRatingChange && onRatingChange(rating);
    } catch (err) {
      console.error('Failed to save rating:', err);
    } finally {
      setLoading(false);
    }
  };

  const renderStar = (value) => {
    const isHalf = value % 1 !== 0;
    const fullStars = Math.floor(value);
    const hasHalf = isHalf && fullStars < value;

    return (
      <div className="flex items-center">
        {Array.from({ length: fullStars }).map((_, i) => (
          <span key={i} className="text-yellow-400 text-2xl">★</span>
        ))}
        {hasHalf && <span className="text-yellow-400 text-2xl">☆</span>}
        {Array.from({ length: 5 - Math.ceil(value) }).map((_, i) => (
          <span key={i + fullStars + (hasHalf ? 1 : 0)} className="text-gray-300 text-2xl">★</span>
        ))}
      </div>
    );
  };

  const handleStarClick = (starNumber, isHalf) => {
    // Left side = half star, right side = full star
    const ratingValue = isHalf ? starNumber - 0.5 : starNumber;
    handleRatingClick(ratingValue);
  };

  const handleStarHover = (starNumber, isHalf) => {
    const ratingValue = isHalf ? starNumber - 0.5 : starNumber;
    setHoveredRating(ratingValue);
  };

  const getStarState = (starNumber, rating) => {
    if (!rating) {
      return { left: 'empty', right: 'empty' };
    }
    
    const fullStars = Math.floor(rating);
    const hasHalf = rating % 1 !== 0;
    
    if (starNumber <= fullStars) {
      return { left: 'full', right: 'full' };
    } else if (starNumber === fullStars + 1 && hasHalf) {
      return { left: 'half', right: 'empty' };
    } else {
      return { left: 'empty', right: 'empty' };
    }
  };

  const renderInteractiveStar = (starNumber) => {
    // Use hover state if hovering, otherwise use current state
    const displayRating = hoveredRating !== null ? hoveredRating : currentRating;
    const displayState = getStarState(starNumber, displayRating);
    const isFullyFilled = displayState?.left === 'full' && displayState?.right === 'full';
    
    return (
      <div className="relative inline-block" style={{ width: '2.5rem', height: '2.5rem', overflow: 'hidden' }}>
        {/* Background star (always show gray background) */}
        <div className="absolute inset-0 text-gray-300 text-4xl pointer-events-none flex items-center justify-center">
          ★
        </div>
        
        {/* Full star overlay for completely filled stars (renders on top, no gaps) */}
        {isFullyFilled && (
          <div className="absolute inset-0 text-yellow-400 text-4xl pointer-events-none flex items-center justify-center z-10">
            ★
          </div>
        )}
        
        {/* Yellow star overlay - positioned at full container level, then clipped */}
        {!isFullyFilled && (
          <>
            {/* Left half star */}
            {(displayState?.left === 'full' || displayState?.left === 'half') && (
              <div className="absolute inset-0 text-yellow-400 text-4xl pointer-events-none flex items-center justify-center z-10" style={{ 
                clipPath: 'polygon(0 0, 50% 0, 50% 100%, 0 100%)',
                WebkitClipPath: 'polygon(0 0, 50% 0, 50% 100%, 0 100%)'
              }}>
                ★
              </div>
            )}
            {/* Right half star */}
            {displayState?.right === 'full' && (
              <div className="absolute inset-0 text-yellow-400 text-4xl pointer-events-none flex items-center justify-center z-10" style={{ 
                clipPath: 'polygon(50% 0, 100% 0, 100% 100%, 50% 100%)',
                WebkitClipPath: 'polygon(50% 0, 100% 0, 100% 100%, 50% 100%)'
              }}>
                ★
              </div>
            )}
          </>
        )}
        
        {/* Left half button (half star) - only show if not fully filled */}
        {!isFullyFilled && (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              handleStarClick(starNumber, true);
            }}
            onMouseEnter={() => handleStarHover(starNumber, true)}
            disabled={loading}
            className={`absolute left-0 top-0 w-1/2 h-full z-20 ${
              loading ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'
            }`}
            title={`${starNumber - 0.5} stars`}
          />
        )}
        
        {/* Right half button (full star) - only show if not fully filled */}
        {!isFullyFilled && (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              handleStarClick(starNumber, false);
            }}
            onMouseEnter={() => handleStarHover(starNumber, false)}
            disabled={loading}
            className={`absolute right-0 top-0 w-1/2 h-full z-20 ${
              loading ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'
            }`}
            title={`${starNumber} stars`}
          />
        )}
        
        {/* Invisible clickable areas for fully filled stars */}
        {isFullyFilled && (
          <>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                handleStarClick(starNumber, true);
              }}
              onMouseEnter={() => handleStarHover(starNumber, true)}
              disabled={loading}
              className={`absolute left-0 top-0 w-1/2 h-full z-30 ${
                loading ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'
              }`}
              title={`${starNumber - 0.5} stars`}
            />
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                handleStarClick(starNumber, false);
              }}
              onMouseEnter={() => handleStarHover(starNumber, false)}
              disabled={loading}
              className={`absolute right-0 top-0 w-1/2 h-full z-30 ${
                loading ? 'cursor-not-allowed opacity-50' : 'cursor-pointer'
              }`}
              title={`${starNumber} stars`}
            />
          </>
        )}
      </div>
    );
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-6">
      <h3 className="text-lg font-semibold mb-4">Rate this Set</h3>

      {/* User Rating Section */}
      {isAuthenticated ? (
        <div className="mb-6">
          <p className="text-sm text-gray-600 mb-3">Your Rating:</p>
          <div 
            className="flex items-center space-x-1"
            onMouseLeave={() => setHoveredRating(null)}
          >
            {[1, 2, 3, 4, 5].map((starNumber) => renderInteractiveStar(starNumber))}
            {(currentRating || hoveredRating !== null) && (
              <span className={`ml-4 text-lg font-medium ${
                hoveredRating !== null ? 'text-gray-500' : 'text-gray-700'
              }`}>
                {(hoveredRating !== null ? hoveredRating : currentRating)?.toFixed(1)} / 5.0
              </span>
            )}
          </div>
          <p className="text-xs text-gray-500 mt-2">
            Click left side for half star, right side for full star
          </p>
        </div>
      ) : (
        <div className="mb-6 p-4 bg-gray-50 rounded-md">
          <p className="text-sm text-gray-600">
            <a href="/login" className="text-primary-600 hover:text-primary-700 font-medium">
              Log in
            </a>{' '}
            to rate this set
          </p>
        </div>
      )}

      {/* Rating Stats */}
      {ratingStats && ratingStats.total_ratings > 0 && (
        <div className="border-t border-gray-200 pt-4">
          <div className="flex items-center justify-between mb-3">
            <div>
              <p className="text-2xl font-bold">{ratingStats.average_rating?.toFixed(1)}</p>
              <p className="text-sm text-gray-600">
                {ratingStats.total_ratings} {ratingStats.total_ratings === 1 ? 'rating' : 'ratings'}
              </p>
            </div>
            {renderStar(ratingStats.average_rating)}
          </div>

          {/* Rating Distribution */}
          {ratingStats.rating_distribution && Object.keys(ratingStats.rating_distribution).length > 0 && (
            <div className="mt-4 space-y-2">
              {[5, 4.5, 4, 3.5, 3, 2.5, 2, 1.5, 1, 0.5].reverse().map((rating) => {
                const count = ratingStats.rating_distribution[rating] || 0;
                const percentage = (count / ratingStats.total_ratings) * 100;
                return (
                  <div key={rating} className="flex items-center space-x-2">
                    <span className="text-sm text-gray-600 w-8">{rating.toFixed(1)}</span>
                    <div className="flex-1 bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-yellow-400 h-2 rounded-full"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                    <span className="text-xs text-gray-500 w-8 text-right">{count}</span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {ratingStats && ratingStats.total_ratings === 0 && (
        <p className="text-sm text-gray-500">No ratings yet. Be the first to rate!</p>
      )}
    </div>
  );
};

export default RatingDisplay;
