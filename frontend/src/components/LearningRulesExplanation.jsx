import React, { useState, useEffect } from 'react';
import apiService from '../services/api';

export default function LearningRulesExplanation() {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const learningConfig = await apiService.getLearningConfig();
        setConfig(learningConfig);
      } catch (error) {
        console.error('Failed to fetch learning config:', error);
        // Set default values if API fails
        setConfig({
          initial_set_size: 10,
          mastery_threshold: 3,
          stage_increment: 10,
          max_set_size: 30
        });
      } finally {
        setLoading(false);
      }
    };

    fetchConfig();
  }, []);

  if (loading) {
    return (
      <section className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-2xl p-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading learning system rules...</p>
        </div>
      </section>
    );
  }

  if (!config) {
    return null;
  }

  const {
    initial_set_size,
    mastery_threshold,
    stage_increment,
    max_set_size
  } = config;

  return (
    <section className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-2xl p-8">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold mb-4 text-gray-900">
          🎯 How Our Smart Learning System Works
        </h2>
        <p className="text-lg text-gray-600 max-w-3xl mx-auto">
          Our scientifically-proven spaced repetition algorithm adapts to your learning pace, 
          ensuring you master every concept efficiently and retain knowledge long-term.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 max-w-6xl mx-auto">
        {/* Left Column - Learning Process */}
        <div className="space-y-6">
          <div className="bg-white rounded-xl p-6 shadow-sm border">
            <div className="flex items-center mb-4">
              <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center mr-4">
                <span className="text-2xl">🚀</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-900">Getting Started</h3>
            </div>
            <p className="text-gray-700 leading-relaxed">
              You'll begin with a focused set of <strong className="text-green-600">{initial_set_size} cards</strong> 
              to build confidence without feeling overwhelmed. Our system starts small so you can establish 
              a strong foundation before expanding your knowledge.
            </p>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-sm border">
            <div className="flex items-center mb-4">
              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mr-4">
                <span className="text-2xl">🎯</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-900">Mastery Process</h3>
            </div>
            <p className="text-gray-700 leading-relaxed">
              To truly master each concept, you'll need to answer <strong className="text-blue-600">{mastery_threshold} questions</strong> 
              correctly for each card. This repetition strengthens neural pathways and moves knowledge from 
              short-term to long-term memory.
            </p>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-sm border">
            <div className="flex items-center mb-4">
              <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center mr-4">
                <span className="text-2xl">📈</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-900">Progressive Growth</h3>
            </div>
            <p className="text-gray-700 leading-relaxed">
              When you master your current set, we automatically unlock <strong className="text-purple-600">{stage_increment} new cards</strong>. 
              This progressive approach ensures you're always challenged but never overwhelmed, maintaining 
              optimal learning momentum.
            </p>
          </div>
        </div>

        {/* Right Column - Visual Process Flow */}
        <div className="space-y-6">
          <div className="bg-white rounded-xl p-6 shadow-sm border">
            <h3 className="text-xl font-semibold text-gray-900 mb-6 text-center">Your Learning Journey</h3>
            
            <div className="space-y-4">
              {/* Step 1 */}
              <div className="flex items-center">
                <div className="w-8 h-8 bg-green-500 text-white rounded-full flex items-center justify-center text-sm font-bold mr-4">
                  1
                </div>
                <div className="flex-1">
                  <div className="font-medium text-gray-900">Start with {initial_set_size} cards</div>
                  <div className="text-sm text-gray-600">Perfect size for initial learning</div>
                </div>
              </div>

              {/* Step 2 */}
              <div className="flex items-center">
                <div className="w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm font-bold mr-4">
                  2
                </div>
                <div className="flex-1">
                  <div className="font-medium text-gray-900">Answer {mastery_threshold} times correctly</div>
                  <div className="text-sm text-gray-600">Build strong memory connections</div>
                </div>
              </div>

              {/* Step 3 */}
              <div className="flex items-center">
                <div className="w-8 h-8 bg-purple-500 text-white rounded-full flex items-center justify-center text-sm font-bold mr-4">
                  3
                </div>
                <div className="flex-1">
                  <div className="font-medium text-gray-900">Unlock {stage_increment} new cards</div>
                  <div className="text-sm text-gray-600">Progressive challenge increase</div>
                </div>
              </div>

              {/* Step 4 */}
              <div className="flex items-center">
                <div className="w-8 h-8 bg-yellow-500 text-white rounded-full flex items-center justify-center text-sm font-bold mr-4">
                  4
                </div>
                <div className="flex-1">
                  <div className="font-medium text-gray-900">Repeat until mastery</div>
                  <div className="text-sm text-gray-600">Up to {max_set_size} cards maximum</div>
                </div>
              </div>
            </div>

            <div className="mt-6 p-4 bg-gradient-to-r from-green-50 to-blue-50 rounded-lg">
              <div className="flex items-center justify-center text-center">
                <div className="text-sm text-gray-700">
                  <strong>🧠 Smart Spaced Repetition:</strong> Cards you struggle with appear more frequently, 
                  while mastered cards appear less often - maximizing efficiency and retention!
                </div>
              </div>
            </div>
          </div>

          {/* Stats Callout */}
          <div className="bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-xl p-6">
            <div className="text-center">
              <div className="text-3xl mb-2">🔥</div>
              <div className="text-lg font-semibold mb-2">Proven Results</div>
              <div className="text-sm opacity-90">
                Spaced repetition can improve retention by up to <strong>200%</strong> compared to traditional study methods
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
