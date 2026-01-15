/**
 * Link set to live event form component.
 * 
 * Allows users to search for and link a set to an existing live event.
 */

import { useState, useEffect } from 'react';
import * as setsService from '../../services/setsService';
import { Link } from 'react-router-dom';

const LinkToLiveEventForm = ({ set, onSuccess, onCancel, loading: externalLoading }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [liveEvents, setLiveEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedEventId, setSelectedEventId] = useState(null);

  useEffect(() => {
    if (searchQuery.trim()) {
      const timeoutId = setTimeout(() => {
        searchLiveEvents();
      }, 300); // Debounce search

      return () => clearTimeout(timeoutId);
    } else {
      setLiveEvents([]);
    }
  }, [searchQuery]);

  const searchLiveEvents = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await setsService.searchLiveEvents(
        { search: searchQuery },
        1,
        10
      );
      setLiveEvents(response.data.items || []);
    } catch (err) {
      console.error('Failed to search live events:', err);
      setError('Failed to search live events');
    } finally {
      setLoading(false);
    }
  };

  const handleLink = async () => {
    if (!selectedEventId) return;

    try {
      await setsService.linkSetToLiveEvent(set.id, selectedEventId);
      if (onSuccess) {
        onSuccess();
      }
    } catch (err) {
      console.error('Failed to link set:', err);
      alert(err.response?.data?.detail || 'Failed to link set to live event');
    }
  };

  const formatEventDate = (dateString) => {
    if (!dateString) return 'Date unknown';
    try {
      return new Date(dateString).toLocaleDateString();
    } catch {
      return dateString;
    }
  };

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
      <h3 className="text-lg font-semibold text-blue-900 mb-3">
        Link to Existing Live Event
      </h3>
      <p className="text-sm text-blue-700 mb-4">
        Search for an existing live event to link this set as a recording.
      </p>

      <div className="space-y-3">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Search Live Events
          </label>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by event name, venue, or DJ..."
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {loading && (
          <div className="text-sm text-gray-600">Searching...</div>
        )}

        {error && (
          <div className="text-sm text-red-600">{error}</div>
        )}

        {liveEvents.length > 0 && (
          <div className="border border-gray-200 rounded-md max-h-60 overflow-y-auto">
            {liveEvents.map((event) => (
              <div
                key={event.id}
                className={`p-3 border-b border-gray-200 last:border-b-0 cursor-pointer hover:bg-blue-100 ${
                  selectedEventId === event.id ? 'bg-blue-200' : ''
                }`}
                onClick={() => setSelectedEventId(event.id)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="font-medium text-gray-900">
                      {event.event_name || event.title}
                    </div>
                    <div className="text-sm text-gray-600">
                      {event.dj_name}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {formatEventDate(event.event_date)}
                      {event.venue_location && ` • ${event.venue_location}`}
                    </div>
                  </div>
                  <Link
                    to={`/events/${event.id}`}
                    onClick={(e) => e.stopPropagation()}
                    className="text-xs text-blue-600 hover:text-blue-800 ml-2"
                  >
                    View →
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}

        {searchQuery.trim() && !loading && liveEvents.length === 0 && (
          <div className="text-sm text-gray-600">
            No live events found. Try a different search term.
          </div>
        )}

        <div className="flex gap-2 pt-2">
          <button
            onClick={handleLink}
            disabled={!selectedEventId || externalLoading}
            className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-medium rounded-md transition-colors"
          >
            {externalLoading ? 'Linking...' : 'Link to Selected Event'}
          </button>
          <button
            onClick={onCancel}
            disabled={externalLoading}
            className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 font-medium rounded-md transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};

export default LinkToLiveEventForm;
