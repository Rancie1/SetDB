import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import useAuthStore from '../store/authStore';
import * as artistsService from '../services/artistsService';

const ArtistPage = () => {
  const { id, name } = useParams();
  const { isAuthenticated } = useAuthStore();

  const [artist, setArtist] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [editing, setEditing] = useState(false);
  const [editForm, setEditForm] = useState({ bio: '', instagram_url: '', soundcloud_url: '' });
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('tracks');

  useEffect(() => {
    loadArtist();
  }, [id, name]);

  const loadArtist = async () => {
    setLoading(true);
    setError(null);
    try {
      let response;
      if (id) {
        response = await artistsService.getArtist(id);
      } else if (name) {
        const lookupResp = await artistsService.getArtistByName(name);
        const artistId = lookupResp.data.id;
        response = await artistsService.getArtist(artistId);
      }
      setArtist(response.data);
      setEditForm({
        bio: response.data.bio || '',
        instagram_url: response.data.instagram_url || '',
        soundcloud_url: response.data.soundcloud_url || '',
      });
    } catch (err) {
      setError(err.response?.data?.detail || 'Artist not found');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!artist) return;
    setSaving(true);
    try {
      const response = await artistsService.updateArtist(artist.id, editForm);
      setArtist(prev => ({ ...prev, ...response.data }));
      setEditing(false);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to update');
    } finally {
      setSaving(false);
    }
  };

  const genres = artist?.genres ? artist.genres.split(', ').filter(Boolean) : [];

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="animate-pulse">
          <div className="flex items-center gap-6 mb-8">
            <div className="w-40 h-40 bg-surface-700 rounded-full"></div>
            <div className="flex-1 space-y-3">
              <div className="h-8 bg-surface-700 rounded-xl w-1/3"></div>
              <div className="h-4 bg-surface-700 rounded w-1/4"></div>
              <div className="h-4 bg-surface-700 rounded w-1/5"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (error || !artist) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-6 text-center">
          <p className="text-red-400 text-lg font-medium">{error || 'Artist not found'}</p>
          <p className="text-red-400/70 text-sm mt-2">
            This artist may not have been imported from Spotify yet. Try searching for one of their tracks first.
          </p>
          <Link to="/tracks" className="mt-4 inline-block text-primary-400 hover:text-primary-300 font-medium">
            Browse Tracks
          </Link>
        </div>
      </div>
    );
  }

  const tabs = [
    { key: 'tracks', label: 'Tracks', count: artist.tracks?.length || 0 },
    { key: 'sets', label: 'Sets', count: artist.sets?.length || 0 },
    { key: 'events', label: 'Events', count: artist.events?.length || 0 },
  ];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Artist Header */}
      <div className="flex flex-col md:flex-row items-start gap-6 mb-8">
        {artist.image_url ? (
          <img
            src={artist.image_url}
            alt={artist.name}
            className="w-40 h-40 rounded-full object-cover shadow-lg flex-shrink-0"
          />
        ) : (
          <div className="w-40 h-40 rounded-full bg-primary-600/20 border border-primary-500/30 flex items-center justify-center text-primary-400 text-5xl font-bold flex-shrink-0">
            {artist.name.charAt(0).toUpperCase()}
          </div>
        )}

        <div className="flex-1">
          <h1 className="text-4xl font-bold text-slate-100 mb-2">{artist.name}</h1>

          {genres.length > 0 && (
            <div className="flex flex-wrap gap-2 mb-3">
              {genres.map((genre) => (
                <span key={genre} className="px-3 py-1 bg-surface-700 text-slate-400 text-sm rounded-full border border-white/5">
                  {genre}
                </span>
              ))}
            </div>
          )}

          {/* Social Links */}
          <div className="flex items-center gap-4 mb-4">
            {artist.spotify_url && (
              <a href={artist.spotify_url} target="_blank" rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 text-sm text-green-400 hover:text-green-300 font-medium transition-colors">
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.66 0 12 0zm5.521 17.34c-.24.359-.66.48-1.021.24-2.82-1.74-6.36-2.101-10.561-1.141-.418.122-.779-.179-.899-.539-.12-.421.18-.78.54-.9 4.56-1.021 8.52-.6 11.64 1.32.42.18.479.659.301 1.02zm1.44-3.3c-.301.42-.841.6-1.262.3-3.239-1.98-8.159-2.58-11.939-1.38-.479.12-1.02-.12-1.14-.6-.12-.48.12-1.021.6-1.141C9.6 9.9 15 10.561 18.72 12.84c.361.181.54.78.241 1.2zm.12-3.36C15.24 8.4 8.82 8.16 5.16 9.301c-.6.179-1.2-.181-1.38-.721-.18-.601.18-1.2.72-1.381 4.26-1.26 11.28-1.02 15.721 1.621.539.3.719 1.02.419 1.56-.299.421-1.02.599-1.559.3z"/>
                </svg>
                Spotify
              </a>
            )}
            {artist.soundcloud_url && (
              <a href={artist.soundcloud_url} target="_blank" rel="noopener noreferrer"
                className="text-sm text-orange-400 hover:text-orange-300 font-medium transition-colors">
                SoundCloud
              </a>
            )}
            {artist.instagram_url && (
              <a href={artist.instagram_url} target="_blank" rel="noopener noreferrer"
                className="text-sm text-pink-400 hover:text-pink-300 font-medium transition-colors">
                Instagram
              </a>
            )}
          </div>

          {/* Bio */}
          {!editing && artist.bio && (
            <p className="text-slate-400 whitespace-pre-wrap mb-3 text-sm leading-relaxed">{artist.bio}</p>
          )}

          {/* Edit section */}
          {isAuthenticated() && !editing && (
            <button
              onClick={() => setEditing(true)}
              className="text-sm text-slate-500 hover:text-primary-400 transition-colors cursor-pointer"
            >
              Edit profile info
            </button>
          )}

          {editing && (
            <div className="mt-3 space-y-3 max-w-lg">
              <div>
                <label className="block text-sm font-medium text-slate-400 mb-1">Bio</label>
                <textarea
                  value={editForm.bio}
                  onChange={(e) => setEditForm(prev => ({ ...prev, bio: e.target.value }))}
                  rows={3}
                  className="w-full bg-surface-700 border border-white/10 text-slate-100 rounded-xl px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-400 mb-1">Instagram URL</label>
                <input
                  type="url"
                  value={editForm.instagram_url}
                  onChange={(e) => setEditForm(prev => ({ ...prev, instagram_url: e.target.value }))}
                  placeholder="https://instagram.com/..."
                  className="w-full bg-surface-700 border border-white/10 text-slate-100 placeholder-slate-500 rounded-xl px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-400 mb-1">SoundCloud URL</label>
                <input
                  type="url"
                  value={editForm.soundcloud_url}
                  onChange={(e) => setEditForm(prev => ({ ...prev, soundcloud_url: e.target.value }))}
                  placeholder="https://soundcloud.com/..."
                  className="w-full bg-surface-700 border border-white/10 text-slate-100 placeholder-slate-500 rounded-xl px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none"
                />
              </div>
              <div className="flex gap-2">
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="px-4 py-2 bg-primary-600 hover:bg-primary-500 text-white text-sm font-medium rounded-xl disabled:opacity-50 cursor-pointer transition-colors"
                >
                  {saving ? 'Saving...' : 'Save'}
                </button>
                <button
                  onClick={() => setEditing(false)}
                  className="px-4 py-2 bg-surface-700 hover:bg-surface-600 text-slate-300 text-sm font-medium rounded-xl border border-white/5 cursor-pointer transition-colors"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Content Tabs */}
      <div className="border-b border-white/5 mb-6">
        <div className="flex gap-8">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`pb-3 text-sm font-medium transition-colors border-b-2 cursor-pointer ${
                activeTab === tab.key
                  ? 'border-primary-400 text-primary-400'
                  : 'border-transparent text-slate-500 hover:text-slate-300'
              }`}
            >
              {tab.label} ({tab.count})
            </button>
          ))}
        </div>
      </div>

      {/* Tracks Tab */}
      {activeTab === 'tracks' && (
        <div>
          {artist.tracks?.length === 0 ? (
            <p className="text-slate-500 text-center py-8">No tracks found for this artist.</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {artist.tracks.map((track) => (
                <Link
                  key={track.id}
                  to={`/tracks/${track.id}`}
                  className="bg-surface-800 rounded-xl border border-white/5 p-4 hover:border-primary-500/30 hover:bg-surface-700 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    {track.thumbnail_url && (
                      <img src={track.thumbnail_url} alt={track.track_name} className="w-12 h-12 rounded-lg object-cover flex-shrink-0" />
                    )}
                    <div className="flex-1 min-w-0">
                      <h4 className="font-semibold text-sm text-slate-200 truncate">{track.track_name}</h4>
                      <p className="text-xs text-slate-500 truncate">{track.artist_name}</p>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Sets Tab */}
      {activeTab === 'sets' && (
        <div>
          {artist.sets?.length === 0 ? (
            <p className="text-slate-500 text-center py-8">No sets found for this artist.</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {artist.sets.map((set) => (
                <Link
                  key={set.id}
                  to={`/sets/${set.id}`}
                  className="bg-surface-800 rounded-xl border border-white/5 p-4 hover:border-primary-500/30 hover:bg-surface-700 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    {set.thumbnail_url && (
                      <img src={set.thumbnail_url} alt={set.title} className="w-12 h-12 rounded-lg object-cover flex-shrink-0" />
                    )}
                    <div className="flex-1 min-w-0">
                      <h4 className="font-semibold text-sm text-slate-200 truncate">{set.title}</h4>
                      <p className="text-xs text-slate-500 truncate">{set.dj_name}</p>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Events Tab */}
      {activeTab === 'events' && (
        <div>
          {artist.events?.length === 0 ? (
            <p className="text-slate-500 text-center py-8">No events found for this artist.</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {artist.events.map((event) => (
                <Link
                  key={event.id}
                  to={`/events/${event.id}`}
                  className="bg-surface-800 rounded-xl border border-white/5 p-4 hover:border-primary-500/30 hover:bg-surface-700 transition-colors"
                >
                  <div className="flex-1 min-w-0">
                    <h4 className="font-semibold text-slate-200 truncate">{event.title}</h4>
                    {event.dj_name && <p className="text-sm text-slate-500">{event.dj_name}</p>}
                    {event.event_date && (
                      <p className="text-xs text-slate-500 mt-1">{new Date(event.event_date).toLocaleDateString()}</p>
                    )}
                    {event.venue_location && (
                      <p className="text-xs text-slate-500">{event.venue_location}</p>
                    )}
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ArtistPage;
