/**
 * Login page component.
 */

import { useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import LoginForm from '../components/auth/LoginForm';
import useAuthStore from '../store/authStore';

const LoginPage = () => {
  const { isAuthenticated } = useAuthStore();

  // Redirect to home if already authenticated
  if (isAuthenticated()) {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <LoginForm />
    </div>
  );
};

export default LoginPage;


