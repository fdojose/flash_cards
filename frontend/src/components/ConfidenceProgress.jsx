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
    isolation_mastered_count = 0,
    integration_review_count = 0,
    weak_count = 0,
    new_count = 0
  } = confidenceBreakdown;

  const {
    phase: learning_phase = 'learning',
    message: phase_message = 'Getting started...'
  } = learningPhase;

  const totalCards = strong_count + isolation_mastered_count + integration_review_count + weak_count + new_count;

  // Calculate percentages for progress bar segments
  const strongPercent            = totalCards > 0 ? (strong_count / totalCards) * 100 : 0;
  const integrationReviewPercent = totalCards > 0 ? (integration_review_count / totalCards) * 100 : 0;
  const isolationMasteredPercent = totalCards > 0 ? (isolation_mastered_count / totalCards) * 100 : 0;
  const weakPercent              = totalCards > 0 ? (weak_count / totalCards) * 100 : 0;

  // Format confidence breakdown text
  const formatConfidenceText = () => {
    const parts = [];
    if (strong_count > 0)            parts.push(`${strong_count} Mastered`);
    if (integration_review_count > 0) parts.push(`${integration_review_count} Reviewing`);
    if (isolation_mastered_count > 0) parts.push(`${isolation_mastered_count} Learned`);
    if (weak_count > 0)              parts.push(`${weak_count} Practicing`);
    if (new_count > 0)               parts.push(`${new_count} New`);
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
  // Use strong / (strong + weak + new) — all from the same response, denominator stays consistent
  const progressPercentage = totalCards > 0 ? (strong_count / totalCards) * 100 : 0;
  const isNearStageProgression = showStageInfo && progressPercentage > 70 && weak_count <= 2 && new_count === 0 && isolation_mastered_count === 0;
  const isReadyForProgression = showStageInfo && strong_count === totalCards && totalCards > 0;

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
            title={`${strong_count} Mastered`}
          ></div>
          <div
            className="progress-segment integration-review"
            style={{ width: `${integrationReviewPercent}%` }}
            title={`${integration_review_count} Reviewing`}
          ></div>
          <div
            className="progress-segment isolation-mastered"
            style={{ width: `${isolationMasteredPercent}%` }}
            title={`${isolation_mastered_count} Learned`}
          ></div>
          <div
            className="progress-segment weak"
            style={{ width: `${weakPercent}%` }}
            title={`${weak_count} Practicing`}
          ></div>
        </div>
      </div>

      {/* Confidence Information */}
      <div className="confidence-info">
        {showStageInfo && (
          <div className="stage-info">
            <div className="stage-header">
              <div className="stage-dots">
                {[...Array(strong_count)].map((_, i) => (
                  <span key={`s${i}`} className="stage-dot strong" title="Mastered" />
                ))}
                {[...Array(integration_review_count)].map((_, i) => (
                  <span key={`ir${i}`} className="stage-dot integration-review" title="Reviewing" />
                ))}
                {[...Array(isolation_mastered_count)].map((_, i) => (
                  <span key={`im${i}`} className="stage-dot isolation-mastered" title="Learned" />
                ))}
                {[...Array(weak_count)].map((_, i) => (
                  <span key={`w${i}`} className="stage-dot weak" title="Practicing" />
                ))}
                {[...Array(new_count)].map((_, i) => (
                  <span key={`n${i}`} className="stage-dot unseen" title="New" />
                ))}
                <span className="stage-lock">{isReadyForProgression ? '🚀' : '🔓'}</span>
              </div>
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
      </div>
    </div>
  );
};

export default ConfidenceProgress;
