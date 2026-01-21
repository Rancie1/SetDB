/**
 * Track details page.
 * 
 * Displays comprehensive information about a track including:
 * - Track metadata (name, artist, SoundCloud link, thumbnail)
 * - Rating section
 * - Reviews section
 * - Linked sets
 * - Top track management
 * - Link to sets functionality
 */

import { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import useAuthStore from '../store/authStore';
import * as standaloneTracksService from '../services/standaloneTracksService';
import * as trackRatingsService from '../services/trackRatingsService';
import * as trackReviewsService from '../services/trackReviewsService';
import * as setsService from '../services/setsService';
import * as tracksService from '../services/tracksService';
import ReviewCard from '../components/reviews/ReviewCard';
import ReviewForm from '../components/reviews/ReviewForm';
import RatingDisplay from '../components/reviews/RatingDisplay';
import SetCard from '../components/sets/SetCard';

const TrackDetailsPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { isAuthenticated, user } = useAuthStore();

  const [track, setTrack] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [reviewsLoading, setReviewsLoading] = useState(false);
  const [showReviewForm, setShowReviewForm] = useState(false);
  const [userReview, setUserReview] = useState(null);
  const [ratingStats, setRatingStats] = useState(null);
  const [userRating, setUserRating] = useState(null);
  const [linkedSets, setLinkedSets] = useState([]);
  const [linkedSetsLoading, setLinkedSetsLoading] = useState(false);
  const [showLinkForm, setShowLinkForm] = useState(false);
  const [linkingSet, setLinkingSet] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [selectedSetId, setSelectedSetId] = useState(null);
  const [timestampInput, setTimestampInput] = useState('');
  const [settingTopTrack, setSettingTopTrack] = useState(false);
  const [showTopTrackSelector, setShowTopTrackSelector] = useState(false);
  const [hoveredRating, setHoveredRating] = useState(null);

  useEffect(() => {
    if (id) {
      loadTrack();
      loadReviews();
      loadRatingStats();
      loadUserRating();
      loadLinkedSets();
    }
  }, [id, isAuthenticated]);

  const loadTrack = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await standaloneTracksService.getTrack(id);
      setTrack(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load track');
    } finally {
      setLoading(false);
    }
  };

  const loadReviews = async () => {
    setReviewsLoading(true);
    try {
      const response = await trackReviewsService.getTrackReviews(id, 1, 20);
      setReviews(response.data.items || []);
      
      // Find user's review
      if (isAuthenticated && user) {
        const userRev = response.data.items?.find(r => r.user_id === user.id);
        setUserReview(userRev || null);
      }
    } catch (err) {
      console.error('Failed to load reviews:', err);
      setReviews([]);
    } finally {
      setReviewsLoading(false);
    }
  };

  const loadRatingStats = async () => {
    try {
      const response = await trackRatingsService.getTrackRatingStats(id);
      setRatingStats(response.data);
    } catch (err) {
      console.error('Failed to load rating stats:', err);
    }
  };

  const loadUserRating = async () => {
    if (!isAuthenticated || !track) return;
    
    try {
      // User rating is included in track response
      if (track.user_rating) {
        setUserRating({ rating: track.user_rating });
      } else {
        setUserRating(null);
      }
    } catch (err) {
      console.error('Failed to load user rating:', err);
    }
  };
  
  useEffect(() => {
    if (track) {
      loadUserRating();
    }
  }, [track, isAuthenticated]);

  const loadLinkedSets = async () => {
    setLinkedSetsLoading(true);
    try {
      const response = await standaloneTracksService.getTrackLinkedSets(id);
      setLinkedSets(response.data || []);
    } catch (err) {
      console.error('Failed to load linked sets:', err);
      setLinkedSets([]);
    } finally {
      setLinkedSetsLoading(false);
    }
  };

  const handleRatingChange = () => {
    loadRatingStats();
    loadUserRating();
    loadTrack(); // Refresh track to get updated user rating
  };

  const handleReviewSubmit = () => {
    setShowReviewForm(false);
    loadReviews();
  };

  const handleReviewDelete = async (reviewId) => {
    if (window.confirm('Are you sure you want to delete this review?')) {
      try {
        await trackReviewsService.deleteTrackReview(id, reviewId);
        loadReviews();
      } catch (err) {
        console.error('Failed to delete review:', err);
        alert('Failed to delete review');
      }
    }
  };

  const searchSets = async () => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }
    
    setSearching(true);
    try {
      const response = await setsService.getSets({ search: searchQuery }, 1, 10);
      setSearchResults(response.data.items || []);
    } catch (err) {
      console.error('Failed to search sets:', err);
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  };

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      searchSets();
    }, 300);
    return () => clearTimeout(timeoutId);
  }, [searchQuery]);

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

  const handleLinkSet = async () => {
    if (!track || !selectedSetId) return;
    
    // Parse timestamp from MM:SS format to decimal minutes
    const timestampMinutes = timestampInput ? parseTimestamp(timestampInput) : null;
    
    if (timestampInput && timestampMinutes === null) {
      alert('Invalid timestamp format. Please use MM:SS format (e.g., 2:30)');
      return;
    }
    
    setLinkingSet(true);
    try {
      // Use the same endpoint as track tagging
      await tracksService.addTrackTag(selectedSetId, {
        track_id: track.id,
        timestamp_minutes: timestampMinutes,
      });
      await loadLinkedSets();
      setShowLinkForm(false);
      setSearchQuery('');
      setSearchResults([]);
      setSelectedSetId(null);
      setTimestampInput('');
    } catch (err) {
      console.error('Failed to link set:', err);
      alert(err.response?.data?.detail || 'Failed to link set to track');
    } finally {
      setLinkingSet(false);
    }
  };

  const handleUnlinkSet = async (setId) => {
    if (!window.confirm('Unlink this set from the track?')) return;
    
    try {
      await standaloneTracksService.unlinkTrackFromSet(track.id, setId);
      await loadLinkedSets();
    } catch (err) {
      console.error('Failed to unlink set:', err);
      alert(err.response?.data?.detail || 'Failed to unlink set');
    }
  };

  const handleSetTopTrack = async (order) => {
    if (!track) return;
    
    setSettingTopTrack(true);
    try {
      await standaloneTracksService.setTopTrack(track.id, order);
      await loadTrack();
      setShowTopTrackSelector(false);
    } catch (err) {
      console.error('Failed to set top track:', err);
      alert(err.response?.data?.detail || 'Failed to set top track');
    } finally {
      setSettingTopTrack(false);
    }
  };

  const handleUnsetTopTrack = async () => {
    if (!track) return;
    
    if (!window.confirm('Remove this track from your top tracks?')) return;
    
    try {
      await standaloneTracksService.unsetTopTrack(track.id);
      await loadTrack();
    } catch (err) {
      console.error('Failed to unset top track:', err);
      alert(err.response?.data?.detail || 'Failed to remove from top tracks');
    }
  };

  const formatDuration = (ms) => {
    if (!ms) return null;
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="animate-pulse">
          <div className="h-64 bg-gray-200 rounded-lg mb-6"></div>
          <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
        </div>
      </div>
    );
  }

  if (error || !track) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Track Not Found</h2>
          <p className="text-gray-600">{error || 'The track you\'re looking for doesn\'t exist.'}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Track Header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 mb-6">
        <div className="flex flex-col md:flex-row gap-6 p-6">
          {/* Thumbnail */}
          {track.thumbnail_url && (
            <div className="flex-shrink-0">
              <img
                src={track.thumbnail_url}
                alt={track.track_name}
                className="w-48 h-48 rounded-lg object-cover"
              />
            </div>
          )}
          
          {/* Track Info */}
          <div className="flex-1">
            <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-2">
              {track.track_name}
            </h1>
            {track.artist_name && (
              <p className="text-xl text-gray-600 mb-4">{track.artist_name}</p>
            )}
            
            <div className="flex flex-wrap items-center gap-4 mb-4">
              {track.duration_ms && (
                <span className="text-sm text-gray-600">⏱️ {formatDuration(track.duration_ms)}</span>
              )}
              {track.soundcloud_url && (
                <a
                  href={track.soundcloud_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center px-4 py-2 bg-orange-600 hover:bg-orange-700 text-white font-medium rounded-md transition-colors"
                >
                  🎵 SoundCloud
                </a>
              )}
              {track.spotify_url && (
                <a
                  href={track.spotify_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center px-4 py-2 bg-green-600 hover:bg-green-700 text-white font-medium rounded-md transition-colors"
                >
                  🎵 Spotify
                </a>
              )}
            </div>

            {/* Top Track Management */}
            {isAuthenticated && (
              <div className="mt-4">
                {track.is_top_track ? (
                  <div className="flex items-center gap-2">
                    <span className="px-3 py-1 bg-primary-600 text-white text-sm font-medium rounded-md">
                      Top Track #{track.top_track_order}
                    </span>
                    <button
                      onClick={() => setShowTopTrackSelector(true)}
                      disabled={settingTopTrack}
                      className="px-3 py-1 bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm font-medium rounded-md disabled:opacity-50"
                    >
                      Change Position
                    </button>
                    <button
                      onClick={handleUnsetTopTrack}
                      disabled={settingTopTrack}
                      className="px-3 py-1 bg-red-100 hover:bg-red-200 text-red-700 text-sm font-medium rounded-md disabled:opacity-50"
                    >
                      Remove from Top
                    </button>
                  </div>
                ) : (
                  <button
                    onClick={() => setShowTopTrackSelector(true)}
                    className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-md"
                  >
                    Add to Top Tracks
                  </button>
                )}
                
                {showTopTrackSelector && (
                  <div className="mt-2 p-3 bg-gray-50 rounded-md">
                    <p className="text-sm text-gray-700 mb-2">Select position (1-5):</p>
                    <div className="flex gap-2">
                      {[1, 2, 3, 4, 5].map((order) => (
                        <button
                          key={order}
                          onClick={() => handleSetTopTrack(order)}
                          disabled={settingTopTrack}
                          className={`px-3 py-1 rounded-md text-sm font-medium ${
                            track.is_top_track && track.top_track_order === order
                              ? 'bg-primary-600 text-white'
                              : 'bg-white border border-gray-300 hover:bg-gray-50'
                          } disabled:opacity-50`}
                        >
                          #{order}
                        </button>
                      ))}
                      <button
                        onClick={() => setShowTopTrackSelector(false)}
                        className="px-3 py-1 bg-gray-200 hover:bg-gray-300 text-gray-700 text-sm font-medium rounded-md"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-8">
          {/* Rating Section - Custom for tracks */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold mb-4">Rate this Track</h3>
            {/* We'll create a track-specific rating component, but for now use a simple version */}
            {isAuthenticated ? (
              <div>
                <p className="text-sm text-gray-600 mb-3">Your Rating:</p>
                <div className="flex items-center space-x-1" onMouseLeave={() => setHoveredRating(null)}>
                  {[1, 2, 3, 4, 5].map((star) => {
                    const displayRating = hoveredRating !== null ? hoveredRating : (userRating?.rating || 0);
                    const isFilled = star <= displayRating;
                    return (
                      <div key={star} className="relative inline-block" style={{ width: '2.5rem', height: '2.5rem' }}>
                        <button
                          onClick={async (e) => {
                            e.stopPropagation();
                            const rating = star;
                            try {
                              await trackRatingsService.createTrackRating(id, rating);
                              handleRatingChange();
                            } catch (err) {
                              console.error('Failed to rate track:', err);
                              alert(err.response?.data?.detail || 'Failed to rate track');
                            }
                          }}
                          onMouseEnter={() => setHoveredRating(star)}
                          className="absolute inset-0 z-20"
                          title={`${star} stars`}
                        />
                        <div className="absolute inset-0 text-gray-300 text-4xl pointer-events-none flex items-center justify-center">
                          ★
                        </div>
                        {isFilled && (
                          <div className="absolute inset-0 text-yellow-400 text-4xl pointer-events-none flex items-center justify-center z-10">
                            ★
                          </div>
                        )}
                      </div>
                    );
                  })}
                  {(userRating || hoveredRating !== null) && (
                    <span className="ml-4 text-lg font-medium text-gray-700">
                      {(hoveredRating !== null ? hoveredRating : userRating?.rating || 0).toFixed(1)} / 5.0
                    </span>
                  )}
                </div>
              </div>
            ) : (
              <p className="text-sm text-gray-600">
                <a href="/login" className="text-primary-600 hover:text-primary-700 font-medium">
                  Log in
                </a>{' '}
                to rate this track
              </p>
            )}
            
            {ratingStats && ratingStats.total_ratings > 0 && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <p className="text-2xl font-bold">{ratingStats.average_rating?.toFixed(1)}</p>
                <p className="text-sm text-gray-600">
                  {ratingStats.total_ratings} {ratingStats.total_ratings === 1 ? 'rating' : 'ratings'}
                </p>
              </div>
            )}
          </div>

          {/* Review Form - Custom for tracks */}
          {showReviewForm && (
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-semibold mb-4">
                {userReview ? 'Edit Review' : 'Write a Review'}
              </h3>
              <form onSubmit={async (e) => {
                e.preventDefault();
                const formData = new FormData(e.target);
                const content = formData.get('content');
                const containsSpoilers = formData.get('contains_spoilers') === 'on';
                const isPublic = formData.get('is_public') !== 'off';
                
                try {
                  if (userReview) {
                    await trackReviewsService.updateTrackReview(id, userReview.id, {
                      content,
                      contains_spoilers: containsSpoilers,
                      is_public: isPublic,
                    });
                  } else {
                    await trackReviewsService.createTrackReview(id, {
                      content,
                      contains_spoilers: containsSpoilers,
                      is_public: isPublic,
                    });
                  }
                  handleReviewSubmit();
                } catch (err) {
                  console.error('Failed to save review:', err);
                  alert(err.response?.data?.detail || 'Failed to save review');
                }
              }}>
                <textarea
                  name="content"
                  defaultValue={userReview?.content || ''}
                  placeholder="Share your thoughts about this track..."
                  rows={6}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500 mb-4"
                  required
                />
                <div className="flex items-center space-x-6 mb-4">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      name="contains_spoilers"
                      defaultChecked={userReview?.contains_spoilers || false}
                      className="mr-2"
                    />
                    <span className="text-sm text-gray-700">Contains spoilers</span>
                  </label>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      name="is_public"
                      defaultChecked={userReview?.is_public ?? true}
                      className="mr-2"
                    />
                    <span className="text-sm text-gray-700">Public review</span>
                  </label>
                </div>
                <div className="flex items-center space-x-3">
                  <button
                    type="submit"
                    className="bg-primary-600 hover:bg-primary-700 text-white font-medium px-6 py-2 rounded-md"
                  >
                    {userReview ? 'Update Review' : 'Post Review'}
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowReviewForm(false)}
                    className="bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium px-6 py-2 rounded-md"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* Reviews Section */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-bold">Reviews</h2>
              {isAuthenticated && (
                <button
                  onClick={() => setShowReviewForm(!showReviewForm)}
                  className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium rounded-md"
                >
                  {userReview ? 'Edit Review' : 'Write Review'}
                </button>
              )}
            </div>

            {reviewsLoading ? (
              <div className="space-y-4">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="bg-gray-100 animate-pulse rounded-lg h-32"></div>
                ))}
              </div>
            ) : reviews.length === 0 ? (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
                <p className="text-gray-600 mb-2">No reviews yet</p>
                <p className="text-gray-400 text-sm">
                  {isAuthenticated
                    ? 'Be the first to review this track'
                    : 'Log in to write a review'}
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

          {/* Linked Sets Section */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-bold">Linked Sets</h2>
              {isAuthenticated && (
                <button
                  onClick={() => setShowLinkForm(!showLinkForm)}
                  className="px-4 py-2 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-md text-sm"
                >
                  {showLinkForm ? 'Cancel' : '+ Link to Set'}
                </button>
              )}
            </div>

            {showLinkForm && (
              <div className="bg-white rounded-lg border border-gray-200 p-4 mb-4">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Search for sets..."
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500 mb-2"
                />
                
                {searching && (
                  <p className="text-sm text-gray-500">Searching...</p>
                )}
                
                {searchResults.length > 0 && (
                  <div className="border border-gray-200 rounded-md max-h-60 overflow-y-auto mb-2">
                    {searchResults.map((set) => (
                      <div
                        key={set.id}
                        onClick={() => setSelectedSetId(set.id)}
                        className={`p-3 border-b border-gray-200 last:border-b-0 cursor-pointer hover:bg-primary-50 ${
                          selectedSetId === set.id ? 'bg-primary-100' : ''
                        }`}
                      >
                        <div className="font-medium text-gray-900">{set.title}</div>
                        <div className="text-sm text-gray-600">{set.dj_name}</div>
                      </div>
                    ))}
                  </div>
                )}

                {selectedSetId && (() => {
                  const selectedSet = searchResults.find(s => s.id === selectedSetId);
                  const hasRecording = selectedSet?.recording_url;
                  return hasRecording && (
                    <div className="mb-2">
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Timestamp (MM:SS)
                      </label>
                      <input
                        type="text"
                        value={timestampInput}
                        onChange={(e) => setTimestampInput(e.target.value)}
                        pattern="[0-9]+:[0-5][0-9]"
                        placeholder="e.g., 2:30"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                      />
                      <p className="text-xs text-gray-500 mt-1">When in the recording this track starts (optional, format: MM:SS)</p>
                    </div>
                  );
                })()}

                <button
                  onClick={handleLinkSet}
                  disabled={!selectedSetId || linkingSet}
                  className="w-full px-4 py-2 bg-primary-600 hover:bg-primary-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-medium rounded-md"
                >
                  {linkingSet ? 'Linking...' : 'Link Selected Set'}
                </button>
              </div>
            )}

            {linkedSetsLoading ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {[1, 2].map((i) => (
                  <div key={i} className="bg-gray-100 animate-pulse rounded-lg h-48"></div>
                ))}
              </div>
            ) : linkedSets.length === 0 ? (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
                <p className="text-gray-600 mb-2">No sets linked yet</p>
                <p className="text-gray-400 text-sm">
                  {isAuthenticated
                    ? 'Link this track to sets where it was played'
                    : 'Log in to link tracks to sets'}
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {linkedSets.map((set) => (
                  <div key={set.id} className="relative">
                    <SetCard set={set} />
                    {isAuthenticated && (
                      <button
                        onClick={() => handleUnlinkSet(set.id)}
                        className="absolute top-2 right-2 px-2 py-1 bg-red-600 hover:bg-red-700 text-white text-xs font-medium rounded-md"
                      >
                        Unlink
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Track Stats */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold mb-4">Track Info</h3>
            <dl className="space-y-3 text-sm">
              {track.artist_name && (
                <div>
                  <dt className="text-gray-500">Artist</dt>
                  <dd className="font-medium text-gray-900">{track.artist_name}</dd>
                </div>
              )}
              {track.duration_ms && (
                <div>
                  <dt className="text-gray-500">Duration</dt>
                  <dd className="font-medium text-gray-900">{formatDuration(track.duration_ms)}</dd>
                </div>
              )}
              {track.average_rating && (
                <div>
                  <dt className="text-gray-500">Average Rating</dt>
                  <dd className="font-medium text-gray-900">
                    ⭐ {track.average_rating.toFixed(1)} / 5.0
                    {track.rating_count > 0 && (
                      <span className="text-gray-500 ml-2">
                        ({track.rating_count} {track.rating_count === 1 ? 'rating' : 'ratings'})
                      </span>
                    )}
                  </dd>
                </div>
              )}
              <div>
                <dt className="text-gray-500">Linked Sets</dt>
                <dd className="font-medium text-gray-900">{track.linked_sets_count || 0}</dd>
              </div>
              <div>
                <dt className="text-gray-500">Added</dt>
                <dd className="font-medium text-gray-900">
                  {new Date(track.created_at).toLocaleDateString()}
                </dd>
              </div>
            </dl>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TrackDetailsPage;
