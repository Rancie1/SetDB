/**
 * Header component with navigation, search, and user menu.
 */

import { Link, useNavigate } from 'react-router-dom';
import useAuthStore from '../../store/authStore';
import { APP_NAME } from '../../utils/constants';

const Header = () => {
  const { user, isAuthenticated, logout } = useAuthStore();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="bg-surface-800 border-b border-white/5 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-md bg-primary-600 flex items-center justify-center">
              <svg viewBox="0 0 24 24" fill="currentColor" className="w-4 h-4 text-white">
                <path d="M12 3v10.55A4 4 0 1 0 14 17V7h4V3h-6z"/>
              </svg>
            </div>
            <span className="text-lg font-semibold tracking-tight text-white">{APP_NAME}</span>
          </Link>

          {/* Navigation */}
          <nav className="hidden md:flex items-center gap-1">
            <Link to="/" className="text-slate-400 hover:text-white hover:bg-white/5 px-3 py-2 rounded-md text-sm font-medium transition-colors duration-150 cursor-pointer">
              Discover
            </Link>
            <Link to="/sets" className="text-slate-400 hover:text-white hover:bg-white/5 px-3 py-2 rounded-md text-sm font-medium transition-colors duration-150 cursor-pointer">
              Sets
            </Link>
            <Link to="/tracks" className="text-slate-400 hover:text-white hover:bg-white/5 px-3 py-2 rounded-md text-sm font-medium transition-colors duration-150 cursor-pointer">
              Tracks
            </Link>
            <Link to="/events" className="text-slate-400 hover:text-white hover:bg-white/5 px-3 py-2 rounded-md text-sm font-medium transition-colors duration-150 cursor-pointer">
              Events
            </Link>
          </nav>

          {/* User Menu */}
          <div className="flex items-center gap-3">
            {isAuthenticated() ? (
              <>
                <Link
                  to={`/users/${user?.id}`}
                  className="text-slate-400 hover:text-white px-3 py-2 text-sm font-medium transition-colors duration-150 cursor-pointer"
                >
                  {user?.username || 'Profile'}
                </Link>
                <button
                  onClick={handleLogout}
                  className="bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white px-4 py-2 rounded-md text-sm font-medium transition-colors duration-150 cursor-pointer"
                >
                  Logout
                </button>
              </>
            ) : (
              <>
                <Link
                  to="/login"
                  className="text-slate-400 hover:text-white px-3 py-2 text-sm font-medium transition-colors duration-150 cursor-pointer"
                >
                  Login
                </Link>
                <Link
                  to="/register"
                  className="bg-primary-600 hover:bg-primary-500 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors duration-150 cursor-pointer"
                >
                  Sign Up
                </Link>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
