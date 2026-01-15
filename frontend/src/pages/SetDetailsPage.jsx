/**
 * Set details page.
 * 
 * Displays comprehensive information about a DJ set including:
 * - Set metadata (title, DJ, thumbnail, description)
 * - Rating section
 * - Reviews section
 * - Link to source
 */

import { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import useSetsStore from '../store/setsStore';
import useAuthStore from '../store/authStore';
import * as reviewsService from '../services/reviewsService';
import * as ratingsService from '../services/ratingsService';
import * as setsService from '../services/setsService';
import * as eventsService from '../services/eventsService';
import ReviewCard from '../components/reviews/ReviewCard';
import ReviewForm from '../components/reviews/ReviewForm';
import RatingDisplay from '../components/reviews/RatingDisplay';
import CreateLiveEventForm from '../components/sets/CreateLiveEventForm';
import LinkToLiveEventForm from '../components/sets/LinkToLiveEventForm';

const SetDetailsPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { fetchSet, currentSet, loading, error } = useSetsStore();
  const { isAuthenticated, user } = useAuthStore();

  const [reviews, setReviews] = useState([]);
  const [reviewsLoading, setReviewsLoading] = useState(false);
  const [reviewsError, setReviewsError] = useState(null);
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [userReview, setUserReview] = useState(null);
  const [ratingStats, setRatingStats] = useState(null);
  const [userRating, setUserRating] = useState(null);
  const [ratingStatsLoading, setRatingStatsLoading] = useState(false);
  const [showCreateLiveEventForm, setShowCreateLiveEventForm] = useState(false);
  const [showLinkToLiveEventForm, setShowLinkToLiveEventForm] = useState(false);
  const [creatingLiveEvent, setCreatingLiveEvent] = useState(false);
  const [linkingToEvent, setLinkingToEvent] = useState(false);
  const [markingAsLive, setMarkingAsLive] = useState(false);

  useEffect(() => {
    if (id) {
      fetchSet(id);
    }
  }, [id]);

  useEffect(() => {
    // Live sets stay on sets page - events are separate entities now
    // Load reviews/ratings for all sets (including live sets)
    if (currentSet) {
      loadReviews();
      loadRatingStats();
      loadUserRating();
    }
  }, [currentSet, id, isAuthenticated]);


  const loadReviews = async () => {
    setReviewsLoading(true);
    setReviewsError(null);
    try {
      const response = await reviewsService.getSetReviews(id);
      setReviews(response.data.items || []);
      
      // Check if current user has a review
      if (isAuthenticated && user) {
        const myReview = response.data.items?.find(r => r.user_id === user.id);
        setUserReview(myReview || null);
      }
    } catch (err) {
      setReviewsError(err.response?.data?.detail || 'Failed to load reviews');
    } finally {
      setReviewsLoading(false);
    }
  };

  const loadRatingStats = async () => {
    setRatingStatsLoading(true);
    try {
      const response = await ratingsService.getSetRatingStats(id);
      setRatingStats(response.data);
    } catch (err) {
      console.error('Failed to load rating stats:', err);
    } finally {
      setRatingStatsLoading(false);
    }
  };

  const loadUserRating = async () => {
    if (!isAuthenticated) {
      setUserRating(null);
      return;
    }
    try {
      const response = await ratingsService.getMyRating(id);
      setUserRating(response.data);
    } catch (err) {
      // 404 means no rating yet, which is fine
      if (err.response?.status !== 404) {
        console.error('Failed to load user rating:', err);
      }
      setUserRating(null);
    }
  };

  const handleReviewSubmit = () => {
    setShowReviewForm(false);
    loadReviews();
  };

  const handleReviewDelete = async (reviewId) => {
    if (window.confirm('Are you sure you want to delete this review?')) {
      try {
        await reviewsService.deleteReview(reviewId);
        loadReviews();
      } catch (err) {
        console.error('Failed to delete review:', err);
        alert('Failed to delete review');
      }
    }
  };

  const handleRatingChange = () => {
    loadRatingStats();
    loadUserRating();
  };

  const handleCreateLiveEvent = async (eventData) => {
    if (!currentSet) return;
    
    setCreatingLiveEvent(true);
    try {
      const response = await eventsService.createEventFromSet(currentSet.id, eventData);
      
      // Navigate to the new event
      if (response.data) {
        navigate(`/events/${response.data.id}`);
      }
      
      setShowCreateLiveEventForm(false);
    } catch (err) {
      console.error('Failed to create live event:', err);
      alert(err.response?.data?.detail || 'Failed to create live event');
    } finally {
      setCreatingLiveEvent(false);
    }
  };

  const handleMarkAsLive = async () => {
    if (!confirm('Are you sure you want to mark this set as a live set? The original URL will be saved as the recording.')) {
      return;
    }
    
    setMarkingAsLive(true);
    try {
      await setsService.markSetAsLive(id);
      // Refresh the set data
      await fetchSet(id);
      alert('Set marked as live successfully!');
    } catch (err) {
      console.error('Failed to mark set as live:', err);
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to mark set as live';
      alert(`Error: ${errorMessage}\n\nPossible reasons:\n- Set is already a live set\n- Only YouTube and SoundCloud sets can be marked as live\n- Only the creator can mark sets as live`);
    } finally {
      setMarkingAsLive(false);
    }
  };

  const handleLinkToLiveEvent = async () => {
    if (!currentSet) return;
    
    setLinkingToEvent(true);
    try {
      // Refresh the current set to show it's now linked
      await fetchSet(id);
      setShowLinkToLiveEventForm(false);
    } catch (err) {
      console.error('Failed to link to live event:', err);
    } finally {
      setLinkingToEvent(false);
    }
  };


  const formatDuration = (minutes) => {
    if (!minutes) return null;
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours > 0) {
      return `${hours}h ${mins}m`;
    }
    return `${mins}m`;
  };

  const getPublishDate = (set) => {
    if (set.extra_metadata?.published_at) {
      return new Date(set.extra_metadata.published_at);
    }
    return set.created_at ? new Date(set.created_at) : null;
  };

  const getSourceIcon = (sourceType) => {
    switch (sourceType?.toLowerCase()) {
      case 'youtube':
        return '▶️';
      case 'soundcloud':
        return '🎵';
      case 'live':
        return '🎤';
      default:
        return '🎧';
    }
  };

  const getSourceColor = (sourceType) => {
    switch (sourceType?.toLowerCase()) {
      case 'youtube':
        return 'bg-red-100 text-red-800';
      case 'soundcloud':
        return 'bg-orange-100 text-orange-800';
      case 'live':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getSetTypeLabel = (set) => {
    if (set.source_type?.toLowerCase() === 'live') {
      return 'Live Set';
    }
    return 'Upload';
  };

  const getSetTypeColor = (set) => {
    if (set.source_type?.toLowerCase() === 'live') {
      return 'bg-purple-100 text-purple-800 border-purple-300';
    }
    return 'bg-gray-100 text-gray-800 border-gray-300';
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-3/4 mb-4"></div>
          <div className="h-64 bg-gray-200 rounded mb-6"></div>
          <div className="space-y-4">
            <div className="h-4 bg-gray-200 rounded w-full"></div>
            <div className="h-4 bg-gray-200 rounded w-5/6"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !currentSet) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
          {error || 'Set not found'}
        </div>
        <Link
          to="/discover"
          className="mt-4 inline-block text-primary-600 hover:text-primary-700"
        >
          ← Back to Discover
        </Link>
      </div>
    );
  }

  const publishDate = getPublishDate(currentSet);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Back Button */}
      <Link
        to="/discover"
        className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-6"
      >
        <span className="mr-2">←</span>
        Back to Discover
      </Link>

      {/* Hero Section */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden mb-8">
        <div className="md:flex">
          {/* Thumbnail */}
          <div className="md:w-1/3 lg:w-1/4">
            <div className="aspect-video md:aspect-square bg-gray-200 relative">
              {currentSet.thumbnail_url ? (
                <img
                  src={`${currentSet.thumbnail_url}${currentSet.thumbnail_url.includes('?') ? '&' : '?'}v=${new Date(currentSet.updated_at || currentSet.created_at).getTime()}`}
                  alt={currentSet.title}
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    const img = e.target;
                    const src = img.src.split('?')[0];
                    if (src.includes('-original.')) {
                      const fallbackUrl = src.replace('-original.', '-large.');
                      if (!img.dataset.fallbackTried) {
                        img.dataset.fallbackTried = 'true';
                        img.src = fallbackUrl;
                        return;
                      }
                    }
                    img.style.display = 'none';
                    if (!img.parentElement.querySelector('.thumbnail-placeholder')) {
                      const placeholder = document.createElement('div');
                      placeholder.className = 'thumbnail-placeholder w-full h-full flex items-center justify-center text-gray-400 absolute inset-0';
                      placeholder.innerHTML = '<span class="text-6xl">🎧</span>';
                      img.parentElement.appendChild(placeholder);
                    }
                  }}
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-gray-400">
                  <span className="text-6xl">🎧</span>
                </div>
              )}
              <div className="absolute top-4 right-4 flex flex-col gap-2 items-end">
                {/* Set type badge */}
                {/* Set type badge */}
                <span
                  className={`inline-flex items-center px-3 py-1 rounded-md text-sm font-medium border ${getSetTypeColor(currentSet)}`}
                >
                  {getSetTypeLabel(currentSet)}
                </span>
                {/* Source platform badge */}
                <span
                  className={`inline-flex items-center px-3 py-1 rounded-md text-sm font-medium ${getSourceColor(
                    currentSet.source_type
                  )}`}
                >
                  <span className="mr-1">{getSourceIcon(currentSet.source_type)}</span>
                  {currentSet.source_type || 'Unknown'}
                </span>
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="md:w-2/3 lg:w-3/4 p-6 md:p-8">
            <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-2">
              {currentSet.title}
            </h1>
            <p className="text-xl text-gray-600 mb-4">{currentSet.dj_name}</p>

            {/* Live set with recording indicator */}
            {currentSet.source_type?.toLowerCase() === 'live' && currentSet.recording_url && (
              <div className="mb-4 p-3 rounded-lg bg-purple-50 border border-purple-200">
                <p className="text-sm font-medium text-purple-800 mb-1">
                  🎵 Recording available
                </p>
                <a
                  href={currentSet.recording_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-purple-600 hover:text-purple-800 underline"
                >
                  Listen to recording →
                </a>
              </div>
            )}

            {/* Mark as Live and Create Live Event buttons for YouTube/SoundCloud sets */}
            {(() => {
              const sourceType = currentSet.source_type?.toLowerCase();
              const isImportedSet = sourceType !== 'live';
              const isYouTubeOrSoundCloud = sourceType === 'youtube' || sourceType === 'soundcloud';
              const isCreator = isAuthenticated && user?.id === currentSet.created_by_id;
              const canMarkAsLive = isYouTubeOrSoundCloud && isAuthenticated && isCreator;
              
              // Show helpful message if user is creator but set can't be marked as live
              if (isAuthenticated && isCreator && !isYouTubeOrSoundCloud && isImportedSet) {
                return (
                  <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-md">
                    <p className="text-sm text-yellow-800">
                      <strong>Cannot mark as live:</strong> Only YouTube and SoundCloud sets can be converted to live sets.
                      <br />
                      Current set type: <strong>{currentSet.source_type || 'unknown'}</strong>
                    </p>
                  </div>
                );
              }
              
              // Show message if user is not the creator
              if (isAuthenticated && !isCreator && isYouTubeOrSoundCloud) {
                return (
                  <div className="mb-6 p-4 bg-gray-50 border border-gray-200 rounded-md">
                    <p className="text-sm text-gray-600">
                      Only the creator of this set can mark it as live.
                    </p>
                  </div>
                );
              }
              
              if (!canMarkAsLive) return null;
              
              return (
                <div className="mb-6 space-y-3">
                  {/* Mark as Live button */}
                  <div>
                    <button
                      onClick={handleMarkAsLive}
                      disabled={markingAsLive}
                      className="inline-flex items-center px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {markingAsLive ? 'Marking as Live...' : '🎤 Mark as Live Set'}
                    </button>
                    <p className="text-sm text-gray-600 mt-2">
                      Convert this set to a live set. The original URL will be saved as the recording.
                    </p>
                  </div>
                  
                  {/* Divider */}
                  <div className="border-t border-gray-200 my-4"></div>
                  
                  {/* Create Live Event button */}
                  {!showCreateLiveEventForm ? (
                    <div>
                      <button
                        onClick={() => setShowCreateLiveEventForm(true)}
                        className="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-md transition-colors"
                      >
                        🎪 Create Separate Live Event
                      </button>
                      <p className="text-sm text-gray-600 mt-2">
                        Create a new live event (separate from this set) that you can link sets to.
                      </p>
                    </div>
                  ) : (
                    <CreateLiveEventForm
                      set={currentSet}
                      onSubmit={handleCreateLiveEvent}
                      onCancel={() => setShowCreateLiveEventForm(false)}
                      loading={creatingLiveEvent}
                    />
                  )}
                </div>
              );
            })()}

            {/* Metadata */}
            <div className="flex flex-wrap items-center gap-4 mb-6 text-sm text-gray-600">
              {formatDuration(currentSet.duration_minutes) && (
                <span className="flex items-center">
                  <span className="mr-1">⏱</span>
                  {formatDuration(currentSet.duration_minutes)}
                </span>
              )}
              {publishDate && (
                <span className="flex items-center">
                  <span className="mr-1">📅</span>
                  {publishDate.toLocaleDateString('en-US', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                  })}
                </span>
              )}
              {currentSet.event_name && (
                <span className="flex items-center">
                  <span className="mr-1">🎪</span>
                  {currentSet.event_name}
                </span>
              )}
              {currentSet.venue_location && (
                <span className="flex items-center">
                  <span className="mr-1">📍</span>
                  {currentSet.venue_location}
                </span>
              )}
            </div>

            {/* Description */}
            {currentSet.description && (
              <div className="mb-6">
                <p className="text-gray-700 whitespace-pre-wrap">{currentSet.description}</p>
              </div>
            )}

            {/* Actions */}
            <div className="flex flex-wrap items-center gap-3">
              {/* Show "Listen" button for YouTube/SoundCloud sets with valid URLs */}
              {currentSet.source_url && 
               (currentSet.source_url.startsWith('http://') || currentSet.source_url.startsWith('https://')) && (
                <a
                  href={currentSet.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-md"
                >
                  <span className="mr-2">
                    {currentSet.source_type?.toLowerCase() === 'youtube' ? '▶️' : '🎵'}
                  </span>
                  Listen on {currentSet.source_type === 'youtube' ? 'YouTube' : 'SoundCloud'}
                </a>
              )}
              
              {isAuthenticated && (
                <button
                  onClick={() => setShowReviewForm(!showReviewForm)}
                  className="inline-flex items-center px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium rounded-md"
                >
                  {userReview ? 'Edit Review' : 'Write Review'}
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-8">
          {/* Rating Section */}
          <RatingDisplay
            setId={id}
            ratingStats={ratingStats}
            userRating={userRating}
            onRatingChange={handleRatingChange}
          />


          {/* Review Form */}
          {showReviewForm && (
            <ReviewForm
              setId={id}
              existingReview={userReview}
              onSubmit={handleReviewSubmit}
              onCancel={() => setShowReviewForm(false)}
            />
          )}

          {/* Reviews Section */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-bold">Reviews</h2>
              {reviews.length > 0 && (
                <span className="text-sm text-gray-600">{reviews.length} reviews</span>
              )}
            </div>

            {reviewsLoading ? (
              <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="bg-gray-100 animate-pulse rounded-lg h-32"></div>
                ))}
              </div>
            ) : reviewsError ? (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
                {reviewsError}
              </div>
            ) : reviews.length === 0 ? (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
                <p className="text-gray-600 mb-2">No reviews yet</p>
                <p className="text-sm text-gray-500">
                  {isAuthenticated
                    ? 'Be the first to write a review!'
                    : 'Log in to write the first review'}
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {reviews.map((review) => (
                  <ReviewCard
                    key={review.id}
                    review={review}
                    onDelete={handleReviewDelete}
                  />
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Additional Info */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold mb-4">Details</h3>
            <dl className="space-y-3 text-sm">
              <div>
                <dt className="text-gray-500">Source</dt>
                <dd className="font-medium text-gray-900 capitalize">
                  {currentSet.source_type || 'Unknown'}
                </dd>
              </div>
              {currentSet.source_id && (
                <div>
                  <dt className="text-gray-500">Source ID</dt>
                  <dd className="font-medium text-gray-900 font-mono text-xs">
                    {currentSet.source_id}
                  </dd>
                </div>
              )}
              <div>
                <dt className="text-gray-500">Added</dt>
                <dd className="font-medium text-gray-900">
                  {new Date(currentSet.created_at).toLocaleDateString()}
                </dd>
              </div>
            </dl>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SetDetailsPage;
