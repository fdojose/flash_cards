export default function Footer() {
  return (
    <footer className="footer-custom py-6 px-4 mt-auto">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between">
        <div className="flex items-center space-x-3 mb-4 md:mb-0">
          <span className="text-2xl">🧠</span>
          <div>
            <p className="font-semibold text-gray-900">FlashLearn</p>
            <p className="text-sm text-gray-600">Smart learning through spaced repetition</p>
          </div>
        </div>
        <div className="flex space-x-6">
          <a className="text-sm text-gray-600 hover:text-gray-900 transition-colors" href="#about">
            About
          </a>
          <a className="text-sm text-gray-600 hover:text-gray-900 transition-colors" href="#privacy">
            Privacy
          </a>
          <a className="text-sm text-gray-600 hover:text-gray-900 transition-colors" href="#contact">
            Contact
          </a>
        </div>
      </div>
    </footer>
  );
}
