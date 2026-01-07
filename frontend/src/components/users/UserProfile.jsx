/**
 * User profile component.
 * 
 * Displays user information, stats, and tabs for different sections.
 */

import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import useAuthStore from '../../store/authStore';
import * as usersService from '../../services/usersService';
import UserStats from './UserStats';

const UserProfile = () => {
  const { id } = useParams();
  const { user: currentUser } = useAuthStore();
  const [user, setUser] = useState(null);
  const [stats, setStats] = useState(null);
  const [activeTab, setActiveTab] = useState('stats');
  const [loading, setLoading] = useState(true);
  const [isFollowing, setIsFollowing] = useState(false);
  const [followingLoading, setFollowingLoading] = useState(false);

  const isOwnProfile = currentUser && String(currentUser.id) === id;

  useEffect(() => {
    loadUserData();
  }, [id]);

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
    } catch (error) {
      console.error('Failed to follow/unfollow:', error);
    } finally {
      setFollowingLoading(false);
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
                ? 'Following'
                : 'Follow'}
            </button>
          )}
          {isOwnProfile && (
            <Link
              to="/settings"
              className="px-6 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-md font-medium"
            >
              Edit Profile
            </Link>
          )}
        </div>
      </div>

      {/* Stats */}
      <div className="mb-6">
        <h2 className="text-xl font-semibold mb-4">Statistics</h2>
        <UserStats stats={stats} loading={loading} />
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6" aria-label="Tabs">
            {[
              { id: 'stats', label: 'Stats' },
              { id: 'sets', label: 'Logged Sets' },
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
          {activeTab === 'sets' && (
            <div>
              <p className="text-gray-600">Logged sets will appear here...</p>
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

