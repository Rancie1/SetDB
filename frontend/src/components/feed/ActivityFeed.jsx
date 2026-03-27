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
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;
  const weeks = Math.floor(days / 7);
  if (weeks < 4) return `${weeks}w ago`;
  const months = Math.floor(days / 30);
  if (months < 12) return `${months}mo ago`;
  return `${Math.floor(days / 365)}y ago`;
};

const Avatar = ({ name }) => (
  <div className="w-10 h-10 rounded-full bg-primary-600/20 flex items-center justify-center text-primary-400 font-semibold text-sm flex-shrink-0">
    {name?.charAt(0).toUpperCase()}
  </div>
);

const ActivityCard = ({ children }) => (
  <div className="bg-surface-800 rounded-xl border border-white/5 p-5 hover:border-white/10 transition-colors">
    {children}
  </div>
);

const ActivityHeader = ({ userLink, userName, action, timeAgo }) => (
  <div className="flex items-center gap-2 mb-3">
    <Link to={userLink} className="font-semibold text-slate-100 hover:text-primary-400 transition-colors text-sm">
      {userName}
    </Link>
    <span className="text-slate-500 text-sm">{action}</span>
    <span className="text-slate-600 text-xs ml-auto">{timeAgo}</span>
  </div>
);

const MediaPreview = ({ to, thumbnail, title, subtitle, extra, accent }) => (
  <Link to={to} className={`flex items-center gap-3 p-3 rounded-lg transition-colors ${
    accent === 'gold'
      ? 'bg-primary-600/10 border border-primary-500/20 hover:bg-primary-600/15'
      : accent === 'blue'
      ? 'bg-indigo-500/10 border border-indigo-500/20 hover:bg-indigo-500/15'
      : 'bg-surface-700 hover:bg-surface-600'
  }`}>
    {thumbnail && (
      <img src={thumbnail} alt={title} className="w-14 h-14 rounded object-cover flex-shrink-0" />
    )}
    <div className="flex-1 min-w-0">
      <h4 className="text-sm font-semibold text-slate-100 truncate">{title}</h4>
      {subtitle && <p className="text-xs text-slate-400 mt-0.5">{subtitle}</p>}
      {extra && <p className="text-xs text-slate-500 mt-0.5">{extra}</p>}
    </div>
  </Link>
);

