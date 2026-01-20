/**
 * Friends Page component.
 * 
 * Displays all friends (users you're following).
 */

import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import * as usersService from '../services/usersService';
import useAuthStore from '../store/authStore';

const FriendsPage = () => {
  const { isAuthenticated } = useAuthStore();
  const [friends, setFriends] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [pagination, setPagination] = useState({
    page: 1,
    limit: 20,
    total: 0,
    pages: 0,
  });

  useEffect(() => {
    if (isAuthenticated()) {
      loadFriends();
    } else {
      setLoading(false);
    }
  }, []);

  const loadFriends = async (page = 1) => {
    setLoading(true);
    setError(null);
    try {
      const response = await usersService.getMyFriends(page, pagination.limit);
      const { items, total, pages } = response.data;
      setFriends(items || []);
      setPagination({
        ...pagination,
        page,
        total,
        pages,
      });
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load friends');
    } finally {
      setLoading(false);
    }
  };

  if (!isAuthenticated()) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center py-12">
          <p className="text-gray-500 text-lg mb-4">
            Please log in to view your friends.
          </p>
          <Link
            to="/login"
            className="text-primary-600 hover:text-primary-700 font-medium"
          >
            Go to Login
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold mb-2">Friends</h1>
          <p className="text-gray-600">
            People you're following.
          </p>
        </div>
        <Link
          to="/friends/search"
          className="bg-primary-600 hover:bg-primary-700 text-white font-medium px-6 py-2 rounded-md"
        >
          Search for New Friends
        </Link>
      </div>

      {/* Friends List */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">Your Friends</h2>
          {pagination.total > 0 && (
            <p className="text-sm text-gray-600">
              {pagination.total} {pagination.total === 1 ? 'friend' : 'friends'}
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
        ) : friends.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg shadow-sm border border-gray-200">
            <p className="text-gray-500 text-lg mb-2">No friends yet</p>
            <p className="text-gray-400 text-sm mb-4">
              Start following people to see them here.
            </p>
            <Link
              to="/friends/search"
              className="inline-block bg-primary-600 hover:bg-primary-700 text-white font-medium px-6 py-2 rounded-md"
            >
              Search for New Friends
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {friends.map((friend) => (
              <Link
                key={friend.id}
                to={`/users/${friend.id}`}
                className="block bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow p-4"
              >
                <div className="flex items-center space-x-4">
                  {/* Avatar */}
                  <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center text-xl font-bold text-primary-600 flex-shrink-0">
                    {friend.username?.[0]?.toUpperCase() || 'F'}
                  </div>
                  
                  {/* Friend Info */}
                  <div className="flex-1 min-w-0">
                    <h3 className="text-lg font-semibold text-gray-900 truncate">
                      {friend.display_name || friend.username}
                    </h3>
                    <p className="text-sm text-gray-600">@{friend.username}</p>
                    {friend.bio && (
                      <p className="text-sm text-gray-700 mt-1 line-clamp-2">
                        {friend.bio}
                      </p>
                    )}
                  </div>
                  
                  {/* View Profile Link */}
                  <div className="flex-shrink-0">
                    <span className="text-primary-600 hover:text-primary-700 font-medium">
                      View Profile →
                    </span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>

      {/* Pagination */}
      {pagination.pages > 1 && (
        <div className="flex items-center justify-center space-x-2">
          <button
            onClick={() => loadFriends(pagination.page - 1)}
            disabled={pagination.page === 1}
            className="px-4 py-2 border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
          >
            Previous
          </button>
          <span className="px-4 py-2 text-sm text-gray-600">
            Page {pagination.page} of {pagination.pages}
          </span>
          <button
            onClick={() => loadFriends(pagination.page + 1)}
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

export default FriendsPage;
