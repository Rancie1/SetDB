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
    
    // We'll check confirmation status by trying to confirm and catching the error
    // Or we could add a separate endpoint to check status
    // For now, we'll check if the user has confirmed by looking at the event data
    // This is a simplified approach - ideally we'd have a separate endpoint
    setIsConfirmed(false); // Will be updated after user confirms/unconfirms
  };

  const handleConfirmEvent = async () => {
    if (!event || !isAuthenticated || confirming) return;
    
    setConfirming(true);
    try {
      if (isConfirmed) {
        await eventsService.unconfirmEvent(event.id);
        setIsConfirmed(false);
        // Reload event to update confirmation count
        await loadEvent();
      } else {
        await eventsService.confirmEvent(event.id);
        setIsConfirmed(true);
        // Reload event to update confirmation count
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
      // All sets are available to link (events are separate entities)
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
      // Refresh linked sets after linking
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
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-3/4 mb-4"></div>
          <div className="h-64 bg-gray-200 rounded mb-6"></div>
          <div className="space-y-4">
            <div className="h-4 bg-gray-200 rounded w-full"></div>
            <div className="h-4 bg-gray-200 rounded w-5/6"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !event) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
          {error || 'Event not found'}
        </div>
        <Link
          to="/events"
          className="mt-4 inline-block text-primary-600 hover:text-primary-700"
        >
          ← Back to Events
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Back Button */}
      <Link
        to="/events"
        className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-6"
      >
        <span className="mr-2">←</span>
        Back to Events
      </Link>

      {/* Hero Section */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden mb-8">
        <div className="md:flex">
          {/* Thumbnail */}
          <div className="md:w-1/3 lg:w-1/4">
            <div className="aspect-video md:aspect-square bg-gray-200 relative">
              {event.thumbnail_url ? (
                <img
                  src={event.thumbnail_url}
                  alt={event.event_name || event.title}
                  className="w-full h-full object-cover"
                  onError={(e) => {
                    e.target.style.display = 'none';
                    if (!e.target.parentElement.querySelector('.thumbnail-placeholder')) {
                      const placeholder = document.createElement('div');
                      placeholder.className = 'thumbnail-placeholder w-full h-full flex items-center justify-center text-gray-400 absolute inset-0';
                      placeholder.innerHTML = '<span class="text-6xl">🎤</span>';
                      e.target.parentElement.appendChild(placeholder);
                    }
                  }}
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center text-gray-400">
                  <span className="text-6xl">🎤</span>
                </div>
              )}
              <div className="absolute top-4 right-4">
                <span
                  className={`inline-flex items-center px-3 py-1 rounded-md text-sm font-medium border ${
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
          </div>

          {/* Content */}
          <div className="md:w-2/3 lg:w-3/4 p-6 md:p-8">
            <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-2">
              {event.event_name || event.title}
            </h1>
            {event.dj_name && event.dj_name !== 'Various Artists' && (
              <p className="text-xl text-gray-600 mb-4">{event.dj_name}</p>
            )}

            {/* Verification Status */}
            <div className="mb-4 p-3 rounded-lg bg-purple-50 border border-purple-200">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  {event.is_verified ? (
                    <>
                      <span className="text-green-600">✓</span>
                      <span className="font-medium text-green-800">Verified Event</span>
                    </>
                  ) : (
                    <>
                      <span className="text-yellow-600">⚠</span>
                      <span className="font-medium text-yellow-800">Unverified Event</span>
                    </>
                  )}
                </div>
                {isAuthenticated && (
                  <>
                    <button
                      onClick={handleConfirmEvent}
                      disabled={confirming}
                      className={`px-3 py-1 rounded-md text-sm font-medium ${
                        isConfirmed
                          ? 'bg-green-100 text-green-800 hover:bg-green-200'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      } disabled:opacity-50`}
                    >
                      {confirming
                        ? '...'
                        : isConfirmed
                        ? '✓ Confirmed'
                        : 'Confirm Attendance'}
                    </button>
                    {isInTop5 ? (
                      <button
                        onClick={handleRemoveFromTop5}
                        disabled={topEventLoading}
                        className="px-3 py-1 rounded-md text-sm font-medium bg-primary-100 text-primary-800 hover:bg-primary-200 disabled:opacity-50"
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
                            className="px-2 py-1 rounded text-xs font-medium bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-50"
                          >
                            #{order}
                          </button>
                        ))}
                      </div>
                    )}
                  </>
                )}
              </div>
              {event.confirmation_count > 0 && (
                <p className="text-sm text-gray-600">
                  {event.confirmation_count} {event.confirmation_count === 1 ? 'person has' : 'people have'} confirmed attending this event
                </p>
              )}
            </div>

            {/* Metadata */}
            <div className="flex flex-wrap items-center gap-4 mb-6 text-sm text-gray-600">
              {formatEventDate(event.event_date) && (
                <span className="flex items-center">
                  <span className="mr-1">📅</span>
                  {formatEventDate(event.event_date)}
                </span>
              )}
              {event.venue_location && (
                <span className="flex items-center">
                  <span className="mr-1">📍</span>
                  {event.venue_location}
                </span>
              )}
              {formatDuration(event.duration_minutes) && (
                <span className="flex items-center">
                  <span className="mr-1">⏱</span>
                  {formatDuration(event.duration_minutes)}
                </span>
              )}
              {linkedSets.length > 0 && (
                <span className="flex items-center">
                  <span className="mr-1">📹</span>
                  {linkedSets.length} {linkedSets.length === 1 ? 'set' : 'sets'} linked
                </span>
              )}
            </div>

            {/* Description */}
            {event.description && (
              <div className="mb-6">
                <p className="text-gray-700 whitespace-pre-wrap">{event.description}</p>
              </div>
            )}

            {/* Actions */}
            <div className="flex flex-wrap items-center gap-3">
              {isAuthenticated && (
                <button
                  onClick={() => setShowLinkForm(!showLinkForm)}
                  className="inline-flex items-center px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-md"
                >
                  🔗 Link Set to Event
                </button>
              )}
              {event.source_url && 
               (event.source_url.startsWith('http://') || event.source_url.startsWith('https://')) && (
                <a
                  href={event.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium rounded-md"
                >
                  <span className="mr-2">🔗</span>
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
            <div className="bg-white rounded-lg border border-gray-200 p-6">
              <h3 className="text-lg font-semibold mb-3">Link Set to Event</h3>
              <p className="text-sm text-gray-600 mb-4">
                Search for a set to link to this event.
              </p>
              
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Search Sets
                  </label>
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search by title or DJ name..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                </div>

                {searching && (
                  <div className="text-sm text-gray-600">Searching...</div>
                )}

                {searchResults.length > 0 && (
                  <div className="border border-gray-200 rounded-md max-h-60 overflow-y-auto">
                    {searchResults.map((set) => (
                      <div
                        key={set.id}
                        onClick={() => setSelectedSetId(set.id)}
                        className={`p-3 border-b border-gray-200 last:border-b-0 cursor-pointer hover:bg-purple-50 ${
                          selectedSetId === set.id ? 'bg-purple-100' : ''
                        }`}
                      >
                        <div className="font-medium text-gray-900">{set.title}</div>
                        <div className="text-sm text-gray-600">{set.dj_name}</div>
                      </div>
                    ))}
                  </div>
                )}

                {searchQuery.trim() && !searching && searchResults.length === 0 && (
                  <div className="text-sm text-gray-600">No sets found</div>
                )}


                <div className="flex gap-2 pt-2">
                  <button
                    onClick={handleLinkSet}
                    disabled={!selectedSetId || linkingSet}
                    className="flex-1 px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-medium rounded-md"
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
                    className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-700 font-medium rounded-md"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Linked Sets Section */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">Linked Sets</h2>
              {linkedSets.length > 0 && (
                <span className="text-sm text-gray-600">{linkedSets.length} {linkedSets.length === 1 ? 'set' : 'sets'}</span>
              )}
            </div>
            {linkedSetsLoading ? (
              <div className="space-y-4">
                {[1, 2].map((i) => (
                  <div key={i} className="bg-gray-100 animate-pulse rounded-lg h-24"></div>
                ))}
              </div>
            ) : linkedSets.length === 0 ? (
              <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 text-center">
                <p className="text-gray-600 mb-2">No sets linked yet</p>
                <p className="text-sm text-gray-500 mb-4">
                  Sets linked to this event will appear here
                </p>
                {isAuthenticated && (
                  <button
                    onClick={() => setShowLinkForm(true)}
                    className="inline-flex items-center px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white font-medium rounded-md"
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
                    className="block bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-lg p-4 transition-colors"
                  >
                    <div className="flex items-center gap-4">
                      {set.thumbnail_url && (
                        <img
                          src={set.thumbnail_url}
                          alt={set.title}
                          className="w-20 h-20 object-cover rounded"
                        />
                      )}
                      <div className="flex-1">
                        <h3 className="font-medium text-gray-900">{set.title}</h3>
                        <p className="text-sm text-gray-600">{set.dj_name}</p>
                        <div className="flex items-center gap-3 mt-1">
                          <span className={`inline-flex items-center px-2 py-1 rounded text-xs font-medium ${
                            set.source_type === 'youtube' 
                              ? 'bg-red-100 text-red-800' 
                              : 'bg-orange-100 text-orange-800'
                          }`}>
                            {set.source_type === 'youtube' ? '▶️ YouTube' : '🎵 SoundCloud'}
                          </span>
                          {set.duration_minutes && (
                            <span className="text-xs text-gray-500">
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
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold mb-4">Event Details</h3>
            <dl className="space-y-3 text-sm">
              <div>
                <dt className="text-gray-500">Status</dt>
                <dd className="font-medium text-gray-900">
                  {event.is_verified ? 'Verified' : 'Unverified'}
                </dd>
              </div>
              <div>
                <dt className="text-gray-500">Confirmations</dt>
                <dd className="font-medium text-gray-900">
                  {event.confirmation_count || 0}
                </dd>
              </div>
              <div>
                <dt className="text-gray-500">Linked Sets</dt>
                <dd className="font-medium text-gray-900">
                  {linkedSets.length}
                </dd>
              </div>
              <div>
                <dt className="text-gray-500">Created</dt>
                <dd className="font-medium text-gray-900">
                  {new Date(event.created_at).toLocaleDateString()}
                </dd>
              </div>
            </dl>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EventDetailsPage;
