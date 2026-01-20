/**
 * Manage Profile Page component.
 * 
 * Allows users to edit their profile information.
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import * as usersService from '../services/usersService';
import useAuthStore from '../store/authStore';

const ManageProfilePage = () => {
  const navigate = useNavigate();
  const { user: currentUser, setUser } = useAuthStore();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm();

  useEffect(() => {
    if (currentUser) {
      // Pre-fill form with current user data
      reset({
        display_name: currentUser.display_name || '',
        bio: currentUser.bio || '',
        avatar_url: currentUser.avatar_url || '',
      });
      setLoading(false);
    }
  }, [currentUser, reset]);

  const onSubmit = async (data) => {
    setSaving(true);
    setError(null);
    setSuccess(false);

    try {
      // Only send fields that have values
      const updateData = {};
      if (data.display_name) updateData.display_name = data.display_name;
      if (data.bio !== undefined) updateData.bio = data.bio || null;
      if (data.avatar_url) updateData.avatar_url = data.avatar_url;

      const response = await usersService.updateProfile(updateData);
      
      // Update the auth store with the new user data
      setUser(response.data);
      
      setSuccess(true);
      
      // Redirect to profile page after a short delay
      setTimeout(() => {
        navigate(`/users/${currentUser.id}`);
      }, 1500);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    navigate(`/users/${currentUser?.id}`);
  };

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/3 mb-4"></div>
            <div className="space-y-4">
              <div className="h-10 bg-gray-200 rounded"></div>
              <div className="h-24 bg-gray-200 rounded"></div>
              <div className="h-10 bg-gray-200 rounded"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Manage Profile</h1>
        <p className="text-gray-600">
          Update your profile information.
        </p>
      </div>

      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        {success && (
          <div className="mb-6 bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-md">
            Profile updated successfully! Redirecting...
          </div>
        )}

        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* Display Name */}
          <div>
            <label htmlFor="display_name" className="block text-sm font-medium text-gray-700 mb-1">
              Display Name
            </label>
            <input
              {...register('display_name', {
                maxLength: {
                  value: 100,
                  message: 'Display name must be 100 characters or less',
                },
              })}
              type="text"
              id="display_name"
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              placeholder="Your display name"
            />
            {errors.display_name && (
              <p className="mt-1 text-sm text-red-600">{errors.display_name.message}</p>
            )}
          </div>

          {/* Bio */}
          <div>
            <label htmlFor="bio" className="block text-sm font-medium text-gray-700 mb-1">
              Bio
            </label>
            <textarea
              {...register('bio')}
              id="bio"
              rows={4}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              placeholder="Tell us about yourself..."
            />
            <p className="mt-1 text-sm text-gray-500">
              A brief description about yourself.
            </p>
          </div>

          {/* Avatar URL */}
          <div>
            <label htmlFor="avatar_url" className="block text-sm font-medium text-gray-700 mb-1">
              Avatar URL
            </label>
            <input
              {...register('avatar_url', {
                maxLength: {
                  value: 500,
                  message: 'Avatar URL must be 500 characters or less',
                },
                pattern: {
                  value: /^https?:\/\/.+/,
                  message: 'Please enter a valid URL starting with http:// or https://',
                },
              })}
              type="url"
              id="avatar_url"
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              placeholder="https://example.com/avatar.jpg"
            />
            {errors.avatar_url && (
              <p className="mt-1 text-sm text-red-600">{errors.avatar_url.message}</p>
            )}
            <p className="mt-1 text-sm text-gray-500">
              URL to your profile picture.
            </p>
          </div>

          {/* Username (read-only) */}
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-1">
              Username
            </label>
            <input
              type="text"
              id="username"
              value={currentUser?.username || ''}
              disabled
              className="w-full px-4 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-500 cursor-not-allowed"
            />
            <p className="mt-1 text-sm text-gray-500">
              Username cannot be changed.
            </p>
          </div>

          {/* Email (read-only) */}
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
              Email
            </label>
            <input
              type="email"
              id="email"
              value={currentUser?.email || ''}
              disabled
              className="w-full px-4 py-2 border border-gray-300 rounded-md bg-gray-50 text-gray-500 cursor-not-allowed"
            />
            <p className="mt-1 text-sm text-gray-500">
              Email cannot be changed here.
            </p>
          </div>

          {/* Form Actions */}
          <div className="flex items-center justify-end space-x-4 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={handleCancel}
              className="px-6 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 font-medium"
              disabled={saving}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-6 py-2 bg-primary-600 hover:bg-primary-700 text-white rounded-md font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={saving}
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ManageProfilePage;
