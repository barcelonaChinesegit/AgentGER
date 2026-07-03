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
      name: 'RefModel Refinement',
      description: 'Feedback-guided improved summary',
      features: ['EvaModel scoring', 'CoE feedback', 'Refined summary'],
      tone: 'emerald',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
    },
    {
      id: 'direct-score',
      name: 'EvaModel Evaluation',
      description: 'Direct five-dimension scoring',
      features: ['Five scores', 'Reason chains'],
      tone: 'brand',
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      ),
    },
  ];

  const canSubmit = uploadedImage && summary.trim() && pipeline && !isLoading;

  return (
    <div className="rounded-xl border border-stone-200 bg-white/90 p-5 shadow-panel">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-brand-500">Evaluation Setup</p>
          <h3 className="mt-1 text-lg font-bold text-stone-950">Describe and run</h3>
        </div>
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-600">
          <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
          </svg>
        </div>
      </div>

      <div className="space-y-5">
      <div>
        <label className="mb-2 flex items-center gap-2 text-sm font-bold text-stone-800">
          <svg className="h-4 w-4 text-brand-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          Figure Summary
        </label>
        <textarea
          value={summary}
          onChange={(e) => setSummary(e.target.value)}
          placeholder="Write your figure summary here..."
          disabled={isLoading}
          rows={4}
          className="min-h-[8.75rem] w-full resize-none rounded-lg border border-stone-200 bg-stone-50/70 px-4 py-3 text-sm leading-6 text-stone-800 placeholder-stone-400 transition-all duration-300 focus:border-brand-400 focus:bg-white focus:outline-none focus:ring-4 focus:ring-brand-100 disabled:opacity-50"
        />
      </div>

      <div>
        <label className="mb-2 flex items-center gap-2 text-sm font-bold text-stone-800">
          <svg className="h-4 w-4 text-brand-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-6m4 6V7m4 10v-3M5 19h14" />
          </svg>
          Select Analysis Mode
        </label>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {pipelines.map((p) => (
            <button
              key={p.id}
              type="button"
              onClick={() => setPipeline(p.id)}
              disabled={isLoading}
              className={`
                relative rounded-lg border p-4 text-left transition-all duration-300
                ${pipeline === p.id
                  ? 'border-brand-300 bg-brand-50/70 shadow-sm'
                  : 'border-stone-200 bg-white hover:border-stone-300 hover:bg-stone-50'
                }
                disabled:opacity-50 disabled:cursor-not-allowed
                group
              `}
            >
              {pipeline === p.id && (
                <div className="absolute -right-2 -top-2 flex h-6 w-6 items-center justify-center rounded-full bg-brand-500 text-white shadow-orange">
                  <svg className="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                </div>
              )}

              <div className="flex items-start gap-3">
                <div className={`
                  rounded-lg p-2 transition-transform duration-300 group-hover:scale-105
                  ${p.tone === 'emerald' ? 'bg-emerald-50 text-emerald-600' : 'bg-brand-50 text-brand-600'}
                `}>
                  {p.icon}
                </div>
                <div className="flex-1">
                  <h3 className="mb-1 font-bold text-stone-950">{p.name}</h3>
                  <p className="mb-3 text-sm text-stone-500">{p.description}</p>
                  <div className="flex flex-wrap gap-1.5">
                    {p.features.map((feature, i) => (
                      <span
                        key={i}
                        className="rounded-full bg-stone-100 px-2 py-0.5 text-[11px] font-medium text-stone-500"
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

      <button
        onClick={onSubmit}
        disabled={!canSubmit}
        className={`
          h-12 w-full rounded-lg px-6 text-base font-bold
          transition-all duration-300
          ${canSubmit
            ? 'btn-primary text-white shadow-orange'
            : 'cursor-not-allowed bg-stone-200 text-stone-400'
          }
        `}
      >
        {isLoading ? (
          <span className="flex items-center justify-center gap-3">
            <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            Processing...
          </span>
        ) : (
          <span className="flex items-center justify-center gap-2">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            Start Analysis
          </span>
        )}
      </button>
      </div>
    </div>
  );
}
