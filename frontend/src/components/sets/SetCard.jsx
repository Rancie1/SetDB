/**
 * Set card component.
 *
 * Displays a single DJ set in a card format.
 */

import { Link } from 'react-router-dom';
import ArtistLink from '../shared/ArtistLink';

const SetCard = ({ set }) => {
  if (!set) return null;

  const formatDuration = (minutes) => {
    if (!minutes || minutes === null || minutes === undefined) {
      return null;
    }
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    if (hours > 0) {
      return `${hours}h ${mins}m`;
    }
    return `${mins}m`;
  };

  const getSourceBadge = (sourceType) => {
    switch (sourceType?.toLowerCase()) {
      case 'youtube':
        return { label: 'YouTube', className: 'bg-red-500/20 text-red-300 border border-red-500/30' };
      case 'soundcloud':
        return { label: 'SoundCloud', className: 'bg-orange-500/20 text-orange-300 border border-orange-500/30' };
      case 'live':
        return { label: 'Live', className: 'bg-violet-500/20 text-violet-300 border border-violet-500/30' };
      default:
        return { label: sourceType || 'Unknown', className: 'bg-white/10 text-slate-300 border border-white/10' };
    }
  };

  const getPublishDate = (set) => {
    if (set.source_type?.toLowerCase() === 'youtube' && set.extra_metadata?.published_at) {
      return new Date(set.extra_metadata.published_at);
    }
    if (set.source_type?.toLowerCase() === 'soundcloud' && set.extra_metadata?.published_at) {
      return new Date(set.extra_metadata.published_at);
    }
    if (set.source_type?.toLowerCase() === 'soundcloud') {
      return null;
    }
    return set.created_at ? new Date(set.created_at) : null;
  };

  const detailUrl = `/sets/${set.id}`;
  const sourceBadge = getSourceBadge(set.source_type);

  return (
    <Link
      to={detailUrl}
      className="block bg-surface-800 rounded-xl border border-white/5 hover:border-primary-500/40 hover:bg-surface-700 transition-all duration-200 overflow-hidden cursor-pointer group"
    >
      {/* Thumbnail */}
      <div className="aspect-video bg-surface-700 relative overflow-hidden">
        {set.thumbnail_url ? (
          <>
            <img
              src={`${set.thumbnail_url}${set.thumbnail_url.includes('?') ? '&' : '?'}v=${new Date(set.updated_at || set.created_at).getTime()}`}
              alt={set.title}
              className="w-full h-full object-cover group-hover:scale-[1.02] transition-transform duration-300"
              onError={(e) => {
                const img = e.target;
                const src = img.src.split('?')[0];
                if (src.includes('-original.')) {
                  const fallbackUrl = src.replace('-original.', '-large.');
                  if (!img.dataset.fallbackTried) {
                    img.dataset.fallbackTried = 'true';
                    img.src = fallbackUrl;
                    return;
                  }
                }
                img.style.display = 'none';
                if (!img.parentElement.querySelector('.thumbnail-placeholder')) {
                  const placeholder = document.createElement('div');
                  placeholder.className = 'thumbnail-placeholder w-full h-full flex items-center justify-center absolute inset-0 bg-surface-700';
                  placeholder.innerHTML = `<svg viewBox="0 0 24 24" fill="currentColor" class="w-10 h-10 text-slate-600"><path d="M12 3v10.55A4 4 0 1 0 14 17V7h4V3h-6z"/></svg>`;
                  img.parentElement.appendChild(placeholder);
                }
              }}
            />
            <div className="thumbnail-placeholder w-full h-full flex items-center justify-center absolute inset-0 bg-surface-700 hidden">
              <svg viewBox="0 0 24 24" fill="currentColor" className="w-10 h-10 text-slate-600">
                <path d="M12 3v10.55A4 4 0 1 0 14 17V7h4V3h-6z"/>
              </svg>
            </div>
          </>
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-surface-700">
            <svg viewBox="0 0 24 24" fill="currentColor" className="w-10 h-10 text-slate-600">
              <path d="M12 3v10.55A4 4 0 1 0 14 17V7h4V3h-6z"/>
            </svg>
          </div>
        )}

        {/* Gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-transparent pointer-events-none" />

        {/* Badges */}
        <div className="absolute top-2 right-2 flex flex-col gap-1 items-end">
          <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium ${sourceBadge.className}`}>
            {sourceBadge.label}
          </span>
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        <h3 className="text-sm font-semibold text-slate-100 mb-1 line-clamp-2 leading-snug">
          {set.title}
        </h3>
        <p className="text-xs text-slate-400 mb-3">
          <ArtistLink name={set.dj_name} />
        </p>

        <div className="flex items-center justify-between text-xs text-slate-500">
          {formatDuration(set.duration_minutes) && (
            <span>{formatDuration(set.duration_minutes)}</span>
          )}
          {getPublishDate(set) && (
            <span className={formatDuration(set.duration_minutes) ? '' : 'ml-auto'}>
              {getPublishDate(set).toLocaleDateString()}
            </span>
          )}
        </div>

        {set.description && (
          <p className="mt-2 text-xs text-slate-500 line-clamp-2">
            {set.description}
          </p>
        )}
      </div>
    </Link>
  );
};

export default SetCard;
