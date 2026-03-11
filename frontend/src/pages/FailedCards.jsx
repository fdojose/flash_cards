import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useState, useEffect } from 'react';
import apiService from '../services/api';

export default function FailedCards() {
  const { datasetId } = useParams();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [dataset, setDataset] = useState(null);
  const [failedCards, setFailedCards] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [expandedCards, setExpandedCards] = useState(new Set());

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/');
      return;
    }

    fetchFailedCards();
  }, [datasetId, isAuthenticated]);

  const fetchFailedCards = async () => {
    try {
      setLoading(true);
      
      // Fetch dataset info
      const datasetResponse = await apiService.get(`/datasets/${datasetId}`);
      setDataset(datasetResponse);
      
      // Fetch failed cards - cards that have been answered incorrectly
      const failedResponse = await apiService.get(`/datasets/${datasetId}/failed-cards`);
      setFailedCards(failedResponse || []);
      
    } catch (err) {
      console.error('Error fetching failed cards:', err);
      setError('Failed to load failed cards');
      setFailedCards([]); // Ensure failedCards is always an array
    } finally {
      setLoading(false);
    }
  };

  const toggleCardExpansion = (cardId) => {
    const newExpanded = new Set(expandedCards);
    if (newExpanded.has(cardId)) {
      newExpanded.delete(cardId);
    } else {
      newExpanded.add(cardId);
    }
    setExpandedCards(newExpanded);
  };

  const startFailedCardsSession = async () => {
    try {
      // Start a session focused on failed cards only
      const response = await apiService.post('/sessions/start', {
        dataset_id: parseInt(datasetId),
        session_type: 'failed_cards_review',
        failed_only: true
      });
      
      // Navigate to the learning page with the session
      navigate(`/learn/${datasetId}?session=${response.data.session_id}&mode=failed`);
    } catch (err) {
      console.error('Error starting failed cards session:', err);
      setError('Failed to start failed cards session');
    }
  };

  if (!isAuthenticated) {
    return null;
  }

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="card-flashcard p-8 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600 mx-auto mb-4"></div>
          <p>Loading failed cards...</p>
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
        <h1 className="text-4xl font-bold mb-4 text-gray-900">Failed Cards Review</h1>
        <p className="text-lg text-gray-600">
          Focus on cards that need more practice
        </p>
      </div>

      {dataset && (
        <div className="card-flashcard p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-xl font-bold text-gray-900">{dataset.name}</h2>
              <p className="text-gray-600">{dataset.description}</p>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-red-600 mb-1">
                {failedCards?.length || 0}
              </div>
              <div className="text-sm text-red-800">Failed Cards</div>
            </div>
          </div>
        </div>
      )}

      {(failedCards?.length || 0) === 0 ? (
        <div className="card-flashcard p-8 text-center">
          <div className="text-6xl mb-6">🎉</div>
          <h2 className="text-2xl font-bold mb-4 text-gray-900">
            No Failed Cards!
          </h2>
          <p className="text-lg text-gray-600 mb-6">
            Great job! You haven't failed any cards in this dataset yet, or all failed cards have been mastered.
          </p>
          <div className="space-x-4">
            <button
              onClick={() => navigate(`/datasets/${datasetId}/practice`)}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Practice All Cards
            </button>
            <button
              onClick={() => navigate('/progress')}
              className="px-6 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
            >
              Back to Progress
            </button>
          </div>
        </div>
      ) : (
        <div className="card-flashcard p-6">
          <h3 className="text-lg font-bold mb-4 text-gray-900">Cards That Need Practice</h3>
          <div className="grid gap-4">
            {(failedCards || []).map((card, index) => (
              <div
                key={card.id}
                className="border rounded-lg p-4 transition-colors bg-red-50 border-red-300"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="font-bold text-lg text-gray-900 mb-2">
                      {card.fields?.nombre_espanol || card.question || card.front}
                    </div>
                    {card.fields?.codigo_espanol && (
                      <div className="text-sm text-gray-700 mb-2">
                        <strong>Código:</strong> {card.fields.codigo_espanol}
                      </div>
                    )}
                    {card.fields?.nombre_chino && (
                      <div className="text-sm text-gray-700 mb-2">
                        <strong>Nombre Chino:</strong> {card.fields.nombre_chino}
                      </div>
                    )}
                  </div>
                  <div className="ml-4 text-right flex-shrink-0 flex flex-col items-end">
                    <div className="text-sm text-red-600 font-medium">
                      Failed {card.failure_count || 1} time{(card.failure_count || 1) !== 1 ? 's' : ''}
                    </div>
                    <div className="text-xs text-gray-500 mb-2">
                      Last attempt: {card.last_attempt ? new Date(card.last_attempt).toLocaleDateString() : 'Unknown'}
                    </div>
                    <button
                      onClick={() => toggleCardExpansion(card.id)}
                      className="px-3 py-1 text-xs bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition-colors"
                    >
                      {expandedCards.has(card.id) ? '▲ Collapse' : '▼ Expand Details'}
                    </button>
                  </div>
                </div>
                
                {expandedCards.has(card.id) && (
                  <div className="grid gap-3">
                    {card.fields?.ubicacion && (
                      <div className="p-3 bg-white rounded border">
                        <strong className="text-gray-800">Ubicación:</strong>
                        <p className="mt-1 text-gray-700">{card.fields.ubicacion}</p>
                      </div>
                    )}
                    
                    {card.fields?.como_encontrarlo && (
                      <div className="p-3 bg-white rounded border">
                        <strong className="text-gray-800">Cómo encontrarlo:</strong>
                        <p className="mt-1 text-gray-700">{card.fields.como_encontrarlo}</p>
                      </div>
                    )}
                    
                    {card.fields?.acciones && (
                      <div className="p-3 bg-white rounded border">
                        <strong className="text-gray-800">Acciones:</strong>
                        <p className="mt-1 text-gray-700">{card.fields.acciones}</p>
                      </div>
                    )}
                    
                    {card.fields?.caracteristicas_especiales && (
                      <div className="p-3 bg-white rounded border">
                        <strong className="text-gray-800">Características Especiales:</strong>
                        <p className="mt-1 text-gray-700">{card.fields.caracteristicas_especiales}</p>
                      </div>
                    )}
                    
                    {/* Fallback for other card types that might not have these specific fields */}
                    {(!card.fields?.ubicacion && !card.fields?.acciones && (card.answer || card.back)) && (
                      <div className="p-3 bg-white rounded border">
                        <strong className="text-gray-800">Answer:</strong>
                        <p className="mt-1 text-gray-700">{card.answer || card.back}</p>
                      </div>
                    )}
                    
                    {/* Show failed attempts */}
                    {card.failed_responses && card.failed_responses.length > 0 && (
                      <div className="p-3 bg-red-100 rounded border border-red-200">
                        <strong className="text-red-800">❌ Your Incorrect Answer(s):</strong>
                        {card.failed_responses.map((attempt, idx) => (
                          <div key={idx} className="mt-2 p-2 bg-red-50 rounded border border-red-100">
                            <div className="text-sm text-red-700 mb-1">
                              <strong>Question was about:</strong> {attempt.question_field} → <strong>Expected:</strong> {attempt.answer_field}
                            </div>
                            <div className="text-sm">
                              <strong className="text-red-800">You answered:</strong>
                              <p className="text-red-700 mt-1 italic">"{attempt.user_answer}"</p>
                            </div>
                            <div className="text-sm mt-2">
                              <strong className="text-green-800">Correct answer:</strong>
                              <p className="text-green-700 mt-1">"{attempt.correct_answer}"</p>
                            </div>
                            <div className="text-xs text-gray-500 mt-1">
                              Failed on: {new Date(attempt.attempted_at).toLocaleString()}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
