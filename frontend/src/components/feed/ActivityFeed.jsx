/**
 * Activity Feed component.
 * 
 * Displays social media-style activity posts showing reviews, ratings, and top track/set additions.
 */

import { Link } from 'react-router-dom';

const formatTimeAgo = (dateString) => {
  const date = new Date(dateString);
  const now = new Date();
  const seconds = Math.floor((now - date) / 1000);
  
  if (seconds < 60) return 'just now';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes} minute${minutes !== 1 ? 's' : ''} ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} hour${hours !== 1 ? 's' : ''} ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days} day${days !== 1 ? 's' : ''} ago`;
  const weeks = Math.floor(days / 7);
  if (weeks < 4) return `${weeks} week${weeks !== 1 ? 's' : ''} ago`;
  const months = Math.floor(days / 30);
  if (months < 12) return `${months} month${months !== 1 ? 's' : ''} ago`;
  const years = Math.floor(days / 365);
  return `${years} year${years !== 1 ? 's' : ''} ago`;
};

const ActivityFeed = ({ activities, loading, error }) => {
  if (loading) {
    return (
      <div className="space-y-4">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
            <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error loading activity feed: {error}</p>
      </div>
    );
  }

  if (!activities || activities.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
        <p className="text-gray-500 text-lg">No activity to show yet.</p>
        <p className="text-gray-400 text-sm mt-2">Start reviewing, rating, or adding tracks to your top 5!</p>
      </div>
    );
  }

  const renderActivity = (activity) => {
    const timeAgo = formatTimeAgo(activity.created_at);
    const userLink = `/users/${activity.user.id}`;
    const userDisplayName = activity.user.display_name || activity.user.username;

    switch (activity.activity_type) {
      case 'set_review':
        return (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
            <div className="flex items-start space-x-4">
              <Link to={userLink} className="flex-shrink-0">
                <div className="w-12 h-12 rounded-full bg-primary-100 flex items-center justify-center text-primary-600 font-semibold">
                  {userDisplayName.charAt(0).toUpperCase()}
                </div>
              </Link>
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2 mb-2">
                  <Link to={userLink} className="font-semibold text-gray-900 hover:text-primary-600">
                    {userDisplayName}
                  </Link>
                  <span className="text-gray-500 text-sm">reviewed a set</span>
                  <span className="text-gray-400 text-xs">· {timeAgo}</span>
                </div>
                {activity.set_review?.set && (
                  <Link to={`/sets/${activity.set_review.set.id}`} className="block mb-3">
                    <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                      {activity.set_review.set.thumbnail_url && (
                        <img
                          src={activity.set_review.set.thumbnail_url}
                          alt={activity.set_review.set.title}
                          className="w-16 h-16 rounded object-cover"
                        />
                      )}
                      <div className="flex-1 min-w-0">
                        <h4 className="font-semibold text-gray-900 truncate">{activity.set_review.set.title}</h4>
                        <p className="text-sm text-gray-600">{activity.set_review.set.dj_name}</p>
                      </div>
                    </div>
                  </Link>
                )}
                <p className="text-gray-700 whitespace-pre-wrap">{activity.set_review.content}</p>
                {activity.set_review.user_rating && (
                  <div className="mt-2 text-sm text-gray-600">
                    Rated {activity.set_review.user_rating} ⭐
                  </div>
                )}
              </div>
            </div>
          </div>
        );

      case 'set_rating':
        return (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
            <div className="flex items-start space-x-4">
              <Link to={userLink} className="flex-shrink-0">
                <div className="w-12 h-12 rounded-full bg-primary-100 flex items-center justify-center text-primary-600 font-semibold">
                  {userDisplayName.charAt(0).toUpperCase()}
                </div>
              </Link>
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2 mb-2">
                  <Link to={userLink} className="font-semibold text-gray-900 hover:text-primary-600">
                    {userDisplayName}
                  </Link>
                  <span className="text-gray-500 text-sm">rated a set</span>
                  <span className="text-gray-400 text-xs">· {timeAgo}</span>
                </div>
                {activity.set_rating?.set && (
                  <Link to={`/sets/${activity.set_rating.set.id}`} className="block">
                    <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                      {activity.set_rating.set.thumbnail_url && (
                        <img
                          src={activity.set_rating.set.thumbnail_url}
                          alt={activity.set_rating.set.title}
                          className="w-16 h-16 rounded object-cover"
                        />
                      )}
                      <div className="flex-1 min-w-0">
                        <h4 className="font-semibold text-gray-900 truncate">{activity.set_rating.set.title}</h4>
                        <p className="text-sm text-gray-600">{activity.set_rating.set.dj_name}</p>
                      </div>
                      <div className="text-2xl font-bold text-primary-600">
                        {activity.set_rating.rating} ⭐
                      </div>
                    </div>
                  </Link>
                )}
              </div>
            </div>
          </div>
        );

      case 'track_review':
        return (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
            <div className="flex items-start space-x-4">
              <Link to={userLink} className="flex-shrink-0">
                <div className="w-12 h-12 rounded-full bg-primary-100 flex items-center justify-center text-primary-600 font-semibold">
                  {userDisplayName.charAt(0).toUpperCase()}
                </div>
              </Link>
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2 mb-2">
                  <Link to={userLink} className="font-semibold text-gray-900 hover:text-primary-600">
                    {userDisplayName}
                  </Link>
                  <span className="text-gray-500 text-sm">reviewed a track</span>
                  <span className="text-gray-400 text-xs">· {timeAgo}</span>
                </div>
                {activity.track_review?.track && (
                  <Link to={`/tracks/${activity.track_review.track.id}`} className="block mb-3">
                    <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                      {activity.track_review.track.thumbnail_url && (
                        <img
                          src={activity.track_review.track.thumbnail_url}
                          alt={activity.track_review.track.track_name}
                          className="w-16 h-16 rounded object-cover"
                        />
                      )}
                      <div className="flex-1 min-w-0">
                        <h4 className="font-semibold text-gray-900 truncate">{activity.track_review.track.track_name}</h4>
                        <p className="text-sm text-gray-600">{activity.track_review.track.artist_name || 'Unknown Artist'}</p>
                      </div>
                    </div>
                  </Link>
                )}
                <p className="text-gray-700 whitespace-pre-wrap">{activity.track_review.content}</p>
                {activity.track_review.user_rating && (
                  <div className="mt-2 text-sm text-gray-600">
                    Rated {activity.track_review.user_rating} ⭐
                  </div>
                )}
              </div>
            </div>
          </div>
        );

      case 'track_rating':
        return (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
            <div className="flex items-start space-x-4">
              <Link to={userLink} className="flex-shrink-0">
                <div className="w-12 h-12 rounded-full bg-primary-100 flex items-center justify-center text-primary-600 font-semibold">
                  {userDisplayName.charAt(0).toUpperCase()}
                </div>
              </Link>
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2 mb-2">
                  <Link to={userLink} className="font-semibold text-gray-900 hover:text-primary-600">
                    {userDisplayName}
                  </Link>
                  <span className="text-gray-500 text-sm">rated a track</span>
                  <span className="text-gray-400 text-xs">· {timeAgo}</span>
                </div>
                {activity.track_rating?.track && (
                  <Link to={`/tracks/${activity.track_rating.track.id}`} className="block">
                    <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                      {activity.track_rating.track.thumbnail_url && (
                        <img
                          src={activity.track_rating.track.thumbnail_url}
                          alt={activity.track_rating.track.track_name}
                          className="w-16 h-16 rounded object-cover"
                        />
                      )}
                      <div className="flex-1 min-w-0">
                        <h4 className="font-semibold text-gray-900 truncate">{activity.track_rating.track.track_name}</h4>
                        <p className="text-sm text-gray-600">{activity.track_rating.track.artist_name || 'Unknown Artist'}</p>
                      </div>
                      <div className="text-2xl font-bold text-primary-600">
                        {activity.track_rating.rating} ⭐
                      </div>
                    </div>
                  </Link>
                )}
              </div>
            </div>
          </div>
        );

      case 'top_track':
        return (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
            <div className="flex items-start space-x-4">
              <Link to={userLink} className="flex-shrink-0">
                <div className="w-12 h-12 rounded-full bg-primary-100 flex items-center justify-center text-primary-600 font-semibold">
                  {userDisplayName.charAt(0).toUpperCase()}
                </div>
              </Link>
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2 mb-2">
                  <Link to={userLink} className="font-semibold text-gray-900 hover:text-primary-600">
                    {userDisplayName}
                  </Link>
                  <span className="text-gray-500 text-sm">added a track to their top 5</span>
                  <span className="text-gray-400 text-xs">· {timeAgo}</span>
                </div>
                {activity.top_track?.track && (
                  <Link to={`/tracks/${activity.top_track.track.id}`} className="block">
                    <div className="flex items-center space-x-3 p-3 bg-gradient-to-r from-yellow-50 to-yellow-100 rounded-lg hover:from-yellow-100 hover:to-yellow-200 transition-colors border border-yellow-200">
                      {activity.top_track.track.thumbnail_url && (
                        <img
                          src={activity.top_track.track.thumbnail_url}
                          alt={activity.top_track.track.track_name}
                          className="w-16 h-16 rounded object-cover"
                        />
                      )}
                      <div className="flex-1 min-w-0">
                        <h4 className="font-semibold text-gray-900 truncate">{activity.top_track.track.track_name}</h4>
                        <p className="text-sm text-gray-600">{activity.top_track.track.artist_name || 'Unknown Artist'}</p>
                      </div>
                      <div className="text-xl font-bold text-yellow-600">
                        #{activity.top_track.order}
                      </div>
                    </div>
                  </Link>
                )}
              </div>
            </div>
          </div>
        );

      case 'top_set':
        return (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
            <div className="flex items-start space-x-4">
              <Link to={userLink} className="flex-shrink-0">
                <div className="w-12 h-12 rounded-full bg-primary-100 flex items-center justify-center text-primary-600 font-semibold">
                  {userDisplayName.charAt(0).toUpperCase()}
                </div>
              </Link>
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2 mb-2">
                  <Link to={userLink} className="font-semibold text-gray-900 hover:text-primary-600">
                    {userDisplayName}
                  </Link>
                  <span className="text-gray-500 text-sm">added a set to their top 5</span>
                  <span className="text-gray-400 text-xs">· {timeAgo}</span>
                </div>
                {activity.top_set?.set && (
                  <Link to={`/sets/${activity.top_set.set.id}`} className="block">
                    <div className="flex items-center space-x-3 p-3 bg-gradient-to-r from-yellow-50 to-yellow-100 rounded-lg hover:from-yellow-100 hover:to-yellow-200 transition-colors border border-yellow-200">
                      {activity.top_set.set.thumbnail_url && (
                        <img
                          src={activity.top_set.set.thumbnail_url}
                          alt={activity.top_set.set.title}
                          className="w-16 h-16 rounded object-cover"
                        />
                      )}
                      <div className="flex-1 min-w-0">
                        <h4 className="font-semibold text-gray-900 truncate">{activity.top_set.set.title}</h4>
                        <p className="text-sm text-gray-600">{activity.top_set.set.dj_name}</p>
                      </div>
                      <div className="text-xl font-bold text-yellow-600">
                        #{activity.top_set.order}
                      </div>
                    </div>
                  </Link>
                )}
              </div>
            </div>
          </div>
        );

      case 'event_created':
        return (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
            <div className="flex items-start space-x-4">
              <Link to={userLink} className="flex-shrink-0">
                <div className="w-12 h-12 rounded-full bg-primary-100 flex items-center justify-center text-primary-600 font-semibold">
                  {userDisplayName.charAt(0).toUpperCase()}
                </div>
              </Link>
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2 mb-2">
                  <Link to={userLink} className="font-semibold text-gray-900 hover:text-primary-600">
                    {userDisplayName}
                  </Link>
                  <span className="text-gray-500 text-sm">created an event</span>
                  <span className="text-gray-400 text-xs">· {timeAgo}</span>
                </div>
                {activity.event_created?.event && (
                  <Link to={`/events/${activity.event_created.event.id}`} className="block">
                    <div className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                      {activity.event_created.event.thumbnail_url && (
                        <img
                          src={activity.event_created.event.thumbnail_url}
                          alt={activity.event_created.event.title}
                          className="w-16 h-16 rounded object-cover"
                        />
                      )}
                      <div className="flex-1 min-w-0">
                        <h4 className="font-semibold text-gray-900 truncate">{activity.event_created.event.title}</h4>
                        <p className="text-sm text-gray-600">{activity.event_created.event.dj_name}</p>
                        {activity.event_created.event.event_name && (
                          <p className="text-xs text-gray-500 mt-1">{activity.event_created.event.event_name}</p>
                        )}
                        {activity.event_created.event.venue_location && (
                          <p className="text-xs text-gray-500">📍 {activity.event_created.event.venue_location}</p>
                        )}
                      </div>
                      {activity.event_created.event.is_verified && (
                        <div className="text-green-600 text-sm font-medium">✓ Verified</div>
                      )}
                    </div>
                  </Link>
                )}
              </div>
            </div>
          </div>
        );

      case 'event_confirmed':
        return (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
            <div className="flex items-start space-x-4">
              <Link to={userLink} className="flex-shrink-0">
                <div className="w-12 h-12 rounded-full bg-primary-100 flex items-center justify-center text-primary-600 font-semibold">
                  {userDisplayName.charAt(0).toUpperCase()}
                </div>
              </Link>
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2 mb-2">
                  <Link to={userLink} className="font-semibold text-gray-900 hover:text-primary-600">
                    {userDisplayName}
                  </Link>
                  <span className="text-gray-500 text-sm">confirmed attendance at an event</span>
                  <span className="text-gray-400 text-xs">· {timeAgo}</span>
                </div>
                {activity.event_confirmed?.event && (
                  <Link to={`/events/${activity.event_confirmed.event.id}`} className="block">
                    <div className="flex items-center space-x-3 p-3 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors border border-blue-200">
                      {activity.event_confirmed.event.thumbnail_url && (
                        <img
                          src={activity.event_confirmed.event.thumbnail_url}
                          alt={activity.event_confirmed.event.title}
                          className="w-16 h-16 rounded object-cover"
                        />
                      )}
                      <div className="flex-1 min-w-0">
                        <h4 className="font-semibold text-gray-900 truncate">{activity.event_confirmed.event.title}</h4>
                        <p className="text-sm text-gray-600">{activity.event_confirmed.event.dj_name}</p>
                        {activity.event_confirmed.event.event_name && (
                          <p className="text-xs text-gray-500 mt-1">{activity.event_confirmed.event.event_name}</p>
                        )}
                        {activity.event_confirmed.event.venue_location && (
                          <p className="text-xs text-gray-500">📍 {activity.event_confirmed.event.venue_location}</p>
                        )}
                      </div>
                      <div className="text-blue-600 text-sm font-medium">✓ Confirmed</div>
                    </div>
                  </Link>
                )}
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="space-y-4">
      {activities.map((activity) => (
        <div key={`${activity.activity_type}-${activity.created_at}`}>
          {renderActivity(activity)}
        </div>
      ))}
    </div>
  );
};

export default ActivityFeed;
