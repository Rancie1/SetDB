/**
 * EventDiscoverForm — search external sources (RA, Ticketmaster, Skiddle)
 * and import events into Deckd.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  searchRAEvents,
  searchTicketmasterEvents,
  searchSkiddleEvents,
  importRAEvent,
  importTicketmasterEvent,
  importSkiddleEvent,
} from '../../services/eventsService';

const SOURCES = ['RA', 'Ticketmaster', 'Skiddle'];

const formatDate = (dateString) => {
  if (!dateString) return null;
  try {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  } catch {
    return dateString;
  }
};

const EventDiscoverForm = () => {
  const navigate = useNavigate();
  const [activeSource, setActiveSource] = useState('RA');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [importingId, setImportingId] = useState(null);
  const [importedIds, setImportedIds] = useState(new Set());
  const [hasSearched, setHasSearched] = useState(false);

  // Shared form fields
  const [keyword, setKeyword] = useState('');

  // RA-specific
  const [raLocation, setRaLocation] = useState('');
  const [raDateFrom, setRaDateFrom] = useState('');
  const [raDateTo, setRaDateTo] = useState('');

  // Ticketmaster-specific
  const [tmCity, setTmCity] = useState('');
  const [tmCountryCode, setTmCountryCode] = useState('');

  // Skiddle-specific
  const [skiddleLat, setSkiddleLat] = useState('');
  const [skiddleLng, setSkiddleLng] = useState('');
  const [skiddleDateFrom, setSkiddleDateFrom] = useState('');
  const [skiddleDateTo, setSkiddleDateTo] = useState('');

  const handleSearch = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResults([]);
    setHasSearched(false);

    try {
      let response;
      if (activeSource === 'RA') {
        response = await searchRAEvents(keyword || undefined, raLocation, raDateFrom || undefined, raDateTo || undefined);
      } else if (activeSource === 'Ticketmaster') {
        response = await searchTicketmasterEvents(keyword || undefined, tmCity || undefined, tmCountryCode || undefined);
      } else {
        response = await searchSkiddleEvents(
          keyword || undefined,
          skiddleLat ? parseFloat(skiddleLat) : undefined,
          skiddleLng ? parseFloat(skiddleLng) : undefined,
          10,
          skiddleDateFrom || undefined,
          skiddleDateTo || undefined,
        );
      }
      setResults(response.data.results || []);
      setHasSearched(true);
    } catch (err) {
      setError(err.response?.data?.detail || 'Search failed. Check that the API key is configured.');
    } finally {
      setLoading(false);
    }
  };

  const handleImport = async (event) => {
    setImportingId(event.external_id);
    try {
      let response;
      if (activeSource === 'RA') {
        const raId = event.external_id.replace('ra_', '');
        response = await importRAEvent(raId);
      } else if (activeSource === 'Ticketmaster') {
        const tmId = event.external_id.replace('tm_', '');
        response = await importTicketmasterEvent(tmId);
      } else {
        const skiddleId = event.external_id.replace('skiddle_', '');
        response = await importSkiddleEvent(skiddleId);
      }
      setImportedIds((prev) => new Set([...prev, event.external_id]));
      navigate(`/events/${response.data.id}`);
    } catch (err) {
      setError(err.response?.data?.detail || 'Import failed.');
    } finally {
      setImportingId(null);
    }
  };

  const handleSourceChange = (source) => {
    setActiveSource(source);
    setResults([]);
    setError(null);
    setKeyword('');
  };

  return (
    <div>
      {/* Source tabs */}
      <div className="flex gap-2 mb-6">
        {SOURCES.map((source) => (
          <button
            key={source}
            onClick={() => handleSourceChange(source)}
            className={`px-5 py-2 rounded-full text-sm font-medium transition-colors cursor-pointer ${
              activeSource === source
                ? 'bg-primary-600 text-white'
                : 'bg-surface-700 text-slate-400 hover:text-slate-200 border border-white/10'
            }`}
          >
            {source}
          </button>
        ))}
      </div>

      {/* Search form */}
      <form onSubmit={handleSearch} className="bg-surface-800 border border-white/5 rounded-xl p-5 mb-6 space-y-4">
        {/* Keyword — Ticketmaster and Skiddle (RA has its own keyword field above) */}
        {activeSource !== 'RA' && (
          <div>
            <label className="block text-xs font-medium text-slate-400 mb-1">Keyword</label>
            <input
              type="text"
              value={keyword}
              onChange={(e) => setKeyword(e.target.value)}
              placeholder="e.g. fabric, techno, drum and bass..."
              className="w-full px-3 py-2 bg-surface-700 border border-white/10 text-slate-100 placeholder-slate-500 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
            />
          </div>
        )}

        {/* RA fields */}
        {activeSource === 'RA' && (
          <>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">City *</label>
                <input
                  type="text"
                  value={raLocation}
                  onChange={(e) => setRaLocation(e.target.value)}
                  placeholder="e.g. London, Berlin, Melbourne"
                  required
                  className="w-full px-3 py-2 bg-surface-700 border border-white/10 text-slate-100 placeholder-slate-500 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Keyword</label>
                <input
                  type="text"
                  value={keyword}
                  onChange={(e) => setKeyword(e.target.value)}
                  placeholder="DJ name, event, venue…"
                  className="w-full px-3 py-2 bg-surface-700 border border-white/10 text-slate-100 placeholder-slate-500 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  From <span className="text-slate-600 font-normal">(default: last 2 years)</span>
                </label>
                <input
                  type="date"
                  value={raDateFrom}
                  onChange={(e) => setRaDateFrom(e.target.value)}
                  className="w-full px-3 py-2 bg-surface-700 border border-white/10 text-slate-100 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  To <span className="text-slate-600 font-normal">(default: today)</span>
                </label>
                <input
                  type="date"
                  value={raDateTo}
                  onChange={(e) => setRaDateTo(e.target.value)}
                  className="w-full px-3 py-2 bg-surface-700 border border-white/10 text-slate-100 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
                />
              </div>
            </div>
          </>
        )}

        {/* Ticketmaster fields */}
        {activeSource === 'Ticketmaster' && (
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">City</label>
              <input
                type="text"
                value={tmCity}
                onChange={(e) => setTmCity(e.target.value)}
                placeholder="e.g. London"
                className="w-full px-3 py-2 bg-surface-700 border border-white/10 text-slate-100 placeholder-slate-500 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1">Country code</label>
              <input
                type="text"
                value={tmCountryCode}
                onChange={(e) => setTmCountryCode(e.target.value)}
                placeholder="e.g. GB, US, DE"
                maxLength={2}
                className="w-full px-3 py-2 bg-surface-700 border border-white/10 text-slate-100 placeholder-slate-500 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none uppercase"
              />
            </div>
          </div>
        )}

        {/* Skiddle fields */}
        {activeSource === 'Skiddle' && (
          <>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Latitude</label>
                <input
                  type="number"
                  step="any"
                  value={skiddleLat}
                  onChange={(e) => setSkiddleLat(e.target.value)}
                  placeholder="e.g. 51.5"
                  className="w-full px-3 py-2 bg-surface-700 border border-white/10 text-slate-100 placeholder-slate-500 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Longitude</label>
                <input
                  type="number"
                  step="any"
                  value={skiddleLng}
                  onChange={(e) => setSkiddleLng(e.target.value)}
                  placeholder="e.g. -0.12"
                  className="w-full px-3 py-2 bg-surface-700 border border-white/10 text-slate-100 placeholder-slate-500 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Date from</label>
                <input
                  type="date"
                  value={skiddleDateFrom}
                  onChange={(e) => setSkiddleDateFrom(e.target.value)}
                  className="w-full px-3 py-2 bg-surface-700 border border-white/10 text-slate-100 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">Date to</label>
                <input
                  type="date"
                  value={skiddleDateTo}
                  onChange={(e) => setSkiddleDateTo(e.target.value)}
                  className="w-full px-3 py-2 bg-surface-700 border border-white/10 text-slate-100 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
                />
              </div>
            </div>
          </>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-primary-600 hover:bg-primary-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-2.5 rounded-lg text-sm transition-colors cursor-pointer"
        >
          {loading ? 'Searching…' : `Search ${activeSource}`}
        </button>
      </form>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 text-red-400 px-4 py-3 rounded-xl mb-4 text-sm">
          {error}
        </div>
      )}

      {/* Results grid */}
      {results.length > 0 && (
        <div>
          <p className="text-sm text-slate-500 mb-4">{results.length} result{results.length !== 1 ? 's' : ''}</p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {results.map((event) => {
              const alreadyImported = importedIds.has(event.external_id);
              const isImporting = importingId === event.external_id;

              return (
                <div
                  key={event.external_id}
                  className="bg-surface-800 border border-white/5 rounded-xl overflow-hidden flex flex-col"
                >
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
                        <svg viewBox="0 0 24 24" fill="currentColor" className="w-10 h-10 text-slate-600">
                          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 14.5v-9l6 4.5-6 4.5z"/>
                        </svg>
                      </div>
                    )}
                    <div className="absolute top-2 left-2">
                      <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-black/60 text-slate-300 border border-white/10">
                        {activeSource}
                      </span>
                    </div>
                  </div>

                  {/* Content */}
                  <div className="p-4 flex-1 flex flex-col">
                    <h3 className="text-sm font-semibold text-slate-100 mb-1 line-clamp-2">
                      {event.event_name || event.title}
                    </h3>
                    <p className="text-xs text-slate-400 mb-1">{event.dj_name}</p>
                    {event.event_date && (
                      <p className="text-xs text-slate-500">{formatDate(event.event_date)}</p>
                    )}
                    {event.venue_location && (
                      <p className="text-xs text-slate-500 mb-3">{event.venue_location}</p>
                    )}

                    <div className="mt-auto flex gap-2">
                      {event.ticket_url && (
                        <a
                          href={event.ticket_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex-1 text-center px-3 py-1.5 text-xs text-slate-300 border border-white/10 rounded-lg hover:bg-surface-700 transition-colors"
                        >
                          View
                        </a>
                      )}
                      <button
                        onClick={() => handleImport(event)}
                        disabled={alreadyImported || isImporting}
                        className={`flex-1 px-3 py-1.5 text-xs font-medium rounded-lg transition-colors cursor-pointer ${
                          alreadyImported
                            ? 'bg-green-500/20 text-green-400 border border-green-500/30 cursor-default'
                            : 'bg-primary-600 hover:bg-primary-500 disabled:opacity-50 disabled:cursor-not-allowed text-white'
                        }`}
                      >
                        {alreadyImported ? 'Imported' : isImporting ? 'Importing…' : 'Import'}
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {!loading && !error && !hasSearched && (
        <div className="text-center py-12 text-slate-500 text-sm">
          Search above to discover events from {activeSource}.
        </div>
      )}

      {!loading && !error && hasSearched && results.length === 0 && (
        <div className="text-center py-12 text-slate-500 text-sm">
          No events found. Try adjusting your search — for RA, try a different city or date range.
        </div>
      )}
    </div>
  );
};

export default EventDiscoverForm;
