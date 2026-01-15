/**
 * Review form component.
 * 
 * Allows users to create or edit reviews.
 */

import { useState } from 'react';
import * as reviewsService from '../../services/reviewsService';

const ReviewForm = ({ setId, existingReview, onSubmit, onCancel }) => {
  const [content, setContent] = useState(existingReview?.content || '');
  const [containsSpoilers, setContainsSpoilers] = useState(existingReview?.contains_spoilers || false);
  const [isPublic, setIsPublic] = useState(existingReview?.is_public ?? true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!content.trim()) {
      setError('Review content cannot be empty');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      if (existingReview) {
        await reviewsService.updateReview(existingReview.id, {
          content,
          contains_spoilers: containsSpoilers,
          is_public: isPublic
        });
      } else {
        await reviewsService.createReview({
          set_id: setId,
          content,
          contains_spoilers: containsSpoilers,
          is_public: isPublic
        });
      }
      onSubmit();
      setContent('');
      setContainsSpoilers(false);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save review');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-lg border border-gray-200 p-6">
      <h3 className="text-lg font-semibold mb-4">
        {existingReview ? 'Edit Review' : 'Write a Review'}
      </h3>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md mb-4">
          {error}
        </div>
      )}

      <div className="mb-4">
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Share your thoughts about this set..."
          rows={6}
          className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          required
        />
      </div>

      <div className="flex items-center space-x-6 mb-4">
        <label className="flex items-center">
          <input
            type="checkbox"
            checked={containsSpoilers}
            onChange={(e) => setContainsSpoilers(e.target.checked)}
            className="mr-2"
          />
          <span className="text-sm text-gray-700">Contains spoilers</span>
        </label>
        <label className="flex items-center">
          <input
            type="checkbox"
            checked={isPublic}
            onChange={(e) => setIsPublic(e.target.checked)}
            className="mr-2"
          />
          <span className="text-sm text-gray-700">Public review</span>
        </label>
      </div>

      <div className="flex items-center space-x-3">
        <button
          type="submit"
          disabled={loading}
          className="bg-primary-600 hover:bg-primary-700 text-white font-medium px-6 py-2 rounded-md disabled:opacity-50"
        >
          {loading ? 'Saving...' : existingReview ? 'Update Review' : 'Post Review'}
        </button>
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium px-6 py-2 rounded-md"
          >
            Cancel
          </button>
        )}
      </div>
    </form>
  );
};

export default ReviewForm;
