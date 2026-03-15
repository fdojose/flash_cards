import React from 'react';
import { useTranslation } from 'react-i18next';
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
  const { t } = useTranslation();

  if (!confidenceStats) {
    return (
      <div className={`confidence-progress loading ${className}`}>
        <div className="confidence-info">
          <span className="confidence-text">{t('confidence.loadingProgress')}</span>
        </div>
      </div>
    );
  }

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

  const strongPercent            = totalCards > 0 ? (strong_count / totalCards) * 100 : 0;
  const integrationReviewPercent = totalCards > 0 ? (integration_review_count / totalCards) * 100 : 0;
  const isolationMasteredPercent = totalCards > 0 ? (isolation_mastered_count / totalCards) * 100 : 0;
  const weakPercent              = totalCards > 0 ? (weak_count / totalCards) * 100 : 0;

  const getPhaseClass = () => {
    switch (learning_phase) {
      case 'learning':  return 'phase-learning';
      case 'building':  return 'phase-building';
      case 'mastering': return 'phase-mastering';
      case 'complete':  return 'phase-complete';
      default:          return 'phase-learning';
    }
  };

  const progressPercentage = totalCards > 0 ? (strong_count / totalCards) * 100 : 0;
  const isNearStageProgression = showStageInfo && progressPercentage > 70 && weak_count <= 2 && new_count === 0 && isolation_mastered_count === 0;
  const isReadyForProgression = showStageInfo && strong_count === totalCards && totalCards > 0;

  const getStageProgressMessage = () => {
    if (!showStageInfo) return null;
    if (isReadyForProgression) {
      return { icon: '🎉', text: t('confidence.stageReady'), style: 'text-green-700 bg-green-100' };
    } else if (isNearStageProgression) {
      return { icon: '🚀', text: t('confidence.stageAlmost', { count: weak_count }), style: 'text-orange-700 bg-orange-100' };
    }
    return null;
  };

  const stageMessage = getStageProgressMessage();

  return (
    <div className={`confidence-progress ${getPhaseClass()} ${showStageInfo ? 'with-stage' : ''} ${className}`}>
      {/* Segmented Progress Bar */}
      <div className="progress-bar-container">
        <div className="progress-bar">
          <div className="progress-segment strong"            style={{ width: `${strongPercent}%` }}            title={`${strong_count} ${t('confidence.mastered')}`}></div>
          <div className="progress-segment integration-review" style={{ width: `${integrationReviewPercent}%` }} title={`${integration_review_count} ${t('confidence.reviewing')}`}></div>
          <div className="progress-segment isolation-mastered" style={{ width: `${isolationMasteredPercent}%` }} title={`${isolation_mastered_count} ${t('confidence.learned')}`}></div>
          <div className="progress-segment weak"              style={{ width: `${weakPercent}%` }}              title={`${weak_count} ${t('confidence.practicing')}`}></div>
        </div>
      </div>

      {/* Confidence Information */}
      <div className="confidence-info">
        {showStageInfo && (
          <div className="stage-info">
            <div className="stage-header">
              <div className="stage-dots">
                {[...Array(strong_count)].map((_, i) => (
                  <span key={`s${i}`} className="stage-dot strong" title={t('confidence.mastered')} />
                ))}
                {[...Array(integration_review_count)].map((_, i) => (
                  <span key={`ir${i}`} className="stage-dot integration-review" title={t('confidence.reviewing')} />
                ))}
                {[...Array(isolation_mastered_count)].map((_, i) => (
                  <span key={`im${i}`} className="stage-dot isolation-mastered" title={t('confidence.learned')} />
                ))}
                {[...Array(weak_count)].map((_, i) => (
                  <span key={`w${i}`} className="stage-dot weak" title={t('confidence.practicing')} />
                ))}
                {[...Array(new_count)].map((_, i) => (
                  <span key={`n${i}`} className="stage-dot unseen" title={t('confidence.new')} />
                ))}
                <span className="stage-lock">{isReadyForProgression ? '🚀' : '🔓'}</span>
              </div>
            </div>
          </div>
        )}

        <div className="confidence-breakdown">
          <div className="confidence-pills">
            {strong_count > 0 && (
              <span className="conf-pill conf-pill-mastered">{strong_count} {t('confidence.mastered')}</span>
            )}
            {integration_review_count > 0 && (
              <span className="conf-pill conf-pill-reviewing">{integration_review_count} {t('confidence.reviewing')}</span>
            )}
            {isolation_mastered_count > 0 && (
              <span className="conf-pill conf-pill-learned">{isolation_mastered_count} {t('confidence.learned')}</span>
            )}
            {weak_count > 0 && (
              <span className="conf-pill conf-pill-practicing">{weak_count} {t('confidence.practicing')}</span>
            )}
            {new_count > 0 && (
              <span className="conf-pill conf-pill-new">{new_count} {t('confidence.new')}</span>
            )}
            {totalCards === 0 && (
              <span className="conf-pill conf-pill-new">{t('confidence.noCards')}</span>
            )}
          </div>
          {showSessionCount && sessionQuestionCount > 0 && (
            <div className="session-pills">
              <span className="conf-pill conf-pill-session">{sessionQuestionCount} {t('confidence.questions')}</span>
              {sessionCorrectCount > 0 && (
                <span className="conf-pill conf-pill-correct">{sessionCorrectCount} {t('confidence.correct')}</span>
              )}
              {sessionIncorrectCount > 0 && (
                <span className="conf-pill conf-pill-incorrect">{sessionIncorrectCount} {t('confidence.incorrect')}</span>
              )}
              <span className="conf-pill conf-pill-accuracy">
                {t('confidence.accuracyPct', { pct: Math.round((sessionCorrectCount / sessionQuestionCount) * 100) })}
              </span>
            </div>
          )}
        </div>
        <div className="phase-message">{phase_message}</div>

        {stageMessage && (
          <div className={`stage-message ${stageMessage.style} px-3 py-2 rounded-lg mt-2 text-sm`}>
            <span className="mr-2">{stageMessage.icon}</span>
            <span>{stageMessage.text}</span>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="confidence-legend">
        <div className="legend-item">
          <div className="legend-color strong"></div>
          <span>{t('confidence.strong')}</span>
        </div>
        <div className="legend-item">
          <div className="legend-color weak"></div>
          <span>{t('confidence.weak')}</span>
        </div>
      </div>
    </div>
  );
};

export default ConfidenceProgress;
