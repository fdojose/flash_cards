import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import LearningRulesExplanation from '../components/LearningRulesExplanation';

export default function Home() {
  const { isAuthenticated } = useAuth();

  const features = [
    {
      icon: '🧠',
      title: 'Smart Learning',
      description: 'Advanced spaced repetition algorithm adapts to your learning pace',
    },
    {
      icon: '📚',
      title: 'Multiple Datasets',
      description: 'Study acupuncture points, anatomy, languages, and more',
    },
    {
      icon: '📊',
      title: 'Progress Tracking',
      description: 'Visual dashboard shows your learning progress and statistics',
    },
    {
      icon: '🏆',
      title: 'Gamification',
      description: 'Earn badges, maintain streaks, and compete on leaderboards',
    },
  ];

  return (
    <div className="space-y-16">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-3xl flex items-center justify-center text-center py-12 px-8">
        <div className="max-w-md">
          <h1 className="text-5xl font-bold mb-6">
            <span className="text-6xl">🧠</span>
            <br />
            FlashLearn
          </h1>
          <p className="text-lg mb-8 text-gray-600">
            Master any subject with intelligent spaced repetition. 
            Learn faster, remember longer, achieve more.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            {isAuthenticated ? (
              <Link to="/learn" className="px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors">
                Start Learning 🚀
              </Link>
            ) : (
              <>
                <Link to="/learn" className="px-6 py-3 bg-blue-600 text-white rounded-lg font-semibold hover:bg-blue-700 transition-colors">
                  Try Demo 🚀
                </Link>
                <button className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg font-semibold hover:bg-gray-50 transition-colors">
                  Login to Save Progress 📊
                </button>
              </>
            )}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section>
        <h2 className="text-3xl font-bold text-center mb-12 text-gray-900">
          Why Choose FlashLearn?
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {features.map((feature, index) => (
            <div key={index} className="card-flashcard p-6 text-center">
              <div className="text-4xl mb-4">{feature.icon}</div>
              <h3 className="text-lg font-semibold mb-3 text-gray-900">
                {feature.title}
              </h3>
              <p className="text-sm text-gray-600">{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Learning Rules Explanation */}
      <LearningRulesExplanation />

      {/* CTA Section */}
      <section className="bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-2xl p-8">
        <div className="text-center">
          <h2 className="text-3xl font-bold mb-4">Ready to Transform Your Learning?</h2>
          <p className="text-lg opacity-90 mb-6">
            Join thousands of learners who have improved their retention with FlashLearn
          </p>
          <Link to="/register" className="px-8 py-3 bg-white text-blue-600 rounded-lg font-semibold hover:bg-gray-100 transition-colors">
            Get Started Free
          </Link>
        </div>
      </section>
    </div>
  );
}
