import { useState, useEffect } from 'react';

const EnhancedProgressIndicator = ({ 
  current, 
  total, 
  stage, 
  showStageProgression = false,
  onProgressionComplete 
}) => {
  const [isAnimating, setIsAnimating] = useState(false);
  const [previousStage, setPreviousStage] = useState(stage);

  useEffect(() => {
    if (showStageProgression && stage > previousStage) {
      setIsAnimating(true);
      
      // Trigger progression animation
      const timer = setTimeout(() => {
        setIsAnimating(false);
        setPreviousStage(stage);
        if (onProgressionComplete) {
          onProgressionComplete();
        }
      }, 2000);

      return () => clearTimeout(timer);
    }
    setPreviousStage(stage);
  }, [stage, showStageProgression, previousStage, onProgressionComplete]);

  const progressPercentage = total > 0 ? (current / total) * 100 : 0;

  return (
    <div className="relative">
      {/* Stage Badge */}
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-gray-700">
          Learning Progress
        </span>
        <div className={`
          px-3 py-1 rounded-full text-sm font-semibold transition-all duration-1000
          ${isAnimating 
            ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-lg animate-pulse' 
            : 'bg-blue-100 text-blue-800'
          }
        `}>
          Stage {stage}
          {isAnimating && (
            <span className="ml-1 animate-bounce">✨</span>
          )}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="relative">
        <div className={`
          w-full bg-gray-200 rounded-full h-4 overflow-hidden transition-all duration-500
          ${isAnimating ? 'shadow-lg ring-4 ring-purple-200 ring-opacity-50' : ''}
        `}>
          <div
            className={`
              h-full transition-all duration-1000 ease-out relative overflow-hidden
              ${isAnimating 
                ? 'bg-gradient-to-r from-purple-500 via-pink-500 to-purple-500 bg-size-200 animate-gradient-x' 
                : 'bg-gradient-to-r from-blue-500 to-green-500'
              }
            `}
            style={{ width: `${Math.min(100, progressPercentage)}%` }}
          >
            {/* Shimmer effect during animation */}
            {isAnimating && (
              <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-30 animate-shimmer" />
            )}
          </div>
        </div>

        {/* Progress Text */}
        <div className="flex justify-between items-center mt-1 text-xs text-gray-600">
          <span>{current} / {total} cards</span>
          <span className={`
            font-medium transition-colors duration-500
            ${isAnimating ? 'text-purple-600' : 'text-gray-600'}
          `}>
            {Math.round(progressPercentage)}%
          </span>
        </div>
      </div>

      {/* Stage Progression Indicator */}
      {isAnimating && (
        <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 z-10">
          <div className="bg-gradient-to-r from-purple-500 to-pink-500 text-white text-xs px-3 py-1 rounded-full shadow-lg animate-bounce">
            🎉 New Stage Unlocked!
          </div>
        </div>
      )}
    </div>
  );
};

export default EnhancedProgressIndicator;
