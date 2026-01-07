/**
 * Home page component.
 */

const HomePage = () => {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Welcome to SetDB
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          Track, rate, and review your favorite DJ sets
        </p>
        <div className="flex justify-center space-x-4">
          <a
            href="/discover"
            className="bg-primary-600 hover:bg-primary-700 text-white px-6 py-3 rounded-md font-medium"
          >
            Discover Sets
          </a>
          <a
            href="/register"
            className="bg-gray-200 hover:bg-gray-300 text-gray-800 px-6 py-3 rounded-md font-medium"
          >
            Get Started
          </a>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-xl font-semibold mb-2">Log Sets</h3>
          <p className="text-gray-600">
            Keep track of all the DJ sets you've listened to or seen live
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-xl font-semibold mb-2">Rate & Review</h3>
          <p className="text-gray-600">
            Rate sets with half-star precision and share your thoughts
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-xl font-semibold mb-2">Discover</h3>
          <p className="text-gray-600">
            Follow other users and discover new music through their reviews
          </p>
        </div>
      </div>
    </div>
  );
};

export default HomePage;


