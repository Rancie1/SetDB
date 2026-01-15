/**
 * Discover page component.
 * 
 * Allows users to import and browse DJ sets from YouTube and SoundCloud.
 */

import { useEffect, useState } from 'react';
import useSetsStore from '../store/setsStore';
import SetImportForm from '../components/sets/SetImportForm';
import SetList from '../components/sets/SetList';

const DiscoverPage = () => {
  const { sets, loading, error, fetchSets, filters, pagination } = useSetsStore();
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    // Load sets on mount
    fetchSets();
  }, []);

  const handleSearch = (e) => {
    e.preventDefault();
    fetchSets({ search: searchQuery }, 1, 20);
  };

  const handleImportSuccess = () => {
    // Sets will be refreshed automatically by the store
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2">Sets</h1>
        <p className="text-gray-600">
          Browse and discover sets from YouTube and SoundCloud.
        </p>
      </div>

      {/* Set Import Form */}
      <div className="mb-6">
        <SetImportForm onSuccess={handleImportSuccess} />
      </div>

      {/* Search Bar */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
        <form onSubmit={handleSearch} className="flex gap-4">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search sets by title or DJ name..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
          <button
            type="submit"
            className="bg-primary-600 hover:bg-primary-700 text-white font-medium px-6 py-2 rounded-md"
          >
            Search
          </button>
          {searchQuery && (
            <button
              type="button"
              onClick={() => {
                setSearchQuery('');
                fetchSets({ search: '' }, 1, 20);
              }}
              className="bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium px-4 py-2 rounded-md"
            >
              Clear
            </button>
          )}
        </form>
      </div>

      {/* Sets List */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">
            {searchQuery ? `Search Results` : 'All Sets'}
          </h2>
          {pagination.total > 0 && (
            <p className="text-sm text-gray-600">
              Showing {sets.length} of {pagination.total} sets
            </p>
          )}
        </div>
        <SetList sets={sets} loading={loading} error={error} />
      </div>

      {/* Pagination (if needed) */}
      {pagination.pages > 1 && (
        <div className="flex items-center justify-center space-x-2">
          <button
            onClick={() => fetchSets(filters, pagination.page - 1, pagination.limit)}
            disabled={pagination.page === 1}
            className="px-4 py-2 border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
          >
            Previous
          </button>
          <span className="px-4 py-2 text-sm text-gray-600">
            Page {pagination.page} of {pagination.pages}
          </span>
          <button
            onClick={() => fetchSets(filters, pagination.page + 1, pagination.limit)}
            disabled={pagination.page >= pagination.pages}
            className="px-4 py-2 border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
};

export default DiscoverPage;
