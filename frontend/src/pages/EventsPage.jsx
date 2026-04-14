/**
 * Events page — search for events and navigate to their detail pages.
 * External events (RA, Ticketmaster) are silently saved to the DB on click.
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  getEvents,
  searchRAEvents,
  searchTicketmasterEvents,
  importRAEvent,
  importTicketmasterEvent,
} from '../services/eventsService';
import useAuthStore from '../store/authStore';

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

const EventsPage = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthStore();

  const [keyword, setKeyword] = useState('');
  const [city, setCity] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [results, setResults] = useState([]);
  const [hasSearched, setHasSearched] = useState(false);
  const [navigatingId, setNavigatingId] = useState(null); // external_id or db id being loaded

  // Load all DB events on mount
  useEffect(() => {
    getEvents({}, 1, 50)
      .then((res) => setResults(res.data?.items ?? []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  // Detect a pasted RA URL (e.g. https://ra.co/events/2283762) and load it directly.
  const handleRAUrl = async (raw) => {
    const match = raw.match(/ra\.co\/events\/(\d+)/i);
    if (!match) return false;

    if (!isAuthenticated) { navigate('/login'); return true; }

    const raId = match[1];
    setNavigatingId(`ra_${raId}`);
    setError(null);
    setLoading(true);
    try {
      const res = await importRAEvent(raId, raId);
      navigate(`/events/${res.data.id}`);
    } catch {
      setError('Could not load this RA event. Make sure the URL is correct.');
      setNavigatingId(null);
      setLoading(false);
    }
    return true;
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!keyword.trim() && !city.trim()) return;

    // If the keyword looks like an RA URL, shortcut directly to that event.
    if (await handleRAUrl(keyword.trim())) return;

    setLoading(true);
    setError(null);
    setResults([]);
    setHasSearched(false);

    const [dbRes, raRes, tmRes] = await Promise.allSettled([
      getEvents({ search: keyword }, 1, 50),
      city.trim()
        ? searchRAEvents(keyword || undefined, city.trim(), undefined, undefined, 1, 30)
        : Promise.resolve(null),
      searchTicketmasterEvents(keyword || undefined, city.trim() || undefined, undefined, 0, 30),
    ]);

    setLoading(false);
    setHasSearched(true);

    const dbEvents = dbRes.status === 'fulfilled' ? (dbRes.value?.data?.items ?? []) : [];
    const raEvents =
      raRes.status === 'fulfilled' && raRes.value
        ? (raRes.value?.data?.results ?? [])
        : [];
    const tmEvents =
      tmRes.status === 'fulfilled' ? (tmRes.value?.data?.results ?? []) : [];

    // Build a set of external_ids already in our DB so we can dedup
    const dbExternalIds = new Set(dbEvents.map((e) => e.external_id).filter(Boolean));

    const taggedExternal = [
      ...raEvents
        .filter((e) => !dbExternalIds.has(e.external_id))
        .map((e) => ({ ...e, _source: 'ra' })),
      ...tmEvents
        .filter((e) => !dbExternalIds.has(e.external_id))
        .map((e) => ({ ...e, _source: 'ticketmaster' })),
    ];

    setResults([...dbEvents, ...taggedExternal]);
  };

  const handleEventClick = async (event) => {
    // Already in our DB — just navigate
    if (event.id) {
      navigate(`/events/${event.id}`);
      return;
    }

    // External event — silently save to DB, then navigate
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    const clickId = event.external_id;
    setNavigatingId(clickId);
    setError(null);

    try {
      let res;
      if (event._source === 'ra') {
        const raId = event.external_id.replace('ra_', '');
        res = await importRAEvent(raId, event.ra_event_id);
      } else {
        const tmId = event.external_id.replace('tm_', '');
        res = await importTicketmasterEvent(tmId);
      }
      navigate(`/events/${res.data.id}`);
    } catch {
      setError('Could not load this event. Please try again.');
      setNavigatingId(null);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2 text-slate-100">Events</h1>
        <p className="text-slate-400">Browse events or search to find one to rate or review.</p>
      </div>

      {/* Search bar */}
      <form onSubmit={handleSearch} className="flex gap-3 mb-8">
        <input
          type="text"
          value={keyword}
          onChange={(e) => setKeyword(e.target.value)}
          placeholder="Artist, event name, venue… or paste an RA URL"
          className="flex-1 px-4 py-3 bg-surface-800 border border-white/10 text-slate-100 placeholder-slate-500 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none text-sm"
        />
        <input
          type="text"
          value={city}
          onChange={(e) => setCity(e.target.value)}
          placeholder="City (optional)"
          className="w-44 px-4 py-3 bg-surface-800 border border-white/10 text-slate-100 placeholder-slate-500 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none text-sm"
        />
        <button
          type="submit"
          disabled={loading || (!keyword.trim() && !city.trim())}
          className="px-6 py-3 bg-primary-600 hover:bg-primary-500 disabled:opacity-40 disabled:cursor-not-allowed text-white font-medium rounded-xl transition-colors text-sm cursor-pointer"
        >
          {loading ? 'Searching…' : 'Search'}
        </button>
      </form>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 text-red-400 px-4 py-3 rounded-xl mb-6 text-sm">
          {error}
        </div>
      )}

      {/* Results */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="bg-surface-700 animate-pulse rounded-xl h-64" />
          ))}
        </div>
      ) : hasSearched && results.length === 0 ? (
        <div className="bg-surface-800 border border-white/5 rounded-xl p-12 text-center">
          <p className="text-slate-400 text-lg mb-1">No events found</p>
          <p className="text-slate-500 text-sm mb-3">
            Try a different keyword{!city.trim() && ', or add a city to search Resident Advisor'}.
          </p>
          <p className="text-slate-500 text-sm">
            Know the event is on Resident Advisor?{' '}
            <span className="text-slate-400">Paste the RA event URL directly into the search bar</span>
            {' '}(e.g. <span className="font-mono text-xs text-slate-500">ra.co/events/1234567</span>).
          </p>
        </div>
      ) : results.length > 0 ? (
        <>
          <p className="text-sm text-slate-500 mb-4">
            {results.length} result{results.length !== 1 ? 's' : ''}
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {results.map((event) => {
              const cardId = event.id ?? event.external_id;
              const isNavigating = navigatingId === (event.id ?? event.external_id);

              return (
                <div
                  key={cardId}
                  onClick={() => !navigatingId && handleEventClick(event)}
                  className={`relative bg-surface-800 rounded-xl border border-white/5 hover:border-primary-500/30 hover:bg-surface-700 transition-colors overflow-hidden ${
                    navigatingId ? 'cursor-wait' : 'cursor-pointer'
                  }`}
                >
                  {/* Loading overlay */}
                  {isNavigating && (
                    <div className="absolute inset-0 bg-surface-900/70 flex items-center justify-center z-10 rounded-xl">
                      <div className="w-6 h-6 border-2 border-primary-400 border-t-transparent rounded-full animate-spin" />
                    </div>
                  )}

                  {/* Thumbnail */}
                  <div className="aspect-video bg-surface-700 relative overflow-hidden">
                    {event.thumbnail_url ? (
                      <img
                        src={event.thumbnail_url}
                        alt={event.event_name || event.title}
                        className="w-full h-full object-cover"
                        onError={(e) => { e.target.style.display = 'none'; }}
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center">
                        <svg viewBox="0 0 24 24" fill="currentColor" className="w-12 h-12 text-slate-600">
                          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 14.5v-9l6 4.5-6 4.5z" />
                        </svg>
                      </div>
                    )}
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
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </>
      ) : null}
    </div>
  );
};

export default EventsPage;
