import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useDatasets, useSession, useDatasetProgress } from '../hooks/useApi';
import apiService from '../services/api';
import Timer from '../components/Timer';
import TimerSettings from '../components/TimerSettings';
import PerformanceFeedback from '../components/PerformanceFeedback';
import ConfidenceProgress from '../components/ConfidenceProgress';
import StageProgressionCelebration from '../components/StageProgressionCelebration';
import { useCorrectSound, useWrongSound } from '../hooks/useCorrectSound';

export default function Learn() {
  const { datasetId } = useParams();
  const { isAuthenticated } = useAuth();
  const playCorrectSound = useCorrectSound();
  const playWrongSound = useWrongSound();
  const { datasets, loading: datasetsLoading } = useDatasets();
  const { datasetProgress, refetch: refetchProgress } = useDatasetProgress();
  const {
    session,
    currentFlashcard,
    progress,
    loading: sessionLoading,
    startSession,
    getNextFlashcard,
    submitAnswer,
    endSession,
    resetSession,
  } = useSession();

  // Helper function to get progress for a specific dataset
  const getDatasetProgress = (datasetId) => {
    if (!isAuthenticated || !datasetProgress) return null;
    return datasetProgress.find(progress => progress.dataset_id === datasetId);
  };

  const [selectedAnswer, setSelectedAnswer] = useState(null);
  const [showResult, setShowResult] = useState(false);
  const [correctAnimKey, setCorrectAnimKey] = useState(null); // option string that was correct
  const [wrongAnimKey, setWrongAnimKey] = useState(null);   // option string that was wrong
  const correctButtonRef = useRef(null);
  const [sessionComplete, setSessionComplete] = useState(false);
  const [isForceReviewMode, setIsForceReviewMode] = useState(false);
  const [showTimerSettings, setShowTimerSettings] = useState(false);
  const [timerSettingsShown, setTimerSettingsShown] = useState(false);
  const [timerSettings, setTimerSettings] = useState({ timerMode: 'disabled', timerDuration: 30 });
  const [timerActive, setTimerActive] = useState(false);
  const [timeSpent, setTimeSpent] = useState(0);
  const [resettingDataset, setResettingDataset] = useState(null);
  const [performanceFeedback, setPerformanceFeedback] = useState(null);
  const [showPerformance, setShowPerformance] = useState(false);
  
  // Session-scoped progress counter state variables
  const [sessionAnsweredCount, setSessionAnsweredCount] = useState(0);
  const [sessionTotalCount, setSessionTotalCount] = useState(0);
  const [sessionAnsweredCards, setSessionAnsweredCards] = useState(() => new Set()); // Use function to prevent recreation
  const [sessionStartTime, setSessionStartTime] = useState(null);
  
  // Stage progression celebration state variables
  const [showStageCelebration, setShowStageCelebration] = useState(false);
  const [stageProgressionInfo, setStageProgressionInfo] = useState({});
  const [currentStage, setCurrentStage] = useState(1);
  const [previousCardsCount, setPreviousCardsCount] = useState(0);
  
  // Confidence-based progress state variables
  const [sessionQuestionCount, setSessionQuestionCount] = useState(0);
  const [sessionCorrectCount, setSessionCorrectCount] = useState(0);
  const [sessionIncorrectCount, setSessionIncorrectCount] = useState(0);
  const [confidenceStats, setConfidenceStats] = useState({
    confidence_breakdown: {
      strong_count: 0,
      weak_count: 0,
      new_count: 0
    },
    learning_phase: {
      phase: "learning",
      message: "Getting started..."
    }
  });

  // Reset all session state when navigating to a different dataset
  useEffect(() => {
    resetSession();
    setSessionComplete(false);
    setTimerSettingsShown(false);
  }, [datasetId]); // eslint-disable-line react-hooks/exhaustive-deps

  // Start session when dataset is selected
  useEffect(() => {
    console.log('Learn component mounted:', { datasetId, isAuthenticated });
    // Only show timer settings once when dataset is first selected
    if (datasetId && isAuthenticated && !session && !timerSettingsShown) {
      console.log('Showing timer settings for dataset:', datasetId);
      setShowTimerSettings(true);
      setTimerSettingsShown(true);
    }
  }, [datasetId, isAuthenticated, session, timerSettingsShown]);

  // Refresh dataset progress when session completes so the card list shows current mastery counts
  useEffect(() => {
    if (sessionComplete) {
      refetchProgress();
    }
  }, [sessionComplete]); // eslint-disable-line react-hooks/exhaustive-deps

  // Debug logging for each card load
  useEffect(() => {
    if (currentFlashcard) {
      const stats = currentFlashcard.fsrs_stats || {};
      console.debug('[Card Debug]', {
        element_id: currentFlashcard.element_id,
        question_field: currentFlashcard.question_field,
        answer_field: currentFlashcard.answer_field,
        status: stats.status,
        review_count: stats.review_count,
        success_streak: stats.success_streak,
        accuracy_percentage: stats.accuracy_percentage,
        integration_attempts: stats.integration_attempts,
        ease_factor: stats.ease_factor,
        interval_days: stats.interval_days,
        stability_score: stats.stability_score,
        is_difficult: stats.is_difficult,
        full_card: currentFlashcard,
      });
      if (!currentFlashcard.question_value || currentFlashcard.question_value.trim() === '') {
        console.warn('[Card Debug] Missing question value:', {
          element_id: currentFlashcard.element_id,
          question_field: currentFlashcard.question_field,
          question_value: currentFlashcard.question_value,
          choices: currentFlashcard.choices,
        });
      }
    }
  }, [currentFlashcard]);

  // Reset timer when new flashcard is loaded
  useEffect(() => {
    if (currentFlashcard && session?.timer_enabled) {
      setTimerActive(true);
      setTimeSpent(0);
    } else {
      setTimerActive(false);
    }
  }, [currentFlashcard, session?.timer_enabled]);

  const handleTimerSettingsStart = async (settings) => {
    setTimerSettings(settings);
    setShowTimerSettings(false);
    
    // Start with regular session first
    await handleStartSession(datasetId, false, settings.timerMode, settings.timerDuration);
  };

  const handleTimerSettingsCancel = () => {
    setShowTimerSettings(false);
    setTimerSettingsShown(false); // Reset so timer settings can be shown again if user returns
    // Go back to dataset selection
    window.history.back();
  };

    const handleStartSession = async (datasetId, forceReview = false, timerMode = 'disabled', timerDuration = 30) => {
    try {
      console.log('handleStartSession called with:', datasetId, 'forceReview:', forceReview, 'timerMode:', timerMode, 'timerDuration:', timerDuration);
      // Reset completion state when starting a new session
      setSessionComplete(false);
      setIsForceReviewMode(forceReview);
      setTimerActive(false);
      setTimeSpent(0);
      
      // Initialize session counters (Step 2)
      console.log('Resetting session counters');
      setSessionAnsweredCount(0);
      setSessionQuestionCount(0); // Reset confidence-based session counter
      setSessionCorrectCount(0); // Reset correct answer counter
      setSessionIncorrectCount(0); // Reset incorrect answer counter
      setSessionAnsweredCards(new Set()); // Reset unique cards set
      setSessionStartTime(new Date());
      
      const newSession = await startSession(datasetId, forceReview, timerMode, timerDuration);
      console.log('handleStartSession result:', newSession);
      
      // Set session total count from session data (Step 2)
      if (newSession && newSession.total_items) {
        setSessionTotalCount(newSession.total_items);
        console.log('Session total count set to:', newSession.total_items);
      }
      
      // Fetch initial confidence stats (Step 2.2) - Use learning_set_id from session
      if (newSession && newSession.learning_set_id) {
        try {
          const confidenceData = await apiService.getConfidenceStats(newSession.learning_set_id);
          
          // Initialize stage progression tracking
          const initialCardsCount = confidenceData.confidence_breakdown.strong_count +
                                  (confidenceData.confidence_breakdown.isolation_mastered_count || 0) +
                                  (confidenceData.confidence_breakdown.integration_review_count || 0) +
                                  confidenceData.confidence_breakdown.weak_count +
                                  confidenceData.confidence_breakdown.new_count;
          setPreviousCardsCount(initialCardsCount);
          
          // Get current stage from dataset progress
          const progressInfo = getDatasetProgress(datasetId);
          if (progressInfo?.current_stage) {
            setCurrentStage(progressInfo.current_stage);
          }
          
          setConfidenceStats(confidenceData);
          console.log('Initial confidence stats loaded:', confidenceData);
          console.log('Stage progression tracking initialized:', {
            initialCardsCount,
            currentStage: progressInfo?.current_stage || 1
          });
        } catch (error) {
          console.error('Error fetching confidence stats:', error);
          // Set default confidence stats on error
          setConfidenceStats({
            confidence_breakdown: {
              strong_count: 0,
              weak_count: 0,
              new_count: 0
            },
            learning_phase: {
              phase: 'learning',
              message: 'Getting started...'
            }
          });
        }
      }
      
      // If startSession returns null, it means all cards are mastered (204 response)
      if (!newSession) {
        console.log('No session returned - all cards mastered, setting complete');
        setSessionComplete(true);
      }
    } catch (error) {
      // 204 means the dataset is fully completed — not a real error
      if (error.status === 204 || error.data?.batchComplete) {
        console.log('Dataset already completed (204) - showing completion screen');
        setSessionComplete(true);
      } else {
        console.error('Error starting session:', error);
        console.error('Error details:', {
          message: error.message,
          status: error.status,
          data: error.data,
          stack: error.stack
        });
      }
    }
  };

  // Unified function to track unique cards (Step 3 - Consolidated)
  const trackUniqueCard = useCallback((elementId) => {
    if (!elementId) {
      console.log('Skipping trackUniqueCard - no elementId');
      return;
    }
    
    setSessionAnsweredCards(prev => {
      const newSet = new Set(prev);
      const wasNewCard = !newSet.has(elementId);
      
      console.log('Processing answer for element:', elementId);
      console.log('Was new card:', wasNewCard);
      console.log('Set size before:', prev.size);
      
      if (wasNewCard) {
        newSet.add(elementId);
        console.log('Added new card to set. Set size after:', newSet.size);
        
        // Update the counter to match the Set size
        setSessionAnsweredCount(newSet.size);
        console.log('Session answered count set to:', newSet.size, 'for element:', elementId);
      } else {
        console.log('Card already answered in this session, not changing counter:', elementId);
      }
      
      return newSet;
    });
  }, []);

  const handleAnswerSelect = (answer) => {
    if (showResult) return;
    setSelectedAnswer(answer);
  };

  const handleSubmitAnswer = async () => {
    if (!selectedAnswer || !currentFlashcard || showResult) return;

    const isCorrect = selectedAnswer === currentFlashcard.correct_answer;
    
    // Stop timer and get time spent
    setTimerActive(false);
    
    try {
      // Track unique cards answered BEFORE submitting to prevent race condition
      trackUniqueCard(currentFlashcard?.element_id);
      
      // Increment confidence-based session question count and correct/incorrect tracking
      setSessionQuestionCount(prev => prev + 1);
      if (isCorrect) {
        setSessionCorrectCount(prev => prev + 1);
      } else {
        setSessionIncorrectCount(prev => prev + 1);
      }

      // Play sound immediately — must be inside the synchronous user-gesture context
      // before any await, otherwise the browser blocks AudioContext creation
      if (isCorrect) {
        playCorrectSound();
        setCorrectAnimKey(currentFlashcard.correct_answer);
      } else {
        playWrongSound();
        setWrongAnimKey(selectedAnswer);
      }

      const result = await submitAnswer(selectedAnswer, isCorrect, timeSpent, false); // Pass false for timerExpired
      setShowResult(true);
      
      // Update confidence stats after submission
      let newCardsUnlocked = false;
      if (result && session?.learning_set_id) {
        try {
          const confidenceData = await apiService.getConfidenceStats(session.learning_set_id);

          const newTotalCards = confidenceData.confidence_breakdown.strong_count +
                               (confidenceData.confidence_breakdown.isolation_mastered_count || 0) +
                                  (confidenceData.confidence_breakdown.integration_review_count || 0) +
                               confidenceData.confidence_breakdown.weak_count +
                               confidenceData.confidence_breakdown.new_count;

          // Detect batch/stage progression: more cards in the set than before
          if (previousCardsCount > 0 && newTotalCards > previousCardsCount) {
            newCardsUnlocked = true;
            const newCardsAdded = newTotalCards - previousCardsCount;

            // Refetch progress so the stage number is current, not stale
            await refetchProgress();
            const freshProgress = getDatasetProgress(datasetId);
            const newStage = freshProgress?.current_stage ?? currentStage;

            setStageProgressionInfo({
              newCardsCount: newCardsAdded,
              newStage,
              masteredCards: confidenceData.confidence_breakdown.strong_count,
              totalCards: newTotalCards,
              previousStage: currentStage
            });
            setCurrentStage(newStage);
            setShowStageCelebration(true);

            console.log('🎉 Batch/stage progression detected!', {
              previousCards: previousCardsCount,
              newCards: newTotalCards,
              cardsAdded: newCardsAdded,
              newStage,
            });
          }

          setPreviousCardsCount(newTotalCards);
          setConfidenceStats(confidenceData);
        } catch (error) {
          console.error('Error updating confidence stats:', error);
        }
      }

      // Show performance feedback if timer was used
      if (session?.timer_enabled && result?.timer_performance) {
        setPerformanceFeedback({
          performance: result.timer_performance.level,
          bonusPoints: result.timer_performance.bonus_points,
          timeSpent: timeSpent,
          timerDuration: session.timer_seconds
        });
        setShowPerformance(true);
      }

      // Auto-advance after 2 seconds — but ONLY if no new cards were unlocked.
      // When new cards are unlocked the celebration modal is the gate; its
      // "Continue Learning" button calls handleNextCard when the user is ready.
      // Setting the timer here would race the celebration and skip a card.
      if (!newCardsUnlocked) {
        setTimeout(() => {
          handleNextCard();
        }, 2000);
      }
    } catch (error) {
      console.error('Failed to submit answer:', error);
    }
  };

  const handleNextCard = async () => {
    setSelectedAnswer(null);
    setShowResult(false);
    setShowPerformance(false);
    setPerformanceFeedback(null);
    setCorrectAnimKey(null);
    setWrongAnimKey(null);
    
    try {
      await getNextFlashcard(isForceReviewMode);
    } catch (error) {
      // Check if this is a batch completion (204 status) - this is expected behavior
      if (error.status === 204 || error.data?.batchComplete) {
        console.log('Batch completed successfully - transitioning to completion screen');
        setSessionComplete(true);
        setTimerActive(false);
      } else {
        // Log unexpected errors
        console.log('Error getting next flashcard:', error);
        // Other errors also end the session
        setSessionComplete(true);
        setTimerActive(false);
      }
    }
  };

  const handleTimeUp = () => {
    console.log('handleTimeUp called - timer_enabled:', session?.timer_enabled, 'showResult:', showResult, 'selectedAnswer:', selectedAnswer);
    // Only trigger timer expiration if no manual answer has been submitted
    if (session?.timer_enabled && !showResult && !selectedAnswer) {
      console.log('Timer expired! Auto-submitting as incorrect');
      // Auto-submit as incorrect when time expires (regardless of timer mode)
      const answer = ""; // Use empty string instead of null for expired answers
      const isCorrect = false; // Always mark as incorrect when time expires
      
      setTimerActive(false);
      console.log('Submitting expired answer:', { answer, isCorrect, timeSpent });
      
      // Track unique cards answered BEFORE submitting for timer expiration to prevent race condition
      trackUniqueCard(currentFlashcard?.element_id);
      
      // Increment confidence-based session question count and track as incorrect (timer expired)
      setSessionQuestionCount(prev => prev + 1);
      setSessionIncorrectCount(prev => prev + 1); // Timer expiry is always incorrect
      
      submitAnswer(answer, isCorrect, timeSpent, true).then(async (result) => { // Pass true for timerExpired
        console.log('Expired answer submitted successfully:', result);
        setShowResult(true);
        
        // Update confidence stats after timer expiry submission
        let timerNewCardsUnlocked = false;
        if (result && session?.learning_set_id) {
          try {
            const confidenceData = await apiService.getConfidenceStats(session.learning_set_id);
            const newTotalCards = confidenceData.confidence_breakdown.strong_count +
                                 (confidenceData.confidence_breakdown.isolation_mastered_count || 0) +
                                  (confidenceData.confidence_breakdown.integration_review_count || 0) +
                                 confidenceData.confidence_breakdown.weak_count +
                                 confidenceData.confidence_breakdown.new_count;

            if (previousCardsCount > 0 && newTotalCards > previousCardsCount) {
              timerNewCardsUnlocked = true;
              const newCardsAdded = newTotalCards - previousCardsCount;
              await refetchProgress();
              const freshProgress = getDatasetProgress(datasetId);
              const newStage = freshProgress?.current_stage ?? currentStage;

              setStageProgressionInfo({
                newCardsCount: newCardsAdded,
                newStage,
                masteredCards: confidenceData.confidence_breakdown.strong_count,
                totalCards: newTotalCards,
                previousStage: currentStage
              });
              setCurrentStage(newStage);
              setShowStageCelebration(true);
            }

            setPreviousCardsCount(newTotalCards);
            setConfidenceStats(confidenceData);
          } catch (error) {
            console.error('Error updating confidence stats:', error);
          }
        }

        // Show performance feedback for expired time
        if (result?.timer_performance) {
          setPerformanceFeedback({
            performance: result.timer_performance.level,
            bonusPoints: result.timer_performance.bonus_points,
            timeSpent: timeSpent,
            timerDuration: session.timer_seconds
          });
          setShowPerformance(true);
        }

        // Same rule: don't auto-advance if celebration is about to show
        if (!timerNewCardsUnlocked) {
          setTimeout(() => {
            handleNextCard();
          }, 3000);
        }
      }).catch(error => {
        console.error('Failed to submit expired answer:', error);
        // Even if submission fails, still advance to next question
        setTimeout(() => {
          console.log('Advancing to next question despite submission error');
          handleNextCard();
        }, 3000);
      });
    } else {
      console.log('Timer expiration blocked - manual answer already submitted or timer disabled');
    }
  };

  const handleTimeSpent = (seconds) => {
    setTimeSpent(seconds);
  };

  const handleEndSession = async () => {
    setTimerActive(false);
    await endSession();
    setSessionComplete(false);
    setIsForceReviewMode(false);
  };

  // Stage progression celebration handlers
  const handleStageCelebrationClose = () => {
    setShowStageCelebration(false);
    setStageProgressionInfo({});
  };

  const handleStageCelebrationContinue = () => {
    setShowStageCelebration(false);
    setStageProgressionInfo({});
    // Continue with the next card immediately
    handleNextCard();
  };

  const handleResetDataset = async (datasetId) => {
    try {
      setResettingDataset(datasetId);
      await apiService.resetDatasetProgress(datasetId);
      
      // Refresh the progress data to reflect the reset
      await refetchProgress();
      
      // Show success message (optional - you can remove this if not needed)
      console.log(`Successfully reset progress for dataset ${datasetId}`);
      
    } catch (error) {
      console.error('Failed to reset dataset progress:', error);
      // You might want to show an error message to the user here
      alert('Failed to reset dataset progress. Please try again.');
    } finally {
      setResettingDataset(null);
    }
  };

  // Debug what the component sees at render time
  console.log('Learn component render state:', {
    datasetId,
    isAuthenticated,
    session: !!session,
    currentFlashcard: !!currentFlashcard,
    sessionComplete,
    sessionLoading,
    showTimerSettings,
    isForceReviewMode,
    conditionMet_sessionAndFlashcard: !!(session && currentFlashcard)
  });

  // Show timer settings when dataset is selected
  if (showTimerSettings) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold mb-4 text-gray-900">Learning Setup</h1>
          <p className="text-lg text-gray-600">
            Configure your learning session preferences
          </p>
        </div>
        
        <TimerSettings
          onStart={handleTimerSettingsStart}
          onCancel={handleTimerSettingsCancel}
          defaultSettings={timerSettings}
        />
      </div>
    );
  }

  // Show dataset selection if no dataset is selected
  if (!datasetId) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold mb-4 text-gray-900">Learning Center</h1>
          <p className="text-lg text-gray-600">
            Choose a dataset and start your learning journey
          </p>
        </div>

        {!isAuthenticated && (
          <div className="card-flashcard p-6 mb-8 bg-yellow-50 border-yellow-200">
            <div className="text-center">
              <div className="text-4xl mb-4">⚠️</div>
              <h3 className="text-lg font-semibold mb-2">Login Required</h3>
              <p className="text-gray-600 mb-4">
                Please log in to start learning sessions and track your progress.
              </p>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {datasetsLoading ? (
            Array.from({ length: 6 }).map((_, index) => (
              <div key={index} className="card-flashcard p-7 animate-pulse">
                <div className="h-4 bg-gray-200 rounded mb-4"></div>
                <div className="h-3 bg-gray-200 rounded mb-2"></div>
                <div className="h-3 bg-gray-200 rounded mb-4"></div>
                <div className="h-8 bg-gray-200 rounded"></div>
              </div>
            ))
          ) : datasets?.length > 0 ? (
            datasets.map((dataset) => {
              const progress = getDatasetProgress(dataset.id);
              return (
                <div key={dataset.id} className="card-flashcard p-7 hover:shadow-lg transition-shadow">
                  <h3 className="text-lg font-semibold mb-2">{dataset.name}</h3>
                  <p className="text-gray-600 text-sm mb-4">{dataset.description}</p>
                  <div className="flex justify-between items-center mb-4 text-sm text-gray-500">
                    <span>{dataset.metadata?.element_count || 0} cards</span>
                    <span className="px-2 py-1 bg-gray-100 rounded">
                      {dataset.difficulty || 'Mixed'}
                    </span>
                  </div>
                  
                  {/* Progress Indicator */}
                  {isAuthenticated && (
                    <div className="mb-4">
                      {progress ? (
                        <>
                          <div className="flex justify-between items-center mb-2">
                            <span className="text-xs text-gray-600">Progress</span>
                            <span className="text-xs text-gray-600">
                              {progress.elements_mastered} / {progress.elements_in_dataset} mastered
                            </span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div 
                              className="bg-green-500 h-2 rounded-full transition-all duration-300"
                              style={{ 
                                width: `${progress.completion_percentage * 100}%` 
                              }}
                            ></div>
                          </div>
                          <div className="flex justify-end items-center mt-1">
                            <span className="text-xs text-gray-500">
                              {Math.round(progress.completion_percentage * 100)}% complete
                            </span>
                          </div>
                          
                          {/* Cards Reviewed & Reset Status */}
                          <div className="flex justify-between items-center mt-3 pt-2 border-t border-gray-100">
                            <div className="flex items-center text-xs text-gray-600">
                              <span className="text-blue-500 mr-1">📊</span>
                              <span className="font-medium">Cards reviewed:</span>
                              <span className="ml-1 text-gray-800">{progress.elements_seen || 0}</span>
                            </div>
                            <button 
                              className="text-xs text-red-500 hover:text-red-700 hover:bg-red-50 px-2 py-1 rounded transition-colors"
                              onClick={(e) => {
                                e.preventDefault();
                                if (window.confirm('Reset learning progress for this dataset? This action cannot be undone.')) {
                                  handleResetDataset(dataset.id);
                                }
                              }}
                              disabled={resettingDataset === dataset.id}
                              title="Reset learning progress"
                            >
                              {resettingDataset === dataset.id ? (
                                <>🔄 Resetting...</>
                              ) : (
                                <>🔄 Reset status</>
                              )}
                            </button>
                          </div>
                        </>
                      ) : (
                        <div className="flex items-center justify-center py-2 bg-blue-50 rounded border border-blue-200">
                          <span className="text-xs text-blue-600 font-medium">Ready to start learning!</span>
                        </div>
                      )}
                    </div>
                  )}
                  
                  <Link
                    to={`/learn/${dataset.id}`}
                    className={`btn w-full ${
                      isAuthenticated 
                        ? 'btn-primary' 
                        : 'btn-disabled cursor-not-allowed'
                    }`}
                    onClick={!isAuthenticated ? (e) => e.preventDefault() : undefined}
                  >
                    {isAuthenticated 
                      ? (progress ? 'Continue Learning' : 'Start Learning') 
                      : 'Login Required'}
                  </Link>
                </div>
              );
            })
          ) : (
            <div className="col-span-full text-center py-12">
              <div className="text-6xl mb-4">📚</div>
              <h3 className="text-xl font-semibold mb-2">No Datasets Available</h3>
              <p className="text-gray-600">
                No learning datasets have been uploaded yet. Check back later!
              </p>
            </div>
          )}
        </div>
      </div>
    );
  }

  // Show session completion
  if (sessionComplete) {
    return (
      <div className="max-w-2xl mx-auto text-center">
        <div className="card-flashcard p-8">
          <div className="text-6xl mb-6">🎉</div>
          <h2 className="text-3xl font-bold mb-4">Session Complete!</h2>
          <p className="text-lg text-gray-600 mb-6">
            Great job! You've completed this learning session.
          </p>
          {progress && (
            <div className="bg-gray-50 rounded-lg p-4 mb-6">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <div className="font-semibold">Correct Answers</div>
                  <div className="text-2xl text-green-600">{progress.correct_count}</div>
                </div>
                <div>
                  <div className="font-semibold">Total Questions</div>
                  <div className="text-2xl text-gray-600">{progress.total_count}</div>
                </div>
              </div>
              <div className="mt-4">
                <div className="font-semibold text-sm mb-1">Accuracy</div>
                <div className="text-2xl text-blue-600">
                  {progress.total_count > 0 
                    ? Math.round((progress.correct_count / progress.total_count) * 100) 
                    : 0}%
                </div>
              </div>
            </div>
          )}
          <div className="flex gap-4 justify-center">
            <button 
              onClick={() => setShowTimerSettings(true)}
              className="btn btn-primary"
            >
              Study Again
            </button>
            <Link to="/learn" className="btn btn-outline">
              Choose Different Dataset
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // Show flashcard interface
  if (session && currentFlashcard) {
    return (
      <>
        <div className="max-w-2xl mx-auto">
          {/* Timer Display */}
          {session?.timer_enabled && (
            <Timer
              duration={session.timer_seconds}
              isActive={timerActive}
              onTimeUp={handleTimeUp}
              onTimeSpent={handleTimeSpent}
              showWarning={session.timer_mode === 'strict'}
            />
          )}

          <div className={`card-flashcard p-8 transition-colors duration-300 ${
            showResult ? (
              currentFlashcard.fsrs_stats?.status === 'new'                  ? 'bg-gray-50' :
              currentFlashcard.fsrs_stats?.status === 'learning'             ? 'bg-yellow-50' :
              currentFlashcard.fsrs_stats?.status === 'isolation_mastered'   ? 'bg-blue-50' :
              currentFlashcard.fsrs_stats?.status === 'integration_review'   ? 'bg-purple-50' :
              currentFlashcard.fsrs_stats?.status === 'integration_confirmed'? 'bg-green-50' :
              ''
            ) : ''
          }`}>
            
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold mb-4">
                {currentFlashcard.question_value && currentFlashcard.question_value.trim() !== '' 
                  ? currentFlashcard.question_value 
                  : `[Missing question for ${currentFlashcard.question_field}]`}
              </h2>
              {currentFlashcard.question_media_url && (
                <img 
                  src={currentFlashcard.question_media_url} 
                  alt="Question"
                  className="max-w-full h-48 object-contain mx-auto mb-4"
                />
              )}
            </div>

          <div className="grid grid-cols-1 gap-3">
            {currentFlashcard.choices?.filter(choice => {
              // Filter out generic "Option X" entries
              return !choice.startsWith('Option ') || !/^Option \d+$/.test(choice);
            }).map((option, index) => {
              const isCorrectOption = option === currentFlashcard.correct_answer;
              const isCorrectAnim = correctAnimKey && isCorrectOption;
              const isWrongAnim = wrongAnimKey === option;
              return (
                <div key={index} className="relative">
                  <button
                    ref={isCorrectOption ? correctButtonRef : null}
                    onClick={() => handleAnswerSelect(option)}
                    disabled={showResult}
                    className={`w-full p-4 rounded-lg border-2 transition-colors text-left ${
                      isCorrectAnim ? 'answer-correct-pop' : ''
                    } ${
                      isWrongAnim ? 'answer-wrong-wobble' : ''
                    } ${
                      showResult
                        ? isCorrectOption
                          ? 'border-green-500 bg-green-50 text-green-800'
                          : option === selectedAnswer
                          ? 'border-red-500 bg-red-50 text-red-800'
                          : 'border-gray-200 bg-gray-50'
                        : option === selectedAnswer
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <span className="font-medium mr-3">
                      {String.fromCharCode(65 + index)}.
                    </span>
                    {option}
                  </button>
                  {isCorrectAnim && (
                    <span className="correct-float" style={{ left: '50%', top: '0' }}>✓</span>
                  )}
                </div>
              );
            })}
          </div>

          {showResult && (
            <div className="mt-6 text-center">
              <span className="text-sm text-gray-500 mr-2">Level:</span>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                currentFlashcard.fsrs_stats?.status === 'new'                  ? 'bg-gray-100 text-gray-800' :
                currentFlashcard.fsrs_stats?.status === 'learning'             ? 'bg-yellow-100 text-yellow-800' :
                currentFlashcard.fsrs_stats?.status === 'isolation_mastered'   ? 'bg-blue-100 text-blue-800' :
                currentFlashcard.fsrs_stats?.status === 'integration_review'   ? 'bg-purple-100 text-purple-800' :
                currentFlashcard.fsrs_stats?.status === 'integration_confirmed'? 'bg-green-100 text-green-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {{
                  'new': 'New',
                  'learning': 'Practicing',
                  'isolation_mastered': 'Learned',
                  'integration_review': 'Reviewing',
                  'integration_confirmed': 'Mastered',
                }[currentFlashcard.fsrs_stats?.status] || 'Unknown'}
              </span>
            </div>
          )}

          <div className="mt-6 flex justify-between">
            <button
              onClick={handleEndSession}
              className="btn btn-outline btn-error"
            >
              End Session
            </button>

            {!showResult ? (
              <button
                onClick={handleSubmitAnswer}
                disabled={!selectedAnswer || sessionLoading}
                className={`btn btn-primary ${sessionLoading ? 'loading' : ''}`}
              >
                Submit Answer
              </button>
            ) : (
              <button
                onClick={handleNextCard}
                className="btn btn-primary"
              >
                Next Question
              </button>
            )}
          </div>

          {/* Progress Indicator - Unified Confidence-based Progress */}
          {progress && (
            <div className="mt-8 pt-6 border-t border-gray-200">
              <ConfidenceProgress
                confidenceStats={confidenceStats}
                sessionQuestionCount={sessionQuestionCount}
                sessionCorrectCount={sessionCorrectCount}
                sessionIncorrectCount={sessionIncorrectCount}
                showSessionCount={true}
                currentStage={currentStage}
                showStageInfo={!isForceReviewMode}
              />
              
              {isForceReviewMode && (
                <div className="mt-4 text-xs text-gray-500 text-center bg-blue-50 p-3 rounded-lg">
                  💡 In force review mode, you can review all cards regardless of mastery status
                </div>
              )}
              {!isForceReviewMode && progress && (
                <div className="mt-4 text-xs text-gray-500 text-center">
                  Overall lifetime progress: {progress.answered_count} / {progress.total_count} cards
                </div>
              )}
            </div>
          )}
        </div>
      </div>
      
      {/* Performance Feedback */}
      <PerformanceFeedback
        performance={performanceFeedback?.performance}
        bonusPoints={performanceFeedback?.bonusPoints}
        timeSpent={performanceFeedback?.timeSpent}
        timerDuration={performanceFeedback?.timerDuration}
        show={showPerformance}
        onClose={() => setShowPerformance(false)}
      />

      {/* Stage Progression Celebration */}
      <StageProgressionCelebration
        show={showStageCelebration}
        onClose={handleStageCelebrationClose}
        onContinue={handleStageCelebrationContinue}
        stageInfo={stageProgressionInfo}
      />
    </>
    );
  }

  // Loading state
  return (
    <div className="max-w-2xl mx-auto">
      <div className="text-center">
        <div className="loading-spinner mb-4"></div>
        <h2 className="text-xl font-semibold mb-2">Loading...</h2>
        <p className="text-gray-600">Preparing your learning session</p>
        <div style={{marginTop: '20px', fontSize: '12px', color: '#666'}}>
          Debug: datasetId={datasetId}, isAuthenticated={isAuthenticated ? 'true' : 'false'}, session={session ? 'exists' : 'null'}
        </div>
      </div>
    </div>
  );
}
