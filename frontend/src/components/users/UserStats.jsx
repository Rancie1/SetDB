/**
 * User statistics component.
 * 
 * Displays user statistics like sets logged, reviews written, etc.
 */

const UserStats = ({ stats, loading }) => {
  if (loading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="bg-gray-100 animate-pulse h-24 rounded-lg"></div>
        ))}
      </div>
    );
  }

  if (!stats) {
    return <div className="text-gray-500">No statistics available</div>;
  }

  const statItems = [
    {
      label: 'Sets Logged',
      value: stats.sets_logged || 0,
      icon: '🎧',
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
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
      {statItems.map((item, index) => (
        <div
          key={index}
          className="bg-white p-4 rounded-lg shadow-sm border border-gray-200"
        >
          <div className="flex items-center space-x-3">
            <span className="text-2xl">{item.icon}</span>
            <div>
              <div className="text-2xl font-bold text-gray-900">{item.value}</div>
              <div className="text-sm text-gray-600">{item.label}</div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default UserStats;


