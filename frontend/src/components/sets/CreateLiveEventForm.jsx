/**
 * Create live event form component.
 * 
 * Allows users to create a live event from an existing set.
 */

import { useState } from 'react';
import { useForm } from 'react-hook-form';

const CreateLiveEventForm = ({ set, onSubmit, onCancel, loading }) => {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    defaultValues: {
      event_name: '',
      event_date: '',
      venue_location: '',
    },
  });

  const handleFormSubmit = (data) => {
    const eventData = {
      event_name: data.event_name || null,
      event_date: data.event_date || null,
      venue_location: data.venue_location || null,
    };
    onSubmit(eventData);
  };

  return (
    <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
      <h3 className="text-lg font-semibold text-purple-900 mb-3">
        Create Live Event
      </h3>
      <p className="text-sm text-purple-700 mb-4">
        This will create a live event. 
        You can add event details below (all optional).
      </p>

      <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-3">
        <div>
          <label htmlFor="event_name" className="block text-sm font-medium text-gray-700 mb-1">
            Event Name
          </label>
          <input
            type="text"
            id="event_name"
            {...register('event_name', {
              maxLength: {
                value: 255,
                message: 'Event name must be less than 255 characters',
              },
            })}
            placeholder="e.g., Time Warp 2024"
            className={`w-full px-3 py-2 border rounded-md text-sm focus:ring-2 focus:ring-purple-500 focus:border-purple-500 ${
              errors.event_name ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.event_name && (
            <p className="mt-1 text-xs text-red-600">{errors.event_name.message}</p>
          )}
        </div>

        <div>
          <label htmlFor="event_date" className="block text-sm font-medium text-gray-700 mb-1">
            Event Date
          </label>
          <input
            type="date"
            id="event_date"
            {...register('event_date')}
            className={`w-full px-3 py-2 border rounded-md text-sm focus:ring-2 focus:ring-purple-500 focus:border-purple-500 ${
              errors.event_date ? 'border-red-500' : 'border-gray-300'
            }`}
          />
        </div>

        <div>
          <label htmlFor="venue_location" className="block text-sm font-medium text-gray-700 mb-1">
            Venue / Location
          </label>
          <input
            type="text"
            id="venue_location"
            {...register('venue_location', {
              maxLength: {
                value: 255,
                message: 'Venue location must be less than 255 characters',
              },
            })}
            placeholder="e.g., Berghain, Berlin"
            className={`w-full px-3 py-2 border rounded-md text-sm focus:ring-2 focus:ring-purple-500 focus:border-purple-500 ${
              errors.venue_location ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.venue_location && (
            <p className="mt-1 text-xs text-red-600">{errors.venue_location.message}</p>
          )}
        </div>

        <div className="flex gap-2 pt-2">
          <button
            type="submit"
            disabled={loading}
            className="flex-1 bg-purple-600 hover:bg-purple-700 text-white font-medium py-2 px-4 rounded-md text-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Creating...' : 'Create Event'}
          </button>
          <button
            type="button"
            onClick={onCancel}
            disabled={loading}
            className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium rounded-md text-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
};

export default CreateLiveEventForm;
