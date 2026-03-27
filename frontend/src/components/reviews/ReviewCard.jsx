/**
 * Review card component.
 *
 * Displays a single review with user info and content.
 */

import { Link } from 'react-router-dom';
import useAuthStore from '../../store/authStore';

const ReviewCard = ({ review, onDelete }) => {
  const { user: currentUser } = useAuthStore();
  const isOwner = currentUser && currentUser.id === review.user_id;

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  return (
    <div className="bg-surface-800 rounded-xl border border-white/5 p-6">
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          {review.user?.avatar_url ? (
            <img
              src={review.user.avatar_url}
              alt={review.user.username}
              className="w-10 h-10 rounded-full"
            />
          ) : (
            <div className="w-10 h-10 rounded-full bg-primary-600/20 flex items-center justify-center">
              <span className="text-primary-400 text-sm font-medium">
                {review.user?.username?.[0]?.toUpperCase() || '?'}
              </span>
            </div>
          )}
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <Link
                to={`/users/${review.user_id}`}
                className="font-semibold text-slate-100 hover:text-primary-400 transition-colors"
              >
                {review.user?.username || 'Unknown User'}
              </Link>
              {review.user_rating && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-accent-500/20 border border-accent-500/30 rounded-md text-accent-400 text-sm font-semibold">
                  {review.user_rating.toFixed(1)}
                </span>
              )}
            </div>
            <p className="text-sm text-slate-500">{formatDate(review.created_at)}</p>
          </div>
        </div>
        {isOwner && onDelete && (
          <button
            onClick={() => onDelete(review.id)}
            className="text-red-400 hover:text-red-300 text-sm font-medium cursor-pointer"
          >
            Delete
          </button>
        )}
      </div>

      {/* Content */}
      <div>
        {review.contains_spoilers && (
          <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-2 mb-3">
            <p className="text-yellow-400 text-sm font-medium">Contains Spoilers</p>
          </div>
        )}
        <p className="text-slate-300 whitespace-pre-wrap text-sm leading-relaxed">{review.content}</p>
      </div>

      {/* Footer */}
      {review.updated_at !== review.created_at && (
        <p className="text-xs text-slate-600 mt-3">
          Edited {formatDate(review.updated_at)}
        </p>
      )}
    </div>
  );
};

export default ReviewCard;
