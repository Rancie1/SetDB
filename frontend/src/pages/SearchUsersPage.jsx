/**
 * Search Friends Page component.
 * 
 * Allows users to search for and discover other friends.
 */

import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import * as usersService from '../services/usersService';
import useAuthStore from '../store/authStore';

const SearchUsersPage = () => {
  const navigate = useNavigate();
  const { isAuthenticated, user: currentUser } = useAuthStore();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [friendStatuses, setFriendStatuses] = useState({}); // Track friend status for each user
  const [loadingStatuses, setLoadingStatuses] = useState({}); // Track loading state for each user
  const [pagination, setPagination] = useState({
    page: 1,
    limit: 20,
    total: 0,
    pages: 0,
  });

  useEffect(() => {
    if (searchQuery.trim()) {
      searchUsers(searchQuery, 1);
    } else {
      // Load initial users or show empty state
      setUsers([]);
      setPagination({ page: 1, limit: 20, total: 0, pages: 0 });
      setFriendStatuses({});
    }
  }, []);

  const searchUsers = async (search = '', page = 1) => {
    setLoading(true);
    setError(null);
    try {
      const response = await usersService.searchUsers(search, page, pagination.limit);
      const { items, total, pages } = response.data;
      setUsers(items || []);
      setPagination({
        ...pagination,
        page,
        total,
        pages,
      });
      
      // Check friend status for each user if authenticated
      if (isAuthenticated() && items) {
        checkFriendStatuses(items);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to search users');
    } finally {
      setLoading(false);
    }
  };

  const checkFriendStatuses = async (userList) => {
    if (!isAuthenticated()) return;
    
    const statusPromises = userList.map(async (user) => {
      // Skip checking status for own profile
      if (currentUser && String(currentUser.id) === String(user.id)) {
        return { userId: user.id, isFriend: false, isOwnProfile: true };
      }
      
      try {
        const response = await usersService.getFollowStatus(user.id);
        return {
          userId: user.id,
          isFriend: response.data.is_following || false,
          isOwnProfile: response.data.is_own_profile || false,
        };
      } catch (error) {
        return { userId: user.id, isFriend: false, isOwnProfile: false };
      }
    });
    
    const statuses = await Promise.all(statusPromises);
    const statusMap = {};
    statuses.forEach((status) => {
      statusMap[status.userId] = status;
    });
    setFriendStatuses(statusMap);
  };

  const handleAddFriend = async (userId, e) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (!isAuthenticated()) {
      navigate('/login');
      return;
    }
    
    setLoadingStatuses({ ...loadingStatuses, [userId]: true });
    
    try {
      const currentStatus = friendStatuses[userId];
      if (currentStatus?.isFriend) {
        await usersService.unfollowUser(userId);
        setFriendStatuses({
          ...friendStatuses,
          [userId]: { ...currentStatus, isFriend: false },
        });
      } else {
        await usersService.followUser(userId);
        setFriendStatuses({
          ...friendStatuses,
          [userId]: { ...currentStatus, isFriend: true },
        });
      }
    } catch (error) {
      console.error('Failed to add/remove friend:', error);
      alert(error.response?.data?.detail || 'Failed to update friend status');
    } finally {
      setLoadingStatuses({ ...loadingStatuses, [userId]: false });
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      searchUsers(searchQuery.trim(), 1);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Search Friends</h1>
        <p className="text-gray-600">
          Find and connect with other friends on the platform.
        </p>
      </div>

      {/* Search Bar */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
        <form onSubmit={handleSearch} className="flex gap-4">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by username or display name..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
          <button
            type="submit"
            className="bg-primary-600 hover:bg-primary-700 text-white font-medium px-6 py-2 rounded-md"
          >
            Search
          </button>
          {searchQuery && (
            <button
              type="button"
              onClick={() => {
                setSearchQuery('');
                setUsers([]);
                setPagination({ page: 1, limit: 20, total: 0, pages: 0 });
                setFriendStatuses({});
              }}
              className="bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium px-4 py-2 rounded-md"
            >
              Clear
            </button>
          )}
        </form>
      </div>

      {/* Users List */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">
            {searchQuery ? `Search Results` : 'Friends'}
          </h2>
          {pagination.total > 0 && (
            <p className="text-sm text-gray-600">
              Showing {users.length} of {pagination.total} {pagination.total === 1 ? 'friend' : 'friends'}
            </p>
          )}
        </div>

        {loading ? (
          <div className="space-y-4">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="bg-gray-100 animate-pulse rounded-lg h-20"></div>
            ))}
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
            {error}
          </div>
        ) : users.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500 text-lg mb-2">
              {searchQuery ? 'No friends found' : 'Search for friends to get started'}
            </p>
            <p className="text-gray-400 text-sm">
              {searchQuery
                ? 'Try a different search term.'
                : 'Enter a username or display name to search.'}
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {users.map((user) => {
              const isOwnProfile = currentUser && String(currentUser.id) === String(user.id);
              const friendStatus = friendStatuses[user.id];
              const isFriend = friendStatus?.isFriend || false;
              const isLoading = loadingStatuses[user.id] || false;
              
              return (
                <div
                  key={user.id}
                  className="block bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow p-4"
                >
                  <div className="flex items-center space-x-4">
                    {/* Avatar */}
                    <Link
                      to={`/users/${user.id}`}
                      className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center text-xl font-bold text-primary-600 flex-shrink-0 hover:bg-primary-200 transition-colors"
                    >
                      {user.username?.[0]?.toUpperCase() || 'U'}
                    </Link>
                    
                    {/* User Info */}
                    <Link
                      to={`/users/${user.id}`}
                      className="flex-1 min-w-0 hover:opacity-80 transition-opacity"
                    >
                      <h3 className="text-lg font-semibold text-gray-900 truncate">
                        {user.display_name || user.username}
                      </h3>
                      <p className="text-sm text-gray-600">@{user.username}</p>
                      {user.bio && (
                        <p className="text-sm text-gray-700 mt-1 line-clamp-2">
                          {user.bio}
                        </p>
                      )}
                    </Link>
                    
                    {/* Action Buttons */}
                    <div className="flex-shrink-0 flex items-center space-x-2">
                      {!isOwnProfile && isAuthenticated() && (
                        <button
                          onClick={(e) => handleAddFriend(user.id, e)}
                          disabled={isLoading}
                          className={`px-4 py-2 rounded-md font-medium text-sm transition-colors disabled:opacity-50 ${
                            isFriend
                              ? 'bg-gray-100 hover:bg-gray-200 text-gray-700'
                              : 'bg-primary-600 hover:bg-primary-700 text-white'
                          }`}
                        >
                          {isLoading
                            ? '...'
                            : isFriend
                            ? 'Friends'
                            : 'Add Friend'}
                        </button>
                      )}
                      <Link
                        to={`/users/${user.id}`}
                        className="px-4 py-2 text-primary-600 hover:text-primary-700 font-medium text-sm"
                      >
                        View Profile →
                      </Link>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Pagination */}
      {pagination.pages > 1 && (
        <div className="flex items-center justify-center space-x-2">
          <button
            onClick={() => searchUsers(searchQuery, pagination.page - 1)}
            disabled={pagination.page === 1}
            className="px-4 py-2 border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
          >
            Previous
          </button>
          <span className="px-4 py-2 text-sm text-gray-600">
            Page {pagination.page} of {pagination.pages}
          </span>
          <button
            onClick={() => searchUsers(searchQuery, pagination.page + 1)}
            disabled={pagination.page >= pagination.pages}
            className="px-4 py-2 border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
};

export default SearchUsersPage;
