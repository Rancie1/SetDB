/**
 * Create Event Form component.
 * 
 * Allows users to create a new event.
 */

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import * as eventsService from '../../services/eventsService';

const CreateEventForm = ({ onCancel, onSubmit }) => {
  const navigate = useNavigate();
  const { register, handleSubmit, formState: { errors } } = useForm();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const handleFormSubmit = async (data) => {
    setSubmitting(true);
    setError(null);
    
    try {
      // Format the event data
      const eventData = {
        title: data.title.trim(),
        dj_name: data.dj_name.trim(),
        event_name: data.event_name?.trim() || null,
        event_date: data.event_date || null,
        duration_days: data.duration_days ? parseInt(data.duration_days, 10) : null,
        venue_location: data.venue_location?.trim() || null,
        description: data.description?.trim() || null,
        thumbnail_url: data.thumbnail_url?.trim() || null,
      };

      const response = await eventsService.createEvent(eventData);
      
      if (onSubmit) {
        onSubmit(response.data);
      } else {
        // Navigate to the new event's detail page
        navigate(`/events/${response.data.id}`);
      }
    } catch (err) {
      console.error('Failed to create event:', err);
      setError(err.response?.data?.detail || 'Failed to create event. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancel = () => {
    if (onCancel) {
      onCancel();
    } else {
      navigate('/events');
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h2 className="text-2xl font-bold mb-6">Create New Event</h2>
      
      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
        {/* Title */}
        <div>
          <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">
            Title <span className="text-red-500">*</span>
          </label>
          <input
            {...register('title', { required: 'Title is required' })}
            type="text"
            id="title"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            placeholder="e.g., SUNSHiiNE Presents GMX"
          />
          {errors.title && (
            <p className="mt-1 text-sm text-red-600">{errors.title.message}</p>
          )}
        </div>

        {/* Company Name */}
        <div>
          <label htmlFor="dj_name" className="block text-sm font-medium text-gray-700 mb-1">
            Company Name <span className="text-red-500">*</span>
          </label>
          <input
            {...register('dj_name', { required: 'Company name is required' })}
            type="text"
            id="dj_name"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            placeholder="e.g., MELÖN"
          />
          {errors.dj_name && (
            <p className="mt-1 text-sm text-red-600">{errors.dj_name.message}</p>
          )}
        </div>

        {/* Event Name */}
        <div>
          <label htmlFor="event_name" className="block text-sm font-medium text-gray-700 mb-1">
            Event Name (Optional)
          </label>
          <input
            {...register('event_name')}
            type="text"
            id="event_name"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            placeholder="e.g., SUNSHiiNE PRESENTS GMX"
          />
        </div>

        {/* Event Date */}
        <div>
          <label htmlFor="event_date" className="block text-sm font-medium text-gray-700 mb-1">
            Event Date (Optional)
          </label>
          <input
            {...register('event_date')}
            type="date"
            id="event_date"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          />
        </div>

        {/* Duration Days */}
        <div>
          <label htmlFor="duration_days" className="block text-sm font-medium text-gray-700 mb-1">
            Event Length (Days) (Optional)
          </label>
          <input
            {...register('duration_days', { 
              min: { value: 1, message: 'Duration must be at least 1 day' },
              valueAsNumber: true
            })}
            type="number"
            id="duration_days"
            min="1"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            placeholder="e.g., 3"
          />
          {errors.duration_days && (
            <p className="mt-1 text-sm text-red-600">{errors.duration_days.message}</p>
          )}
        </div>

        {/* Venue Location */}
        <div>
          <label htmlFor="venue_location" className="block text-sm font-medium text-gray-700 mb-1">
            Venue Location (Optional)
          </label>
          <input
            {...register('venue_location')}
            type="text"
            id="venue_location"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            placeholder="e.g., GMX, Melbourne"
          />
        </div>

        {/* Thumbnail URL */}
        <div>
          <label htmlFor="thumbnail_url" className="block text-sm font-medium text-gray-700 mb-1">
            Thumbnail URL (Optional)
          </label>
          <input
            {...register('thumbnail_url')}
            type="url"
            id="thumbnail_url"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            placeholder="https://example.com/image.jpg"
          />
        </div>

        {/* Description */}
        <div>
          <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
            Description (Optional)
          </label>
          <textarea
            {...register('description')}
            id="description"
            rows={4}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            placeholder="Add details about the event..."
          />
        </div>

        {/* Form Actions */}
        <div className="flex items-center justify-end gap-3 pt-4">
          <button
            type="button"
            onClick={handleCancel}
            disabled={submitting}
            className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={submitting}
            className="px-6 py-2 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {submitting ? 'Creating...' : 'Create Event'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default CreateEventForm;
