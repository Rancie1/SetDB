/**
 * Events page component.
 *
 * Displays live events and allows users to browse and search events.
 */

import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import * as eventsService from '../services/eventsService';
import useAuthStore from '../store/authStore';

const EventsPage = () => {
  const { isAuthenticated } = useAuthStore();
  const navigate = useNavigate();
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [pagination, setPagination] = useState({
    page: 1,
    limit: 20,
    total: 0,
    pages: 0,
  });

  useEffect(() => {
    fetchEvents();
  }, []);

  const fetchEvents = async (search = '', page = 1) => {
    setLoading(true);
    setError(null);
    try {
      const response = await eventsService.getEvents({ search }, page, pagination.limit);
      const { items, total, pages } = response.data;
      setEvents(items || []);
      setPagination({ ...pagination, page, total, pages });
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch events');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    fetchEvents(searchQuery, 1);
  };

  const formatEventDate = (dateString) => {
    if (!dateString) return null;
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      });
    } catch {
      return dateString;
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold mb-2 text-slate-100">Events</h1>
          <p className="text-slate-400">Browse and discover live DJ events. View event details and their recordings.</p>
        </div>
        {isAuthenticated && (
          <Link
            to="/events/create"
            className="px-6 py-2 bg-primary-600 hover:bg-primary-500 text-white font-medium rounded-xl transition-colors"
          >
            + Create Event
          </Link>
        )}
      </div>

      {/* Search Bar */}
      <div className="mb-6">
        <form onSubmit={handleSearch} className="flex gap-3">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search events by name, DJ, or venue..."
            className="flex-1 px-4 py-3 bg-surface-800 border border-white/10 text-slate-100 placeholder-slate-500 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none text-sm"
          />
          <button
            type="submit"
            className="bg-primary-600 hover:bg-primary-500 text-white font-medium px-6 py-3 rounded-xl transition-colors cursor-pointer"
          >
            Search
          </button>
          {searchQuery && (
            <button
              type="button"
              onClick={() => { setSearchQuery(''); fetchEvents('', 1); }}
              className="bg-surface-700 hover:bg-surface-600 text-slate-300 font-medium px-4 py-3 rounded-xl border border-white/5 transition-colors cursor-pointer"
            >
              Clear
            </button>
          )}
        </form>
      </div>

      {/* Events List */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-slate-100">
            {searchQuery ? 'Search Results' : 'All Events'}
          </h2>
          {pagination.total > 0 && (
            <p className="text-sm text-slate-500">
              Showing {events.length} of {pagination.total} events
            </p>
          )}
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="bg-surface-700 animate-pulse rounded-xl h-64"></div>
            ))}
          </div>
        ) : error ? (
          <div className="bg-red-500/10 border border-red-500/20 text-red-400 px-4 py-3 rounded-xl">
            {error}
          </div>
        ) : events.length === 0 ? (
          <div className="bg-surface-800 border border-white/5 rounded-xl p-12 text-center">
            <p className="text-slate-400 text-lg mb-2">No events found</p>
            <p className="text-slate-500 text-sm">
              {searchQuery ? 'Try a different search term.' : 'Events will appear here once they are created.'}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {events.map((event) => (
              <Link
                key={event.id}
                to={`/events/${event.id}`}
                className="block bg-surface-800 rounded-xl border border-white/5 hover:border-primary-500/30 hover:bg-surface-700 transition-colors overflow-hidden cursor-pointer"
              >
                {/* Thumbnail */}
                <div className="aspect-video bg-surface-700 relative overflow-hidden">
                  {event.thumbnail_url ? (
                    <img
                      src={event.thumbnail_url}
                      alt={event.title}
                      className="w-full h-full object-cover"
                      onError={(e) => { e.target.style.display = 'none'; }}
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <svg viewBox="0 0 24 24" fill="currentColor" className="w-12 h-12 text-slate-600">
                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 14.5v-9l6 4.5-6 4.5z"/>
                      </svg>
                    </div>
                  )}
                  <div className="absolute top-2 right-2">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded-lg text-xs font-medium border ${
                      event.is_verified
                        ? 'bg-green-500/20 text-green-300 border-green-500/30'
                        : 'bg-violet-500/20 text-violet-300 border-violet-500/30'
                    }`}>
                      {event.is_verified && <span className="mr-1">✓</span>}
                      Live Event
                    </span>
                  </div>
                </div>

                {/* Content */}
                <div className="p-4">
                  <h3 className="text-base font-semibold text-slate-100 mb-1 line-clamp-2">
                    {event.event_name || event.title}
                  </h3>
                  <p className="text-sm text-slate-400 mb-2">{event.dj_name}</p>

                  <div className="space-y-0.5">
                    {formatEventDate(event.event_date) && (
                      <p className="text-xs text-slate-500">{formatEventDate(event.event_date)}</p>
                    )}
                    {event.venue_location && (
                      <p className="text-xs text-slate-500">{event.venue_location}</p>
                    )}
                    {event.confirmation_count > 0 && (
                      <p className="text-xs text-slate-500">
                        {event.confirmation_count} {event.confirmation_count === 1 ? 'person' : 'people'} confirmed
                      </p>
                    )}
                  </div>

                  {event.description && (
                    <p className="mt-2 text-xs text-slate-500 line-clamp-2">{event.description}</p>
                  )}
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>

      {/* Pagination */}
      {pagination.pages > 1 && (
        <div className="flex items-center justify-center gap-2">
          <button
            onClick={() => fetchEvents(searchQuery, pagination.page - 1)}
            disabled={pagination.page === 1}
            className="px-4 py-2 bg-surface-800 border border-white/5 rounded-lg text-sm text-slate-300 hover:text-white hover:bg-surface-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors cursor-pointer"
          >
            Previous
          </button>
          <span className="px-4 py-2 text-sm text-slate-500">
            {pagination.page} / {pagination.pages}
          </span>
          <button
            onClick={() => fetchEvents(searchQuery, pagination.page + 1)}
            disabled={pagination.page >= pagination.pages}
            className="px-4 py-2 bg-surface-800 border border-white/5 rounded-lg text-sm text-slate-300 hover:text-white hover:bg-surface-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors cursor-pointer"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
};

export default EventsPage;
