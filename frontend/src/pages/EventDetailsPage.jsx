/**
 * Event details page.
 *
 * Displays comprehensive information about a live event including:
 * - Event metadata (name, date, venue, verification status)
 * - Recordings linked to this event
 * - Event confirmation functionality
 * - Ability to link sets to this event
 */

import { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import useAuthStore from '../store/authStore';
import * as eventsService from '../services/eventsService';
import * as setsService from '../services/setsService';
import * as usersService from '../services/usersService';
import ArtistLink from '../components/shared/ArtistLink';

const EventDetailsPage = () => {
  const { id } = useParams();
  const { isAuthenticated, user } = useAuthStore();

  const [event, setEvent] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [linkedSets, setLinkedSets] = useState([]);
  const [linkedSetsLoading, setLinkedSetsLoading] = useState(false);
  const [showLinkForm, setShowLinkForm] = useState(false);
  const [linkingSet, setLinkingSet] = useState(false);
  const [isConfirmed, setIsConfirmed] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [selectedSetId, setSelectedSetId] = useState(null);
  const [isInTop5, setIsInTop5] = useState(false);
  const [topEventOrder, setTopEventOrder] = useState(null);
  const [topEventLoading, setTopEventLoading] = useState(false);

  useEffect(() => {
    if (id) {
      loadEvent();
      loadLinkedSets();
    }
  }, [id]);

  useEffect(() => {
    if (event && isAuthenticated && user) {
      checkConfirmation();
      checkTopEvent();
    }
  }, [event, isAuthenticated, user]);

  const checkTopEvent = async () => {
    if (!user || !event) return;
    try {
      const res = await usersService.getUserTopEvents(user.id);
      const list = res.data || [];
      const found = list.find((e) => e.id === event.id);
      setIsInTop5(!!found);
      setTopEventOrder(found ? found.order : null);
    } catch {
      setIsInTop5(false);
      setTopEventOrder(null);
    }
  };

  const handleAddToTop5 = async (order) => {
    if (!event || !isAuthenticated || topEventLoading) return;
    setTopEventLoading(true);
    try {
      await usersService.addTopEvent(event.id, order);
      setIsInTop5(true);
      setTopEventOrder(order);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to add to top 5');
    } finally {
      setTopEventLoading(false);
    }
  };

  const handleRemoveFromTop5 = async () => {
    if (!event || !isAuthenticated || topEventLoading) return;
    setTopEventLoading(true);
    try {
      await usersService.removeTopEvent(event.id);
      setIsInTop5(false);
      setTopEventOrder(null);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to remove from top 5');
    } finally {
      setTopEventLoading(false);
    }
  };

  const loadEvent = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await eventsService.getEvent(id);
      setEvent(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load event');
    } finally {
      setLoading(false);
    }
  };

  const loadLinkedSets = async () => {
    setLinkedSetsLoading(true);
    try {
      const response = await eventsService.getEventLinkedSets(id);
      setLinkedSets(response.data.items || []);
    } catch (err) {
      console.error('Failed to load linked sets:', err);
      setLinkedSets([]);
    } finally {
      setLinkedSetsLoading(false);
    }
  };

  const checkConfirmation = async () => {
    if (!event || !isAuthenticated) {
      setIsConfirmed(false);
      return;
    }
    setIsConfirmed(false);
  };

  const handleConfirmEvent = async () => {
    if (!event || !isAuthenticated || confirming) return;

    setConfirming(true);
    try {
      if (isConfirmed) {
        await eventsService.unconfirmEvent(event.id);
        setIsConfirmed(false);
        await loadEvent();
      } else {
        await eventsService.confirmEvent(event.id);
        setIsConfirmed(true);
        await loadEvent();
      }
    } catch (err) {
      console.error('Failed to confirm/unconfirm event:', err);
      alert(err.response?.data?.detail || 'Failed to update confirmation');
    } finally {
      setConfirming(false);
    }
  };

  const searchSets = async () => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }

    setSearching(true);
    try {
      const response = await setsService.getSets({ search: searchQuery }, 1, 10);
      setSearchResults(response.data.items || []);
    } catch (err) {
      console.error('Failed to search sets:', err);
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  };

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      searchSets();
    }, 300);
    return () => clearTimeout(timeoutId);
  }, [searchQuery]);

  const handleLinkSet = async () => {
    if (!event || !selectedSetId) return;

    setLinkingSet(true);
    try {
      await eventsService.linkSetToEvent(event.id, selectedSetId);
      await loadLinkedSets();
      setShowLinkForm(false);
      setSearchQuery('');
      setSearchResults([]);
      setSelectedSetId(null);
    } catch (err) {
      console.error('Failed to link set:', err);
      alert(err.response?.data?.detail || 'Failed to link set to event');
    } finally {
      setLinkingSet(false);
    }
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

  const formatDuration = (minutes) => {
    if (!minutes) return null;
    const days = Math.floor(minutes / (24 * 60));
    const hours = Math.floor((minutes % (24 * 60)) / 60);
    const mins = minutes % 60;

    const parts = [];
    if (days > 0) parts.push(`${days} ${days === 1 ? 'day' : 'days'}`);
    if (hours > 0) parts.push(`${hours}h`);
    if (mins > 0 && days === 0) parts.push(`${mins}m`);

    return parts.join(' ') || null;
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-surface-700 rounded-xl w-3/4"></div>
          <div className="h-64 bg-surface-700 rounded-xl"></div>
          <div className="space-y-3">
            <div className="h-4 bg-surface-700 rounded w-full"></div>
            <div className="h-4 bg-surface-700 rounded w-5/6"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !event) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-red-500/10 border border-red-500/20 text-red-400 px-4 py-3 rounded-xl">
          {error || 'Event not found'}
        </div>
        <Link to="/events" className="mt-4 inline-block text-primary-400 hover:text-primary-300">
          ← Back to Events
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Back Button */}
      <Link to="/events" className="inline-flex items-center text-slate-500 hover:text-slate-300 mb-6 transition-colors">
        <span className="mr-2">←</span>
        Back to Events
      </Link>

      {/* Hero Section */}
      <div className="bg-surface-800 rounded-xl border border-white/5 overflow-hidden mb-8">
        <div className="md:flex">
          {/* Thumbnail */}
          <div className="md:w-1/3 lg:w-1/4">
            <div className="aspect-video md:aspect-square bg-surface-700 relative">
              {event.thumbnail_url ? (
                <img
                  src={event.thumbnail_url}
                  alt={event.event_name || event.title}
                  className="w-full h-full object-cover"
                  onError={(e) => { e.target.style.display = 'none'; }}
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center">
                  <svg viewBox="0 0 24 24" fill="currentColor" className="w-16 h-16 text-slate-600">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 14.5v-9l6 4.5-6 4.5z"/>
                  </svg>
                </div>
              )}
              <div className="absolute top-3 right-3">
                <span className={`inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium border ${
                  event.is_verified
                    ? 'bg-green-500/20 text-green-300 border-green-500/30'
                    : 'bg-violet-500/20 text-violet-300 border-violet-500/30'
                }`}>
                  {event.is_verified && <span className="mr-1">✓</span>}
                  Live Event
                </span>
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="md:w-2/3 lg:w-3/4 p-6 md:p-8">
            <h1 className="text-3xl md:text-4xl font-bold text-slate-100 mb-2">
              {event.event_name || event.title}
            </h1>
            {event.dj_name && event.dj_name !== 'Various Artists' && (
              <p className="text-xl text-slate-400 mb-4">
                <ArtistLink name={event.dj_name} />
              </p>
            )}

            {/* Verification Status */}
            <div className="mb-4 p-3 rounded-xl bg-violet-500/10 border border-violet-500/20">
              <div className="flex items-center justify-between mb-2 flex-wrap gap-2">
                <div className="flex items-center gap-2">
                  {event.is_verified ? (
                    <>
                      <span className="text-green-400">✓</span>
                      <span className="font-medium text-green-400">Verified Event</span>
                    </>
                  ) : (
                    <>
                      <span className="text-yellow-400">⚠</span>
                      <span className="font-medium text-yellow-400">Unverified Event</span>
                    </>
                  )}
                </div>
                {isAuthenticated && (
                  <div className="flex items-center gap-2 flex-wrap">
                    <button
                      onClick={handleConfirmEvent}
                      disabled={confirming}
                      className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors cursor-pointer ${
                        isConfirmed
                          ? 'bg-green-500/20 text-green-300 border border-green-500/30 hover:bg-green-500/30'
                          : 'bg-surface-700 text-slate-400 hover:text-slate-200 border border-white/5'
                      } disabled:opacity-50`}
                    >
                      {confirming ? '...' : isConfirmed ? '✓ Confirmed' : 'Confirm Attendance'}
                    </button>
                    {isInTop5 ? (
                      <button
                        onClick={handleRemoveFromTop5}
                        disabled={topEventLoading}
                        className="px-3 py-1 rounded-lg text-sm font-medium bg-primary-600/20 text-primary-300 border border-primary-500/30 hover:bg-primary-600/30 disabled:opacity-50 cursor-pointer transition-colors"
                      >
                        {topEventLoading ? '...' : `#${topEventOrder} in Top 5 — Remove`}
                      </button>
                    ) : (
                      <div className="flex gap-1">
                        {[1, 2, 3, 4, 5].map((order) => (
                          <button
                            key={order}
                            onClick={() => handleAddToTop5(order)}
                            disabled={topEventLoading}
                            className="px-2 py-1 rounded-lg text-xs font-medium bg-primary-600 text-white hover:bg-primary-500 disabled:opacity-50 cursor-pointer transition-colors"
                          >
                            #{order}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
              {event.confirmation_count > 0 && (
                <p className="text-sm text-slate-400">
                  {event.confirmation_count} {event.confirmation_count === 1 ? 'person has' : 'people have'} confirmed attending this event
                </p>
              )}
            </div>

            {/* Metadata */}
            <div className="flex flex-wrap items-center gap-4 mb-6 text-sm text-slate-500">
              {formatEventDate(event.event_date) && (
                <span>{formatEventDate(event.event_date)}</span>
              )}
              {event.venue_location && (
                <span>{event.venue_location}</span>
              )}
              {formatDuration(event.duration_minutes) && (
                <span>{formatDuration(event.duration_minutes)}</span>
              )}
              {linkedSets.length > 0 && (
                <span>{linkedSets.length} {linkedSets.length === 1 ? 'set' : 'sets'} linked</span>
              )}
            </div>

            {/* Description */}
            {event.description && (
              <div className="mb-6">
                <p className="text-slate-300 whitespace-pre-wrap text-sm leading-relaxed">{event.description}</p>
              </div>
            )}

            {/* Actions */}
            <div className="flex flex-wrap items-center gap-3">
              {isAuthenticated && (
                <button
                  onClick={() => setShowLinkForm(!showLinkForm)}
                  className="inline-flex items-center px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white font-medium rounded-xl transition-colors cursor-pointer"
                >
                  Link Set to Event
                </button>
              )}
              {event.source_url &&
               (event.source_url.startsWith('http://') || event.source_url.startsWith('https://')) && (
                <a
                  href={event.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center px-4 py-2 bg-surface-700 hover:bg-surface-600 text-slate-300 font-medium rounded-xl transition-colors border border-white/5"
                >
                  Event Link
                </a>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-8">
          {/* Link Set Form */}
          {showLinkForm && isAuthenticated && (
            <div className="bg-surface-800 rounded-xl border border-white/5 p-6">
              <h3 className="text-lg font-semibold text-slate-100 mb-3">Link Set to Event</h3>
              <p className="text-sm text-slate-500 mb-4">Search for a set to link to this event.</p>

              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-slate-400 mb-1">Search Sets</label>
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search by title or DJ name..."
                    className="w-full px-3 py-2 bg-surface-700 border border-white/10 text-slate-100 placeholder-slate-500 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  />
                </div>

                {searching && (
                  <div className="text-sm text-slate-500">Searching...</div>
                )}

                {searchResults.length > 0 && (
                  <div className="bg-surface-700 border border-white/10 rounded-lg max-h-60 overflow-y-auto">
                    {searchResults.map((set) => (
                      <div
                        key={set.id}
                        onClick={() => setSelectedSetId(set.id)}
                        className={`p-3 border-b border-white/5 last:border-b-0 cursor-pointer transition-colors ${
                          selectedSetId === set.id
                            ? 'bg-primary-600/20'
                            : 'hover:bg-surface-600'
                        }`}
                      >
                        <div className="font-medium text-slate-200">{set.title}</div>
                        <div className="text-sm text-slate-500">{set.dj_name}</div>
                      </div>
                    ))}
                  </div>
                )}

                {searchQuery.trim() && !searching && searchResults.length === 0 && (
                  <div className="text-sm text-slate-500">No sets found</div>
                )}

                <div className="flex gap-2 pt-2">
                  <button
                    onClick={handleLinkSet}
                    disabled={!selectedSetId || linkingSet}
                    className="flex-1 px-4 py-2 bg-violet-600 hover:bg-violet-500 disabled:bg-surface-700 disabled:text-slate-500 disabled:cursor-not-allowed text-white font-medium rounded-xl transition-colors cursor-pointer"
                  >
                    {linkingSet ? 'Linking...' : 'Link Selected Set'}
                  </button>
                  <button
                    onClick={() => {
                      setShowLinkForm(false);
                      setSearchQuery('');
                      setSearchResults([]);
                      setSelectedSetId(null);
                    }}
                    disabled={linkingSet}
                    className="px-4 py-2 bg-surface-700 hover:bg-surface-600 text-slate-300 font-medium rounded-xl border border-white/5 transition-colors cursor-pointer"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Linked Sets Section */}
          <div className="bg-surface-800 rounded-xl border border-white/5 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-slate-100">Linked Sets</h2>
              {linkedSets.length > 0 && (
                <span className="text-sm text-slate-500">{linkedSets.length} {linkedSets.length === 1 ? 'set' : 'sets'}</span>
              )}
            </div>
            {linkedSetsLoading ? (
              <div className="space-y-4">
                {[1, 2].map((i) => (
                  <div key={i} className="bg-surface-700 animate-pulse rounded-xl h-24"></div>
                ))}
              </div>
            ) : linkedSets.length === 0 ? (
              <div className="bg-surface-700 border border-white/5 rounded-xl p-6 text-center">
                <p className="text-slate-400 mb-2">No sets linked yet</p>
                <p className="text-sm text-slate-500 mb-4">Sets linked to this event will appear here</p>
                {isAuthenticated && (
                  <button
                    onClick={() => setShowLinkForm(true)}
                    className="inline-flex items-center px-4 py-2 bg-violet-600 hover:bg-violet-500 text-white font-medium rounded-xl transition-colors cursor-pointer"
                  >
                    Link a Set
                  </button>
                )}
              </div>
            ) : (
              <div className="space-y-3">
                {linkedSets.map((set) => (
                  <Link
                    key={set.id}
                    to={`/sets/${set.id}`}
                    className="block bg-surface-700 hover:bg-surface-600 border border-white/5 hover:border-primary-500/20 rounded-xl p-4 transition-colors"
                  >
                    <div className="flex items-center gap-4">
                      {set.thumbnail_url && (
                        <img
                          src={set.thumbnail_url}
                          alt={set.title}
                          className="w-20 h-20 object-cover rounded-lg flex-shrink-0"
                        />
                      )}
                      <div className="flex-1 min-w-0">
                        <h3 className="font-medium text-slate-200 truncate">{set.title}</h3>
                        <p className="text-sm text-slate-500">{set.dj_name}</p>
                        <div className="flex items-center gap-3 mt-1">
                          <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${
                            set.source_type === 'youtube'
                              ? 'bg-red-500/20 text-red-300 border-red-500/30'
                              : 'bg-orange-500/20 text-orange-300 border-orange-500/30'
                          }`}>
                            {set.source_type === 'youtube' ? 'YouTube' : 'SoundCloud'}
                          </span>
                          {set.duration_minutes && (
                            <span className="text-xs text-slate-500">
                              {Math.floor(set.duration_minutes / 60)}h {set.duration_minutes % 60}m
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Event Details */}
          <div className="bg-surface-800 rounded-xl border border-white/5 p-6">
            <h3 className="text-lg font-semibold text-slate-100 mb-4">Event Details</h3>
            <dl className="space-y-3 text-sm">
              <div>
                <dt className="text-slate-500">Status</dt>
                <dd className="font-medium text-slate-200">{event.is_verified ? 'Verified' : 'Unverified'}</dd>
              </div>
              <div>
                <dt className="text-slate-500">Confirmations</dt>
                <dd className="font-medium text-slate-200">{event.confirmation_count || 0}</dd>
              </div>
              <div>
                <dt className="text-slate-500">Linked Sets</dt>
                <dd className="font-medium text-slate-200">{linkedSets.length}</dd>
              </div>
              <div>
                <dt className="text-slate-500">Created</dt>
                <dd className="font-medium text-slate-200">{new Date(event.created_at).toLocaleDateString()}</dd>
              </div>
            </dl>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EventDetailsPage;