const ActivityFeed = ({ activities, loading, error }) => {
  if (loading) {
    return (
      <div className="space-y-3">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="bg-surface-800 rounded-xl border border-white/5 p-5 animate-pulse">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-full bg-surface-700"></div>
              <div className="h-3 bg-surface-700 rounded w-1/3"></div>
            </div>
            <div className="h-3 bg-surface-700 rounded w-3/4 mb-2"></div>
            <div className="h-3 bg-surface-700 rounded w-1/2"></div>
          </div>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-4">
        <p className="text-red-400 text-sm">Error loading activity feed: {error}</p>
      </div>
    );
  }

  if (!activities || activities.length === 0) {
    return (
      <div className="bg-surface-800 rounded-xl border border-white/5 p-12 text-center">
        <p className="text-slate-400 text-lg mb-1">No activity yet</p>
        <p className="text-slate-500 text-sm">Start reviewing, rating, or adding tracks to your top 5!</p>
      </div>
    );
  }

  const renderActivity = (activity) => {
    const timeAgo = formatTimeAgo(activity.created_at);
    const userLink = `/users/${activity.user.id}`;
    const userName = activity.user.display_name || activity.user.username;

    switch (activity.activity_type) {
      case 'set_review':
        return (
          <ActivityCard>
            <div className="flex items-start gap-3">
              <Link to={userLink}><Avatar name={userName} /></Link>
              <div className="flex-1 min-w-0">
                <ActivityHeader userLink={userLink} userName={userName} action="reviewed a set" timeAgo={timeAgo} />
                {activity.set_review?.set && (
                  <div className="mb-3">
                    <MediaPreview
                      to={`/sets/${activity.set_review.set.id}`}
                      thumbnail={activity.set_review.set.thumbnail_url}
                      title={activity.set_review.set.title}
                      subtitle={activity.set_review.set.dj_name}
                    />
                  </div>
                )}
                <p className="text-slate-300 text-sm whitespace-pre-wrap">{activity.set_review?.content}</p>
                {activity.set_review?.user_rating && (
                  <p className="mt-2 text-xs text-slate-500">Rated {activity.set_review.user_rating} / 5</p>
                )}
              </div>
            </div>
          </ActivityCard>
        );

      case 'set_rating':
        return (
          <ActivityCard>
            <div className="flex items-start gap-3">
              <Link to={userLink}><Avatar name={userName} /></Link>
              <div className="flex-1 min-w-0">
                <ActivityHeader userLink={userLink} userName={userName} action="rated a set" timeAgo={timeAgo} />
                {activity.set_rating?.set && (
                  <MediaPreview
                    to={`/sets/${activity.set_rating.set.id}`}
                    thumbnail={activity.set_rating.set.thumbnail_url}
                    title={activity.set_rating.set.title}
                    subtitle={activity.set_rating.set.dj_name}
                    extra={`${activity.set_rating.rating} / 5`}
                  />
                )}
              </div>
            </div>
          </ActivityCard>
        );

      case 'track_review':
        return (
          <ActivityCard>
            <div className="flex items-start gap-3">
              <Link to={userLink}><Avatar name={userName} /></Link>
              <div className="flex-1 min-w-0">
                <ActivityHeader userLink={userLink} userName={userName} action="reviewed a track" timeAgo={timeAgo} />
                {activity.track_review?.track && (
                  <div className="mb-3">
                    <MediaPreview
                      to={`/tracks/${activity.track_review.track.id}`}
                      thumbnail={activity.track_review.track.thumbnail_url}
                      title={activity.track_review.track.track_name}
                      subtitle={activity.track_review.track.artist_name || 'Unknown Artist'}
                    />
                  </div>
                )}
                <p className="text-slate-300 text-sm whitespace-pre-wrap">{activity.track_review?.content}</p>
                {activity.track_review?.user_rating && (
                  <p className="mt-2 text-xs text-slate-500">Rated {activity.track_review.user_rating} / 5</p>
                )}
              </div>
            </div>
          </ActivityCard>
        );

      case 'track_rating':
        return (
          <ActivityCard>
            <div className="flex items-start gap-3">
              <Link to={userLink}><Avatar name={userName} /></Link>
              <div className="flex-1 min-w-0">
                <ActivityHeader userLink={userLink} userName={userName} action="rated a track" timeAgo={timeAgo} />
                {activity.track_rating?.track && (
                  <MediaPreview
                    to={`/tracks/${activity.track_rating.track.id}`}
                    thumbnail={activity.track_rating.track.thumbnail_url}
                    title={activity.track_rating.track.track_name}
                    subtitle={activity.track_rating.track.artist_name || 'Unknown Artist'}
                    extra={`${activity.track_rating.rating} / 5`}
                  />
                )}
              </div>
            </div>
          </ActivityCard>
        );

      case 'top_track':
        return (
          <ActivityCard>
            <div className="flex items-start gap-3">
              <Link to={userLink}><Avatar name={userName} /></Link>
              <div className="flex-1 min-w-0">
                <ActivityHeader userLink={userLink} userName={userName} action="added a track to their top 5" timeAgo={timeAgo} />
                {activity.top_track?.track && (
                  <div className="flex items-center gap-3">
                    <span className="text-lg font-bold text-primary-400 w-8 text-center flex-shrink-0">
                      #{activity.top_track.order}
                    </span>
                    <div className="flex-1 min-w-0">
                      <MediaPreview
                        to={`/tracks/${activity.top_track.track.id}`}
                        thumbnail={activity.top_track.track.thumbnail_url}
                        title={activity.top_track.track.track_name}
                        subtitle={activity.top_track.track.artist_name || 'Unknown Artist'}
                        accent="gold"
                      />
                    </div>
                  </div>
                )}
              </div>
            </div>
          </ActivityCard>
        );

      case 'top_set':
        return (
          <ActivityCard>
            <div className="flex items-start gap-3">
              <Link to={userLink}><Avatar name={userName} /></Link>
              <div className="flex-1 min-w-0">
                <ActivityHeader userLink={userLink} userName={userName} action="added a set to their top 5" timeAgo={timeAgo} />
                {activity.top_set?.set && (
                  <div className="flex items-center gap-3">
                    <span className="text-lg font-bold text-primary-400 w-8 text-center flex-shrink-0">
                      #{activity.top_set.order}
                    </span>
                    <div className="flex-1 min-w-0">
                      <MediaPreview
                        to={`/sets/${activity.top_set.set.id}`}
                        thumbnail={activity.top_set.set.thumbnail_url}
                        title={activity.top_set.set.title}
                        subtitle={activity.top_set.set.dj_name}
                        accent="gold"
                      />
                    </div>
                  </div>
                )}
              </div>
            </div>
          </ActivityCard>
        );

      case 'event_created':
        return (
          <ActivityCard>
            <div className="flex items-start gap-3">
              <Link to={userLink}><Avatar name={userName} /></Link>
              <div className="flex-1 min-w-0">
                <ActivityHeader userLink={userLink} userName={userName} action="created an event" timeAgo={timeAgo} />
                {activity.event_created?.event && (
                  <MediaPreview
                    to={`/events/${activity.event_created.event.id}`}
                    thumbnail={activity.event_created.event.thumbnail_url}
                    title={activity.event_created.event.title}
                    subtitle={activity.event_created.event.dj_name}
                    extra={activity.event_created.event.venue_location}
                  />
                )}
              </div>
            </div>
          </ActivityCard>
        );

      case 'event_confirmed':
        return (
          <ActivityCard>
            <div className="flex items-start gap-3">
              <Link to={userLink}><Avatar name={userName} /></Link>
              <div className="flex-1 min-w-0">
                <ActivityHeader userLink={userLink} userName={userName} action="confirmed attendance at an event" timeAgo={timeAgo} />
                {activity.event_confirmed?.event && (
                  <MediaPreview
                    to={`/events/${activity.event_confirmed.event.id}`}
                    thumbnail={activity.event_confirmed.event.thumbnail_url}
                    title={activity.event_confirmed.event.title}
                    subtitle={activity.event_confirmed.event.dj_name}
                    extra={activity.event_confirmed.event.venue_location}
                    accent="blue"
                  />
                )}
              </div>
            </div>
          </ActivityCard>
        );

      default:
        return null;
    }
  };

  return (
    <div className="space-y-3">
      {activities.map((activity) => (
        <div key={`${activity.activity_type}-${activity.created_at}`}>
          {renderActivity(activity)}
        </div>
      ))}
    </div>
  );
};

export default ActivityFeed;
