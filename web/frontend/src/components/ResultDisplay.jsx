import { useState, useEffect } from 'react';

const DIMENSIONS = [
  { key: 'faithfulness', fallback: 'accuracy', name: 'Faithfulness', label: 'Grounding', color: 'bg-sky-500' },
  { key: 'completeness', name: 'Completeness', label: 'Coverage', color: 'bg-emerald-500' },
  { key: 'conciseness', name: 'Conciseness', label: 'Brevity', color: 'bg-amber-500' },
  { key: 'logicality', fallback: 'fluency', name: 'Logicality', label: 'Coherence', color: 'bg-indigo-500' },
  { key: 'analysis', fallback: 'insight', name: 'Analysis', label: 'Insight', color: 'bg-rose-500' },
];

const DIMENSION_NAMES = {
  faithfulness: 'Faithfulness',
  completeness: 'Completeness',
  conciseness: 'Conciseness',
  logicality: 'Logicality',
  analysis: 'Analysis',
};

const PROCESS_ITEMS = [
  {
    title: '1. Figure Parsing',
    description: 'Reading chart image, labels, axes, and visual marks',
    icon: (
      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4-4a2 2 0 012.8 0L16 17m-2-2l1-1a2 2 0 012.8 0L20 16M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
      </svg>
    ),
  },
  {
    title: '2. Summary Evaluation',
    description: 'Scoring faithfulness, completeness, conciseness, logicality, and analysis',
    icon: (
      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-6m4 6V7m4 10v-3M5 19h14" />
      </svg>
    ),
  },
  {
    title: '3. Guided Refinement',
    description: 'Using evaluation feedback to improve weak or missing statements',
    icon: (
      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 4h2m-1 0v16m7-12l-2 2m-10 0L5 8m14 8l-2-2M7 14l-2 2" />
      </svg>
    ),
  },
  {
    title: '4. Report Generation',
    description: 'Packaging the score report and final summary',
    icon: (
      <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5l5 5v11a2 2 0 01-2 2z" />
      </svg>
    ),
  },
];

function getDimensionScore(scores, dimension) {
  const value = scores[dimension.key] ?? scores[dimension.fallback];
  return typeof value === 'number' ? value : 0;
}

function getDimensionReason(reasons, dimension) {
  return reasons[dimension.key] || reasons[dimension.fallback] || '';
}

function ScoreRing({ score, size = 96, strokeWidth = 8 }) {
  const [animatedScore, setAnimatedScore] = useState(0);
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (animatedScore / 10) * circumference;

  useEffect(() => {
    const timer = setTimeout(() => setAnimatedScore(score), 100);
    return () => clearTimeout(timer);
  }, [score]);

  const getScoreColor = (s) => {
    if (s >= 8) return '#10b981';
    if (s >= 6) return '#f59e0b';
    if (s >= 4) return '#ed7420';
    return '#ef4444';
  };

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width={size} height={size} className="transform -rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="#eee9e2"
          strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={getScoreColor(score)}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-1000 ease-out"
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="text-2xl font-extrabold text-stone-950">{score.toFixed(1)}</span>
      </div>
    </div>
  );
}

function DimensionBar({ dimension, score, reason, delay = 0 }) {
  const [show, setShow] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setShow(true), delay);
    return () => clearTimeout(timer);
  }, [delay]);

  return (
    <div
      className={`
        transform transition-all duration-500 ease-out
        ${show ? 'translate-y-0 opacity-100' : 'translate-y-4 opacity-0'}
      `}
    >
      <div className="flex items-center justify-between mb-2">
        <div>
          <span className="text-sm font-bold text-stone-900">{dimension.name}</span>
          <span className="ml-2 text-xs font-medium text-stone-400">{dimension.label}</span>
        </div>
        <span className="text-sm font-extrabold text-stone-950">{score}/2</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-stone-100">
        <div
          className={`h-full ${dimension.color} rounded-full transition-all duration-1000 ease-out`}
          style={{ width: show ? `${(score / 2) * 100}%` : '0%' }}
        />
      </div>
      {reason && (
        <p className="mt-2 line-clamp-2 text-xs leading-5 text-stone-500">{reason}</p>
      )}
    </div>
  );
}

const STATUS_STEP_INDEX = {
  pending: 0,
  parsing: 0,
  processing: 1,
  evaluating: 1,
  refining: 2,
  reporting: 3,
};

const STATUS_LABELS = {
  pending: 'Queued',
  parsing: 'Parsing',
  processing: 'Evaluating',
  evaluating: 'Evaluating',
  refining: 'Refining',
  reporting: 'Generating report',
};

