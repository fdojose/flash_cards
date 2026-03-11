import { useState, useEffect, useCallback } from 'react';

const Timer = ({ 
  duration, 
  isActive, 
  onTimeUp, 
  onTimeSpent,
  showWarning = true 
}) => {
  const [timeLeft, setTimeLeft] = useState(duration);
  const [startTime, setStartTime] = useState(null);

  useEffect(() => {
    setTimeLeft(duration);
    if (isActive) {
      setStartTime(Date.now());
    } else {
      setStartTime(null);
    }
  }, [duration, isActive]);

  const calculateTimeSpent = useCallback(() => {
    if (startTime) {
      return Math.round((Date.now() - startTime) / 1000);
    }
    return 0;
  }, [startTime]);

  useEffect(() => {
    if (!isActive) return;

    const interval = setInterval(() => {
      setTimeLeft(prev => {
        if (prev <= 1) {
          const timeSpent = calculateTimeSpent();
          onTimeSpent?.(timeSpent);
          onTimeUp?.();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [isActive, onTimeUp, onTimeSpent, calculateTimeSpent]);

  const handleStop = () => {
    const timeSpent = calculateTimeSpent();
    onTimeSpent?.(timeSpent);
  };

  // Auto-report time spent when component unmounts or timer stops
  useEffect(() => {
    return () => {
      if (startTime) {
        const timeSpent = calculateTimeSpent();
        onTimeSpent?.(timeSpent);
      }
    };
  }, [startTime, calculateTimeSpent, onTimeSpent]);

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getTimerColor = () => {
    const percentage = (timeLeft / duration) * 100;
    if (percentage <= 20) return 'text-red-600';
    if (percentage <= 50) return 'text-yellow-600';
    return 'text-green-600';
  };

  const getProgressColor = () => {
    const percentage = (timeLeft / duration) * 100;
    if (percentage <= 20) return 'bg-red-500';
    if (percentage <= 50) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  const shouldShowWarning = showWarning && timeLeft <= duration * 0.2 && timeLeft > 0;

  if (!isActive && timeLeft === duration) {
    return null; // Don't show timer if not active and at full duration
  }

  return (
    <div className="timer-container mb-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-gray-600">Time Remaining</span>
        <span className={`text-lg font-bold ${getTimerColor()}`}>
          {formatTime(timeLeft)}
        </span>
      </div>
      
      <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
        <div 
          className={`h-2 rounded-full transition-all duration-1000 ${getProgressColor()}`}
          style={{ 
            width: `${(timeLeft / duration) * 100}%` 
          }}
        ></div>
      </div>

      {shouldShowWarning && (
        <div className="text-sm text-red-600 font-medium animate-pulse">
          ⚠️ Time running out!
        </div>
      )}

      {timeLeft === 0 && (
        <div className="text-sm text-red-600 font-bold">
          ⏰ Time's up!
        </div>
      )}
    </div>
  );
};

export default Timer;
