/**
 * User statistics component.
 * 
 * Displays user statistics like sets logged, reviews written, etc.
 */

import { Link } from 'react-router-dom';
import useAuthStore from '../../store/authStore';

const UserStats = ({ stats, loading, userId, isOwnProfile }) => {
  const { user: currentUser } = useAuthStore();
  if (loading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="bg-surface-700 animate-pulse h-24 rounded-xl"></div>
        ))}
      </div>
    );
  }

  if (!stats) {
    return <div className="text-gray-500">No statistics available</div>;
  }

  const formatHours = (hours) => {
    if (hours === 0) return '0';
    if (hours < 1) {
      const minutes = Math.round(hours * 60);
      return `${minutes}m`;
    }
    if (hours < 10) {
      return hours.toFixed(1);
    }
    return Math.round(hours).toString();
  };

  const statItems = [
    {
      label: 'Sets Logged',
      value: stats.sets_logged || 0,
      icon: '🎧',
    },
    {
      label: 'Hours Listened',
      value: stats.hours_listened !== undefined 
        ? `${formatHours(stats.hours_listened)}`
        : '0',
      icon: '⏱️',
    },
    {
      label: 'Reviews Written',
      value: stats.reviews_written || 0,
      icon: '✍️',
    },
    {
      label: 'Lists Created',
      value: stats.lists_created || 0,
      icon: '📋',
    },
    {
      label: 'Average Rating',
      value: stats.average_rating ? stats.average_rating.toFixed(1) : 'N/A',
      icon: '⭐',
    },
    {
      label: 'Friends',
      value: stats.following_count || 0,
      icon: '👥',
    },
    {
      label: 'Followers',
      value: stats.followers_count || 0,
      icon: '❤️',
    },
    {
      label: 'Venues Attended',
      value: stats.venues_attended || 0,
      icon: '📍',
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
      {statItems.map((item, index) => {
        const StatContent = (
          <div className="flex items-center space-x-3">
            <span className="text-2xl">{item.icon}</span>
            <div>
              <div className="text-2xl font-bold text-slate-100">{item.value}</div>
              <div className="text-sm text-gray-600">{item.label}</div>
            </div>
          </div>
        );

        // Make Friends stat clickable for own profile
        if (item.label === 'Friends' && isOwnProfile) {
          return (
            <Link
              key={index}
              to="/friends"
              className="bg-surface-800 p-4 rounded-xl border border-white/5 hover:border-primary-500/30 hover:bg-surface-700 transition-colors cursor-pointer"
            >
              {StatContent}
            </Link>
          );
        }

        return (
          <div
            key={index}
            className="bg-surface-800 p-4 rounded-xl border border-white/5"
          >
            {StatContent}
          </div>
        );
      })}
    </div>
  );
};

export default UserStats;


