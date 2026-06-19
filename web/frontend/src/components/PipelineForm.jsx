import { useState } from 'react';

export default function PipelineForm({ 
  summary, 
  setSummary, 
  pipeline, 
  setPipeline, 
  onSubmit, 
  isLoading,
  uploadedImage 
}) {
  const pipelines = [
    {
      id: 'optimize',
      name: 'RefModel 优化',
      description: '评价反馈 + 改进摘要',
      features: ['五维度评分', 'CoE 分析', '改进摘要'],
      color: 'from-emerald-500 to-teal-600',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
    },
    {
      id: 'direct-score',
      name: 'EvaModel 评价',
      description: '直接输出五维评价',
      features: ['五维度评分', 'CoE 分析'],
      color: 'from-violet-500 to-purple-600',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      ),
    },
  ];

  const canSubmit = uploadedImage && summary.trim() && pipeline && !isLoading;

  return (
    <div className="space-y-6">
      {/* Summary 输入 */}
      <div>
        <label className="block text-sm font-medium text-slate-300 mb-3 flex items-center gap-2">
          <svg className="w-4 h-4 text-brand-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          图表总结
        </label>
        <textarea
          value={summary}
          onChange={(e) => setSummary(e.target.value)}
          placeholder="请输入您对图表的总结描述..."
          disabled={isLoading}
          rows={4}
          className="w-full px-4 py-3 bg-slate-800/50 border border-slate-600 rounded-xl 
                     text-slate-200 placeholder-slate-500 resize-none
                     focus:outline-none focus:border-brand-500 focus:ring-2 focus:ring-brand-500/20
                     transition-all duration-300 disabled:opacity-50"
        />
        <p className="mt-2 text-xs text-slate-500">
          例如："Revenue went up and down. Ended higher than started."
        </p>
      </div>

      {/* Pipeline 选择 */}
      <div>
        <label className="block text-sm font-medium text-slate-300 mb-3 flex items-center gap-2">
          <svg className="w-4 h-4 text-brand-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
          </svg>
          选择处理方式
        </label>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {pipelines.map((p) => (
            <button
              key={p.id}
              type="button"
              onClick={() => setPipeline(p.id)}
              disabled={isLoading}
              className={`
                relative p-4 rounded-xl text-left transition-all duration-300
                ${pipeline === p.id
                  ? 'glass border-brand-500/50 glow-sm'
                  : 'glass-light border-transparent hover:border-slate-500/30'
                }
                disabled:opacity-50 disabled:cursor-not-allowed
                group
              `}
            >
              {/* 选中指示器 */}
              {pipeline === p.id && (
                <div className="absolute -top-1 -right-1 w-6 h-6 bg-brand-500 rounded-full flex items-center justify-center">
                  <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                </div>
              )}

              <div className="flex items-start gap-3">
                <div className={`
                  p-2 rounded-lg bg-gradient-to-br ${p.color} bg-opacity-20
                  group-hover:scale-110 transition-transform duration-300
                `}>
                  <div className="text-white">{p.icon}</div>
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-slate-200 mb-1">{p.name}</h3>
                  <p className="text-sm text-slate-400 mb-2">{p.description}</p>
                  <div className="flex flex-wrap gap-1.5">
                    {p.features.map((feature, i) => (
                      <span
                        key={i}
                        className="px-2 py-0.5 text-xs rounded-full bg-slate-700/50 text-slate-400"
                      >
                        {feature}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* 提交按钮 */}
      <button
        onClick={onSubmit}
        disabled={!canSubmit}
        className={`
          w-full py-4 px-6 rounded-xl font-semibold text-lg
          transition-all duration-300
          ${canSubmit
            ? 'btn-primary text-white'
            : 'bg-slate-700 text-slate-400 cursor-not-allowed'
          }
        `}
      >
        {isLoading ? (
          <span className="flex items-center justify-center gap-3">
            <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            处理中...
          </span>
        ) : (
          <span className="flex items-center justify-center gap-2">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            开始分析
          </span>
        )}
      </button>
    </div>
  );
}
