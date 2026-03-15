import React from 'react';
import { useTranslation } from 'react-i18next';

export default function RankingCard({ item, rank, isCurrentUser, activeTab }) {
  const { t } = useTranslation();

  const getRankBadgeColor = (rank) => {
    if (rank === 1) return 'bg-gradient-to-br from-yellow-400 to-yellow-600 text-white shadow-lg';
    if (rank === 2) return 'bg-gradient-to-br from-gray-300 to-gray-500 text-white shadow-md';
    if (rank === 3) return 'bg-gradient-to-br from-orange-400 to-orange-600 text-white shadow-md';
    if (rank <= 10) return 'bg-gradient-to-br from-blue-400 to-blue-600 text-white';
    return 'bg-gray-200 text-gray-700';
  };

  const getRankIcon = (rank) => {
    if (rank === 1) return '👑';
    if (rank === 2) return '🥈';
    if (rank === 3) return '🥉';
    if (rank <= 10) return '⭐';
    return '🏅';
  };

  const formatValue = (item) => {
    switch (activeTab) {
      case 'cards-answered': return `${item.total_cards_answered.toLocaleString()}`;
      case 'accuracy':       return `${item.accuracy_percentage.toFixed(1)}%`;
      case 'speed':          return `${item.speed_score.toFixed(1)}`;
      case 'overall':        return `${item.overall_score.toFixed(1)}`;
      default:               return '';
    }
  };

  const getValueLabel = () => {
    switch (activeTab) {
      case 'cards-answered': return t('rankingCard.cards');
      case 'accuracy':       return t('rankingCard.accuracy');
      case 'speed':          return t('rankingCard.speedPts');
      case 'overall':        return t('rankingCard.overallPts');
      default:               return '';
    }
  };

  const getSecondaryInfo = (item) => {
    switch (activeTab) {
      case 'cards-answered':
        return `${item.accuracy_percentage?.toFixed(1)}% ${t('rankingCard.accuracy')}`;
      case 'accuracy':
        return `${item.total_cards_answered.toLocaleString()} ${t('rankingCard.cardsAnswered')}`;
      case 'speed':
        return `${item.average_response_time_ms}${t('rankingCard.avgMs')} • ${item.total_cards_answered.toLocaleString()} ${t('rankingCard.cards')}`;
      case 'overall':
        return `${item.total_cards_answered.toLocaleString()} ${t('rankingCard.cards')} • ${item.accuracy_percentage?.toFixed(1)}% ${t('rankingCard.accuracy')}`;
      default:
        return '';
    }
  };

  return (
    <div
      className={`relative p-4 rounded-xl border-2 transition-all duration-200 hover:scale-[1.02] ${
        isCurrentUser
          ? 'border-blue-400 bg-gradient-to-r from-blue-50 to-indigo-50 shadow-lg'
          : rank <= 3
          ? 'border-yellow-200 bg-gradient-to-r from-yellow-50 to-orange-50 shadow-md'
          : 'border-gray-200 bg-white hover:bg-gray-50 shadow-sm'
      }`}
    >
      {isCurrentUser && (
        <div className="absolute -top-2 -right-2 bg-blue-500 text-white text-xs px-2 py-1 rounded-full font-semibold animate-pulse">
          {t('rankingCard.you')}
        </div>
      )}

      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          {/* Rank Badge */}
          <div className="relative">
            <div
              className={`w-12 h-12 rounded-full flex items-center justify-center text-lg font-bold ${getRankBadgeColor(rank)} ${
                rank <= 3 ? 'animate-pulse' : ''
              }`}
            >
              {rank <= 3 ? getRankIcon(rank) : rank}
            </div>
            {rank <= 3 && (
              <div className="absolute -bottom-1 -right-1 text-lg">
                {getRankIcon(rank)}
              </div>
            )}
          </div>

          {/* User Info */}
          <div>
            <div className={`font-bold text-lg ${isCurrentUser ? 'text-blue-900' : 'text-gray-900'}`}>
              {item.user_name}
              {isCurrentUser && (
                <span className="ml-2 text-blue-600 font-semibold text-sm">
                  {t('rankingCard.youLabel')}
                </span>
              )}
            </div>
            <div className="text-sm text-gray-600">
              {getSecondaryInfo(item)}
            </div>
            {item.last_activity && (
              <div className="text-xs text-gray-500 mt-1">
                {t('rankingCard.lastActive', { date: new Date(item.last_activity).toLocaleDateString() })}
              </div>
            )}
          </div>
        </div>

        {/* Performance Value */}
        <div className="text-right">
          <div className={`text-2xl font-bold ${isCurrentUser ? 'text-blue-900' : rank <= 3 ? 'text-yellow-700' : 'text-gray-900'}`}>
            {formatValue(item)}
          </div>
          <div className="text-sm text-gray-600 font-medium">
            {getValueLabel()}
          </div>
          {rank <= 10 && (
            <div className="text-xs text-gray-500 mt-1">
              {rank <= 3 ? t('rankingCard.top3') : t('rankingCard.top10')}
            </div>
          )}
        </div>
      </div>

      {/* Progress Bar for Overall Score */}
      {activeTab === 'overall' && (
        <div className="mt-3">
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className={`h-2 rounded-full ${
                isCurrentUser ? 'bg-blue-500' : rank <= 3 ? 'bg-yellow-500' : 'bg-gray-400'
              }`}
              style={{
                width: `${Math.min((item.overall_score / Math.max(item.overall_score, 1000)) * 100, 100)}%`
              }}
            ></div>
          </div>
        </div>
      )}
    </div>
  );
}
