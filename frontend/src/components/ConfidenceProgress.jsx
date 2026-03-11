import React from 'react';
import './ConfidenceProgress.css';

const ConfidenceProgress = ({ 
  confidenceStats, 
  sessionQuestionCount, 
  sessionCorrectCount = 0,
  sessionIncorrectCount = 0,
  className = "",
  showSessionCount = true,
  currentStage = null,
  showStageInfo = false
}) => {
  // Fallback for when confidenceStats is not yet loaded
  if (!confidenceStats) {
    return (
      <div className={`confidence-progress loading ${className}`}>
        <div className="confidence-info">
          <span className="confidence-text">Loading progress...</span>
        </div>
      </div>
    );
  }

  // Extract data from the nested API response structure
  const confidenceBreakdown = confidenceStats?.confidence_breakdown || {};
  const learningPhase = confidenceStats?.learning_phase || {};
  
  const { 
    strong_count = 0, 
    weak_count = 0, 
    new_count = 0
  } = confidenceBreakdown;

  const {
    phase: learning_phase = 'learning',
    message: phase_message = 'Getting started...'
  } = learningPhase;

  const totalCards = strong_count + weak_count + new_count;
  
  // Calculate percentages for progress bar segments
  const strongPercent = totalCards > 0 ? (strong_count / totalCards) * 100 : 0;
  const weakPercent = totalCards > 0 ? (weak_count / totalCards) * 100 : 0;
  const newPercent = totalCards > 0 ? (new_count / totalCards) * 100 : 0;

  // Format confidence breakdown text
  const formatConfidenceText = () => {
    const parts = [];
    if (strong_count > 0) {
      // Show "Mastered" when learning phase is complete, "Strong" otherwise
      const label = learning_phase === 'complete' ? 'Mastered' : 'Strong';
      parts.push(`${strong_count} ${label}`);
    }
    if (weak_count > 0) parts.push(`${weak_count} Weak`);
    if (new_count > 0) parts.push(`${new_count} New`);
    
    return parts.length > 0 ? parts.join(', ') : 'No cards available';
  };

  // Get phase-specific styling
  const getPhaseClass = () => {
    switch (learning_phase) {
      case 'learning': return 'phase-learning';
      case 'building': return 'phase-building';
      case 'mastering': return 'phase-mastering';
      case 'complete': return 'phase-complete';
      default: return 'phase-learning';
    }
  };

  // Stage progression logic (if enabled)
  const masteredCards = strong_count;
  const progressPercentage = totalCards > 0 ? (masteredCards / totalCards) * 100 : 0;
  const isNearStageProgression = showStageInfo && progressPercentage > 70 && weak_count <= 2 && new_count === 0;
  const isReadyForProgression = showStageInfo && masteredCards === totalCards && new_count === 0;

  const getStageProgressMessage = () => {
    if (!showStageInfo) return null;
    
    if (isReadyForProgression) {
      return { 
        icon: '🎉', 
        text: 'Ready for stage progression! New cards will be unlocked.',
        style: 'text-green-700 bg-green-100'
      };
    } else if (isNearStageProgression) {
      return { 
        icon: '🚀', 
        text: `Almost ready! Master the remaining ${weak_count} cards to advance.`,
        style: 'text-orange-700 bg-orange-100'
      };
    } else {
      // Only show message when it's actionable - no generic "keep learning" message
      return null;
    }
  };

  const stageMessage = getStageProgressMessage();

  return (
    <div className={`confidence-progress ${getPhaseClass()} ${showStageInfo ? 'with-stage' : ''} ${className}`}>
      {/* Segmented Progress Bar */}
      <div className="progress-bar-container">
        <div className="progress-bar">
          <div 
            className="progress-segment strong" 
            style={{ width: `${strongPercent}%` }}
            title={`${strong_count} Strong cards (${Math.round(strongPercent)}%)`}
          ></div>
          <div 
            className="progress-segment weak" 
            style={{ width: `${weakPercent}%` }}
            title={`${weak_count} Weak cards (${Math.round(weakPercent)}%)`}
          ></div>
          <div 
            className="progress-segment new" 
            style={{ width: `${newPercent}%` }}
            title={`${new_count} New cards (${Math.round(newPercent)}%)`}
          ></div>
        </div>
      </div>

      {/* Confidence Information */}
      <div className="confidence-info">
        {showStageInfo && currentStage && (
          <div className="stage-info">
            <div className="stage-header">
              <span className="stage-title">📈 Stage {currentStage}</span>
              <span className="stage-progress">{Math.round(progressPercentage)}% complete</span>
            </div>
          </div>
        )}
        
        <div className="confidence-breakdown">
          <span className="confidence-text">{formatConfidenceText()}</span>
          {showSessionCount && (
            <span className="session-count">
              • {sessionQuestionCount} questions
              {sessionQuestionCount > 0 && (
                <span className="answer-stats">
                  {sessionCorrectCount > 0 && (
                    <span className="correct-count"> • {sessionCorrectCount} correct</span>
                  )}
                  {sessionIncorrectCount > 0 && (
                    <span className="incorrect-count"> • {sessionIncorrectCount} incorrect</span>
                  )}
                  {sessionQuestionCount > 0 && (
                    <span className="accuracy-rate">
                      {` (${Math.round((sessionCorrectCount / sessionQuestionCount) * 100)}% accuracy)`}
                    </span>
                  )}
                </span>
              )}
            </span>
          )}
        </div>
        <div className="phase-message">{phase_message}</div>
        
        {/* Stage Progression Message */}
        {stageMessage && (
          <div className={`stage-message ${stageMessage.style} px-3 py-2 rounded-lg mt-2 text-sm`}>
            <span className="mr-2">{stageMessage.icon}</span>
            <span>{stageMessage.text}</span>
          </div>
        )}
      </div>

      {/* Legend (optional, can be hidden with CSS) */}
      <div className="confidence-legend">
        <div className="legend-item">
          <div className="legend-color strong"></div>
          <span>Strong</span>
        </div>
        <div className="legend-item">
          <div className="legend-color weak"></div>
          <span>Weak</span>
        </div>
        <div className="legend-item">
          <div className="legend-color new"></div>
          <span>New</span>
        </div>
      </div>
    </div>
  );
};

export default ConfidenceProgress;
