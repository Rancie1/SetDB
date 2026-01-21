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
import UserStats from './UserStats';
import SetCard from '../sets/SetCard';
import TopSets from './TopSets';
import TopTracks from './TopTracks';

const UserProfile = () => {
  const { id } = useParams();
  const { user: currentUser } = useAuthStore();
  const [user, setUser] = useState(null);
  const [stats, setStats] = useState(null);
  const [activeTab, setActiveTab] = useState('stats');
  const [loading, setLoading] = useState(true);
  const [isFollowing, setIsFollowing] = useState(false);
  const [followingLoading, setFollowingLoading] = useState(false);
  
  // Live sets seen
  const [liveSetsSeen, setLiveSetsSeen] = useState([]);
  const [liveSetsLoading, setLiveSetsLoading] = useState(false);
  const [liveSetsPage, setLiveSetsPage] = useState(1);
  const [liveSetsTotal, setLiveSetsTotal] = useState(0);
  
  // Listened sets (non-live)
  const [listenedSets, setListenedSets] = useState([]);
  const [listenedSetsLoading, setListenedSetsLoading] = useState(false);
  const [listenedSetsPage, setListenedSetsPage] = useState(1);
  const [listenedSetsTotal, setListenedSetsTotal] = useState(0);
  
  // Events attended
  const [eventsAttended, setEventsAttended] = useState([]);
  const [eventsLoading, setEventsLoading] = useState(false);
  const [eventsPage, setEventsPage] = useState(1);
  const [eventsTotal, setEventsTotal] = useState(0);

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
    if (activeTab === 'live-sets' && id) {
      loadLiveSetsSeen();
    } else if (activeTab === 'listened' && id) {
      loadListenedSets();
    } else if (activeTab === 'events' && id) {
      loadEventsAttended();
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

  const loadLiveSetsSeen = async (page = 1) => {
    setLiveSetsLoading(true);
    try {
      const response = await logsService.getUserLogs(id, page, 20, 'live');
      const logs = response.data.items || [];
      // Extract the set from each log (the API now includes set in the response)
      const sets = logs.map(log => log.set).filter(Boolean);
      setLiveSetsSeen(sets);
      setLiveSetsPage(page);
      setLiveSetsTotal(response.data.total || 0);
    } catch (error) {
      console.error('Failed to load live sets seen:', error);
      setLiveSetsSeen([]);
    } finally {
      setLiveSetsLoading(false);
    }
  };

  const loadListenedSets = async (page = 1) => {
    setListenedSetsLoading(true);
    try {
      // Get YouTube and SoundCloud sets separately, then combine
      const [youtubeResponse, soundcloudResponse] = await Promise.all([
        logsService.getUserLogs(id, 1, 100, 'youtube').catch(() => ({ data: { items: [] } })),
        logsService.getUserLogs(id, 1, 100, 'soundcloud').catch(() => ({ data: { items: [] } }))
      ]);
      
      const youtubeLogs = youtubeResponse.data.items || [];
      const soundcloudLogs = soundcloudResponse.data.items || [];
      
      // Combine and extract sets
      const allLogs = [...youtubeLogs, ...soundcloudLogs];
      const sets = allLogs.map(log => log.set).filter(Boolean);
      
      // Apply pagination on frontend
      const limit = 20;
      const offset = (page - 1) * limit;
      const paginatedSets = sets.slice(offset, offset + limit);
      
      setListenedSets(paginatedSets);
      setListenedSetsPage(page);
      setListenedSetsTotal(sets.length);
    } catch (error) {
      console.error('Failed to load listened sets:', error);
      console.error('Error details:', error.response?.data);
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

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="animate-pulse">
          <div className="h-32 bg-gray-200 rounded-lg mb-6"></div>
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-4"></div>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">User Not Found</h2>
          <p className="text-gray-600">The user you're looking for doesn't exist.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Profile Header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-4">
            {/* Avatar */}
            <div className="w-20 h-20 bg-primary-100 rounded-full flex items-center justify-center text-2xl font-bold text-primary-600">
              {user.username?.[0]?.toUpperCase() || 'U'}
            </div>
            
            {/* User Info */}
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                {user.display_name || user.username}
              </h1>
              <p className="text-gray-600">@{user.username}</p>
              {user.bio && (
                <p className="text-gray-700 mt-2">{user.bio}</p>
              )}
              <p className="text-sm text-gray-500 mt-2">
                Joined {new Date(user.created_at).toLocaleDateString()}
              </p>
            </div>
          </div>

          {/* Follow/Edit Button */}
          {!isOwnProfile && (
            <button
              onClick={handleFollow}
              disabled={followingLoading}
              className={`px-6 py-2 rounded-md font-medium ${
                isFollowing
                  ? 'bg-gray-100 hover:bg-gray-200 text-gray-700'
                  : 'bg-primary-600 hover:bg-primary-700 text-white'
              } disabled:opacity-50`}
            >
              {followingLoading
                ? '...'
                : isFollowing
                ? 'Friends'
                : 'Add Friend'}
            </button>
          )}
          {isOwnProfile && (
            <Link
              to="/profile/manage"
              className="px-6 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-md font-medium"
            >
              Manage Profile
            </Link>
          )}
        </div>
      </div>

      {/* Stats */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold mb-4">Statistics</h2>
        <UserStats stats={stats} loading={loading} />
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

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6" aria-label="Tabs">
            {[
              { id: 'stats', label: 'Stats' },
              { id: 'listened', label: 'Listened Sets' },
              { id: 'live-sets', label: 'Live Sets Seen' },
              { id: 'events', label: 'Events Attended' },
              { id: 'reviews', label: 'Reviews' },
              { id: 'lists', label: 'Lists' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === tab.id
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
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
              <p className="text-gray-600">Detailed statistics coming soon...</p>
            </div>
          )}
          {activeTab === 'listened' && (
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">Listened Sets</h3>
                {listenedSetsTotal > 0 && (
                  <p className="text-sm text-gray-600">
                    Showing {listenedSets.length} of {listenedSetsTotal} listened sets
                  </p>
                )}
              </div>
              {listenedSetsLoading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="bg-gray-100 animate-pulse rounded-lg h-64"></div>
                  ))}
                </div>
              ) : listenedSets.length === 0 ? (
                <div className="text-center py-12">
                  <p className="text-gray-500 text-lg mb-2">No listened sets yet</p>
                  <p className="text-gray-400 text-sm">
                    Sets you mark as listened (YouTube/SoundCloud) will appear here
                  </p>
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
          {activeTab === 'live-sets' && (
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">Live Sets Seen</h3>
                {liveSetsTotal > 0 && (
                  <p className="text-sm text-gray-600">
                    {liveSetsSeen.length} of {liveSetsTotal} live sets
                  </p>
                )}
              </div>
              {liveSetsLoading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="bg-gray-100 animate-pulse rounded-lg h-64"></div>
                  ))}
                </div>
              ) : liveSetsSeen.length === 0 ? (
                <div className="text-center py-12">
                  <p className="text-gray-500 text-lg mb-2">No live sets seen yet</p>
                  <p className="text-gray-400 text-sm">
                    Live sets you mark as seen will appear here
                  </p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {liveSetsSeen.map((set) => (
                    <SetCard key={set.id} set={set} />
                  ))}
                </div>
              )}
            </div>
          )}
          {activeTab === 'events' && (
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">Events Attended</h3>
                {eventsTotal > 0 && (
                  <p className="text-sm text-gray-600">
                    {eventsAttended.length} of {eventsTotal} events
                  </p>
                )}
              </div>
              {eventsLoading ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="bg-gray-100 animate-pulse rounded-lg h-64"></div>
                  ))}
                </div>
              ) : eventsAttended.length === 0 ? (
                <div className="text-center py-12">
                  <p className="text-gray-500 text-lg mb-2">No events attended yet</p>
                  <p className="text-gray-400 text-sm">
                    Events you confirm will appear here
                  </p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                  {eventsAttended.map((event) => (
                    <Link
                      key={event.id}
                      to={`/events/${event.id}`}
                      className="block bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow overflow-hidden"
                    >
                      <div className="aspect-video bg-gray-200 relative overflow-hidden">
                        {event.thumbnail_url ? (
                          <img
                            src={event.thumbnail_url}
                            alt={event.title}
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center text-gray-400">
                            <span className="text-4xl">🎤</span>
                          </div>
                        )}
                        <div className="absolute top-2 right-2">
                          <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium border bg-green-100 text-green-800 border-green-300">
                            ✓ Attended
                          </span>
                        </div>
                      </div>
                      <div className="p-4">
                        <h3 className="text-lg font-semibold text-gray-900 mb-1 line-clamp-2">
                          {event.event_name || event.title}
                        </h3>
                        <p className="text-sm text-gray-600 mb-2">{event.dj_name}</p>
                        {event.event_date && (
                          <p className="text-sm text-gray-700">
                            📅 {new Date(event.event_date).toLocaleDateString()}
                          </p>
                        )}
                        {event.venue_location && (
                          <p className="text-sm text-gray-700 mt-1">
                            📍 {event.venue_location}
                          </p>
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
              <p className="text-gray-600">Reviews will appear here...</p>
            </div>
          )}
          {activeTab === 'lists' && (
            <div>
              <p className="text-gray-600">Lists will appear here...</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default UserProfile;

