import { useState, useEffect } from 'react';

const DIMENSIONS = [
  { key: 'accuracy', name: '准确性', color: 'from-blue-400 to-blue-600' },
  { key: 'completeness', name: '完整性', color: 'from-emerald-400 to-emerald-600' },
  { key: 'fluency', name: '流畅性', color: 'from-violet-400 to-violet-600' },
  { key: 'conciseness', name: '简洁性', color: 'from-amber-400 to-amber-600' },
  { key: 'insight', name: '洞察力', color: 'from-rose-400 to-rose-600' },
];

function ScoreRing({ score, size = 80, strokeWidth = 6 }) {
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
    if (s >= 4) return '#f97316';
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
          stroke="rgba(100, 116, 139, 0.2)"
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
        <span className="text-2xl font-bold text-white">{score.toFixed(1)}</span>
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
        <span className="text-sm font-medium text-slate-300">{dimension.name}</span>
        <span className="text-sm font-bold text-white">{score}/2</span>
      </div>
      <div className="h-2 bg-slate-700/50 rounded-full overflow-hidden">
        <div
          className={`h-full bg-gradient-to-r ${dimension.color} rounded-full transition-all duration-1000 ease-out`}
          style={{ width: show ? `${(score / 2) * 100}%` : '0%' }}
        />
      </div>
      {reason && (
        <p className="mt-1.5 text-xs text-slate-500 line-clamp-2">{reason}</p>
      )}
    </div>
  );
}

export default function ResultDisplay({ result, status, pipeline }) {
  if (status === 'pending' || status === 'processing') {
    return (
      <div className="glass rounded-2xl p-8">
        <div className="flex flex-col items-center justify-center py-8">
          <div className="relative">
            <div className="w-16 h-16 border-4 border-brand-500/30 rounded-full" />
            <div className="absolute inset-0 w-16 h-16 border-4 border-brand-500 border-t-transparent rounded-full animate-spin" />
          </div>
          <p className="mt-6 text-slate-300 font-medium">正在分析中...</p>
          <p className="mt-2 text-sm text-slate-500">请稍候，这可能需要一些时间</p>
        </div>
      </div>
    );
  }

  if (status === 'failed' || status === 'error') {
    return (
      <div className="glass rounded-2xl p-8 border-red-500/30">
        <div className="flex items-start gap-4">
          <div className="p-3 rounded-full bg-red-500/20">
            <svg className="w-6 h-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <h3 className="font-semibold text-red-400">处理失败</h3>
            <p className="mt-1 text-sm text-slate-400">
              {result?.error || '请检查输入后重试'}
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
  const totalScore = Object.values(scores).reduce((a, b) => a + b, 0);
  const improvedSummary = result.improved_summary;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* 总分卡片 */}
      <div className="glass rounded-2xl p-6 glow">
        <div className="flex items-center gap-6">
          <ScoreRing score={totalScore} size={100} strokeWidth={8} />
          <div>
            <h3 className="text-lg font-semibold text-slate-200">综合评分</h3>
            <p className="text-sm text-slate-400 mt-1">
              {totalScore >= 8 ? '优秀' : totalScore >= 6 ? '良好' : totalScore >= 4 ? '一般' : '需改进'}
            </p>
            <div className="flex items-center gap-2 mt-2">
              <span className="px-2 py-0.5 text-xs rounded-full bg-brand-500/20 text-brand-400">
                {pipeline === 'optimize' || pipeline === 'pipeline2' ? 'RefModel 优化' : 'EvaModel 评价'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 各维度评分 */}
      <div className="glass rounded-2xl p-6">
        <h3 className="text-lg font-semibold text-slate-200 mb-4 flex items-center gap-2">
          <svg className="w-5 h-5 text-brand-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
          各维度评分
        </h3>
        <div className="space-y-5">
          {DIMENSIONS.map((dim, index) => (
            <DimensionBar
              key={dim.key}
              dimension={dim}
              score={scores[dim.key] || 0}
              reason={reasons[dim.key]}
              delay={index * 100}
            />
          ))}
        </div>
      </div>

      {/* RefModel 改进结果 */}
      {improvedSummary && (
        <div className="glass rounded-2xl p-6 border-emerald-500/30">
          <h3 className="text-lg font-semibold text-slate-200 mb-3 flex items-center gap-2">
            <svg className="w-5 h-5 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
            改进后的总结
          </h3>
          <div className="relative">
            <div className="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-emerald-400 to-emerald-600 rounded-full" />
            <p className="pl-4 text-slate-300 leading-relaxed">{improvedSummary}</p>
          </div>
          <button
            onClick={() => navigator.clipboard.writeText(improvedSummary)}
            className="mt-4 flex items-center gap-2 px-3 py-1.5 text-sm text-emerald-400 hover:text-emerald-300 
                       bg-emerald-500/10 hover:bg-emerald-500/20 rounded-lg transition-colors"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
            复制
          </button>
        </div>
      )}
    </div>
  );
}
