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
      const response = await eventsService.getEvents(
        { search },
        page,
        pagination.limit
      );
      const { items, total, pages } = response.data;
      setEvents(items || []);
      setPagination({
        ...pagination,
        page,
        total,
        pages,
      });
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
          <h1 className="text-3xl font-bold mb-2">Events</h1>
          <p className="text-gray-600">
            Browse and discover live DJ events. View event details and their recordings.
          </p>
        </div>
        {isAuthenticated && (
          <Link
            to="/events/create"
            className="px-6 py-2 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-md inline-block"
          >
            + Create Event
          </Link>
        )}
      </div>

      {/* Search Bar */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
        <form onSubmit={handleSearch} className="flex gap-4">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search events by name, DJ, or venue..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
          <button
            type="submit"
            className="bg-primary-600 hover:bg-primary-700 text-white font-medium px-6 py-2 rounded-md"
          >
            Search
          </button>
          {searchQuery && (
            <button
              type="button"
              onClick={() => {
                setSearchQuery('');
                fetchEvents('', 1);
              }}
              className="bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium px-4 py-2 rounded-md"
            >
              Clear
            </button>
          )}
        </form>
      </div>

      {/* Events List */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">
            {searchQuery ? `Search Results` : 'All Events'}
          </h2>
          {pagination.total > 0 && (
            <p className="text-sm text-gray-600">
              Showing {events.length} of {pagination.total} events
            </p>
          )}
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="bg-gray-100 animate-pulse rounded-lg h-64"></div>
            ))}
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
            {error}
          </div>
        ) : events.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500 text-lg mb-2">No events found</p>
            <p className="text-gray-400 text-sm">
              {searchQuery
                ? 'Try a different search term.'
                : 'Events will appear here once they are created.'}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {events.map((event) => (
              <Link
                key={event.id}
                to={`/events/${event.id}`}
                className="block bg-white rounded-lg shadow-sm border border-gray-200 hover:shadow-md transition-shadow overflow-hidden"
              >
                {/* Thumbnail */}
                <div className="aspect-video bg-gray-200 relative overflow-hidden">
                  {event.thumbnail_url ? (
                    <img
                      src={event.thumbnail_url}
                      alt={event.title}
                      className="w-full h-full object-cover"
                      onError={(e) => {
                        e.target.style.display = 'none';
                        if (!e.target.parentElement.querySelector('.thumbnail-placeholder')) {
                          const placeholder = document.createElement('div');
                          placeholder.className = 'thumbnail-placeholder w-full h-full flex items-center justify-center text-gray-400 absolute inset-0';
                          placeholder.innerHTML = '<span class="text-4xl">🎤</span>';
                          e.target.parentElement.appendChild(placeholder);
                        }
                      }}
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center text-gray-400">
                      <span className="text-4xl">🎤</span>
                    </div>
                  )}
                  {/* Badges */}
                  <div className="absolute top-2 right-2 flex flex-col gap-1 items-end">
                    <span
                      className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium border ${
                        event.is_verified
                          ? 'bg-green-100 text-green-800 border-green-300'
                          : 'bg-purple-100 text-purple-800 border-purple-300'
                      }`}
                    >
                      {event.is_verified && <span className="mr-1">✓</span>}
                      Live Event
                    </span>
                  </div>
                </div>

                {/* Content */}
                <div className="p-4">
                  <h3 className="text-lg font-semibold text-gray-900 mb-1 line-clamp-2">
                    {event.event_name || event.title}
                  </h3>
                  <p className="text-sm text-gray-600 mb-2">{event.dj_name}</p>

                  {/* Event info */}
                  <div className="mb-2 space-y-1">
                    {formatEventDate(event.event_date) && (
                      <p className="text-sm text-gray-700">
                        📅 {formatEventDate(event.event_date)}
                      </p>
                    )}
                    {event.venue_location && (
                      <p className="text-sm text-gray-700">
                        📍 {event.venue_location}
                      </p>
                    )}
                    {event.confirmation_count > 0 && (
                      <p className="text-xs text-gray-500">
                        {event.confirmation_count}{' '}
                        {event.confirmation_count === 1 ? 'person' : 'people'} confirmed
                      </p>
                    )}
                    {/* Linked sets count would be shown here if needed */}
                  </div>

                  {/* Description preview */}
                  {event.description && (
                    <p className="mt-2 text-sm text-gray-600 line-clamp-2">
                      {event.description}
                    </p>
                  )}
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>

      {/* Pagination */}
      {pagination.pages > 1 && (
        <div className="flex items-center justify-center space-x-2">
          <button
            onClick={() => fetchEvents(searchQuery, pagination.page - 1)}
            disabled={pagination.page === 1}
            className="px-4 py-2 border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
          >
            Previous
          </button>
          <span className="px-4 py-2 text-sm text-gray-600">
            Page {pagination.page} of {pagination.pages}
          </span>
          <button
            onClick={() => fetchEvents(searchQuery, pagination.page + 1)}
            disabled={pagination.page >= pagination.pages}
            className="px-4 py-2 border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
};

export default EventsPage;
