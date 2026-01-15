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

  const getSetTypeLabel = (set) => {
    if (set.source_type?.toLowerCase() === 'live') {
      return 'Live Set';
    }
    return 'Upload';
  };

  const getSetTypeColor = (set) => {
    if (set.source_type?.toLowerCase() === 'live') {
      return 'bg-purple-100 text-purple-800 border-purple-300';
    }
    return 'bg-gray-100 text-gray-800 border-gray-300';
  };

  const getPublishDate = (set) => {
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

  // All sets (including live sets) go to the sets detail page
  const detailUrl = `/sets/${set.id}`;

  return (
    <Link
      to={detailUrl}
      className="block bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow overflow-hidden"
    >
      {/* Thumbnail */}
      <div className="aspect-video bg-gray-200 relative overflow-hidden">
        {set.thumbnail_url ? (
          <>
            <img
              src={`${set.thumbnail_url}${set.thumbnail_url.includes('?') ? '&' : '?'}v=${new Date(set.updated_at || set.created_at).getTime()}`}
              alt={set.title}
              className="w-full h-full object-cover"
              onError={(e) => {
                // Try fallback to -large.jpg if -original.jpg fails
                const img = e.target;
                const src = img.src.split('?')[0]; // Remove query params
                if (src.includes('-original.')) {
                  const fallbackUrl = src.replace('-original.', '-large.');
                  // Prevent infinite loop if fallback also fails
                  if (!img.dataset.fallbackTried) {
                    img.dataset.fallbackTried = 'true';
                    img.src = fallbackUrl;
                    return;
                  }
                }
                // If fallback also fails or not applicable, hide image and show placeholder
                img.style.display = 'none';
                if (!img.parentElement.querySelector('.thumbnail-placeholder')) {
                  const placeholder = document.createElement('div');
                  placeholder.className = 'thumbnail-placeholder w-full h-full flex items-center justify-center text-gray-400 absolute inset-0';
                  placeholder.innerHTML = '<span class="text-4xl">🎧</span>';
                  img.parentElement.appendChild(placeholder);
                }
              }}
            />
            {/* Placeholder that shows if image fails (hidden by default) */}
            <div className="thumbnail-placeholder w-full h-full flex items-center justify-center text-gray-400 absolute inset-0 hidden">
              <span className="text-4xl">🎧</span>
            </div>
          </>
        ) : (
          <div className="w-full h-full flex items-center justify-center text-gray-400">
            <span className="text-4xl">🎧</span>
          </div>
        )}
        {/* Badges */}
        <div className="absolute top-2 right-2 flex flex-col gap-1 items-end">
          {/* Set type badge (Live Set / Upload) */}
          <span
            className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium border ${getSetTypeColor(set)}`}
          >
            {getSetTypeLabel(set)}
          </span>
          
          {/* Source platform badge */}
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

        {/* Live set with recording indicator */}
        {set.source_type?.toLowerCase() === 'live' && set.recording_url && (
          <div className="mb-2">
            <p className="text-xs text-purple-600 font-medium">
              🎵 Has Recording
            </p>
          </div>
        )}

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

