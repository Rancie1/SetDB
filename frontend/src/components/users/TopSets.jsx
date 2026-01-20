/**
 * Top Sets component.
 * 
 * Displays a user's top 5 sets on their profile page.
 */

import SetCard from '../sets/SetCard';

const TopSets = ({ topSets, loading, isOwnProfile, userId }) => {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="bg-gray-100 animate-pulse rounded-lg h-64"></div>
        ))}
      </div>
    );
  }

  if (!topSets || topSets.length === 0) {
    return (
      <div className="text-center py-8 bg-white rounded-lg shadow-sm border border-gray-200">
        <p className="text-gray-500">
          {isOwnProfile 
            ? "You haven't selected any top sets yet. Mark sets as your favorites to display them here!"
            : "This user hasn't selected any top sets yet."}
        </p>
      </div>
    );
  }

  return (
    <div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {topSets.map((log, index) => (
          <div key={log.id} className="relative">
            {isOwnProfile && (
              <div className="absolute top-2 left-2 z-10 bg-primary-600 text-white text-sm font-bold px-2 py-1 rounded shadow-lg">
                #{log.top_set_order || index + 1}
              </div>
            )}
            {log.set && (
              <SetCard set={log.set} />
            )}
          </div>
        ))}
      </div>
      
      {/* Fill empty slots if less than 5 */}
      {topSets.length < 5 && isOwnProfile && (
        <div className="mt-4 text-center">
          <p className="text-sm text-gray-500">
            {5 - topSets.length} more slot{5 - topSets.length !== 1 ? 's' : ''} available for your top sets
          </p>
        </div>
      )}
    </div>
  );
};

export default TopSets;
