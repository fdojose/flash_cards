import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useProgressHistory, useDatasetProgress } from '../hooks/useApi';
import DetailedCardStats from '../components/DetailedCardStats';

export default function Progress() {
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();
  const { history, loading: historyLoading, error: historyError } = useProgressHistory(30); // Last 30 days
  const { datasetProgress, loading: progressLoading, error: progressError } = useDatasetProgress();
  const [selectedLearningSetId, setSelectedLearningSetId] = useState(null);

  const loading = historyLoading || progressLoading;
  const error = historyError || progressError;

  if (!isAuthenticated) {
    return (
      <div className="max-w-4xl mx-auto text-center py-12">
        <div className="card-flashcard p-8">
          <div className="text-6xl mb-6">🔒</div>
          <h2 className="text-2xl font-bold mb-4">Login Required</h2>
          <p className="text-gray-600 mb-6">
            Please log in to view your progress and learning analytics.
          </p>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold mb-4 text-gray-900">Learning Progress</h1>
          <p className="text-lg text-gray-600">
            Track your progress across all datasets and daily learning activity
          </p>
        </div>
        <div className="card-flashcard p-8 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p>Loading your progress data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold mb-4 text-gray-900">Learning Progress</h1>
          <p className="text-lg text-gray-600">
            Track your progress across all datasets and daily learning activity
          </p>
        </div>
        <div className="card-flashcard p-8 text-center">
          <div className="text-6xl mb-6">⚠️</div>
          <h2 className="text-2xl font-bold mb-4 text-gray-900">
            Unable to Load Progress Data
          </h2>
          <p className="text-lg text-gray-600 mb-6">
            Start learning with flashcards to track your progress here.
          </p>
        </div>
      </div>
    );
  }

  const defaultHistory = [
    { date: new Date().toISOString().split('T')[0], reviews: 0, accuracy: 0 }
  ];

  const displayHistory = history && history.length > 0 ? history : defaultHistory;
  const totalReviews = displayHistory.reduce((sum, day) => sum + day.reviews, 0);
  const averageAccuracy = displayHistory.length > 0 
    ? displayHistory.reduce((sum, day) => sum + day.accuracy, 0) / displayHistory.length 
    : 0;

  // Calculate dataset statistics
  const totalDatasets = datasetProgress ? datasetProgress.length : 0;
  const completedDatasets = datasetProgress ? datasetProgress.filter(d => d.status === 'completed').length : 0;
  const inProgressDatasets = datasetProgress ? datasetProgress.filter(d => d.status === 'in_progress').length : 0;
  const totalElementsMastered = datasetProgress ? datasetProgress.reduce((sum, d) => sum + d.elements_mastered, 0) : 0;
  const totalElements = datasetProgress ? datasetProgress.reduce((sum, d) => sum + d.elements_in_dataset, 0) : 0;
  const overallProgress = totalDatasets > 0 
    ? datasetProgress.reduce((sum, d) => sum + d.completion_percentage, 0) / totalDatasets 
    : 0;

  // Calculate learning streak and other metrics
  const recentActivity = displayHistory.slice(-7); // Last 7 days
  const totalSessionsLastWeek = recentActivity.reduce((sum, day) => sum + (day.reviews > 0 ? 1 : 0), 0);
  const averageSessionsPerWeek = totalSessionsLastWeek;

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4 text-gray-900">Learning Progress</h1>
        <p className="text-lg text-gray-600">
          Track your progress across all datasets and daily learning activity
        </p>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="card-flashcard p-6 text-center">
          <div className="text-3xl mb-2">�</div>
          <div className="text-sm text-gray-600 mb-1">Total Datasets</div>
          <div className="text-2xl font-bold text-blue-600">{totalDatasets}</div>
        </div>
        <div className="card-flashcard p-6 text-center">
          <div className="text-3xl mb-2">✅</div>
          <div className="text-sm text-gray-600 mb-1">Completed</div>
          <div className="text-2xl font-bold text-green-600">{completedDatasets}</div>
        </div>
        <div className="card-flashcard p-6 text-center">
          <div className="text-3xl mb-2">🎯</div>
          <div className="text-sm text-gray-600 mb-1">Cards Mastered</div>
          <div className="text-2xl font-bold text-purple-600">{totalElementsMastered}</div>
        </div>
        <div className="card-flashcard p-6 text-center">
          <div className="text-3xl mb-2">📊</div>
          <div className="text-sm text-gray-600 mb-1">Overall Progress</div>
          <div className="text-2xl font-bold text-orange-600">{Math.round(overallProgress)}%</div>
        </div>
      </div>

      {/* Daily Activity */}
      <div className="card-flashcard p-6">
        <h2 className="text-xl font-bold mb-4 flex items-center text-gray-900">
          <span className="text-2xl mr-2">📈</span>
          Daily Learning Activity
        </h2>
        
        {totalReviews === 0 ? (
          <div className="text-center py-8">
            <div className="text-4xl mb-4">🌱</div>
            <p className="text-gray-600 mb-4">
              Start practicing with flashcards to see your progress here!
            </p>
            <p className="text-sm text-gray-500">
              Your daily review activity and accuracy will be tracked automatically.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {displayHistory.slice().reverse().slice(0, 7).map((day, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-4">
                  <div className="text-sm font-medium text-gray-900">
                    {new Date(day.date).toLocaleDateString('en-US', { 
                      weekday: 'short', 
                      month: 'short', 
                      day: 'numeric' 
                    })}
                  </div>
                  <div className="text-sm text-gray-600">
                    {day.reviews} reviews
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <div className="text-sm font-medium text-gray-900">
                    {Math.round(day.accuracy)}% accuracy
                  </div>
                  <div className="w-16 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-green-600 h-2 rounded-full" 
                      style={{ width: `${day.accuracy}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Performance Insights */}
      <div className="card-flashcard p-6">
        <h2 className="text-xl font-bold mb-4 flex items-center text-gray-900">
          <span className="text-2xl mr-2">🎯</span>
          Performance Insights
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-blue-50 p-4 rounded-lg">
            <div className="text-sm font-medium text-blue-800 mb-1">Average Accuracy</div>
            <div className="text-2xl font-bold text-blue-600">
              {totalReviews > 0 ? Math.round(averageAccuracy) : 0}%
            </div>
            <div className="text-xs text-blue-600 mt-1">
              Based on {totalReviews} reviews
            </div>
          </div>
          
          <div className="bg-green-50 p-4 rounded-lg">
            <div className="text-sm font-medium text-green-800 mb-1">Completion Rate</div>
            <div className="text-2xl font-bold text-green-600">
              {totalDatasets > 0 ? Math.round((completedDatasets / totalDatasets) * 100) : 0}%
            </div>
            <div className="text-xs text-green-600 mt-1">
              {completedDatasets} of {totalDatasets} datasets
            </div>
          </div>
          
          <div className="bg-purple-50 p-4 rounded-lg">
            <div className="text-sm font-medium text-purple-800 mb-1">Learning Streak</div>
            <div className="text-2xl font-bold text-purple-600">
              {(() => {
                let streak = 0;
                const sortedHistory = [...displayHistory].sort((a, b) => new Date(b.date) - new Date(a.date));
                for (let day of sortedHistory) {
                  if (day.reviews > 0) {
                    streak++;
                  } else {
                    break;
                  }
                }
                return streak;
              })()}
            </div>
            <div className="text-xs text-purple-600 mt-1">
              consecutive days
            </div>
          </div>
        </div>
        
        {inProgressDatasets > 0 && (
          <div className="bg-orange-50 p-4 rounded-lg">
            <div className="flex items-center justify-between mb-2">
              <div className="text-sm font-medium text-orange-800">Datasets in Progress</div>
              <div className="text-lg font-bold text-orange-600">{inProgressDatasets}</div>
            </div>
            <div className="text-xs text-orange-600">
              Keep practicing to complete these datasets!
            </div>
          </div>
        )}
      </div>

      {/* Dataset Progress */}
      <div className="card-flashcard p-6">
        <h2 className="text-xl font-bold mb-4 flex items-center text-gray-900">
          <span className="text-2xl mr-2">📚</span>
          Progress by Dataset
        </h2>
        
        {datasetProgress && datasetProgress.length > 0 ? (
          <div className="space-y-4">
            {datasetProgress.map((dataset) => (
              <div key={dataset.dataset_id} className="border rounded-lg p-4 bg-gray-50">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h3 className="font-semibold text-gray-900">{dataset.dataset_name}</h3>
                    <p className="text-sm text-gray-600">
                      {dataset.elements_mastered} / {dataset.elements_in_dataset} mastered
                    </p>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold text-blue-600">
                      {dataset.completion_percentage === 0 
                        ? '0%'
                        : dataset.completion_percentage < 0.01
                        ? '<1%'
                        : `${Math.round(dataset.completion_percentage * 100)}%`}
                    </div>
                    <div className="text-sm text-gray-600">
                      {Math.round(dataset.accuracy_rate)}% accuracy
                    </div>
                  </div>
                </div>
                
                <div className="mb-3">
                  <div className="flex justify-between text-sm text-gray-600 mb-1">
                    <span>Progress</span>
                    <span>{dataset.elements_mastered}/{dataset.elements_in_dataset}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div 
                      className={`h-3 rounded-full ${
                        dataset.completion_percentage === 1 
                          ? 'bg-green-500' 
                          : dataset.completion_percentage >= 0.8 
                          ? 'bg-blue-500' 
                          : dataset.completion_percentage >= 0.5 
                          ? 'bg-yellow-500' 
                          : 'bg-orange-500'
                      }`}
                      style={{ width: `${Math.max(dataset.completion_percentage * 100, dataset.completion_percentage > 0 ? 1 : 0)}%` }}
                    ></div>
                  </div>
                </div>
                
                <div className="flex items-center justify-between text-sm mb-3">
                  <div className="flex items-center space-x-4">
                    <span className={`px-2 py-1 rounded-full text-xs ${
                      dataset.status === 'completed' 
                        ? 'bg-green-100 text-green-800' 
                        : dataset.status === 'in_progress' 
                        ? 'bg-blue-100 text-blue-800' 
                        : 'bg-gray-100 text-gray-800'
                    }`}>
                      {dataset.status === 'completed' ? '✅ Complete' : 
                       dataset.status === 'in_progress' ? '📈 In Progress' : 
                       '🌱 Started'}
                    </span>
                    <span className="text-gray-600">
                      Stage {dataset.current_stage}
                    </span>
                  </div>
                  <div className="text-gray-500">
                    {dataset.last_studied ? (
                      <>Last studied: {new Date(dataset.last_studied).toLocaleDateString()}</>
                    ) : (
                      <>Started: {new Date(dataset.started_at).toLocaleDateString()}</>
                    )}
                  </div>
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    {dataset.failed_elements && dataset.failed_elements > 0 && (
                      <button
                        onClick={() => navigate(`/datasets/${dataset.dataset_id}/failed-cards`)}
                        className="px-3 py-1 text-xs bg-red-100 text-red-700 rounded-md hover:bg-red-200 transition-colors"
                      >
                        ❌ Failed Cards ({dataset.failed_elements})
                      </button>
                    )}
                    <button
                      onClick={() => setSelectedLearningSetId(dataset.learning_set_id)}
                      className="px-3 py-1 text-xs bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200 transition-colors"
                    >
                      📊 View Stats
                    </button>
                  </div>
                  <div className="flex items-center space-x-2 text-xs text-gray-500">
                    <span>{dataset.elements_mastered} mastered</span>
                    <span>•</span>
                    <span>{dataset.elements_in_dataset - dataset.elements_mastered} remaining</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8">
            <div className="text-4xl mb-4">📖</div>
            <p className="text-gray-600 mb-4">
              No dataset progress to show yet.
            </p>
            <p className="text-sm text-gray-500">
              Start learning with flashcards to see your progress by dataset here!
            </p>
          </div>
        )}
      </div>

      {/* Detailed Card Statistics */}
      <DetailedCardStats learningSetId={selectedLearningSetId} />
    </div>
  );
}
