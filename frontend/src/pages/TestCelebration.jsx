import { useState } from 'react';
import StageProgressionCelebration from '../components/StageProgressionCelebration';
import ConfidenceProgress from '../components/ConfidenceProgress';

const TestCelebration = () => {
  const [showCelebration, setShowCelebration] = useState(false);
  const [simulationStep, setSimulationStep] = useState(0);

  const handleClose = () => {
    setShowCelebration(false);
  };

  const sampleStageInfo = {
    newCardsCount: 3,
    newStage: 4,
    masteredCards: 6,
    totalCards: 12,
    previousStage: 3
  };

  // Different confidence stats for simulation steps
  const confidenceSteps = [
    // Step 0: Starting with some progress
    {
      confidence_breakdown: { strong_count: 2, weak_count: 3, new_count: 1 },
      learning_phase: { phase: 'learning', message: 'Building knowledge...' }
    },
    // Step 1: Getting closer to mastery
    {
      confidence_breakdown: { strong_count: 4, weak_count: 2, new_count: 0 },
      learning_phase: { phase: 'building', message: 'Making great progress!' }
    },
    // Step 2: Ready for progression
    {
      confidence_breakdown: { strong_count: 6, weak_count: 0, new_count: 0 },
      learning_phase: { phase: 'mastering', message: 'Almost complete!' }
    },
    // Step 3: After stage progression (more cards added)
    {
      confidence_breakdown: { strong_count: 6, weak_count: 0, new_count: 3 },
      learning_phase: { phase: 'learning', message: 'New stage unlocked!' }
    }
  ];

  const triggerSimulation = () => {
    if (simulationStep < 3) {
      setSimulationStep(simulationStep + 1);
      
      // Show celebration when transitioning to step 3
      if (simulationStep === 2) {
        setTimeout(() => {
          setShowCelebration(true);
        }, 500);
      }
    } else {
      // Reset simulation
      setSimulationStep(0);
    }
  };

  const currentStats = confidenceSteps[simulationStep];
  const currentStage = simulationStep < 3 ? 3 : 4;

  return (
    <div className="max-w-4xl mx-auto p-8">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-bold mb-4">🎉 Stage Progression Demo</h1>
        <p className="text-gray-600 mb-6">
          Watch how stage progression works in progressive learning mode
        </p>
        
        <button
          onClick={triggerSimulation}
          className="bg-gradient-to-r from-blue-500 to-purple-500 text-white px-6 py-3 rounded-xl font-semibold hover:from-blue-600 hover:to-purple-600 transform hover:scale-105 transition-all duration-200 shadow-lg"
        >
          {simulationStep < 3 ? `Step ${simulationStep + 1}: Continue Learning` : '🔄 Reset Demo'}
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Live Indicator */}
        <div className="space-y-6">
          <div className="bg-white rounded-xl p-6 shadow-lg">
            <h2 className="text-xl font-semibold mb-4">📊 Unified Progress Indicator</h2>
            <ConfidenceProgress
              confidenceStats={currentStats}
              sessionQuestionCount={simulationStep * 3}
              sessionCorrectCount={simulationStep * 2}
              sessionIncorrectCount={simulationStep * 1}
              showSessionCount={true}
              currentStage={currentStage}
              showStageInfo={true}
            />
          </div>

          <div className="bg-white rounded-xl p-6 shadow-lg">
            <h2 className="text-xl font-semibold mb-4">📈 Simulation Steps</h2>
            <div className="space-y-2">
              {confidenceSteps.map((_, index) => (
                <div key={index} className={`flex items-center space-x-3 p-2 rounded ${
                  index === simulationStep ? 'bg-blue-100 border border-blue-300' : 
                  index < simulationStep ? 'bg-green-50 border border-green-200' : 'bg-gray-50'
                }`}>
                  <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                    index === simulationStep ? 'bg-blue-500 text-white' :
                    index < simulationStep ? 'bg-green-500 text-white' : 'bg-gray-300 text-gray-600'
                  }`}>
                    {index + 1}
                  </span>
                  <span className="text-sm">
                    {index === 0 && "Starting: Learning current stage cards"}
                    {index === 1 && "Progress: Most cards understood"}
                    {index === 2 && "Ready: All current cards mastered"}
                    {index === 3 && "🎉 Stage advanced! New cards unlocked"}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Explanation */}
        <div className="space-y-6">
          <div className="bg-white rounded-xl p-6 shadow-lg">
            <h2 className="text-xl font-semibold mb-4">🔍 What's Happening</h2>
            
            <div className="space-y-4 text-sm text-gray-700">
              <div className={`p-3 rounded-lg ${simulationStep === 0 ? 'bg-blue-50 border border-blue-200' : 'bg-gray-50'}`}>
                <h3 className="font-semibold text-gray-800 mb-1">Step 1: Active Learning</h3>
                <p>User answers questions in current stage. Some cards mastered (strong), some still learning (weak), some new.</p>
              </div>

              <div className={`p-3 rounded-lg ${simulationStep === 1 ? 'bg-blue-50 border border-blue-200' : 'bg-gray-50'}`}>
                <h3 className="font-semibold text-gray-800 mb-1">Step 2: Near Completion</h3>
                <p>Most cards mastered. Only a few weak cards remain. System indicates user is close to stage advancement.</p>
              </div>

              <div className={`p-3 rounded-lg ${simulationStep === 2 ? 'bg-blue-50 border border-blue-200' : 'bg-gray-50'}`}>
                <h3 className="font-semibold text-gray-800 mb-1">Step 3: Stage Ready</h3>
                <p>All current stage cards mastered! System is ready to advance to next stage with more cards.</p>
              </div>

              <div className={`p-3 rounded-lg ${simulationStep === 3 ? 'bg-green-50 border border-green-200' : 'bg-gray-50'}`}>
                <h3 className="font-semibold text-green-800 mb-1">🎉 Step 4: Progression!</h3>
                <p>Backend automatically adds new cards to learning set. Celebration animation shows! User continues with expanded card set.</p>
              </div>
            </div>

            {simulationStep === 3 && (
              <div className="mt-4 p-3 bg-purple-50 border border-purple-200 rounded-lg">
                <p className="text-sm text-purple-700">
                  <strong>Backend Logic:</strong> When getNextFlashcard() detects all cards are mastered AND more elements exist in dataset AND stage_increment {'>'}
                   0, it automatically adds {sampleStageInfo.newCardsCount} new cards and advances the stage.
                </p>
              </div>
            )}
          </div>

          <div className="bg-white rounded-xl p-6 shadow-lg">
            <h2 className="text-xl font-semibold mb-4">⚙️ Technical Details</h2>
            <div className="text-xs text-gray-600 space-y-2">
              <div><strong>Detection:</strong> Frontend compares card counts between API calls</div>
              <div><strong>Trigger:</strong> previousCardsCount {'<'} newCardsCount</div>
              <div><strong>Animation:</strong> Modal with confetti, progress info, and celebration</div>
              <div><strong>Continue:</strong> Smooth transition back to learning</div>
            </div>
            
            <div className="mt-4 p-3 bg-gray-50 rounded">
              <h3 className="font-medium mb-2">Current Stats:</h3>
              <pre className="text-xs">{JSON.stringify(currentStats, null, 2)}</pre>
            </div>
          </div>
        </div>
      </div>

      <StageProgressionCelebration
        show={showCelebration}
        onClose={handleClose}
        onContinue={handleClose}
        stageInfo={sampleStageInfo}
      />
    </div>
  );
};

export default TestCelebration;
