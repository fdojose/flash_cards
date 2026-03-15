// Custom hooks for API data fetching
// ===================================

import { useState, useEffect, useCallback } from 'react';
import apiService from '../services/api';

// Generic data fetching hook
export const useApi = (endpoint, options = {}) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const { immediate = true, dependencies = [] } = options;

  const execute = useCallback(async (customEndpoint = null) => {
    try {
      setLoading(true);
      setError(null);
      const result = await apiService.get(customEndpoint || endpoint);
      setData(result);
      return result;
    } catch (err) {
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [endpoint]);

  useEffect(() => {
    if (immediate && endpoint) {
      execute();
    }
  }, [execute, immediate, ...dependencies]);

  return { data, loading, error, execute, refetch: execute };
};

// Hook for datasets
export const useDatasets = () => {
  const [datasets, setDatasets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchDatasets = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await apiService.getDatasets();
      setDatasets(result || []);
    } catch (err) {
      setError(err);
      setDatasets([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDatasets();
  }, [fetchDatasets]);

  const createDataset = async (datasetData) => {
    const newDataset = await apiService.createDataset(datasetData);
    setDatasets(prev => [...prev, newDataset]);
    return newDataset;
  };

  const uploadDataset = async (file, metadata) => {
    const newDataset = await apiService.uploadDataset(file, metadata);
    setDatasets(prev => [...prev, newDataset]);
    return newDataset;
  };

  const deleteDataset = async (datasetId) => {
    await apiService.deleteDataset(datasetId);
    setDatasets(prev => prev.filter(d => d.id !== datasetId));
  };

  return {
    datasets,
    loading,
    error,
    refetch: fetchDatasets,
    createDataset,
    uploadDataset,
    deleteDataset,
  };
};

// Hook for user dashboard data
export const useDashboard = () => {
  const [dashboardData, setDashboardData] = useState({
    progress: null,
    stats: null,
    achievements: null,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [progress, stats, achievements] = await Promise.all([
        apiService.getUserProgress(),
        apiService.getUserStats(),
        apiService.getUserAchievements(),
      ]);

      setDashboardData({ progress, stats, achievements });
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  return {
    ...dashboardData,
    loading,
    error,
    refetch: fetchDashboardData,
  };
};

// Hook for learning sessions
export const useSession = () => {
  const [session, setSession] = useState(null);
  const [currentFlashcard, setCurrentFlashcard] = useState(null);
  const [progress, setProgress] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const startSession = async (datasetId, forceReview = false, timerMode = 'disabled', timerDuration = 30) => {
    try {
      setLoading(true);
      setError(null);
      console.log('Starting session for dataset:', datasetId, 'forceReview:', forceReview, 'timerMode:', timerMode, 'timerDuration:', timerDuration);
      const newSession = await apiService.startSession(datasetId, forceReview, timerMode, timerDuration);
      console.log('Session started:', newSession);
      setSession(newSession);
      
      // Fetch initial progress
      try {
        const sessionProgress = await apiService.getSessionProgress(newSession.learning_set_id);
        console.log('Session progress:', sessionProgress);
        // Convert backend progress format to frontend format
        setProgress({
          total_count: sessionProgress.total_questions || sessionProgress.total_items,
          answered_count: sessionProgress.total_questions || (sessionProgress.mastered_count + (sessionProgress.total_items - sessionProgress.new_count - sessionProgress.mastered_count)),
          correct_count: sessionProgress.correct_answers || sessionProgress.mastered_count
        });
      } catch (progressError) {
        console.warn('Could not fetch session progress:', progressError);
      }
      
      // Automatically fetch the first flashcard
      try {
        console.log('Fetching first flashcard...');
        const firstFlashcard = await apiService.getNextFlashcard(newSession.learning_set_id, forceReview);
        console.log('First flashcard received:', firstFlashcard);
        setCurrentFlashcard(firstFlashcard);
      } catch (flashcardError) {
        // If no flashcards available, session is complete
        console.log('Session complete - no flashcards available:', flashcardError);
        setCurrentFlashcard(null);
        // Don't throw the error here - let the component handle completion state
      }
      
      return newSession;
    } catch (err) {
      console.error('Error starting session:', err);
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const getNextFlashcard = async (forceReview = false) => {
    if (!session) return null;

    try {
      setLoading(true);
      const flashcard = await apiService.getNextFlashcard(session.learning_set_id, forceReview);
      setCurrentFlashcard(flashcard);
      return flashcard;
    } catch (err) {
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const submitAnswer = async (answer, isCorrect, timeSpent = null, timerExpired = false) => {
    if (!session || !currentFlashcard) return null;

    const wasTimed = session.timer_enabled;

    try {
      const result = await apiService.submitAnswer(
        currentFlashcard.element_id,
        currentFlashcard.question_field,
        currentFlashcard.answer_field,
        answer,
        currentFlashcard.correct_answer,
        isCorrect,
        timeSpent,
        timerExpired,
        wasTimed
      );
      
      // Update progress after successful answer submission
      try {
        const sessionProgress = await apiService.getSessionProgress(session.learning_set_id);
        setProgress({
          total_count: sessionProgress.total_questions || sessionProgress.total_items,
          answered_count: sessionProgress.total_questions || (sessionProgress.mastered_count + (sessionProgress.total_items - sessionProgress.new_count - sessionProgress.mastered_count)),
          correct_count: sessionProgress.correct_answers || sessionProgress.mastered_count
        });
      } catch (progressError) {
        console.warn('Could not update session progress:', progressError);
      }
      
      return result;
    } catch (err) {
      setError(err);
      throw err;
    }
  };

  const endSession = async () => {
    if (!session) return null;

    // Best-effort analytics call — don't block the user if it fails
    try {
      const cardsReviewed = progress?.answered_count ?? 0;
      const cardsCorrect = progress?.correct_count ?? 0;
      await apiService.endSession(session.id, cardsReviewed, cardsCorrect);
    } catch (_) {
      // Ignore — session tracking is non-critical
    }

    setSession(null);
    setCurrentFlashcard(null);
    setProgress(null);
    return null;
  };

  const resetSession = () => {
    setSession(null);
    setCurrentFlashcard(null);
    setProgress(null);
  };

  return {
    session,
    currentFlashcard,
    progress,
    loading,
    error,
    startSession,
    getNextFlashcard,
    submitAnswer,
    endSession,
    resetSession,
  };
};

// Hook for leaderboard data
export const useLeaderboard = (datasetId = null) => {
  const { data: leaderboard, loading, error, refetch } = useApi(
    `/dashboard/leaderboard${datasetId ? `?dataset_id=${datasetId}` : ''}`,
    { dependencies: [datasetId] }
  );

  return { leaderboard, loading, error, refetch };
};

// Hook for progress history
export const useProgressHistory = (days = 30) => {
  const { data: history, loading, error, refetch } = useApi(
    `/dashboard/progress-history?days=${days}`,
    { dependencies: [days] }
  );

  return { history, loading, error, refetch };
};

// Hook for dataset progress data
export const useDatasetProgress = () => {
  const [datasetProgress, setDatasetProgress] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchDatasetProgress = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await apiService.getDatasetProgress();
      setDatasetProgress(result || []);
    } catch (err) {
      // Don't set error for authentication issues - user might not be logged in
      if (err.status !== 401 && err.status !== 403) {
        setError(err);
      }
      setDatasetProgress([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDatasetProgress();
  }, [fetchDatasetProgress]);

  return {
    datasetProgress,
    loading,
    error,
    refetch: fetchDatasetProgress,
  };
};

// Hook for detailed card statistics
export const useDetailedCardStats = (learningSetId) => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchStats = useCallback(async () => {
    if (!learningSetId) return;
    
    try {
      setLoading(true);
      setError(null);
      const result = await apiService.get(`/sessions/learning-sets/${learningSetId}/detailed-stats`);
      setStats(result);
      return result;
    } catch (err) {
      console.error('Failed to fetch detailed card stats:', err);
      if (err.status !== 401 && err.status !== 403) {
        setError(err);
      }
      setStats(null);
    } finally {
      setLoading(false);
    }
  }, [learningSetId]);

  useEffect(() => {
    if (learningSetId) {
      fetchStats();
    }
  }, [fetchStats, learningSetId]);

  return {
    stats,
    loading,
    error,
    refetch: fetchStats,
  };
};
