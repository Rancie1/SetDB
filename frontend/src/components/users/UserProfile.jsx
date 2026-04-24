/**
 * User profile component.
 * 
 * Displays user information, stats, and tabs for different sections.
 */

import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import useAuthStore from '../../store/authStore';
import * as usersService from '../../services/usersService';
import * as logsService from '../../services/logsService';
import * as eventsService from '../../services/eventsService';
import * as reviewsService from '../../services/reviewsService';
import UserStats from './UserStats';
import SetCard from '../sets/SetCard';
import TopSets from './TopSets';
import TopTracks from './TopTracks';
import TopEvents from './TopEvents';

const UserProfile = () => {
  const { id } = useParams();
  const { user: currentUser } = useAuthStore();
  const [user, setUser] = useState(null);
  const [stats, setStats] = useState(null);
  const [activeTab, setActiveTab] = useState('listened');
  const [loading, setLoading] = useState(true);
  const [isFollowing, setIsFollowing] = useState(false);
  const [followingLoading, setFollowingLoading] = useState(false);
  
  // Listened sets (all)
  const [listenedSets, setListenedSets] = useState([]);
  const [listenedSetsLoading, setListenedSetsLoading] = useState(false);
  const [listenedSetsPage, setListenedSetsPage] = useState(1);
  const [listenedSetsTotal, setListenedSetsTotal] = useState(0);
  
  // Events attended
  const [eventsAttended, setEventsAttended] = useState([]);
  const [eventsLoading, setEventsLoading] = useState(false);
  const [eventsPage, setEventsPage] = useState(1);
  const [eventsTotal, setEventsTotal] = useState(0);

  // Reviews
  const [userReviews, setUserReviews] = useState([]);
  const [reviewsLoading, setReviewsLoading] = useState(false);
  const [reviewsTotal, setReviewsTotal] = useState(0);

  // Top sets
  const [topSets, setTopSets] = useState([]);
  const [topSetsLoading, setTopSetsLoading] = useState(false);

  const isOwnProfile = currentUser && String(currentUser.id) === id;

  useEffect(() => {
    loadUserData();
    loadTopSets();
    if (!isOwnProfile && currentUser) {
      checkFollowingStatus();
    }
  }, [id, currentUser]);

  useEffect(() => {
    if (activeTab === 'listened' && id) {
      loadListenedSets();
    } else if (activeTab === 'events' && id) {
      loadEventsAttended();
    } else if (activeTab === 'reviews' && id) {
      loadUserReviews();
    }
  }, [activeTab, id]);

  const checkFollowingStatus = async () => {
    if (!currentUser || isOwnProfile) return;
    
    try {
      const response = await usersService.getFollowStatus(id);
      setIsFollowing(response.data.is_following || false);
    } catch (error) {
      console.error('Failed to check following status:', error);
      setIsFollowing(false);
    }
  };

  const loadUserData = async () => {
    setLoading(true);
    try {
      const [userResponse, statsResponse] = await Promise.all([
        usersService.getUser(id),
        usersService.getUserStats(id),
      ]);
      setUser(userResponse.data);
      setStats(statsResponse.data);
    } catch (error) {
      console.error('Failed to load user data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadTopSets = async () => {
    setTopSetsLoading(true);
    try {
      const response = await logsService.getUserTopSets(id);
      setTopSets(response.data || []);
    } catch (error) {
      console.error('Failed to load top sets:', error);
      setTopSets([]);
    } finally {
      setTopSetsLoading(false);
    }
  };

  const handleFollow = async () => {
    if (isOwnProfile) return;
    
    setFollowingLoading(true);
    try {
      if (isFollowing) {
        await usersService.unfollowUser(id);
        setIsFollowing(false);
      } else {
        await usersService.followUser(id);
        setIsFollowing(true);
      }
      // Reload stats to update follower count
      const statsResponse = await usersService.getUserStats(id);
      setStats(statsResponse.data);
    } catch (error) {
      console.error('Failed to follow/unfollow:', error);
      alert(error.response?.data?.detail || 'Failed to follow/unfollow user');
    } finally {
      setFollowingLoading(false);
    }
  };

  const loadListenedSets = async (page = 1) => {
    setListenedSetsLoading(true);
    try {
      const response = await logsService.getUserLogs(id, page, 20);
      const logs = response.data.items || [];
      const sets = logs.map(log => log.set).filter(Boolean);
      setListenedSets(sets);
      setListenedSetsPage(page);
      setListenedSetsTotal(response.data.total || 0);
    } catch (error) {
      console.error('Failed to load listened sets:', error);
      setListenedSets([]);
    } finally {
      setListenedSetsLoading(false);
    }
  };

  const loadEventsAttended = async (page = 1) => {
    setEventsLoading(true);
    try {
      const response = await eventsService.getUserConfirmedEvents(id, page, 20);
      setEventsAttended(response.data.items || []);
      setEventsPage(page);
      setEventsTotal(response.data.total || 0);
    } catch (error) {
      console.error('Failed to load events attended:', error);
      setEventsAttended([]);
    } finally {
      setEventsLoading(false);
    }
  };

  const loadUserReviews = async (page = 1) => {
    setReviewsLoading(true);
    try {
      const response = await reviewsService.getUserReviews(id, page, 20);
      setUserReviews(response.data.items || []);
      setReviewsTotal(response.data.total || 0);
    } catch (error) {
      console.error('Failed to load reviews:', error);
      setUserReviews([]);
    } finally {
      setReviewsLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="animate-pulse">
          <div className="h-32 bg-surface-700 rounded-xl mb-6"></div>
          <div className="h-8 bg-surface-700 rounded w-1/4 mb-4"></div>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-slate-100 mb-2">User Not Found</h2>
          <p className="text-slate-400">The user you're looking for doesn't exist.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Profile Header */}
      <div className="bg-surface-800 rounded-xl border border-white/5 p-6 mb-6">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            {/* Avatar */}
            <div className="w-20 h-20 bg-primary-600/20 rounded-full flex items-center justify-center text-2xl font-bold text-primary-400">
              {user.username?.[0]?.toUpperCase() || 'U'}
            </div>

            {/* User Info */}
            <div>
              <h1 className="text-2xl font-bold text-slate-100">
                {user.display_name || user.username}
              </h1>
              <p className="text-slate-400 text-sm">@{user.username}</p>
              {user.bio && (
                <p className="text-slate-300 mt-2 text-sm">{user.bio}</p>
              )}
              <p className="text-xs text-slate-500 mt-2">
                Joined {new Date(user.created_at).toLocaleDateString()}
              </p>
            </div>
          </div>

          {/* Follow/Edit Button */}
          {!isOwnProfile && (
            <button
              onClick={handleFollow}
              disabled={followingLoading}
              className={`px-5 py-2 rounded-lg text-sm font-medium transition-colors cursor-pointer disabled:opacity-50 ${
                isFollowing
                  ? 'bg-white/5 hover:bg-white/10 text-slate-300'
                  : 'bg-primary-600 hover:bg-primary-500 text-white'
              }`}
            >
              {followingLoading ? '...' : isFollowing ? 'Friends' : 'Add Friend'}
            </button>
          )}
          {isOwnProfile && (
            <div className="flex gap-2">
              <Link
                to="/friends"
                className="px-5 py-2 bg-primary-600 hover:bg-primary-500 text-white rounded-lg text-sm font-medium transition-colors"
              >
                Friends
              </Link>
              <Link
                to="/profile/manage"
                className="px-5 py-2 bg-white/5 hover:bg-white/10 text-slate-300 rounded-lg text-sm font-medium transition-colors"
              >
                Manage Profile
              </Link>
            </div>
          )}
        </div>
      </div>

      {/* Top Sets */}
      {(topSets.length > 0 || isOwnProfile) && (
        <div className="mb-6">
          <h2 className="text-xl font-semibold mb-4">Top 5 Sets</h2>
          <TopSets 
            topSets={topSets} 
            loading={topSetsLoading} 
            isOwnProfile={isOwnProfile}
            userId={id}
          />
        </div>
      )}
      
      {/* Top Tracks */}
      <div className="mb-6">
        <TopTracks userId={id} isOwnProfile={isOwnProfile} />
      </div>

      {/* Top Events */}
      <div className="mb-6">
        <TopEvents userId={id} isOwnProfile={isOwnProfile} />
      </div>

      {/* Tabs */}
      <div className="bg-surface-800 rounded-xl border border-white/5">
        <div className="border-b border-white/5">
          <nav className="flex gap-1 px-4 pt-2" aria-label="Tabs">
            {[
              { id: 'listened', label: 'Sets' },
              { id: 'events', label: 'Events Attended' },
              { id: 'reviews', label: 'Reviews' },
              { id: 'stats', label: 'Statistics' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-3 px-4 text-sm font-medium border-b-2 transition-colors cursor-pointer ${
                  activeTab === tab.id
                    ? 'border-primary-400 text-primary-400'
                    : 'border-transparent text-slate-500 hover:text-slate-300 hover:border-white/20'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {activeTab === 'stats' && (
            <div>
              <h3 className="text-lg font-semibold mb-4 text-slate-100">Statistics</h3>
              <UserStats stats={stats} loading={loading} userId={id} isOwnProfile={isOwnProfile} />
            </div>
          )}
          {activeTab === 'listened' && (
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-slate-100">Sets</h3>
                {listenedSetsTotal > 0 && (
                  <p className="text-sm text-slate-400">
                    {listenedSets.length} of {listenedSetsTotal}
                  </p>
                )}
              </div>
              {listenedSetsLoading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="bg-surface-700 animate-pulse rounded-xl h-64"></div>
                  ))}
                </div>
              ) : listenedSets.length === 0 ? (
                <div className="text-center py-12">
                  <p className="text-slate-400 text-lg mb-2">No listened sets yet</p>
                  <p className="text-slate-500 text-sm">Sets you mark as listened will appear here</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {listenedSets.map((set) => (
                    <SetCard key={set.id} set={set} />
                  ))}
                </div>
              )}
            </div>
          )}
          {activeTab === 'events' && (
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-slate-100">Events Attended</h3>
                {eventsTotal > 0 && (
                  <p className="text-sm text-slate-400">{eventsAttended.length} of {eventsTotal}</p>
                )}
              </div>
              {eventsLoading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="bg-surface-700 animate-pulse rounded-xl h-64"></div>
                  ))}
                </div>
              ) : eventsAttended.length === 0 ? (
                <div className="text-center py-12">
                  <p className="text-slate-400 text-lg mb-2">No events attended yet</p>
                  <p className="text-slate-500 text-sm">Events you confirm will appear here</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {eventsAttended.map((event) => (
                    <Link
                      key={event.id}
                      to={`/events/${event.id}`}
                      className="block bg-surface-800 rounded-xl border border-white/5 hover:border-primary-500/30 hover:bg-surface-700 transition-colors overflow-hidden cursor-pointer"
                    >
                      <div className="aspect-video bg-surface-700 relative overflow-hidden">
                        {event.thumbnail_url ? (
                          <img src={event.thumbnail_url} alt={event.title} className="w-full h-full object-cover" />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center">
                            <svg viewBox="0 0 24 24" fill="currentColor" className="w-10 h-10 text-slate-600">
                              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 14.5v-9l6 4.5-6 4.5z"/>
                            </svg>
                          </div>
                        )}
                        <div className="absolute top-2 right-2">
                          <span className="inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium bg-accent-500/20 text-accent-400 border border-accent-500/30">
                            Attended
                          </span>
                        </div>
                      </div>
                      <div className="p-4">
                        <h3 className="text-sm font-semibold text-slate-100 mb-1 line-clamp-2">
                          {event.event_name || event.title}
                        </h3>
                        <p className="text-xs text-slate-400 mb-2">{event.dj_name}</p>
                        {event.event_date && (
                          <p className="text-xs text-slate-500">
                            {new Date(event.event_date).toLocaleDateString()}
                          </p>
                        )}
                        {event.venue_location && (
                          <p className="text-xs text-slate-500 mt-0.5 truncate">{event.venue_location}</p>
                        )}
                      </div>
                    </Link>
                  ))}
                </div>
              )}
            </div>
          )}
          {activeTab === 'reviews' && (
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-slate-100">Reviews</h3>
                {reviewsTotal > 0 && <p className="text-sm text-slate-400">{reviewsTotal} reviews</p>}
              </div>
              {reviewsLoading ? (
                <div className="space-y-4">
                  {[1, 2, 3].map((i) => <div key={i} className="bg-surface-700 animate-pulse rounded-xl h-32"></div>)}
                </div>
              ) : userReviews.length === 0 ? (
                <div className="text-center py-12">
                  <p className="text-slate-400 text-lg mb-2">No reviews yet</p>
                  <p className="text-slate-500 text-sm">Reviews written will appear here</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {userReviews.map((review) => (
                    <div key={review.id} className="bg-surface-800 rounded-xl border border-white/5 p-5">
                      {review.set && (
                        <Link
                          to={`/sets/${review.set.id}`}
                          className="flex items-center gap-3 mb-3 group"
                        >
                          {review.set.thumbnail_url && (
                            <img src={review.set.thumbnail_url} alt={review.set.title}
                              className="w-12 h-12 rounded-lg object-cover flex-shrink-0" />
                          )}
                          <div className="min-w-0">
                            <p className="font-medium text-slate-200 group-hover:text-primary-400 transition-colors truncate text-sm">
                              {review.set.title}
                            </p>
                            <p className="text-xs text-slate-500 truncate">{review.set.dj_name}</p>
                          </div>
                          {review.user_rating && (
                            <span className="ml-auto flex-shrink-0 px-2 py-0.5 bg-accent-500/20 border border-accent-500/30 rounded-md text-accent-400 text-sm font-semibold">
                              {review.user_rating.toFixed(1)}
                            </span>
                          )}
                        </Link>
                      )}
                      {review.contains_spoilers && (
                        <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-2 mb-2">
                          <p className="text-yellow-400 text-xs font-medium">Contains Spoilers</p>
                        </div>
                      )}
                      <p className="text-slate-300 text-sm whitespace-pre-wrap leading-relaxed">{review.content}</p>
                      <p className="text-xs text-slate-600 mt-2">
                        {new Date(review.created_at).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default UserProfile;