function ProcessingPanel({ status }) {
  const activeIndex = STATUS_STEP_INDEX[status] ?? 0;
  const statusLabel = STATUS_LABELS[status] ?? 'Processing';

  return (
    <div className="rounded-xl border border-stone-200 bg-white/90 p-5 shadow-panel">
      <div className="mb-5 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-brand-500">Running Pipeline</p>
          <h3 className="mt-1 text-xl font-extrabold text-stone-950">Analyzing the figure...</h3>
        </div>
        <span className="inline-flex w-fit items-center gap-2 rounded-full bg-brand-50 px-3 py-1.5 text-xs font-bold text-brand-600">
          <span className="h-2 w-2 animate-pulse rounded-full bg-brand-500" />
          {statusLabel}
        </span>
      </div>

      <div className="space-y-3">
        {PROCESS_ITEMS.map((item, index) => {
          const isComplete = index < activeIndex;
          const isActive = index === activeIndex;

          return (
            <div
              key={item.title}
              className={`rounded-xl border p-4 transition ${
                isActive
                  ? 'border-brand-200 bg-brand-50/45 shadow-sm'
                  : isComplete
                    ? 'border-emerald-100 bg-emerald-50/50'
                    : 'border-stone-200 bg-white'
              }`}
            >
              <div className="flex items-start gap-4">
                <div
                  className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${
                    isComplete
                      ? 'bg-emerald-100 text-emerald-600'
                      : isActive
                        ? 'bg-brand-100 text-brand-600'
                        : 'bg-stone-100 text-stone-400'
                  }`}
                >
                  {isComplete ? (
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.4} d="M5 13l4 4L19 7" />
                    </svg>
                  ) : (
                    item.icon
                  )}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between gap-3">
                    <h4 className="font-bold text-stone-950">{item.title}</h4>
                    {isActive && <span className="h-4 w-4 animate-spin rounded-full border-2 border-brand-500 border-t-transparent" />}
                  </div>
                  <p className="mt-1 text-sm leading-5 text-stone-500">{item.description}</p>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function ResultDisplay({ result, status, pipeline }) {
  if (['pending', 'parsing', 'processing', 'evaluating', 'refining', 'reporting'].includes(status)) {
    return <ProcessingPanel status={status} />;
  }

  if (status === 'failed' || status === 'error') {
    return (
      <div className="rounded-xl border border-red-200 bg-white/90 p-6 shadow-panel">
        <div className="flex items-start gap-4">
          <div className="rounded-lg bg-red-50 p-3 text-red-500">
            <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <h3 className="font-bold text-red-600">Analysis failed</h3>
            <p className="mt-1 text-sm leading-6 text-stone-500">
              {result?.error || 'Please check the input and try again.'}
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (!result || status !== 'completed') {
    return null;
  }

  const scores = result.scores || {};
  const reasons = result.reasons || {};
  const weights = result.weights || {};
  const hasWeights = Object.keys(weights).length > 0;
  const totalScore = DIMENSIONS.reduce((sum, dim) => sum + getDimensionScore(scores, dim), 0);
  const improvedSummary = result.improved_summary;
  const scoreLabel = totalScore >= 8 ? 'Excellent' : totalScore >= 6 ? 'Good' : totalScore >= 4 ? 'Fair' : 'Needs improvement';

  return (
    <div className="animate-fade-in space-y-5">
      <div className="rounded-xl border border-stone-200 bg-white/92 p-6 shadow-panel">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-5">
          <ScoreRing score={totalScore} size={100} strokeWidth={8} />
          <div>
              <p className="text-xs font-bold uppercase tracking-[0.18em] text-brand-500">Final Report</p>
              <h3 className="mt-1 text-xl font-extrabold text-stone-950">Overall Score</h3>
              <p className="mt-1 text-sm font-medium text-stone-500">{scoreLabel} · Total {totalScore.toFixed(1)}/10</p>
            <div className="flex items-center gap-2 mt-2">
                <span className="rounded-full bg-brand-50 px-2.5 py-1 text-xs font-bold text-brand-600">
                {pipeline === 'optimize' || pipeline === 'pipeline2' ? 'RefModel Refinement' : 'EvaModel Evaluation'}
              </span>
            </div>
          </div>
          </div>
          <div className="rounded-lg border border-stone-200 bg-stone-50 px-4 py-3 text-sm text-stone-500">
            Five-dimensional Chain-of-Evaluation result
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-stone-200 bg-white/92 p-6 shadow-panel">
        <h3 className="mb-5 flex items-center gap-2 text-lg font-extrabold text-stone-950">
          <svg className="h-5 w-5 text-brand-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          Dimension Scores
        </h3>
        <div className="space-y-5">
          {DIMENSIONS.map((dim, index) => (
            <DimensionBar
              key={dim.key}
              dimension={dim}
              score={getDimensionScore(scores, dim)}
              reason={getDimensionReason(reasons, dim)}
              delay={index * 100}
            />
          ))}
        </div>
      </div>

      {hasWeights && (
        <div className="rounded-xl border border-stone-200 bg-white/92 p-6 shadow-panel">
          <h3 className="mb-4 flex items-center gap-2 text-lg font-extrabold text-stone-950">
            <svg className="h-5 w-5 text-brand-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 3h2v18h-2zM4 10h2v11H4zM18 7h2v14h-2z" />
            </svg>
            Dimension Weights
          </h3>
          <div className="grid gap-3 sm:grid-cols-5">
            {DIMENSIONS.map((dim) => {
              const weight = weights[dim.key] ?? 0;
              return (
                <div key={dim.key} className="rounded-lg border border-stone-200 bg-stone-50 p-3">
                  <p className="text-xs font-bold text-stone-500">{DIMENSION_NAMES[dim.key]}</p>
                  <p className="mt-1 text-xl font-extrabold text-stone-950">{Math.round(weight * 100)}%</p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {improvedSummary && (
        <div className="rounded-xl border border-emerald-200 bg-white/92 p-6 shadow-panel">
          <h3 className="mb-3 flex items-center gap-2 text-lg font-extrabold text-stone-950">
            <svg className="h-5 w-5 text-emerald-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
            Improved Summary
          </h3>
          <div className="relative">
            <div className="absolute bottom-0 left-0 top-0 w-1 rounded-full bg-emerald-500" />
            <p className="pl-4 leading-7 text-stone-700">{improvedSummary}</p>
          </div>
          <button
            onClick={() => navigator.clipboard.writeText(improvedSummary)}
            className="mt-4 flex items-center gap-2 rounded-lg bg-emerald-50 px-3 py-1.5 text-sm font-bold text-emerald-600 transition-colors hover:bg-emerald-100"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
            Copy
          </button>
        </div>
      )}
    </div>
  );
}
