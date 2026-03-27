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
          <div key={i} className="bg-surface-700 animate-pulse rounded-xl aspect-square"></div>
        ))}
      </div>
    );
  }

  if (topTracks.length === 0 && !isOwnProfile) return null;

  if (topTracks.length === 0) {
    return (
      <div className="bg-surface-800 border border-white/5 rounded-xl p-8 text-center">
        <p className="text-slate-400 mb-1">No top tracks yet</p>
        <p className="text-slate-500 text-sm">Mark tracks as your favorites to display them here</p>
      </div>
    );
  }

  return (
    <div>
      <h3 className="text-lg font-semibold mb-4 text-slate-100">Top 5 Tracks</h3>
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {topTracks.map((track, index) => (
          <div key={track.id} className="relative">
            {isOwnProfile && (
              <div className="absolute top-2 left-2 z-10 bg-primary-600 text-white text-xs font-bold px-2 py-1 rounded-md shadow-lg">
                #{track.top_track_order || index + 1}
              </div>
            )}
            <Link
              to={`/tracks/${track.id}`}
              className="block bg-surface-800 rounded-xl border border-white/5 p-3 hover:border-primary-500/30 hover:bg-surface-700 transition-colors cursor-pointer"
            >
              {track.thumbnail_url && (
                <img
                  src={track.thumbnail_url}
                  alt={track.track_name}
                  className="w-full h-32 object-cover rounded-lg mb-3"
                />
              )}
              <p className="text-sm font-medium text-slate-100 line-clamp-2">{track.track_name}</p>
              {track.artist_name && (
                <p className="text-xs text-slate-400 mt-1 line-clamp-1">{track.artist_name}</p>
              )}
              {track.average_rating && (
                <div className="mt-2 flex items-center gap-1 text-xs text-slate-500">
                  <span>{track.average_rating.toFixed(1)}</span>
                  {track.rating_count > 0 && <span>({track.rating_count})</span>}
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
