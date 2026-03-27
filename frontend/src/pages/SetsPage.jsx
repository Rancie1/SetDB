/**
 * Sets page.
 *
 * Single unified search across DB and SoundCloud.
 * When not searching, shows all sets in Deckd.
 * Clicking a SoundCloud result auto-imports it and navigates to the detail page.
 */

import { useEffect, useState, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import * as setsService from '../services/setsService';
import useAuthStore from '../store/authStore';

const sourceBadge = (sourceType) => {
  switch (sourceType?.toLowerCase()) {
    case 'youtube': return 'bg-red-500/20 text-red-300 border border-red-500/30';
    case 'soundcloud': return 'bg-orange-500/20 text-orange-300 border border-orange-500/30';
    case 'live': return 'bg-violet-500/20 text-violet-300 border border-violet-500/30';
    default: return 'bg-white/5 text-slate-400 border border-white/10';
  }
};

const sourceLabel = (sourceType) => {
  switch (sourceType?.toLowerCase()) {
    case 'youtube': return 'YouTube';
    case 'soundcloud': return 'SoundCloud';
    case 'live': return 'Live';
    default: return sourceType || 'Unknown';
  }
};

const SetsPage = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthStore();

  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);

  const [dbSets, setDbSets] = useState([]);
  const [dbLoading, setDbLoading] = useState(false);
  const [dbError, setDbError] = useState(null);
  const [sortBy, setSortBy] = useState('created_at');
  const [pagination, setPagination] = useState({ page: 1, limit: 20, total: 0, pages: 0 });

  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [importingId, setImportingId] = useState(null);

  const searchTimeout = useRef(null);

  useEffect(() => {
    if (!isSearching) loadDbSets();
  }, [pagination.page, sortBy, isSearching]);

  useEffect(() => {
    if (searchTimeout.current) clearTimeout(searchTimeout.current);
    if (!searchQuery.trim()) { setIsSearching(false); setSearchResults([]); return; }
    setIsSearching(true);
    setSearchLoading(true);
    searchTimeout.current = setTimeout(() => performSearch(searchQuery.trim()), 400);
    return () => { if (searchTimeout.current) clearTimeout(searchTimeout.current); };
  }, [searchQuery]);

  const loadDbSets = async () => {
    setDbLoading(true); setDbError(null);
    try {
      const response = await setsService.getSets({ sort: sortBy }, pagination.page, pagination.limit);
      setDbSets(response.data.items || []);
      setPagination(prev => ({ ...prev, total: response.data.total || 0, pages: response.data.pages || 0 }));
    } catch (err) {
      setDbError(err.response?.data?.detail || 'Failed to load sets');
      setDbSets([]);
    } finally { setDbLoading(false); }
  };

  const performSearch = async (query) => {
    setSearchLoading(true);
    try {
      const [dbResponse, scResponse] = await Promise.all([
        setsService.getSets({ search: query }, 1, 10),
        setsService.searchSoundCloudSets(query, 15).catch(() => ({ data: [] })),
      ]);
      const dbItems = (dbResponse.data.items || []).map(s => ({ ...s, _source: 'db', _dbId: s.id }));
      const scItems = (scResponse.data || []).map(s => ({ ...s, _source: 'soundcloud', _dbId: null, _scId: s.id }));
      const dbUrls = new Set(dbItems.map(s => s.source_url).filter(Boolean));
      setSearchResults([...dbItems, ...scItems.filter(s => !dbUrls.has(s.soundcloud_url))]);
    } catch (err) { setSearchResults([]); }
    finally { setSearchLoading(false); }
  };

  const handleSetClick = async (set) => {
    if (set._dbId) { navigate(`/sets/${set._dbId}`); return; }
    if (!isAuthenticated()) { navigate('/login'); return; }
    if (!set.soundcloud_url) return;
    setImportingId(set._scId);
    try {
      const response = await setsService.importSetFromSoundCloud(set.soundcloud_url);
      navigate(`/sets/${response.data.id}`);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to import set');
    } finally { setImportingId(null); }
  };

  const handleSortChange = (newSort) => {
    setSortBy(newSort);
    setPagination(prev => ({ ...prev, page: 1 }));
  };

  const handleClear = () => { setSearchQuery(''); setIsSearching(false); setSearchResults([]); };

  const formatDuration = (ms) => {
    if (!ms) return '';
    const totalMinutes = Math.floor(ms / 60000);
    const hours = Math.floor(totalMinutes / 60);
    const mins = totalMinutes % 60;
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
  };

  const formatDurationMinutes = (minutes) => {
    if (!minutes) return '';
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
  };

  const MusicIcon = () => (
    <svg viewBox="0 0 24 24" fill="currentColor" className="w-8 h-8 text-slate-600">
      <path d="M12 3v10.55A4 4 0 1 0 14 17V7h4V3h-6z"/>
    </svg>
  );

  const renderSetCard = (set, index) => {
    const isDb = set._source === 'db';
    const isImporting = importingId === set._scId;
    const cardClass = "block bg-surface-800 rounded-xl border border-white/5 overflow-hidden hover:border-primary-500/30 hover:bg-surface-700 transition-colors cursor-pointer";

    const cardInner = (
      <div className="flex">
        <div className="w-36 h-24 flex-shrink-0 bg-surface-700 relative overflow-hidden">
          {set.thumbnail_url ? (
            <img src={set.thumbnail_url} alt={set.title} className="w-full h-full object-cover" onError={(e) => { e.target.style.display = 'none'; }} />
          ) : (
            <div className="w-full h-full flex items-center justify-center"><MusicIcon /></div>
          )}
          {set.source_type && (
            <span className={`absolute top-1 right-1 px-1.5 py-0.5 rounded text-[10px] font-medium ${sourceBadge(set.source_type)}`}>
              {sourceLabel(set.source_type)}
            </span>
          )}
          {!isDb && (
            <span className={`absolute top-1 right-1 px-1.5 py-0.5 rounded text-[10px] font-medium ${sourceBadge('soundcloud')}`}>
              SoundCloud
            </span>
          )}
        </div>
        <div className="flex-1 p-3 min-w-0">
          <div className="flex items-center gap-2 mb-0.5">
            <h3 className="font-semibold text-slate-100 truncate text-sm">{set.title}</h3>
            {isImporting && <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-primary-400 flex-shrink-0"></div>}
          </div>
          <p className="text-xs text-slate-400 truncate">{set.dj_name}</p>
          <div className="flex items-center gap-3 mt-2 text-xs text-slate-500">
            {isDb && set.duration_minutes > 0 && <span>{formatDurationMinutes(set.duration_minutes)}</span>}
            {!isDb && set.duration_ms > 0 && <span>{formatDuration(set.duration_ms)}</span>}
            {!isDb && set.playback_count > 0 && <span>{set.playback_count.toLocaleString()} plays</span>}
            {set.source_type === 'live' && set.recording_url && <span className="text-violet-400">Has Recording</span>}
          </div>
        </div>
      </div>
    );

    if (isDb) {
      return <Link key={`db-${set._dbId}-${index}`} to={`/sets/${set._dbId}`} className={cardClass}>{cardInner}</Link>;
    }
    return (
      <button key={`sc-${set._scId}-${index}`} onClick={() => handleSetClick(set)} disabled={isImporting}
        className={`w-full text-left ${cardClass} disabled:opacity-60`}>
        {cardInner}
      </button>
    );
  };

  const Skeleton = () => (
    <div className="space-y-3">
      {[1,2,3,4,5].map(i => <div key={i} className="bg-surface-700 animate-pulse rounded-xl h-24"></div>)}
    </div>
  );

  const EmptyState = ({ title, subtitle }) => (
    <div className="bg-surface-800 border border-white/5 rounded-xl p-8 text-center">
      <p className="text-slate-400 mb-1">{title}</p>
      <p className="text-slate-500 text-sm">{subtitle}</p>
    </div>
  );

  const Pagination = ({ page, pages, onChange }) => pages > 1 && (
    <div className="flex items-center justify-center gap-2 mt-6">
      <button onClick={() => onChange(page - 1)} disabled={page === 1}
        className="px-4 py-2 bg-surface-800 border border-white/5 rounded-lg text-sm text-slate-300 hover:text-white hover:bg-surface-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors cursor-pointer">
        Previous
      </button>
      <span className="px-4 py-2 text-sm text-slate-500">{page} / {pages}</span>
      <button onClick={() => onChange(page + 1)} disabled={page >= pages}
        className="px-4 py-2 bg-surface-800 border border-white/5 rounded-lg text-sm text-slate-300 hover:text-white hover:bg-surface-700 disabled:opacity-30 disabled:cursor-not-allowed transition-colors cursor-pointer">
        Next
      </button>
    </div>
  );

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2 text-slate-100">Sets</h1>
        <p className="text-slate-400">Search across Deckd and SoundCloud — or browse what's already here.</p>
      </div>

      {/* Search Bar */}
      <div className="mb-6">
        <div className="relative">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search for any DJ set, mix, or artist..."
            className="w-full px-4 py-3 pl-11 bg-surface-800 border border-white/10 text-slate-100 placeholder-slate-500 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none text-sm"
          />
          <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
            <svg className="w-5 h-5 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          {searchQuery && (
            <button onClick={handleClear} className="absolute inset-y-0 right-0 flex items-center pr-3 text-slate-500 hover:text-slate-300 cursor-pointer">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
        {isSearching && !searchLoading && searchResults.length > 0 && (
          <p className="text-xs text-slate-500 mt-2">{searchResults.length} results from Deckd and SoundCloud</p>
        )}
      </div>

      {isSearching ? (
        <div>
          {searchLoading ? <Skeleton /> : searchResults.length === 0
            ? <EmptyState title="No sets found" subtitle="Try a different search term" />
            : <div className="space-y-3">{searchResults.map((set, i) => renderSetCard(set, i))}</div>
          }
        </div>
      ) : (
        <div>
          {/* Sort Options */}
          <div className="flex items-center gap-3 flex-wrap mb-6">
            <span className="text-sm text-slate-500">Sort by:</span>
            {[
              { value: 'created_at', label: 'Newest' },
              { value: 'title', label: 'Title' },
              { value: 'dj_name', label: 'DJ Name' },
            ].map((option) => (
              <button key={option.value} onClick={() => handleSortChange(option.value)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors cursor-pointer ${
                  sortBy === option.value ? 'bg-primary-600 text-white' : 'bg-surface-700 text-slate-400 hover:bg-surface-600 hover:text-slate-200'
                }`}>
                {option.label}
              </button>
            ))}
          </div>

          {pagination.total > 0 && (
            <p className="text-sm text-slate-500 mb-4">{dbSets.length} of {pagination.total} sets</p>
          )}

          {dbLoading ? <Skeleton />
            : dbError ? (
              <div className="bg-red-500/10 border border-red-500/20 text-red-400 px-4 py-3 rounded-xl">{dbError}</div>
            ) : dbSets.length === 0 ? (
              <EmptyState title="No sets yet" subtitle="Search above to find and import sets from SoundCloud" />
            ) : (
              <div className="space-y-3">
                {dbSets.map((set, i) => renderSetCard({ ...set, _source: 'db', _dbId: set.id }, i))}
              </div>
            )
          }

          <Pagination page={pagination.page} pages={pagination.pages}
            onChange={(p) => setPagination(prev => ({ ...prev, page: p }))} />
        </div>
      )}
    </div>
  );
};

export default SetsPage;
