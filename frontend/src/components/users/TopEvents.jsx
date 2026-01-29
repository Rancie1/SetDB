/**
 * Top Events component.
 * Displays a user's top 5 events (same pattern as Top Sets / Top Tracks).
 */

import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import * as usersService from '../../services/usersService';

const TopEvents = ({ userId, isOwnProfile }) => {
  const [topEvents, setTopEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTopEvents();
  }, [userId]);

  const loadTopEvents = async () => {
    setLoading(true);
    try {
      const response = await usersService.getUserTopEvents(userId);
      setTopEvents(response.data || []);
    } catch (error) {
      console.error('Failed to load top events:', error);
      setTopEvents([]);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="bg-gray-100 animate-pulse rounded-lg h-48"></div>
        ))}
      </div>
    );
  }

  if (topEvents.length === 0 && !isOwnProfile) return null;

  if (topEvents.length === 0) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
        <p className="text-gray-600 mb-2">No top events yet</p>
        <p className="text-gray-400 text-sm">
          Add events to your top 5 from event pages to display them here
        </p>
      </div>
    );
  }

  return (
    <div>
      <h3 className="text-xl font-bold mb-4">Top 5 Events</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {topEvents.map((event, index) => (
          <div key={event.id} className="relative">
            {isOwnProfile && (
              <div className="absolute top-2 left-2 z-10 bg-primary-600 text-white text-sm font-bold px-2 py-1 rounded shadow-lg">
                #{event.order || index + 1}
              </div>
            )}
            <Link
              to={`/events/${event.id}`}
              className="block bg-white rounded-lg border border-gray-200 overflow-hidden hover:shadow-md transition-shadow"
            >
              <div className="aspect-video bg-gray-200">
                {event.thumbnail_url ? (
                  <img src={event.thumbnail_url} alt={event.title} className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full flex items-center justify-center text-gray-400 text-4xl">🎤</div>
                )}
              </div>
              <div className="p-3">
                <p className="text-sm font-medium text-gray-900 line-clamp-2">{event.event_name || event.title}</p>
                <p className="text-xs text-gray-600 mt-1">{event.dj_name}</p>
                {event.venue_location && (
                  <p className="text-xs text-gray-500 mt-1">📍 {event.venue_location}</p>
                )}
              </div>
            </Link>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TopEvents;
