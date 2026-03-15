import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTranslation } from 'react-i18next';
import LearningRulesExplanation from '../components/LearningRulesExplanation';
import { Brain, ShieldCheck, BarChart3, Trophy, Sparkles, RefreshCw } from 'lucide-react';

export default function Home() {
  const { isAuthenticated } = useAuth();
  const { t } = useTranslation();

  const features = [
    {
      icon: <Brain className="w-7 h-7" />,
      color: 'bg-indigo-100 text-indigo-600',
      title: t('home.features.phases.title'),
      description: t('home.features.phases.desc'),
    },
    {
      icon: <ShieldCheck className="w-7 h-7" />,
      color: 'bg-emerald-100 text-emerald-600',
      title: t('home.features.confirmation.title'),
      description: t('home.features.confirmation.desc'),
    },
    {
      icon: <BarChart3 className="w-7 h-7" />,
      color: 'bg-blue-100 text-blue-600',
      title: t('home.features.tracking.title'),
      description: t('home.features.tracking.desc'),
    },
    {
      icon: <Trophy className="w-7 h-7" />,
      color: 'bg-amber-100 text-amber-600',
      title: t('home.features.leaderboards.title'),
      description: t('home.features.leaderboards.desc'),
    },
  ];

  return (
    <div className="space-y-16">
      {/* Hero Section */}
      <section className="rounded-3xl flex items-center justify-center text-center py-14 px-8"
        style={{ background: 'linear-gradient(135deg, #eef2ff 0%, #f5f3ff 50%, #ede9fe 100%)' }}>
        <div className="max-w-lg">
          <div className="flex justify-center mb-4">
            <div className="w-20 h-20 bg-indigo-100 rounded-2xl flex items-center justify-center">
              <Brain className="w-11 h-11 text-indigo-600" />
            </div>
          </div>
          <h1 className="text-4xl md:text-5xl font-bold mb-4 text-gray-900">FlashLearn</h1>
          <p className="text-lg mb-8 text-gray-500 leading-relaxed">
            {t('home.tagline')}
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            {isAuthenticated ? (
              <Link to="/learn" className="btn btn-primary px-8">
                {t('home.startLearning')}
              </Link>
            ) : (
              <>
                <Link to="/learn" className="btn btn-primary px-8">
                  {t('home.tryDemo')}
                </Link>
                <Link to="/learn" className="btn btn-neutral px-8">
                  {t('home.loginToSave')}
                </Link>
              </>
            )}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section>
        <h2 className="text-3xl font-bold text-center mb-12 text-gray-900">
          {t('home.whyChoose')}
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {features.map((feature, index) => (
            <div key={index} className="card-flashcard p-6 text-center">
              <div className={`w-14 h-14 ${feature.color} rounded-2xl flex items-center justify-center mx-auto mb-4`}>
                {feature.icon}
              </div>
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
          <div className="flex justify-center mb-4">
            <Sparkles className="w-10 h-10 opacity-80" />
          </div>
          <h2 className="text-2xl md:text-3xl font-bold mb-4">{t('home.cta.title')}</h2>
          <p className="text-lg opacity-80 mb-6">
            {t('home.cta.subtitle')}
          </p>
          <Link to="/learn" className="inline-block px-8 py-3 bg-white text-indigo-600 rounded-xl font-semibold hover:bg-indigo-50 transition-colors shadow-md">
            {t('home.cta.button')}
          </Link>
        </div>
      </section>
    </div>
  );
}
