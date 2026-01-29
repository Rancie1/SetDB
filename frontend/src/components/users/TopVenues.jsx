/**
 * Top Venues component.
 * Displays a user's top 5 venues (same pattern as Top Tracks; venue is free text).
 */

import { useEffect, useState } from 'react';
import * as usersService from '../../services/usersService';

const TopVenues = ({ userId, isOwnProfile, onRemove }) => {
  const [topVenues, setTopVenues] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newVenue, setNewVenue] = useState('');
  const [adding, setAdding] = useState(false);

  useEffect(() => {
    loadTopVenues();
  }, [userId]);

  const loadTopVenues = async () => {
    setLoading(true);
    try {
      const response = await usersService.getUserTopVenues(userId);
      setTopVenues(response.data || []);
    } catch (error) {
      console.error('Failed to load top venues:', error);
      setTopVenues([]);
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = async (e) => {
    e.preventDefault();
    const name = newVenue.trim();
    if (!name || adding) return;
    setAdding(true);
    try {
      const order = topVenues.length < 5 ? topVenues.length + 1 : 5;
      await usersService.addTopVenue(name, order);
      setNewVenue('');
      loadTopVenues();
      onRemove?.();
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to add venue');
    } finally {
      setAdding(false);
    }
  };

  const handleRemove = async (venueId) => {
    try {
      await usersService.removeTopVenue(venueId);
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
          <div key={i} className="bg-gray-100 animate-pulse rounded-lg h-16"></div>
        ))}
      </div>
    );
  }

  if (topVenues.length === 0 && !isOwnProfile) return null;

  return (
    <div>
      <h3 className="text-xl font-bold mb-4">Top 5 Venues</h3>
      <div className="flex flex-wrap gap-3 items-center">
        {topVenues.map((v, index) => (
          <div
            key={v.id}
            className="flex items-center gap-2 bg-white border border-gray-200 rounded-lg px-4 py-2 shadow-sm"
          >
            {isOwnProfile && (
              <span className="bg-primary-600 text-white text-xs font-bold w-6 h-6 rounded flex items-center justify-center">
                {v.order || index + 1}
              </span>
            )}
            <span className="font-medium text-gray-900">{v.venue_name}</span>
            {isOwnProfile && (
              <button
                type="button"
                onClick={() => handleRemove(v.id)}
                className="text-red-600 hover:text-red-700 text-sm"
              >
                ×
              </button>
            )}
          </div>
        ))}
      </div>
      {isOwnProfile && topVenues.length < 5 && (
        <form onSubmit={handleAdd} className="mt-4 flex gap-2 flex-wrap">
          <input
            type="text"
            value={newVenue}
            onChange={(e) => setNewVenue(e.target.value)}
            placeholder="Add a venue name"
            className="px-3 py-2 border border-gray-300 rounded-md text-sm w-48"
          />
          <button
            type="submit"
            disabled={adding || !newVenue.trim()}
            className="px-4 py-2 bg-primary-600 text-white rounded-md text-sm font-medium disabled:opacity-50"
          >
            {adding ? 'Adding…' : 'Add'}
          </button>
        </form>
      )}
      {topVenues.length === 0 && isOwnProfile && (
        <p className="text-gray-500 text-sm mt-2">Add your top 5 venues above.</p>
      )}
    </div>
  );
};

export default TopVenues;
