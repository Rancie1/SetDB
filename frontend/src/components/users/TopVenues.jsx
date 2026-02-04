/**
 * Top Venues component.
 * Displays a user's top 5 venues (venue entities: search or create, then add by venue_id).
 */

import { useEffect, useState } from 'react';
import * as usersService from '../../services/usersService';
import * as venuesService from '../../services/venuesService';

const TopVenues = ({ userId, isOwnProfile, onRemove }) => {
  const [topVenues, setTopVenues] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [adding, setAdding] = useState(false);
  const [createName, setCreateName] = useState('');
  const [createLocation, setCreateLocation] = useState('');
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    loadTopVenues();
  }, [userId]);

  const loadTopVenues = async () => {
    setLoading(true);
    try {
      const response = await usersService.getUserTopVenues(userId);
      setTopVenues(Array.isArray(response?.data) ? response.data : []);
    } catch (error) {
      console.error('Failed to load top venues:', error);
      setTopVenues([]);
    } finally {
      setLoading(false);
    }
  };

  const runSearch = async () => {
    const q = search.trim();
    if (!q) {
      setSearchResults([]);
      return;
    }
    setSearching(true);
    try {
      const data = await venuesService.searchVenues(q, 1, 10);
      setSearchResults(data?.items ?? []);
    } catch {
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  };

  const handleAddVenue = async (venueId) => {
    if (adding || !venueId) return;
    setAdding(true);
    try {
      const order = topVenues.length < 5 ? topVenues.length + 1 : 5;
      await usersService.addTopVenue(venueId, order);
      setSearch('');
      setSearchResults([]);
      loadTopVenues();
      onRemove?.();
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to add venue');
    } finally {
      setAdding(false);
    }
  };

  const handleCreateAndAdd = async (e) => {
    e.preventDefault();
    const name = createName.trim();
    if (!name || creating) return;
    setCreating(true);
    try {
      const venue = await venuesService.createVenue({
        name,
        location: createLocation.trim() || undefined,
      });
      const order = topVenues.length < 5 ? topVenues.length + 1 : 5;
      await usersService.addTopVenue(venue.id, order);
      setCreateName('');
      setCreateLocation('');
      loadTopVenues();
      onRemove?.();
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to create or add venue');
    } finally {
      setCreating(false);
    }
  };

  const handleRemove = async (userTopVenueId) => {
    try {
      await usersService.removeTopVenue(userTopVenueId);
      loadTopVenues();
      onRemove?.();
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to remove venue');
    }
  };

  if (loading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="bg-gray-100 animate-pulse rounded-lg h-16" />
        ))}
      </div>
    );
  }

  if (topVenues.length === 0 && !isOwnProfile) return null;

  const displayName = (v) => v.name ?? v.venue_name;
  const displayId = (v) => v.id;

  return (
    <div>
      <h3 className="text-xl font-bold mb-4">Top 5 Venues</h3>
      <div className="flex flex-wrap gap-3 items-center">
        {topVenues.map((v, index) => (
          <div
            key={displayId(v)}
            className="flex items-center gap-2 bg-white border border-gray-200 rounded-lg px-4 py-2 shadow-sm"
          >
            {isOwnProfile && (
              <span className="bg-primary-600 text-white text-xs font-bold w-6 h-6 rounded flex items-center justify-center">
                {v.order ?? index + 1}
              </span>
            )}
            <span className="font-medium text-gray-900">{displayName(v)}</span>
            {v.location && (
              <span className="text-gray-500 text-sm">({v.location})</span>
            )}
            {isOwnProfile && (
              <button
                type="button"
                onClick={() => handleRemove(displayId(v))}
                className="text-red-600 hover:text-red-700 text-sm"
              >
                ×
              </button>
            )}
          </div>
        ))}
      </div>
      {isOwnProfile && topVenues.length < 5 && (
        <div className="mt-4 space-y-3">
          <div className="flex gap-2 flex-wrap items-center">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              onBlur={runSearch}
              onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), runSearch())}
              placeholder="Search venues"
              className="px-3 py-2 border border-gray-300 rounded-md text-sm w-48"
            />
            <button
              type="button"
              onClick={runSearch}
              disabled={searching}
              className="px-3 py-2 bg-gray-200 rounded-md text-sm"
            >
              {searching ? 'Searching…' : 'Search'}
            </button>
          </div>
          {searchResults.length > 0 && (
            <ul className="border border-gray-200 rounded-md divide-y max-h-32 overflow-y-auto">
              {searchResults.map((venue) => (
                <li key={venue.id} className="flex justify-between items-center px-3 py-2">
                  <span>{venue.name}{venue.location ? ` — ${venue.location}` : ''}</span>
                  <button
                    type="button"
                    onClick={() => handleAddVenue(venue.id)}
                    disabled={adding}
                    className="text-primary-600 text-sm font-medium"
                  >
                    Add
                  </button>
                </li>
              ))}
            </ul>
          )}
          <form onSubmit={handleCreateAndAdd} className="flex gap-2 flex-wrap items-end">
            <input
              type="text"
              value={createName}
              onChange={(e) => setCreateName(e.target.value)}
              placeholder="Or create venue name"
              className="px-3 py-2 border border-gray-300 rounded-md text-sm w-48"
            />
            <input
              type="text"
              value={createLocation}
              onChange={(e) => setCreateLocation(e.target.value)}
              placeholder="Location (optional)"
              className="px-3 py-2 border border-gray-300 rounded-md text-sm w-40"
            />
            <button
              type="submit"
              disabled={creating || !createName.trim()}
              className="px-4 py-2 bg-primary-600 text-white rounded-md text-sm font-medium disabled:opacity-50"
            >
              {creating ? 'Adding…' : 'Create & add'}
            </button>
          </form>
        </div>
      )}
      {topVenues.length === 0 && isOwnProfile && (
        <p className="text-gray-500 text-sm mt-2">Search or create a venue to add to your top 5.</p>
      )}
    </div>
  );
};

export default TopVenues;
