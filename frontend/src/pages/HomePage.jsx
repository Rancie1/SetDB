/**
 * Home page component.
 */

const HomePage = () => {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-slate-100 mb-4">
          Welcome to SetDB
        </h1>
        <p className="text-xl text-slate-400 mb-8">
          Track, rate, and review your favorite DJ sets
        </p>
        <div className="flex justify-center space-x-4">
          <a
            href="/"
            className="bg-primary-600 hover:bg-primary-500 text-white px-6 py-3 rounded-xl font-medium transition-colors"
          >
            Discover Sets
          </a>
          <a
            href="/register"
            className="bg-surface-700 hover:bg-surface-600 text-slate-300 px-6 py-3 rounded-xl font-medium border border-white/5 transition-colors"
          >
            Get Started
          </a>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
        <div className="bg-surface-800 p-6 rounded-xl border border-white/5">
          <h3 className="text-xl font-semibold mb-2 text-slate-100">Log Sets</h3>
          <p className="text-slate-400">
            Keep track of all the DJ sets you've listened to or seen live
          </p>
        </div>
        <div className="bg-surface-800 p-6 rounded-xl border border-white/5">
          <h3 className="text-xl font-semibold mb-2 text-slate-100">Rate & Review</h3>
          <p className="text-slate-400">
            Rate sets with half-star precision and share your thoughts
          </p>
        </div>
        <div className="bg-surface-800 p-6 rounded-xl border border-white/5">
          <h3 className="text-xl font-semibold mb-2 text-slate-100">Discover</h3>
          <p className="text-slate-400">
            Follow other users and discover new music through their reviews
          </p>
        </div>
      </div>
    </div>
  );
};

export default HomePage;
