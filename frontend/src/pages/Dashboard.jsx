import { useAuth } from '../contexts/AuthContext';
import { useDashboard, useProgressHistory } from '../hooks/useApi';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Trophy, Flame, FileText, Target, Zap, Clock, BarChart3, Lock } from 'lucide-react';

export default function Dashboard() {
  const { user, isAuthenticated } = useAuth();
  const { progress, stats, achievements, loading: dashboardLoading, error } = useDashboard();
  const { history, loading: historyLoading } = useProgressHistory(7);
  const navigate = useNavigate();
  const { t } = useTranslation();

  if (!isAuthenticated) {
    return (
      <div className="max-w-4xl mx-auto text-center py-12">
        <div className="card-flashcard p-8">
          <div className="flex justify-center mb-6"><Lock className="w-16 h-16 text-gray-300" /></div>
          <h2 className="text-2xl font-bold mb-4">{t('common.loginRequired')}</h2>
          <p className="text-gray-600 mb-6">{t('dashboard.loginRequiredDesc')}</p>
        </div>
      </div>
    );
  }

  const defaultStats = [
    { label: t('dashboard.stats.mastered'), value: 0,    icon: <Trophy   className="w-7 h-7" />, bg: 'bg-emerald-100', color: 'text-emerald-600' },
    { label: t('dashboard.stats.streak'),   value: 0,    icon: <Flame    className="w-7 h-7" />, bg: 'bg-orange-100',  color: 'text-orange-600' },
    { label: t('dashboard.stats.reviews'),  value: 0,    icon: <FileText className="w-7 h-7" />, bg: 'bg-blue-100',    color: 'text-blue-600' },
    { label: t('dashboard.stats.accuracy'), value: '0%', icon: <Target   className="w-7 h-7" />, bg: 'bg-purple-100',  color: 'text-purple-600' },
  ];

  const displayStats = stats ? [
    { label: t('dashboard.stats.mastered'), value: stats.mastered_count || 0,                        icon: <Trophy   className="w-7 h-7" />, bg: 'bg-emerald-100', color: 'text-emerald-600' },
    { label: t('dashboard.stats.streak'),   value: stats.current_streak || 0,                        icon: <Flame    className="w-7 h-7" />, bg: 'bg-orange-100',  color: 'text-orange-600' },
    { label: t('dashboard.stats.reviews'),  value: stats.total_reviews || 0,                         icon: <FileText className="w-7 h-7" />, bg: 'bg-blue-100',    color: 'text-blue-600' },
    { label: t('dashboard.stats.accuracy'), value: `${Math.round(stats.accuracy_rate || 0)}%`,       icon: <Target   className="w-7 h-7" />, bg: 'bg-purple-100',  color: 'text-purple-600' },
  ] : defaultStats;

  const defaultActivity = [
    { dataset: t('dashboard.noActivity'), correct: 0, total: 0, time: t('dashboard.noActivityDesc') },
  ];

  const displayActivity = progress?.recent_sessions || defaultActivity;

  return (
    <div className="space-y-8">
      <div className="text-center">
        <h1 className="text-2xl md:text-4xl font-bold mb-4 text-gray-900">
          {t('dashboard.welcome', { name: user?.username })}
        </h1>
        <p className="text-lg text-gray-600">{t('dashboard.subtitle')}</p>
      </div>

      {error && (
        <div className="alert alert-warning">
          <span>{t('dashboard.offlineWarning')}</span>
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {dashboardLoading ? (
          Array.from({ length: 4 }).map((_, index) => (
            <div key={index} className="card-flashcard p-6 text-center animate-pulse">
              <div className="w-8 h-8 bg-gray-200 rounded-full mx-auto mb-2"></div>
              <div className="h-4 bg-gray-200 rounded mb-1"></div>
              <div className="h-6 bg-gray-200 rounded"></div>
            </div>
          ))
        ) : (
          displayStats.map((stat, index) => (
            <div key={index} className="card-flashcard p-6 text-center">
              <div className={`w-12 h-12 ${stat.bg} ${stat.color} rounded-2xl flex items-center justify-center mx-auto mb-3`}>
                {stat.icon}
              </div>
              <div className="text-sm text-gray-500 mb-1">{stat.label}</div>
              <div className={`text-2xl font-bold ${stat.color}`}>{stat.value}</div>
            </div>
          ))
        )}
      </div>

      {/* Quick Actions */}
      <div className="card-flashcard p-6">
        <h2 className="text-xl font-bold mb-4 flex items-center gap-2 text-gray-900">
          <Zap className="w-5 h-5 text-indigo-500" /> {t('dashboard.quickActions')}
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => navigate('/progress')}
            className="p-4 bg-blue-50 hover:bg-blue-100 rounded-xl border-2 border-blue-100 hover:border-blue-200 transition-all text-left group"
          >
            <div className="w-10 h-10 bg-blue-100 group-hover:bg-blue-200 text-blue-600 rounded-xl flex items-center justify-center mb-3 transition-colors">
              <BarChart3 className="w-5 h-5" />
            </div>
            <div className="font-semibold text-gray-900">{t('dashboard.viewProgress')}</div>
            <div className="text-sm text-gray-500">{t('dashboard.viewProgressDesc')}</div>
          </button>

          <button
            onClick={() => navigate('/rankings')}
            className="p-4 bg-amber-50 hover:bg-amber-100 rounded-xl border-2 border-amber-100 hover:border-amber-200 transition-all text-left group"
          >
            <div className="w-10 h-10 bg-amber-100 group-hover:bg-amber-200 text-amber-600 rounded-xl flex items-center justify-center mb-3 transition-colors">
              <Trophy className="w-5 h-5" />
            </div>
            <div className="font-semibold text-gray-900">{t('dashboard.viewRankings')}</div>
            <div className="text-sm text-gray-500">{t('dashboard.viewRankingsDesc')}</div>
          </button>

          <button
            onClick={() => navigate('/learn')}
            className="p-4 bg-emerald-50 hover:bg-emerald-100 rounded-xl border-2 border-emerald-100 hover:border-emerald-200 transition-all text-left group"
          >
            <div className="w-10 h-10 bg-emerald-100 group-hover:bg-emerald-200 text-emerald-600 rounded-xl flex items-center justify-center mb-3 transition-colors">
              <Zap className="w-5 h-5" />
            </div>
            <div className="font-semibold text-gray-900">{t('dashboard.startLearning')}</div>
            <div className="text-sm text-gray-500">{t('dashboard.startLearningDesc')}</div>
          </button>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="card-flashcard p-6">
        <h2 className="text-xl font-bold mb-4 flex items-center gap-2 text-gray-900">
          <Clock className="w-5 h-5 text-indigo-500" /> {t('dashboard.recentActivity')}
        </h2>
        <div className="space-y-3">
          {displayActivity.map((activity, index) => (
            <div key={index} className="flex items-center justify-between p-3 rounded-xl border border-gray-100 bg-white/60">
              <div>
                <div className="font-medium text-gray-900">{activity.dataset}</div>
                <div className="text-sm text-gray-600">{activity.time}</div>
              </div>
              <div className="text-right">
                <div className="font-bold text-gray-900">
                  {activity.correct}/{activity.total}
                </div>
                <div className="text-sm text-gray-600">
                  {activity.total > 0 ? Math.round((activity.correct / activity.total) * 100) : 0}% {t('dashboard.correct')}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
