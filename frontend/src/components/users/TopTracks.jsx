/**
 * Top Tracks component.
 * 
 * Displays a user's top 5 tracks with numbered badges.
 */

import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import * as usersService from '../../services/usersService';

const TopTracks = ({ userId, isOwnProfile }) => {
  const [topTracks, setTopTracks] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadTopTracks();
  }, [userId]);

  const loadTopTracks = async () => {
    setLoading(true);
    try {
      const response = await usersService.getUserTopTracks(userId);
      setTopTracks(response.data || []);
    } catch (error) {
      console.error('Failed to load top tracks:', error);
      setTopTracks([]);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="bg-gray-100 animate-pulse rounded-lg aspect-square"></div>
        ))}
      </div>
    );
  }

  if (topTracks.length === 0 && !isOwnProfile) {
    return null; // Don't show empty state for other users
  }

  if (topTracks.length === 0) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
        <p className="text-gray-600 mb-2">No top tracks yet</p>
        <p className="text-gray-400 text-sm">
          Mark tracks as your favorites to display them here
        </p>
      </div>
    );
  }

  return (
    <div>
      <h3 className="text-xl font-bold mb-4">Top 5 Tracks</h3>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {topTracks.map((track, index) => (
          <div key={track.id} className="relative">
            {isOwnProfile && (
              <div className="absolute top-2 left-2 z-10 bg-primary-600 text-white text-sm font-bold px-2 py-1 rounded shadow-lg">
                #{track.top_track_order || index + 1}
              </div>
            )}
            <Link
              to={`/tracks/${track.id}`}
              className="block bg-white rounded-lg border border-gray-200 p-3 hover:shadow-md transition-shadow"
            >
              {track.thumbnail_url && (
                <img
                  src={track.thumbnail_url}
                  alt={track.track_name}
                  className="w-full h-32 object-cover rounded mb-2"
                />
              )}
              <div className="mb-2">
                <p className="text-sm font-medium text-gray-900 line-clamp-2">
                  {track.track_name}
                </p>
                {track.artist_name && (
                  <p className="text-xs text-gray-600 mt-1 line-clamp-1">
                    {track.artist_name}
                  </p>
                )}
              </div>
              {track.average_rating && (
                <div className="mt-2 flex items-center gap-1 text-xs text-gray-600">
                  <span className="text-yellow-500">⭐</span>
                  <span>{track.average_rating.toFixed(1)}</span>
                  {track.rating_count > 0 && (
                    <span className="text-gray-500">({track.rating_count})</span>
                  )}
                </div>
              )}
            </Link>
          </div>
        ))}
      </div>
    </div>
  );
};

export default TopTracks;
