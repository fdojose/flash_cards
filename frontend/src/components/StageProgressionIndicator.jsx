import { useState, useEffect } from 'react';

const StageProgressionIndicator = ({ 
  confidenceStats, 
  currentStage, 
  totalCardsInSet,
  showCelebrationDemo = false 
}) => {
  const [showDemo, setShowDemo] = useState(false);
  
  if (!confidenceStats?.confidence_breakdown) return null;

  const { strong_count, weak_count, new_count } = confidenceStats.confidence_breakdown;
  const totalCards = strong_count + weak_count + new_count;
  const masteredCards = strong_count;
  const progressPercentage = totalCards > 0 ? (masteredCards / totalCards) * 100 : 0;

  // Estimate if stage progression is likely
  const isNearStageProgression = progressPercentage > 70 && weak_count <= 2 && new_count === 0;
  const isReadyForProgression = masteredCards === totalCards && new_count === 0;

  return (
    <div className="bg-gradient-to-r from-blue-50 to-purple-50 border border-blue-200 rounded-xl p-4 mb-4">
      {/* Current Stage Info */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <span className="text-2xl">📈</span>
          <div>
            <div className="font-semibold text-gray-800">
              Stage {currentStage} Progress
            </div>
            <div className="text-sm text-gray-600">
              {masteredCards} mastered, {weak_count} learning, {new_count} new
            </div>
          </div>
        </div>
        <div className="text-right">
          <div className="text-lg font-bold text-blue-600">
            {Math.round(progressPercentage)}%
          </div>
          <div className="text-xs text-gray-500">
            Stage progress
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-3">
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className={`h-2 rounded-full transition-all duration-1000 ${
              isReadyForProgression 
                ? 'bg-gradient-to-r from-green-400 to-green-500 animate-pulse' 
                : isNearStageProgression 
                ? 'bg-gradient-to-r from-yellow-400 to-orange-500' 
                : 'bg-gradient-to-r from-blue-400 to-blue-500'
            }`}
            style={{ width: `${progressPercentage}%` }}
          />
        </div>
      </div>

      {/* Stage Progression Status */}
      <div className="text-sm">
        {isReadyForProgression ? (
          <div className="flex items-center space-x-2 text-green-700 bg-green-100 px-3 py-2 rounded-lg">
            <span>🎉</span>
            <span className="font-semibold">Ready for stage progression! New cards will be unlocked.</span>
          </div>
        ) : isNearStageProgression ? (
          <div className="flex items-center space-x-2 text-orange-700 bg-orange-100 px-3 py-2 rounded-lg">
            <span>🚀</span>
            <span>Almost ready! Master the remaining {weak_count} cards to advance.</span>
          </div>
        ) : (
          <div className="flex items-center space-x-2 text-blue-700 bg-blue-100 px-3 py-2 rounded-lg">
            <span>📚</span>
            <span>Keep learning! Progress through current stage cards.</span>
          </div>
        )}
      </div>

      {/* Demo Button */}
      {showCelebrationDemo && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <button
            onClick={() => setShowDemo(true)}
            className="text-xs bg-purple-500 text-white px-3 py-1 rounded-full hover:bg-purple-600 transition-colors"
          >
            🎊 Preview Celebration
          </button>
        </div>
      )}
    </div>
  );
};

export default StageProgressionIndicator;
