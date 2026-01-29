/**
 * Top Lists page component.
 * 
 * Allows users to create and manage top 5 lists for sets, events, venues, and tracks.
 */

import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import * as listsService from '../services/listsService';
import * as setsService from '../services/setsService';
import * as eventsService from '../services/eventsService';
import * as tracksService from '../services/tracksService';
import useAuthStore from '../store/authStore';
import SetCard from '../components/sets/SetCard';

const TopListsPage = () => {
  const { id: listId } = useParams();
  const { user, isAuthenticated } = useAuthStore();
  const [lists, setLists] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingList, setEditingList] = useState(null);
  const [selectedList, setSelectedList] = useState(null);
  const [showAddItemForm, setShowAddItemForm] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [selectedItem, setSelectedItem] = useState(null);
  const [venueName, setVenueName] = useState('');
  const [newListData, setNewListData] = useState({
    name: '',
    description: '',
    list_type: 'sets',
    is_public: true,
    max_items: 5,
  });

  useEffect(() => {
    if (listId) {
      // View specific list
      handleViewList(listId);
    } else if (isAuthenticated() && user) {
      // View all lists
      loadLists();
    } else {
      setLoading(false);
    }
  }, [listId, isAuthenticated(), user]);

  const loadLists = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await listsService.getLists(1, 100, user.id);
      setLists(response.data.items || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load lists');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateList = async (e) => {
    e.preventDefault();
    try {
      await listsService.createList(newListData);
      setShowCreateForm(false);
      setNewListData({
        name: '',
        description: '',
        list_type: 'sets',
        is_public: true,
        max_items: 5,
      });
      loadLists();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to create list');
    }
  };

  const handleDeleteList = async (listId) => {
    if (!confirm('Are you sure you want to delete this list?')) return;
    try {
      await listsService.deleteList(listId);
      loadLists();
      if (selectedList?.id === listId) {
        setSelectedList(null);
      }
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to delete list');
    }
  };

  const handleViewList = async (listId) => {
    try {
      const response = await listsService.getList(listId);
      setSelectedList(response.data);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to load list');
    }
  };

  const handleSearch = async (query) => {
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }
    setSearching(true);
    try {
      let results = [];
      if (selectedList.list_type === 'sets') {
        const response = await setsService.getSets({ search: query }, 1, 10);
        results = response.data.items || [];
      } else if (selectedList.list_type === 'events') {
        const response = await eventsService.getEvents({ search: query }, 1, 10);
        results = response.data.items || [];
      } else if (selectedList.list_type === 'tracks') {
        const response = await tracksService.searchSoundCloud(query, 10);
        results = response.data || [];
      }
      setSearchResults(results);
    } catch (err) {
      console.error('Search error:', err);
      setSearchResults([]);
    } finally {
      setSearching(false);
    }
  };

  const handleAddItem = async () => {
    if (!selectedList) return;
    
    let itemData = { position: (selectedList.items?.length || 0) + 1 };
    
    try {
      if (selectedList.list_type === 'sets' && selectedItem) {
        itemData.set_id = selectedItem.id;
      } else if (selectedList.list_type === 'events' && selectedItem) {
        itemData.event_id = selectedItem.id;
      } else if (selectedList.list_type === 'tracks' && selectedItem) {
        itemData.track_id = selectedItem.id;
      } else if (selectedList.list_type === 'venues' && venueName.trim()) {
        itemData.venue_name = venueName.trim();
      } else {
        alert('Please select an item or enter a venue name');
        return;
      }

      await listsService.addItemToList(selectedList.id, itemData);
      await handleViewList(selectedList.id);
      setShowAddItemForm(false);
      setSelectedItem(null);
      setSearchQuery('');
      setSearchResults([]);
      setVenueName('');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to add item to list');
    }
  };

  const handleRemoveItem = async (itemId) => {
    if (!confirm('Remove this item from the list?')) return;
    try {
      await listsService.removeItemFromList(selectedList.id, itemId);
      await handleViewList(selectedList.id);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to remove item');
    }
  };

  if (!isAuthenticated()) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center py-12">
          <p className="text-gray-500 text-lg mb-4">
            Please log in to create and manage your top 5 lists.
          </p>
          <Link
            to="/login"
            className="text-primary-600 hover:text-primary-700 font-medium"
          >
            Go to Login
          </Link>
        </div>
      </div>
    );
  }

  if (selectedList) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          {selectedList && user && String(selectedList.user_id) === String(user.id) ? (
            <Link
              to={`/users/${user.id}`}
              className="text-primary-600 hover:text-primary-700 mb-4 inline-block"
            >
              ← Back to Profile
            </Link>
          ) : (
            <Link
              to={selectedList ? `/users/${selectedList.user_id}` : '/'}
              className="text-primary-600 hover:text-primary-700 mb-4 inline-block"
            >
              ← Back
            </Link>
          )}
          <h1 className="text-3xl font-bold mb-2">{selectedList.name}</h1>
          {selectedList.description && (
            <p className="text-gray-600 mb-4">{selectedList.description}</p>
          )}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4 text-sm text-gray-500">
              <span>Type: {selectedList.list_type}</span>
              <span>•</span>
              <span>Max items: {selectedList.max_items || 5}</span>
              <span>•</span>
              <span>{selectedList.items?.length || 0} items</span>
            </div>
            {selectedList && user && String(selectedList.user_id) === String(user.id) && 
             (selectedList.items?.length || 0) < (selectedList.max_items || 5) && (
              <button
                onClick={() => setShowAddItemForm(!showAddItemForm)}
                className="bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-md font-medium"
              >
                {showAddItemForm ? 'Cancel' : 'Add Item'}
              </button>
            )}
          </div>
        </div>

        {/* Add Item Form */}
        {showAddItemForm && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">Add Item to List</h2>
            {selectedList.list_type === 'venues' ? (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Venue Name
                  </label>
                  <input
                    type="text"
                    value={venueName}
                    onChange={(e) => setVenueName(e.target.value)}
                    className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    placeholder="Enter venue name"
                  />
                </div>
                <button
                  onClick={handleAddItem}
                  className="bg-primary-600 hover:bg-primary-700 text-white px-6 py-2 rounded-md font-medium"
                >
                  Add Venue
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Search {selectedList.list_type.charAt(0).toUpperCase() + selectedList.list_type.slice(1)}
                  </label>
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => {
                      setSearchQuery(e.target.value);
                      handleSearch(e.target.value);
                    }}
                    className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                    placeholder={`Search ${selectedList.list_type}...`}
                  />
                </div>
                {searching && (
                  <p className="text-sm text-gray-500">Searching...</p>
                )}
                {searchResults.length > 0 && (
                  <div className="border border-gray-200 rounded-md max-h-64 overflow-y-auto">
                    {searchResults.map((item) => (
                      <div
                        key={item.id}
                        onClick={() => setSelectedItem(item)}
                        className={`p-4 border-b border-gray-200 cursor-pointer hover:bg-gray-50 ${
                          selectedItem?.id === item.id ? 'bg-primary-50 border-primary-200' : ''
                        }`}
                      >
                        {selectedList.list_type === 'sets' && (
                          <>
                            <h3 className="font-semibold">{item.title}</h3>
                            <p className="text-sm text-gray-600">{item.dj_name}</p>
                          </>
                        )}
                        {selectedList.list_type === 'events' && (
                          <>
                            <h3 className="font-semibold">{item.title}</h3>
                            <p className="text-sm text-gray-600">{item.dj_name}</p>
                            {item.venue_location && (
                              <p className="text-xs text-gray-500">📍 {item.venue_location}</p>
                            )}
                          </>
                        )}
                        {selectedList.list_type === 'tracks' && (
                          <>
                            <h3 className="font-semibold">{item.track_name}</h3>
                            <p className="text-sm text-gray-600">{item.artist_name || 'Unknown Artist'}</p>
                          </>
                        )}
                      </div>
                    ))}
                  </div>
                )}
                {selectedItem && (
                  <button
                    onClick={handleAddItem}
                    className="bg-primary-600 hover:bg-primary-700 text-white px-6 py-2 rounded-md font-medium"
                  >
                    Add Selected Item
                  </button>
                )}
              </div>
            )}
          </div>
        )}

        {/* List Items */}
        <div className="space-y-4">
          {selectedList.items && selectedList.items.length > 0 ? (
            selectedList.items
              .sort((a, b) => a.position - b.position)
              .map((item, index) => (
                <div
                  key={item.id}
                  className="bg-white rounded-lg shadow-sm border border-gray-200 p-6"
                >
                  <div className="flex items-start space-x-4">
                    <div className="flex-shrink-0 w-12 h-12 bg-gradient-to-br from-yellow-400 to-yellow-600 rounded-lg flex items-center justify-center text-white font-bold text-xl">
                      {item.position}
                    </div>
                    <div className="flex-1">
                      {selectedList.list_type === 'sets' && item.set && (
                        <SetCard set={item.set} />
                      )}
                      {selectedList.list_type === 'events' && item.event && (
                        <Link
                          to={`/events/${item.event.id}`}
                          className="block bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition-colors"
                        >
                          <h3 className="font-semibold text-lg">{item.event.title}</h3>
                          <p className="text-gray-600">{item.event.dj_name}</p>
                          {item.event.event_name && (
                            <p className="text-sm text-gray-500 mt-1">{item.event.event_name}</p>
                          )}
                          {item.event.venue_location && (
                            <p className="text-sm text-gray-500">📍 {item.event.venue_location}</p>
                          )}
                        </Link>
                      )}
                      {selectedList.list_type === 'tracks' && item.track && (
                        <Link
                          to={`/tracks/${item.track.id}`}
                          className="block bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition-colors"
                        >
                          <h3 className="font-semibold text-lg">{item.track.track_name}</h3>
                          <p className="text-gray-600">{item.track.artist_name || 'Unknown Artist'}</p>
                        </Link>
                      )}
                      {selectedList.list_type === 'venues' && item.venue_name && (
                        <div className="bg-gray-50 rounded-lg p-4">
                          <h3 className="font-semibold text-lg">{item.venue_name}</h3>
                        </div>
                      )}
                      {item.notes && (
                        <p className="text-sm text-gray-600 mt-2">{item.notes}</p>
                      )}
                    </div>
                    {selectedList && user && String(selectedList.user_id) === String(user.id) && (
                      <button
                        onClick={() => handleRemoveItem(item.id)}
                        className="text-red-600 hover:text-red-700 text-sm"
                      >
                        Remove
                      </button>
                    )}
                  </div>
                </div>
              ))
          ) : (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 text-center">
              <p className="text-gray-500">No items in this list yet.</p>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold mb-2">Top 5 Lists</h1>
            <p className="text-gray-600">
              Create and manage your top 5 lists for sets, events, venues, and tracks.
            </p>
          </div>
          <button
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="bg-primary-600 hover:bg-primary-700 text-white px-6 py-2 rounded-md font-medium"
          >
            {showCreateForm ? 'Cancel' : 'Create New List'}
          </button>
        </div>

        {/* Create List Form */}
        {showCreateForm && (
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
            <h2 className="text-xl font-semibold mb-4">Create New List</h2>
            <form onSubmit={handleCreateList} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  List Name
                </label>
                <input
                  type="text"
                  value={newListData.name}
                  onChange={(e) => setNewListData({ ...newListData, name: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  placeholder="e.g., Top 5 Techno Sets 2024"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description (optional)
                </label>
                <textarea
                  value={newListData.description}
                  onChange={(e) => setNewListData({ ...newListData, description: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  rows="3"
                  placeholder="Describe your list..."
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  List Type
                </label>
                <select
                  value={newListData.list_type}
                  onChange={(e) => setNewListData({ ...newListData, list_type: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                >
                  <option value="sets">Sets</option>
                  <option value="events">Events</option>
                  <option value="venues">Venues</option>
                  <option value="tracks">Tracks</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Maximum Items (default: 5)
                </label>
                <input
                  type="number"
                  value={newListData.max_items}
                  onChange={(e) => setNewListData({ ...newListData, max_items: parseInt(e.target.value) || 5 })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  min="1"
                  max="100"
                />
              </div>
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="is_public"
                  checked={newListData.is_public}
                  onChange={(e) => setNewListData({ ...newListData, is_public: e.target.checked })}
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <label htmlFor="is_public" className="ml-2 text-sm text-gray-700">
                  Make this list public
                </label>
              </div>
              <div className="flex space-x-3">
                <button
                  type="submit"
                  className="bg-primary-600 hover:bg-primary-700 text-white px-6 py-2 rounded-md font-medium"
                >
                  Create List
                </button>
                <button
                  type="button"
                  onClick={() => setShowCreateForm(false)}
                  className="bg-gray-100 hover:bg-gray-200 text-gray-700 px-6 py-2 rounded-md font-medium"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}
      </div>

      {/* Lists Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="bg-gray-100 animate-pulse rounded-lg h-48"></div>
          ))}
        </div>
      ) : error ? (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error}</p>
        </div>
      ) : lists.length === 0 ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
          <p className="text-gray-500 text-lg mb-2">No lists yet</p>
          <p className="text-gray-400 text-sm mb-4">
            Create your first top 5 list to get started!
          </p>
          <button
            onClick={() => setShowCreateForm(true)}
            className="bg-primary-600 hover:bg-primary-700 text-white px-6 py-2 rounded-md font-medium"
          >
            Create Your First List
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {lists.map((list) => (
            <div
              key={list.id}
              className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="text-xl font-semibold text-gray-900 mb-1">{list.name}</h3>
                  <p className="text-sm text-gray-500 capitalize">{list.list_type}</p>
                </div>
                <div className="flex space-x-2">
                  <button
                    onClick={() => handleDeleteList(list.id)}
                    className="text-red-600 hover:text-red-700 text-sm"
                  >
                    Delete
                  </button>
                </div>
              </div>
              {list.description && (
                <p className="text-sm text-gray-600 mb-4 line-clamp-2">{list.description}</p>
              )}
              <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
                <span>{list.items?.length || 0} / {list.max_items || 5} items</span>
                {list.is_public && (
                  <span className="text-green-600">Public</span>
                )}
              </div>
              <button
                onClick={() => handleViewList(list.id)}
                className="w-full bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-md font-medium"
              >
                View List
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default TopListsPage;
