/**
 * Main App component with routing.
 */

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { useEffect } from 'react';
import Layout from './components/layout/Layout';
import ProtectedRoute from './components/auth/ProtectedRoute';
import useAuthStore from './store/authStore';

// Pages
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DiscoverPage from './pages/DiscoverPage';
import TracksDiscoverPage from './pages/TracksDiscoverPage';
import EventsPage from './pages/EventsPage';
import EventDetailsPage from './pages/EventDetailsPage';
import CreateEventPage from './pages/CreateEventPage';
import UserProfilePage from './pages/UserProfilePage';
import SearchUsersPage from './pages/SearchUsersPage';
import FriendsPage from './pages/FriendsPage';
import ManageProfilePage from './pages/ManageProfilePage';
import SoundCloudCallbackPage from './pages/SoundCloudCallbackPage';
import SetDetailsPage from './pages/SetDetailsPage';
import TrackDetailsPage from './pages/TrackDetailsPage';

function App() {
  const { checkAuth } = useAuthStore();

  // Check authentication on app load
  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={
            <Layout>
              <HomePage />
            </Layout>
          }
        />
        <Route
          path="/login"
          element={
            <Layout>
              <LoginPage />
            </Layout>
          }
        />
        <Route
          path="/register"
          element={
            <Layout>
              <RegisterPage />
            </Layout>
          }
        />
        <Route
          path="/auth/soundcloud/callback"
          element={
            <Layout>
              <SoundCloudCallbackPage />
            </Layout>
          }
        />
        <Route
          path="/sets"
          element={
            <Layout>
              <DiscoverPage />
            </Layout>
          }
        />
        <Route
          path="/tracks"
          element={
            <Layout>
              <TracksDiscoverPage />
            </Layout>
          }
        />
        <Route
          path="/events"
          element={
            <Layout>
              <EventsPage />
            </Layout>
          }
        />
        <Route
          path="/events/create"
          element={
            <ProtectedRoute>
              <Layout>
                <CreateEventPage />
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/feed"
          element={
            <ProtectedRoute>
              <Layout>
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                  <h1 className="text-3xl font-bold mb-6">Your Feed</h1>
                  <p className="text-gray-600">Activity from users you follow will appear here.</p>
                </div>
              </Layout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/events/:id"
          element={
            <Layout>
              <EventDetailsPage />
            </Layout>
          }
        />
        <Route
          path="/sets/:id"
          element={
            <Layout>
              <SetDetailsPage />
            </Layout>
          }
        />
        <Route
          path="/tracks/:id"
          element={
            <Layout>
              <TrackDetailsPage />
            </Layout>
          }
        />
        <Route
          path="/friends"
          element={
            <Layout>
              <FriendsPage />
            </Layout>
          }
        />
        <Route
          path="/friends/search"
          element={
            <Layout>
              <SearchUsersPage />
            </Layout>
          }
        />
        <Route
          path="/users/:id"
          element={
            <Layout>
              <UserProfilePage />
            </Layout>
          }
        />
        <Route
          path="/profile/manage"
          element={
            <ProtectedRoute>
              <Layout>
                <ManageProfilePage />
              </Layout>
            </ProtectedRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
