import { useState } from 'react';

const TimerSettings = ({ onStart, onCancel, defaultSettings = {} }) => {
  const [timerMode, setTimerMode] = useState(defaultSettings.timerMode || 'disabled');
  const [timerDuration, setTimerDuration] = useState(defaultSettings.timerDuration || 30);

  const handleStart = () => {
    onStart({
      timerMode,
      timerDuration: timerMode === 'disabled' ? 0 : timerDuration
    });
  };

  const timerModes = [
    { value: 'disabled', label: 'No Timer', description: 'Take your time with each question' },
    { value: 'optional', label: 'Optional Timer', description: 'Timer marks as fail when expired' },
  ];

  const durationOptions = [15, 30, 60];

  return (
    <div className="max-w-md mx-auto">
      <div className="card-flashcard p-6">
        <h3 className="text-xl font-bold mb-4 text-center">Timer Settings</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Timer Mode
            </label>
            <div className="space-y-2">
              {timerModes.map((mode) => (
                <label key={mode.value} className="flex items-start space-x-3 cursor-pointer">
                  <input
                    type="radio"
                    name="timerMode"
                    value={mode.value}
                    checked={timerMode === mode.value}
                    onChange={(e) => setTimerMode(e.target.value)}
                    className="mt-1"
                  />
                  <div>
                    <div className="font-medium">{mode.label}</div>
                    <div className="text-sm text-gray-600">{mode.description}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {timerMode !== 'disabled' && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Timer Duration (seconds)
              </label>
              <div className="grid grid-cols-3 gap-2">
                {durationOptions.map((duration) => (
                  <button
                    key={duration}
                    onClick={() => setTimerDuration(duration)}
                    className={`p-2 rounded border text-sm font-medium ${
                      timerDuration === duration
                        ? 'border-blue-500 bg-blue-50 text-blue-700'
                        : 'border-gray-300 hover:border-gray-400'
                    }`}
                  >
                    {duration}s
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="pt-4 border-t">
            <div className="flex space-x-3">
              <button
                onClick={handleStart}
                className="flex-1 btn btn-primary"
              >
                Start Learning
              </button>
              <button
                onClick={onCancel}
                className="flex-1 btn btn-outline"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>

        {timerMode !== 'disabled' && (
          <div className="mt-4 p-3 bg-blue-50 rounded-lg">
            <div className="text-sm text-blue-800">
              <div className="font-medium mb-1">💡 Timer Benefits:</div>
              <ul className="list-disc list-inside space-y-1 text-xs">
                <li>Fast answers (≤25% time): +20 bonus points</li>
                <li>Good answers (≤50% time): +10 bonus points</li>
                <li>Improves focus and retention</li>
                <li>Builds confidence under pressure</li>
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TimerSettings;
