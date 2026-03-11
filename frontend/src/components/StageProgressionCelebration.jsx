import { useState, useEffect } from 'react';

const StageProgressionCelebration = ({ 
  show, 
  onClose, 
  stageInfo = {},
  onContinue
}) => {
  const [animationPhase, setAnimationPhase] = useState(0);

  useEffect(() => {
    if (show) {
      // Reset animation
      setAnimationPhase(0);
      
      // Animation sequence
      const timer1 = setTimeout(() => setAnimationPhase(1), 100);
      const timer2 = setTimeout(() => setAnimationPhase(2), 800);
      const timer3 = setTimeout(() => setAnimationPhase(3), 1500);
      
      return () => {
        clearTimeout(timer1);
        clearTimeout(timer2);
        clearTimeout(timer3);
      };
    }
  }, [show]);

  if (!show) return null;

  const messages = [
    "🎉 Amazing progress!",
    "🚀 You're mastering this!",
    "⭐ Outstanding work!",
    "💪 Keep up the momentum!",
    "🔥 You're on fire!",
    "🎯 Bullseye! Great job!",
    "✨ Fantastic learning!",
    "🌟 Stellar performance!"
  ];

  const encouragements = [
    "Your dedication is paying off!",
    "Building lasting knowledge, one card at a time!",
    "Great learning patterns emerging!",
    "You're developing mastery!",
    "Knowledge is building momentum!",
    "Excellent retention skills!",
    "Your brain is making connections!"
  ];

  const randomMessage = messages[Math.floor(Math.random() * messages.length)];
  const randomEncouragement = encouragements[Math.floor(Math.random() * encouragements.length)];

  return (
    <>
      {/* Backdrop */}
      <div 
        className={`fixed inset-0 bg-black transition-opacity duration-500 z-50 ${
          show ? 'bg-opacity-50' : 'bg-opacity-0'
        }`}
        onClick={onClose}
      />

      {/* Celebration Modal */}
      <div className={`fixed inset-0 flex items-center justify-center z-50 transition-all duration-500 ${
        show ? 'scale-100 opacity-100' : 'scale-75 opacity-0'
      }`}>
        <div className="bg-white rounded-2xl shadow-2xl max-w-lg mx-4 overflow-hidden">
          
          {/* Animated Header */}
          <div className="bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 p-8 text-white text-center relative overflow-hidden">
            
            {/* Floating Particles Animation */}
            <div className="absolute inset-0">
              {[...Array(20)].map((_, i) => (
                <div
                  key={i}
                  className={`absolute w-2 h-2 bg-white rounded-full transition-all duration-2000 ${
                    animationPhase >= 1 ? 'animate-bounce' : ''
                  }`}
                  style={{
                    left: `${Math.random() * 100}%`,
                    top: `${Math.random() * 100}%`,
                    animationDelay: `${Math.random() * 2}s`,
                    animationDuration: `${1 + Math.random() * 2}s`
                  }}
                />
              ))}
            </div>

            <div className={`relative z-10 transition-all duration-1000 ${
              animationPhase >= 1 ? 'transform scale-110' : 'transform scale-75 opacity-0'
            }`}>
              <div className="text-6xl mb-4 animate-pulse">🎉</div>
              <h2 className="text-2xl font-bold mb-2">{randomMessage}</h2>
              <p className="text-blue-100">Stage Progression Unlocked!</p>
            </div>
          </div>

          {/* Content */}
          <div className="p-8">
            
            {/* Stage Progression Info */}
            <div className={`mb-6 transition-all duration-1000 delay-300 ${
              animationPhase >= 2 ? 'transform translateY-0 opacity-100' : 'transform translateY-4 opacity-0'
            }`}>
              <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-xl p-6 border border-green-200">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center space-x-3">
                    <div className="flex items-center space-x-2">
                      <span className="text-2xl">📈</span>
                      <div>
                        <div className="font-semibold text-gray-800">
                          New Cards Unlocked!
                        </div>
                        <div className="text-sm text-gray-600">
                          {stageInfo.newCardsCount || 3} more cards added to your learning set
                        </div>
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-bold text-blue-600">
                      Stage {stageInfo.newStage || 'N+1'}
                    </div>
                    <div className="text-sm text-gray-500">
                      Level up!
                    </div>
                  </div>
                </div>
                
                {/* Progress Visualization */}
                <div className="flex items-center space-x-2 mb-3">
                  <span className="text-sm text-gray-600">Progress:</span>
                  <div className="flex-1 bg-gray-200 rounded-full h-3 overflow-hidden">
                    <div 
                      className="h-full bg-gradient-to-r from-green-400 to-blue-500 transition-all duration-2000 ease-out"
                      style={{ 
                        width: animationPhase >= 2 ? `${Math.min(100, ((stageInfo.masteredCards || 3) / (stageInfo.totalCards || 10)) * 100)}%` : '0%'
                      }}
                    />
                  </div>
                </div>
                
                <div className="text-sm text-gray-600 text-center">
                  {stageInfo.masteredCards || 3} mastered • {stageInfo.totalCards || 10} total cards
                </div>
              </div>
            </div>

            {/* Encouragement Message */}
            <div className={`text-center mb-6 transition-all duration-1000 delay-500 ${
              animationPhase >= 3 ? 'transform translateY-0 opacity-100' : 'transform translateY-4 opacity-0'
            }`}>
              <p className="text-gray-600 mb-2">{randomEncouragement}</p>
              <div className="flex justify-center space-x-2">
                {[...Array(5)].map((_, i) => (
                  <span 
                    key={i} 
                    className={`text-2xl transition-all duration-300 ${
                      animationPhase >= 3 ? 'animate-pulse' : 'opacity-0'
                    }`}
                    style={{ animationDelay: `${i * 200}ms` }}
                  >
                    ⭐
                  </span>
                ))}
              </div>
            </div>

            {/* Action Buttons */}
            <div className={`flex space-x-3 transition-all duration-1000 delay-700 ${
              animationPhase >= 3 ? 'transform translateY-0 opacity-100' : 'transform translateY-4 opacity-0'
            }`}>
              <button
                onClick={onContinue || onClose}
                className="flex-1 bg-gradient-to-r from-blue-500 to-purple-500 text-white py-3 px-6 rounded-xl font-semibold hover:from-blue-600 hover:to-purple-600 transform hover:scale-105 transition-all duration-200 shadow-lg"
              >
                Continue Learning! 🚀
              </button>
              
              <button
                onClick={onClose}
                className="px-6 py-3 border-2 border-gray-300 text-gray-700 rounded-xl font-semibold hover:bg-gray-50 hover:border-gray-400 transition-all duration-200"
              >
                Take a Break ⏸️
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Confetti Animation */}
      {show && (
        <div className="fixed inset-0 pointer-events-none z-40">
          {[...Array(50)].map((_, i) => (
            <div
              key={i}
              className={`absolute w-3 h-3 transition-all duration-3000 ${
                ['bg-red-400', 'bg-blue-400', 'bg-green-400', 'bg-yellow-400', 'bg-purple-400', 'bg-pink-400'][i % 6]
              } ${
                animationPhase >= 1 ? 'animate-bounce' : 'opacity-0'
              }`}
              style={{
                left: `${Math.random() * 100}%`,
                top: '-20px',
                transform: `rotate(${Math.random() * 360}deg)`,
                animationDelay: `${Math.random() * 1}s`,
                animationDuration: `${2 + Math.random() * 2}s`,
                borderRadius: Math.random() > 0.5 ? '50%' : '0%'
              }}
            />
          ))}
        </div>
      )}
    </>
  );
};

export default StageProgressionCelebration;
