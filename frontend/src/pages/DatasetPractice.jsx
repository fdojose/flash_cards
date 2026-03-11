import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useState, useEffect } from 'react';
import apiService from '../services/api';

export default function DatasetPractice() {
  const { datasetId } = useParams();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [dataset, setDataset] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/');
      return;
    }

    fetchDatasetInfo();
  }, [datasetId, isAuthenticated]);

  const fetchDatasetInfo = async () => {
    try {
      setLoading(true);
      const response = await apiService.get(`/datasets/${datasetId}`);
      setDataset(response.data);
    } catch (err) {
      console.error('Error fetching dataset:', err);
      setError('Failed to load dataset information');
    } finally {
      setLoading(false);
    }
  };

  const startPracticeSession = async () => {
    try {
      // Start a learning session for this specific dataset
      const response = await apiService.post('/sessions/start', {
        dataset_id: parseInt(datasetId),
        session_type: 'practice'
      });
      
      // Navigate to the learning page with the session
      navigate(`/learn/${datasetId}?session=${response.data.session_id}`);
    } catch (err) {
      console.error('Error starting practice session:', err);
      setError('Failed to start practice session');
    }
  };

  if (!isAuthenticated) {
    return null; // Will redirect in useEffect
  }

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="card-flashcard p-8 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p>Loading dataset information...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="card-flashcard p-8 text-center">
          <div className="text-6xl mb-6">⚠️</div>
          <h2 className="text-2xl font-bold mb-4 text-gray-900">Error</h2>
          <p className="text-lg text-gray-600 mb-6">{error}</p>
          <button
            onClick={() => navigate('/progress')}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Back to Progress
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4 text-gray-900">Practice Session</h1>
        <p className="text-lg text-gray-600">
          Ready to practice with flashcards from this dataset
        </p>
      </div>

      {dataset && (
        <div className="card-flashcard p-8">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold mb-4 text-gray-900">{dataset.name}</h2>
            <p className="text-gray-600 mb-6">{dataset.description}</p>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-blue-600 mb-1">
                  {dataset.total_elements || 0}
                </div>
                <div className="text-sm text-blue-800">Total Cards</div>
              </div>
              
              <div className="bg-green-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-green-600 mb-1">
                  {dataset.mastered_elements || 0}
                </div>
                <div className="text-sm text-green-800">Mastered</div>
              </div>
              
              <div className="bg-orange-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-orange-600 mb-1">
                  {(dataset.total_elements || 0) - (dataset.mastered_elements || 0)}
                </div>
                <div className="text-sm text-orange-800">Remaining</div>
              </div>
            </div>
          </div>

          <div className="text-center space-y-4">
            <button
              onClick={startPracticeSession}
              className="px-8 py-3 bg-blue-600 text-white text-lg font-semibold rounded-lg hover:bg-blue-700 transition-colors"
            >
              🚀 Start Practice Session
            </button>
            
            <div className="flex justify-center space-x-4">
              <button
                onClick={() => navigate('/progress')}
                className="px-4 py-2 text-gray-600 hover:text-gray-900 transition-colors"
              >
                ← Back to Progress
              </button>
              
              <button
                onClick={() => navigate(`/datasets/${datasetId}/failed-cards`)}
                className="px-4 py-2 text-red-600 hover:text-red-900 transition-colors"
              >
                Review Failed Cards →
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
