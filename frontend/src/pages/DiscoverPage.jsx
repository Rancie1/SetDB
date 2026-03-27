/**
 * Discover page component.
 * 
 * Shows activity feed with reviews, ratings, and top track/set additions.
 * Can filter between public feed (all users) and friends-only feed.
 */

import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import ActivityFeed from '../components/feed/ActivityFeed';
import * as usersService from '../services/usersService';
import useAuthStore from '../store/authStore';

const DiscoverPage = () => {
  const { isAuthenticated } = useAuthStore();
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [friendsOnly, setFriendsOnly] = useState(false);
  const [pagination, setPagination] = useState({
    page: 1,
    limit: 20,
    total: 0,
    pages: 0,
  });

  useEffect(() => {
    loadActivities();
  }, [friendsOnly]);

  const loadActivities = async (page = 1) => {
    setLoading(true);
    setError(null);
    try {
      // Only allow friends-only if user is authenticated
      const friendsOnlyFilter = isAuthenticated() && friendsOnly;
      const response = await usersService.getActivityFeed(page, pagination.limit, friendsOnlyFilter);
      const { items, total, pages } = response.data;
      setActivities(items || []);
      setPagination({
        ...pagination,
        page,
        total,
        pages,
      });
    } catch (err) {
      console.error('Activity feed error:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to load activity feed');
    } finally {
      setLoading(false);
    }
  };

  const handlePageChange = (newPage) => {
    loadActivities(newPage);
  };

  const handleFilterChange = (newFriendsOnly) => {
    setFriendsOnly(newFriendsOnly);
    setPagination({
      ...pagination,
      page: 1,
    });
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2 text-slate-100">Discover</h1>
        <p className="text-slate-400">
          See what your friends and the community are reviewing, rating, and adding to their top 5.
        </p>
      </div>

      {/* Filter Tabs */}
      {isAuthenticated() && (
        <div className="mb-6 bg-surface-800 rounded-xl border border-white/5 p-1 flex">
          <button
            onClick={() => handleFilterChange(false)}
            className={`flex-1 px-4 py-2 rounded-lg text-sm font-medium transition-colors duration-150 cursor-pointer ${
              !friendsOnly
                ? 'bg-primary-600 text-white'
                : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
            }`}
          >
            Public Feed
          </button>
          <button
            onClick={() => handleFilterChange(true)}
            className={`flex-1 px-4 py-2 rounded-lg text-sm font-medium transition-colors duration-150 cursor-pointer ${
              friendsOnly
                ? 'bg-primary-600 text-white'
                : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
            }`}
          >
            Friends Only
          </button>
        </div>
      )}

      {!isAuthenticated() && (
        <div className="mb-6 bg-primary-600/10 border border-primary-500/20 rounded-xl p-4">
          <p className="text-primary-300 text-sm">
            <Link to="/login" className="font-semibold hover:underline">Sign in</Link> to see activity from your friends.
          </p>
        </div>
      )}

      {/* Activity Feed */}
      <ActivityFeed activities={activities} loading={loading} error={error} />

      {/* Pagination */}
      {pagination.pages > 1 && (
        <div className="mt-6 flex items-center justify-center gap-2">
          <button
            onClick={() => handlePageChange(pagination.page - 1)}
            disabled={pagination.page === 1}
            className="px-4 py-2 bg-surface-800 border border-white/5 rounded-lg text-sm text-slate-300 hover:text-white hover:bg-surface-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors duration-150 cursor-pointer"
          >
            Previous
          </button>
          <span className="px-4 py-2 text-sm text-slate-500">
            {pagination.page} / {pagination.pages}
          </span>
          <button
            onClick={() => handlePageChange(pagination.page + 1)}
            disabled={pagination.page >= pagination.pages}
            className="px-4 py-2 bg-surface-800 border border-white/5 rounded-lg text-sm text-slate-300 hover:text-white hover:bg-surface-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors duration-150 cursor-pointer"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
};

export default DiscoverPage;
