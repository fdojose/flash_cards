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
      <section className="rounded-3xl flex items-center justify-center text-center py-14 px-8"
        style={{ background: 'linear-gradient(135deg, #eef2ff 0%, #f5f3ff 50%, #ede9fe 100%)' }}>
        <div className="max-w-lg">
          <div className="text-7xl mb-4">🧠</div>
          <h1 className="text-4xl md:text-5xl font-bold mb-4 text-gray-900">FlashLearn</h1>
          <p className="text-lg mb-8 text-gray-500 leading-relaxed">
            Master any subject with intelligent spaced repetition.
            Learn faster, remember longer, achieve more.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            {isAuthenticated ? (
              <Link to="/learn" className="btn btn-primary px-8">
                Start Learning 🚀
              </Link>
            ) : (
              <>
                <Link to="/learn" className="btn btn-primary px-8">
                  Try Demo 🚀
                </Link>
                <Link to="/learn" className="btn btn-neutral px-8">
                  Login to Save Progress 📊
                </Link>
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
      <section className="text-white rounded-2xl p-10"
        style={{ background: 'linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%)', boxShadow: '0 8px 32px rgba(79,70,229,0.3)' }}>
        <div className="text-center">
          <h2 className="text-2xl md:text-3xl font-bold mb-4">Ready to Transform Your Learning?</h2>
          <p className="text-lg opacity-80 mb-6">
            Join learners who have improved their retention with FlashLearn
          </p>
          <Link to="/learn" className="inline-block px-8 py-3 bg-white text-indigo-600 rounded-xl font-semibold hover:bg-indigo-50 transition-colors shadow-md">
            Get Started Free
          </Link>
        </div>
      </section>
    </div>
  );
}
