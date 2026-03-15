import { useAuth } from '../contexts/AuthContext';
import { useDashboard, useProgressHistory } from '../hooks/useApi';
import { useNavigate } from 'react-router-dom';

export default function Dashboard() {
  const { user, isAuthenticated } = useAuth();
  const { progress, stats, achievements, loading: dashboardLoading, error } = useDashboard();
  const { history, loading: historyLoading } = useProgressHistory(7); // Last 7 days
  const navigate = useNavigate();

  if (!isAuthenticated) {
    return (
      <div className="max-w-4xl mx-auto text-center py-12">
        <div className="card-flashcard p-8">
          <div className="text-6xl mb-6">🔒</div>
          <h2 className="text-2xl font-bold mb-4">Login Required</h2>
          <p className="text-gray-600 mb-6">
            Please log in to view your dashboard and track your learning progress.
          </p>
        </div>
      </div>
    );
  }

  // Mock data for when API data is not available
  const defaultStats = [
    { label: 'Elements Mastered', value: 0, icon: '🏆', color: 'text-green-600' },
    { label: 'Current Streak', value: 0, icon: '🔥', color: 'text-orange-600' },
    { label: 'Total Reviews', value: 0, icon: '📝', color: 'text-blue-600' },
    { label: 'Accuracy Rate', value: '0%', icon: '🎯', color: 'text-purple-600' },
  ];

  const displayStats = stats ? [
    { label: 'Elements Mastered', value: stats.mastered_count || 0, icon: '🏆', color: 'text-green-600' },
    { label: 'Current Streak', value: stats.current_streak || 0, icon: '🔥', color: 'text-orange-600' },
    { label: 'Total Reviews', value: stats.total_reviews || 0, icon: '📝', color: 'text-blue-600' },
    { label: 'Accuracy Rate', value: `${Math.round(stats.accuracy_rate || 0)}%`, icon: '🎯', color: 'text-purple-600' },
  ] : defaultStats;

  const defaultActivity = [
    { dataset: 'No recent activity', correct: 0, total: 0, time: 'Start learning to see activity' },
  ];

  const displayActivity = progress?.recent_sessions || defaultActivity;

  return (
    <div className="space-y-8">
      <div className="text-center">
        <h1 className="text-2xl md:text-4xl font-bold mb-4 text-gray-900">
          Welcome back, {user?.username}! 👋
        </h1>
        <p className="text-lg text-gray-600">
          Track your learning progress and achievements
        </p>
      </div>

      {error && (
        <div className="alert alert-warning">
          <span>⚠️ Unable to load dashboard data. Showing offline view.</span>
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
              <div className="text-3xl mb-2">{stat.icon}</div>
              <div className="text-sm text-gray-600 mb-1">{stat.label}</div>
              <div className={`text-2xl font-bold ${stat.color}`}>{stat.value}</div>
            </div>
          ))
        )}
      </div>

      {/* Quick Actions */}
      <div className="card-flashcard p-6">
        <h2 className="text-xl font-bold mb-4 flex items-center text-gray-900">
          <span className="text-2xl mr-2">⚡</span>
          Quick Actions
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => navigate('/progress')}
            className="p-4 bg-blue-50 hover:bg-blue-100 rounded-lg border-2 border-blue-200 hover:border-blue-300 transition-colors text-left"
          >
            <div className="text-2xl mb-2">📊</div>
            <div className="font-semibold text-gray-900">View Progress</div>
            <div className="text-sm text-gray-600">Track your learning journey</div>
          </button>
          
          <button
            onClick={() => navigate('/rankings')}
            className="p-4 bg-yellow-50 hover:bg-yellow-100 rounded-lg border-2 border-yellow-200 hover:border-yellow-300 transition-colors text-left"
          >
            <div className="text-2xl mb-2">🏆</div>
            <div className="font-semibold text-gray-900">View Rankings</div>
            <div className="text-sm text-gray-600">See how you rank against others</div>
          </button>
          
          <button
            onClick={() => navigate('/learn')}
            className="p-4 bg-green-50 hover:bg-green-100 rounded-lg border-2 border-green-200 hover:border-green-300 transition-colors text-left"
          >
            <div className="text-2xl mb-2">🚀</div>
            <div className="font-semibold text-gray-900">Start Learning</div>
            <div className="text-sm text-gray-600">Continue your studies</div>
          </button>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="card-flashcard p-6">
        <h2 className="text-xl font-bold mb-4 flex items-center text-gray-900">
          <span className="text-2xl mr-2">🕐</span>
          Recent Activity
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
                  {activity.total > 0 ? Math.round((activity.correct / activity.total) * 100) : 0}% correct
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
