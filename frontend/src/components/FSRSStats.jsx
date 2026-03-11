import React from 'react';

const FSRSStats = ({ stats, isCompact = false }) => {
  if (!stats) return null;

  if (isCompact) {
    // Compact version for the main learning interface
    return (
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-3 mb-4 border border-blue-200">
        <div className="flex items-center justify-between text-xs">
          <div className="flex items-center space-x-4">
            <div className="flex items-center">
              <span className="text-blue-600 font-semibold">📊</span>
              <span className="ml-1 text-gray-700">Reviews: <span className="font-semibold">{stats.review_count}</span></span>
            </div>
            <div className="flex items-center">
              <span className="text-green-600">🔥</span>
              <span className="ml-1 text-gray-700">Streak: <span className="font-semibold">{stats.success_streak}</span></span>
            </div>
            <div className="flex items-center">
              <span className="text-purple-600">⭐</span>
              <span className="ml-1 text-gray-700">Ease: <span className="font-semibold">{stats.ease_factor}</span></span>
            </div>
          </div>
          <div className="flex items-center space-x-3">
            <div className="flex items-center">
              <span className="text-amber-600">🧠</span>
              <span className="ml-1 text-gray-700">Stability: <span className="font-semibold">{stats.stability_score}</span></span>
            </div>
            <div className="flex items-center">
              <span className="text-red-600">📅</span>
              <span className="ml-1 text-gray-700">Interval: <span className="font-semibold">{stats.interval_days}d</span></span>
            </div>
          </div>
        </div>
        
        {/* Second row with status and accuracy */}
        <div className="flex items-center justify-between mt-2 text-xs border-t border-blue-100 pt-2">
          <div className="flex items-center space-x-4">
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(stats.status)}`}>
              {getStatusIcon(stats.status)} {stats.status.toUpperCase()}
            </span>
            {stats.accuracy_percentage > 0 && (
              <span className="text-gray-600">
                Accuracy: <span className="font-semibold text-green-600">{stats.accuracy_percentage}%</span>
              </span>
            )}
          </div>
          <div className="flex items-center space-x-3">
            {stats.is_difficult && (
              <span className="text-xs bg-red-100 text-red-700 px-2 py-1 rounded-full">
                🔸 Difficult
              </span>
            )}
            {stats.integration_confirmed && (
              <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full">
                ✓ Integrated
              </span>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Detailed version (could be used in a modal or detailed view)
  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
      <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center">
        <span className="text-blue-500 mr-2">🧠</span>
        FSRS Learning Statistics
      </h3>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="text-center p-3 bg-blue-50 rounded-lg">
          <div className="text-2xl font-bold text-blue-600">{stats.review_count}</div>
          <div className="text-xs text-blue-700">Reviews</div>
        </div>
        
        <div className="text-center p-3 bg-green-50 rounded-lg">
          <div className="text-2xl font-bold text-green-600">{stats.success_streak}</div>
          <div className="text-xs text-green-700">Success Streak</div>
        </div>
        
        <div className="text-center p-3 bg-purple-50 rounded-lg">
          <div className="text-2xl font-bold text-purple-600">{stats.ease_factor}</div>
          <div className="text-xs text-purple-700">Ease Factor</div>
        </div>
        
        <div className="text-center p-3 bg-amber-50 rounded-lg">
          <div className="text-2xl font-bold text-amber-600">{stats.stability_score}</div>
          <div className="text-xs text-amber-700">Stability Score</div>
        </div>
        
        <div className="text-center p-3 bg-red-50 rounded-lg">
          <div className="text-2xl font-bold text-red-600">{stats.interval_days}</div>
          <div className="text-xs text-red-700">Interval (days)</div>
        </div>
        
        <div className="text-center p-3 bg-gray-50 rounded-lg">
          <div className="text-2xl font-bold text-gray-600">{stats.days_until_due}</div>
          <div className="text-xs text-gray-700">Days Until Due</div>
        </div>
        
        <div className="text-center p-3 bg-indigo-50 rounded-lg">
          <div className="text-2xl font-bold text-indigo-600">{stats.accuracy_percentage}%</div>
          <div className="text-xs text-indigo-700">Accuracy</div>
        </div>
        
        <div className="text-center p-3 bg-cyan-50 rounded-lg">
          <div className="text-2xl font-bold text-cyan-600">{stats.integration_attempts}</div>
          <div className="text-xs text-cyan-700">Integration Attempts</div>
        </div>
      </div>
      
      <div className="mt-4 flex flex-wrap gap-2">
        <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(stats.status)}`}>
          {getStatusIcon(stats.status)} {stats.status.toUpperCase()}
        </span>
        
        {stats.is_difficult && (
          <span className="px-3 py-1 bg-red-100 text-red-700 rounded-full text-sm font-medium">
            🔸 Difficult Card
          </span>
        )}
        
        {stats.integration_confirmed && (
          <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-medium">
            ✓ Integration Confirmed
          </span>
        )}
      </div>
    </div>
  );
};

const getStatusColor = (status) => {
  switch (status) {
    case 'new':
      return 'bg-blue-100 text-blue-700';
    case 'learning':
      return 'bg-yellow-100 text-yellow-700';
    case 'due':
      return 'bg-orange-100 text-orange-700';
    case 'mastered':
      return 'bg-green-100 text-green-700';
    case 'integration_review':
      return 'bg-purple-100 text-purple-700';
    default:
      return 'bg-gray-100 text-gray-700';
  }
};

const getStatusIcon = (status) => {
  switch (status) {
    case 'new':
      return '🆕';
    case 'learning':
      return '📚';
    case 'due':
      return '⏰';
    case 'mastered':
      return '🏆';
    case 'integration_review':
      return '🔄';
    default:
      return '❓';
  }
};

export default FSRSStats;
