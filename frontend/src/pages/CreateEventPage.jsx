/**
 * Create Event Page component.
 * 
 * Page for creating a new event.
 */

import CreateEventForm from '../components/events/CreateEventForm';

const CreateEventPage = () => {
  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <CreateEventForm />
    </div>
  );
};

export default CreateEventPage;
