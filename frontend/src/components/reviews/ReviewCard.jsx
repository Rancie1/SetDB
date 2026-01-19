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
    <div className="bg-white rounded-lg border border-gray-200 p-6">
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
            <div className="w-10 h-10 rounded-full bg-gray-300 flex items-center justify-center">
              <span className="text-gray-600 text-sm font-medium">
                {review.user?.username?.[0]?.toUpperCase() || '?'}
              </span>
            </div>
          )}
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <Link
                to={`/users/${review.user_id}`}
                className="font-semibold text-gray-900 hover:text-primary-600"
              >
                {review.user?.username || 'Unknown User'}
              </Link>
              {review.user_rating && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-yellow-50 border border-yellow-200 rounded-md text-yellow-700 text-sm font-semibold">
                  <span className="text-yellow-500">★</span>
                  <span>{review.user_rating.toFixed(1)}</span>
                </span>
              )}
            </div>
            <p className="text-sm text-gray-500">{formatDate(review.created_at)}</p>
          </div>
        </div>
        {isOwner && onDelete && (
          <button
            onClick={() => onDelete(review.id)}
            className="text-red-600 hover:text-red-700 text-sm font-medium"
          >
            Delete
          </button>
        )}
      </div>

      {/* Content */}
      <div className="prose prose-sm max-w-none">
        {review.contains_spoilers && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-md p-2 mb-3">
            <p className="text-yellow-800 text-sm font-medium">⚠️ Contains Spoilers</p>
          </div>
        )}
        <p className="text-gray-700 whitespace-pre-wrap">{review.content}</p>
      </div>

      {/* Footer */}
      {review.updated_at !== review.created_at && (
        <p className="text-xs text-gray-400 mt-3">
          Edited {formatDate(review.updated_at)}
        </p>
      )}
    </div>
  );
};

export default ReviewCard;
