import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import RankingCard from '../components/RankingCard';
import apiService from '../services/api';
import { Trophy, Target, Zap, Star, RefreshCw, ArrowLeft, Lock } from 'lucide-react';

export default function Rankings() {
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('cards-answered');
  const [rankings, setRankings] = useState({
    'cards-answered': [],
    'accuracy': [],
    'speed': [],
    'overall': []
  });

  const tabs = [
    { id: 'cards-answered', label: 'Cards Answered', icon: <Trophy  className="w-4 h-4" />, description: 'Most cards answered' },
    { id: 'accuracy',       label: 'Accuracy',       icon: <Target  className="w-4 h-4" />, description: 'Highest accuracy (min. 20 cards)' },
    { id: 'speed',          label: 'Speed',          icon: <Zap     className="w-4 h-4" />, description: 'Fastest responses (min. 50 cards)' },
    { id: 'overall',        label: 'Overall',        icon: <Star    className="w-4 h-4" />, description: 'Combined performance score' },
  ];

  useEffect(() => {
    if (!isAuthenticated) return;
    fetchRankings();
  }, [isAuthenticated]);

  const fetchRankings = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const [cardsAnswered, accuracy, speed, overall] = await Promise.all([
        apiService.get('/dashboard/rankings/cards-answered?limit=20'),
        apiService.get('/dashboard/rankings/accuracy?limit=20&min_cards=20'),
        apiService.get('/dashboard/rankings/speed?limit=20&min_cards=50'),
        apiService.get('/dashboard/rankings/overall?limit=20')
      ]);

      setRankings({
        'cards-answered': cardsAnswered,
        'accuracy': accuracy,
        'speed': speed,
        'overall': overall
      });
    } catch (err) {
      console.error('Error fetching rankings:', err);
      setError('Failed to load rankings data');
    } finally {
      setLoading(false);
    }
  };

  const refreshMyStats = async () => {
    try {
      await apiService.post(`/dashboard/rankings/refresh/${user.id}`);
      await fetchRankings(); // Refresh the rankings
    } catch (err) {
      console.error('Error refreshing stats:', err);
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="max-w-4xl mx-auto text-center py-12">
        <div className="card-flashcard p-8">
          <div className="flex justify-center mb-6"><Lock className="w-16 h-16 text-gray-300" /></div>
          <h2 className="text-2xl font-bold mb-4">Login Required</h2>
          <p className="text-gray-600 mb-6">
            Please log in to view rankings and leaderboards.
          </p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-2xl md:text-4xl font-bold mb-4 text-gray-900 flex items-center justify-center gap-3"><Trophy className="w-8 h-8 text-amber-500" /> Rankings & Leaderboards</h1>
          <p className="text-lg text-gray-600">
            See how you rank against other learners
          </p>
        </div>
        <div className="card-flashcard p-8 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p>Loading rankings...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-2xl md:text-4xl font-bold mb-4 text-gray-900 flex items-center justify-center gap-3"><Trophy className="w-8 h-8 text-amber-500" /> Rankings & Leaderboards</h1>
        </div>
        <div className="card-flashcard p-8 text-center">
          <div className="text-6xl mb-6">⚠️</div>
          <h2 className="text-2xl font-bold mb-4 text-gray-900">Unable to Load Rankings</h2>
          <p className="text-lg text-gray-600 mb-6">{error}</p>
          <button
            onClick={fetchRankings}
            className="btn btn-primary"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  const currentRankings = rankings[activeTab] || [];
  const currentTab = tabs.find(tab => tab.id === activeTab);

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4 text-gray-900">🏆 Rankings & Leaderboards</h1>
        <p className="text-lg text-gray-600">
          See how you rank against other learners across different categories
        </p>
      </div>

      {/* Action Buttons */}
      <div className="flex justify-center space-x-4">
        <button onClick={refreshMyStats} className="btn btn-secondary flex items-center gap-2">
          <RefreshCw className="w-4 h-4" />
          <span>Refresh My Stats</span>
        </button>
        <button onClick={() => navigate('/dashboard')} className="btn btn-neutral flex items-center gap-2">
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Dashboard</span>
        </button>
      </div>

      {/* Category Tabs */}
      <div className="card-flashcard p-6">
        <div className="flex flex-wrap justify-center gap-2 mb-6">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`tab-btn ${activeTab === tab.id ? 'tab-btn-active' : 'tab-btn-inactive'}`}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
            </button>
          ))}
        </div>

        <div className="text-center mb-4">
          <h2 className="text-xl font-semibold text-gray-900 flex items-center justify-center space-x-2">
            <span>{currentTab?.icon}</span>
            <span>{currentTab?.label} Rankings</span>
          </h2>
          <p className="text-gray-600 text-sm">{currentTab?.description}</p>
        </div>

        {/* Rankings List */}
        <div className="space-y-3">
          {currentRankings.length > 0 ? (
            currentRankings.map((item, index) => {
              const isCurrentUser = item.user_id === user.id;
              return (
                <RankingCard
                  key={item.user_id}
                  item={item}
                  rank={item.rank}
                  isCurrentUser={isCurrentUser}
                  activeTab={activeTab}
                />
              );
            })
          ) : (
            <div className="text-center py-8">
              <div className="text-4xl mb-4">📊</div>
              <p className="text-gray-600">
                No rankings available yet. Start learning to join the leaderboards!
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Rankings Explanation */}
      <div className="card-flashcard p-6">
        <h3 className="text-lg font-semibold mb-4 text-gray-900">How Rankings Work</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-600">
          <div className="space-y-2">
            <div><strong>🏆 Cards Answered:</strong> Total number of flashcards you've practiced</div>
            <div><strong>🎯 Accuracy:</strong> Percentage of correct answers (minimum 20 cards required)</div>
          </div>
          <div className="space-y-2">
            <div><strong>⚡ Speed:</strong> Fast response time weighted by volume (minimum 50 cards)</div>
            <div><strong>🌟 Overall:</strong> Combined score considering all factors</div>
          </div>
        </div>
        <div className="mt-4 p-3 bg-blue-50 rounded-lg">
          <p className="text-sm text-blue-800">
            <strong>Note:</strong> Rankings are updated in real-time as you practice. 
            Use "Refresh My Stats" to ensure your latest performance is reflected.
          </p>
        </div>
      </div>
    </div>
  );
}
