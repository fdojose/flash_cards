import { useEffect, useState } from 'react';

const PerformanceFeedback = ({ 
  performance, 
  bonusPoints, 
  timeSpent, 
  timerDuration, 
  show = false,
  onClose 
}) => {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    if (show) {
      setIsVisible(true);
      // Auto-hide after 3 seconds
      const timer = setTimeout(() => {
        setIsVisible(false);
        onClose?.();
      }, 3000);
      return () => clearTimeout(timer);
    }
  }, [show, onClose]);

  if (!show || !performance) return null;

  const performanceConfig = {
    fast: {
      icon: '🚀',
      title: 'Lightning Fast!',
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      borderColor: 'border-green-200'
    },
    good: {
      icon: '👍',
      title: 'Good Timing!',
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
      borderColor: 'border-blue-200'
    },
    slow: {
      icon: '🐌',
      title: 'Take Your Time',
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-50',
      borderColor: 'border-yellow-200'
    },
    expired: {
      icon: '⏰',
      title: 'Time Expired',
      color: 'text-red-600',
      bgColor: 'bg-red-50',
      borderColor: 'border-red-200'
    }
  };

  const config = performanceConfig[performance] || performanceConfig.slow;
  const percentage = timerDuration > 0 ? Math.round((timeSpent / timerDuration) * 100) : 0;

  return (
    <div className={`
      fixed top-4 right-4 z-50 max-w-sm transform transition-all duration-500 ease-in-out
      ${isVisible ? 'translate-x-0 opacity-100' : 'translate-x-full opacity-0'}
    `}>
      <div className={`
        p-4 rounded-lg border-2 shadow-lg
        ${config.bgColor} ${config.borderColor}
      `}>
        <div className="flex items-center space-x-3">
          <div className="text-2xl">{config.icon}</div>
          <div className="flex-1">
            <div className={`font-bold ${config.color}`}>
              {config.title}
            </div>
            <div className="text-sm text-gray-600">
              {timeSpent}s / {timerDuration}s ({percentage}%)
            </div>
            {bonusPoints > 0 && (
              <div className="text-sm font-medium text-green-600">
                +{bonusPoints} bonus points! ✨
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PerformanceFeedback;
