import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import apiService from '../services/api';
import { Rocket, Target, TrendingUp, Brain, Flame, RefreshCw, ShieldCheck, Layers } from 'lucide-react';

export default function LearningRulesExplanation() {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const { t } = useTranslation();

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const learningConfig = await apiService.getLearningConfig();
        setConfig(learningConfig);
      } catch (error) {
        console.error('Failed to fetch learning config:', error);
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
          <p className="text-gray-600">{t('common.loading')}</p>
        </div>
      </section>
    );
  }

  if (!config) {
    return null;
  }

  const { initial_set_size, stage_increment, max_set_size } = config;

  const phases = [
    {
      number: 1,
      key: 'learning',
      color: 'bg-slate-500',
      border: 'border-slate-200',
      bg: 'bg-slate-50',
      accent: 'text-slate-700',
      icon: <Rocket className="w-5 h-5" />,
      iconBg: 'bg-slate-100 text-slate-600',
      description: t('rules.phases.learning.desc', { count: initial_set_size }),
    },
    {
      number: 2,
      key: 'isolationMastered',
      color: 'bg-blue-500',
      border: 'border-blue-200',
      bg: 'bg-blue-50',
      accent: 'text-blue-700',
      icon: <Target className="w-5 h-5" />,
      iconBg: 'bg-blue-100 text-blue-600',
      description: t('rules.phases.isolationMastered.desc'),
    },
    {
      number: 3,
      key: 'integrationReview',
      color: 'bg-purple-500',
      border: 'border-purple-200',
      bg: 'bg-purple-50',
      accent: 'text-purple-700',
      icon: <Layers className="w-5 h-5" />,
      iconBg: 'bg-purple-100 text-purple-600',
      description: t('rules.phases.integrationReview.desc'),
    },
    {
      number: 4,
      key: 'integrationConfirmed',
      color: 'bg-emerald-500',
      border: 'border-emerald-200',
      bg: 'bg-emerald-50',
      accent: 'text-emerald-700',
      icon: <ShieldCheck className="w-5 h-5" />,
      iconBg: 'bg-emerald-100 text-emerald-600',
      description: t('rules.phases.integrationConfirmed.desc', { increment: stage_increment, max: max_set_size }),
    },
    {
      number: 5,
      key: 'spiralReview',
      color: 'bg-rose-500',
      border: 'border-rose-200',
      bg: 'bg-rose-50',
      accent: 'text-rose-700',
      icon: <RefreshCw className="w-5 h-5" />,
      iconBg: 'bg-rose-100 text-rose-600',
      description: t('rules.phases.spiralReview.desc'),
    },
  ];

  return (
    <section className="bg-gradient-to-r from-purple-50 to-blue-50 rounded-2xl p-8">
      <div className="text-center mb-10">
        <h2 className="text-2xl md:text-3xl font-bold mb-4 text-gray-900 flex items-center justify-center gap-3">
          <Target className="w-8 h-8 text-indigo-500" /> {t('rules.title')}
        </h2>
        <p className="text-lg text-gray-600 max-w-3xl mx-auto">
          {t('rules.subtitle')}
        </p>
      </div>

      {/* Phase cards — vertical stacked timeline */}
      <div className="max-w-3xl mx-auto space-y-4 mb-10">
        {phases.map((phase, index) => (
          <div key={phase.number} className="relative">
            {/* Connector line */}
            {index < phases.length - 1 && (
              <div className="absolute left-[19px] top-full h-4 w-0.5 bg-gray-200 z-0" />
            )}
            <div className={`relative bg-white rounded-xl border ${phase.border} p-5 shadow-sm`}>
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0">
                  <div className={`w-10 h-10 ${phase.iconBg} rounded-full flex items-center justify-center`}>
                    {phase.icon}
                  </div>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-2">
                    <span className={`text-xs font-bold uppercase tracking-wide px-2 py-0.5 rounded-full ${phase.bg} ${phase.accent}`}>
                      {t('rules.phase')} {phase.number}
                    </span>
                    <h3 className="text-base font-semibold text-gray-900">{t(`rules.phases.${phase.key}.title`)}</h3>
                  </div>
                  <p className="text-sm text-gray-600 leading-relaxed">{phase.description}</p>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Bottom callouts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-3xl mx-auto">
        <div className="bg-white rounded-xl p-5 shadow-sm border">
          <div className="flex items-center justify-center text-center">
            <div className="text-sm text-gray-700">
              <Brain className="w-4 h-4 inline mr-1 text-indigo-500" />
              <strong>{t('rules.spacedRep')}</strong> {t('rules.spacedRepDesc')}
            </div>
          </div>
        </div>

        <div className="bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-xl p-5">
          <div className="text-center">
            <div className="flex justify-center mb-2"><Flame className="w-6 h-6 opacity-90" /></div>
            <div className="text-sm font-semibold mb-1">{t('rules.why5Title')}</div>
            <div className="text-xs opacity-90">
              {t('rules.why5Desc')}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
