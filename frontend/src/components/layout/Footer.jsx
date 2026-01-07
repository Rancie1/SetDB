/**
 * Footer component.
 */

const Footer = () => {
  return (
    <footer className="bg-white border-t border-gray-200 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center text-gray-600 text-sm">
          <p>&copy; {new Date().getFullYear()} SetDB. Built with ❤️ for the DJ community.</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;


