/**
 * Set import form component.
 * 
 * Allows users to import DJ sets from YouTube or SoundCloud by pasting a URL.
 */

import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import useSetsStore from '../../store/setsStore';

const SetImportForm = ({ onSuccess }) => {
  const { importSet, loading, error, clearError } = useSetsStore();
  const [successMessage, setSuccessMessage] = useState(null);

  // Clear error when component mounts or form is reset
  useEffect(() => {
    return () => {
      clearError();
    };
  }, [clearError]);
  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    watch,
  } = useForm({
    defaultValues: {
      mark_as_live: false,
    },
  });

  const markAsLive = watch('mark_as_live');

  const onSubmit = async (data) => {
    setSuccessMessage(null);
    try {
      const result = await importSet(data.url, data.mark_as_live || false);
      if (result.success) {
        setSuccessMessage(
          data.mark_as_live 
            ? 'Live set created successfully! The recording URL has been saved.' 
            : 'Set imported successfully!'
        );
        reset();
        if (onSuccess) {
          onSuccess(result.data);
        }
      }
    } catch (err) {
      // Error is handled by the store
    }
  };

  const detectPlatform = (url) => {
    if (!url) return null;
    const lowerUrl = url.toLowerCase();
    if (lowerUrl.includes('youtube.com') || lowerUrl.includes('youtu.be')) {
      return 'YouTube';
    }
    if (lowerUrl.includes('soundcloud.com')) {
      return 'SoundCloud';
    }
    return null;
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
      <h2 className="text-xl font-semibold mb-4">Import a DJ Set</h2>
      <p className="text-gray-600 mb-4">
        Paste a YouTube or SoundCloud URL to import a set
      </p>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <label htmlFor="url" className="block text-sm font-medium text-gray-700 mb-2">
            Set URL
          </label>
          <div className="relative">
            <input
              type="url"
              id="url"
              {...register('url', {
                required: 'URL is required',
                validate: (value) => {
                  const platform = detectPlatform(value);
                  if (!platform) {
                    return 'Please provide a valid YouTube or SoundCloud URL';
                  }
                  return true;
                },
              })}
              placeholder="https://www.youtube.com/watch?v=..."
              className={`w-full px-4 py-2 border rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500 ${
                errors.url ? 'border-red-500' : 'border-gray-300'
              }`}
              onChange={(e) => {
                const platform = detectPlatform(e.target.value);
                // You could show platform detection here if needed
              }}
            />
            {errors.url && (
              <p className="mt-1 text-sm text-red-600">{errors.url.message}</p>
            )}
          </div>
          <p className="mt-2 text-sm text-gray-500">
            Supported platforms: YouTube, SoundCloud
          </p>
        </div>

        <div className="bg-purple-50 border border-purple-200 rounded-md p-3">
          <label className="flex items-center cursor-pointer">
            <input
              type="checkbox"
              {...register('mark_as_live')}
              className="mr-2 h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
            />
            <span className="text-sm text-gray-700">
              Mark as live set
            </span>
          </label>
          <p className="text-xs text-gray-500 mt-1 ml-6">
            {markAsLive 
              ? 'This will create a live set with the imported URL as the recording. The set will appear on the discover page as a live set.'
              : 'If checked, creates a live set instead of a regular import. The URL will be stored as the recording.'}
          </p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
            {error}
          </div>
        )}

        {successMessage && (
          <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-md">
            {successMessage}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full bg-primary-600 hover:bg-primary-700 text-white font-medium py-2 px-4 rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Importing...' : 'Import Set'}
        </button>
      </form>
    </div>
  );
};

export default SetImportForm;

