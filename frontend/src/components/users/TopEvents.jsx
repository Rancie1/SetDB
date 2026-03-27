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
          <div key={i} className="bg-surface-700 animate-pulse rounded-xl h-48"></div>
        ))}
      </div>
    );
  }

  if (topEvents.length === 0 && !isOwnProfile) return null;

  if (topEvents.length === 0) {
    return (
      <div className="bg-surface-800 border border-white/5 rounded-xl p-8 text-center">
        <p className="text-slate-400 mb-1">No top events yet</p>
        <p className="text-slate-500 text-sm">Add events to your top 5 from event pages to display them here</p>
      </div>
    );
  }

  return (
    <div>
      <h3 className="text-lg font-semibold mb-4 text-slate-100">Top 5 Events</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {topEvents.map((event, index) => (
          <div key={event.id} className="relative">
            {isOwnProfile && (
              <div className="absolute top-2 left-2 z-10 bg-primary-600 text-white text-xs font-bold px-2 py-1 rounded-md shadow-lg">
                #{event.order || index + 1}
              </div>
            )}
            <Link
              to={`/events/${event.id}`}
              className="block bg-surface-800 rounded-xl border border-white/5 overflow-hidden hover:border-primary-500/30 hover:bg-surface-700 transition-colors cursor-pointer"
            >
              <div className="aspect-video bg-surface-700">
                {event.thumbnail_url ? (
                  <img src={event.thumbnail_url} alt={event.title} className="w-full h-full object-cover" />
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <svg viewBox="0 0 24 24" fill="currentColor" className="w-10 h-10 text-slate-600">
                      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 14.5v-9l6 4.5-6 4.5z"/>
                    </svg>
                  </div>
                )}
              </div>
              <div className="p-3">
                <p className="text-sm font-medium text-slate-100 line-clamp-2">{event.event_name || event.title}</p>
                <p className="text-xs text-slate-400 mt-1">{event.dj_name}</p>
                {event.venue_location && (
                  <p className="text-xs text-slate-500 mt-1 truncate">{event.venue_location}</p>
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
