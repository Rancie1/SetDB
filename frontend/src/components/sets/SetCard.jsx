/**
 * Set card component.
 * 
 * Displays a single DJ set in a card format.
 */

import { Link } from 'react-router-dom';

const SetCard = ({ set }) => {
  if (!set) return null;

  const formatDuration = (minutes) => {
    if (!minutes || minutes === null || minutes === undefined) {
      return null; // Return null instead of "Unknown" so we can conditionally render
    }
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours > 0) {
      return `${hours}h ${mins}m`;
    }
    return `${mins}m`;
  };

  const getSourceIcon = (sourceType) => {
    switch (sourceType?.toLowerCase()) {
      case 'youtube':
        return '▶️';
      case 'soundcloud':
        return '🎵';
      case 'live':
        return '🎤';
      default:
        return '🎧';
    }
  };

  const getSourceColor = (sourceType) => {
    switch (sourceType?.toLowerCase()) {
      case 'youtube':
        return 'bg-red-100 text-red-800';
      case 'soundcloud':
        return 'bg-orange-100 text-orange-800';
      case 'live':
        return 'bg-purple-100 text-purple-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getPublishDate = (set) => {
    // For live sets, use event_date if available
    if (set.source_type?.toLowerCase() === 'live' && set.event_date) {
      return new Date(set.event_date);
    }
    
    // For YouTube, get publishedAt from metadata
    if (set.source_type?.toLowerCase() === 'youtube' && set.extra_metadata?.published_at) {
      return new Date(set.extra_metadata.published_at);
    }
    
    // For SoundCloud, get published_at from metadata (if using full API)
    if (set.source_type?.toLowerCase() === 'soundcloud' && set.extra_metadata?.published_at) {
      return new Date(set.extra_metadata.published_at);
    }
    
    // For SoundCloud without API, return null (no date shown)
    if (set.source_type?.toLowerCase() === 'soundcloud') {
      return null;
    }
    
    // Fallback to created_at if no publish date available
    return set.created_at ? new Date(set.created_at) : null;
  };

  return (
    <Link
      to={`/sets/${set.id}`}
      className="block bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow overflow-hidden"
    >
      {/* Thumbnail */}
      <div className="aspect-video bg-gray-200 relative overflow-hidden">
        {set.thumbnail_url ? (
          <img
            src={set.thumbnail_url}
            alt={set.title}
            className="w-full h-full object-cover"
            onError={(e) => {
              e.target.style.display = 'none';
            }}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-400">
            <span className="text-4xl">🎧</span>
          </div>
        )}
        {/* Source badge */}
        <div className="absolute top-2 right-2">
          <span
            className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium ${getSourceColor(
              set.source_type
            )}`}
          >
            <span className="mr-1">{getSourceIcon(set.source_type)}</span>
            {set.source_type || 'Unknown'}
          </span>
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-1 line-clamp-2">
          {set.title}
        </h3>
        <p className="text-sm text-gray-600 mb-2">{set.dj_name}</p>

        {/* Metadata */}
        <div className="flex items-center justify-between text-xs text-gray-500">
          {formatDuration(set.duration_minutes) && (
            <span>{formatDuration(set.duration_minutes)}</span>
          )}
          {getPublishDate(set) && (
            <span className={formatDuration(set.duration_minutes) ? '' : 'ml-auto'}>
              {getPublishDate(set).toLocaleDateString()}
            </span>
          )}
        </div>

        {/* Description preview */}
        {set.description && (
          <p className="mt-2 text-sm text-gray-600 line-clamp-2">
            {set.description}
          </p>
        )}
      </div>
    </Link>
  );
};

export default SetCard;

