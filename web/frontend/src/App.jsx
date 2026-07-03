import { useState, useCallback, useEffect, useRef } from 'react';
import ImageUpload from './components/ImageUpload';
import PipelineForm from './components/PipelineForm';
import ResultDisplay from './components/ResultDisplay';
import HistoryList from './components/HistoryList';

const PIPELINE_STEPS = [
  { id: 'upload', name: 'Figure Parsing', shortName: 'Parse' },
  { id: 'evaluate', name: 'Summary Evaluation', shortName: 'Evaluate' },
  { id: 'refine', name: 'Guided Refinement', shortName: 'Refine' },
  { id: 'report', name: 'Report Generation', shortName: 'Report' },
];

const SAMPLE_ORIGINAL_SUMMARY = "This chart compares education efficiency across different school levels, showing how metrics like literacy, attendance, and research output vary. Overall, performance tends to be higher at the graduate level compared to primary and high school stages, with undergraduate levels showing moderate scores across most indicators.";

const DEMO_RESULT = {
  scores: {
    faithfulness: 1,
    completeness: 1,
    conciseness: 2,
    logicality: 2,
    analysis: 1,
  },
  reasons: {
    faithfulness: "The original summary hallucinates trends. It claims performance is higher at the graduate level and moderate at the undergraduate level. However, the chart in 1364.png shows that four out of five metrics are perfectly uniform across all school levels. Only Research Output actually varies.",
    completeness: "The summary fails to mention all the evaluated metrics, omits the specific values shown on the axes, and misses the glaring formatting issue (the floating-point error on the axis).",
    conciseness: "The summary is brief and efficiently structured, although its contents are factually inaccurate based on the image.",
    logicality: "The summary presents a logical, albeit entirely fabricated, progression of education levels that relies on assumed knowledge rather than the chart.",
    analysis: "The analysis relies on real-world assumptions rather than the actual visual data presented in the chart, which shows a highly unusual, symmetrical distribution for most of the plotted metrics.",
  },
  weights: {
    faithfulness: 0.35,
    completeness: 0.25,
    conciseness: 0.2,
    logicality: 0.15,
    analysis: 0.05,
  },
  improved_summary: "This radar chart evaluates five education metrics across four school levels. Notably, the chart in 1364.png contains visual and technical anomalies, such as a floating-point error on the vertical axis label ('59.400000000000006'). Contrary to typical real-world expectations, the visual data indicates that Literacy Rate, Student Attendance, Faculty Qualification, and Infrastructure Quality are identically plotted across all four school levels, forming nearly symmetrical polygons. The only metric that shows variation is Research Output, which is zero for both Primary and High School, but peaks near the maximum value of 99.0 for both Undergraduate and Graduate levels.",
  image_path: "1364.png",
  quality_level: "high",
  validation_scores: {
    faithfulness: 2,
    completeness: 2,
    conciseness: 2,
    logicality: 2,
    analysis: 2,
  },
};

const INFERENCE_TIMELINE = [
  { status: 'evaluating', delay: 1800 },
  { status: 'refining', delay: 4800 },
  { status: 'reporting', delay: 7800 },
  { status: 'completed', delay: 10400 },
];

function getActiveStep(status, uploadedImage, currentResult) {
  if (currentResult || status === 'completed') return PIPELINE_STEPS.length;
  if (status === 'reporting') return 3;
  if (status === 'refining' || status === 'processing') return 2;
  if (status === 'evaluating') return 1;
  if (status === 'parsing' || status === 'pending') return 0;
  if (uploadedImage) return 0;
  return -1;
}

function Sidebar({ showHistory, setShowHistory, onNewAnalysis, children }) {
  return (
    <aside className="hidden lg:flex fixed inset-y-0 left-0 z-40 w-64 flex-col border-r border-stone-200 bg-white/88 backdrop-blur-xl">
      <div className="flex h-full flex-col">
        <div className="px-6 pt-6 pb-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-500 text-sm font-bold text-white shadow-soft">
              A
            </div>
            <div>
              <h1 className="text-base font-bold tracking-tight text-stone-950">AgentGER</h1>
              <p className="text-xs font-medium text-stone-500">Figure Intelligence</p>
            </div>
          </div>
        </div>

        <div className="px-5 pb-5">
          <button
            type="button"
            onClick={onNewAnalysis}
            className="flex h-11 w-full items-center justify-center gap-2 rounded-lg bg-brand-500 text-sm font-semibold text-white shadow-orange transition hover:bg-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-300"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v14m7-7H5" />
            </svg>
            New Analysis
          </button>
        </div>

        <div className="border-t border-stone-100 px-5 py-4">
          <button
            type="button"
            onClick={() => setShowHistory(!showHistory)}
            className="flex w-full items-center gap-2 rounded-md px-2 py-2 text-left text-sm font-semibold text-stone-700 transition hover:bg-stone-50"
          >
            <svg className="h-4 w-4 text-stone-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7h5l2 2h11v9a2 2 0 01-2 2H5a2 2 0 01-2-2V7z" />
            </svg>
            Recent Projects
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-4 pb-5">
          {children}
        </div>

        <div className="border-t border-stone-100 px-6 py-4">
          <p className="text-xs leading-5 text-stone-500">
            Paper-aligned figure-summary evaluation workspace.
          </p>
        </div>
      </div>
    </aside>
  );
}

function ProcessStepper({ activeStep }) {
  return (
    <div className="mx-auto max-w-3xl rounded-xl border border-stone-200 bg-white/90 px-5 py-5 shadow-panel">
      <div className="grid grid-cols-4 items-start gap-2">
        {PIPELINE_STEPS.map((step, index) => {
          const isDone = activeStep >= PIPELINE_STEPS.length || index < activeStep;
          const isActive = index === activeStep && activeStep < PIPELINE_STEPS.length;
          const isFuture = index > activeStep && activeStep < PIPELINE_STEPS.length;

          return (
            <div key={step.id} className="relative flex flex-col items-center gap-2 text-center">
              {index < PIPELINE_STEPS.length - 1 && (
                <div
                  className={`absolute left-[calc(50%+1.25rem)] right-[calc(-50%+1.25rem)] top-5 h-px ${
                    isDone ? 'bg-emerald-300' : 'bg-stone-200'
                  }`}
                />
              )}
              <div
                className={`relative z-10 flex h-10 w-10 items-center justify-center rounded-full text-sm font-semibold transition ${
                  isDone
                    ? 'bg-emerald-500 text-white shadow-emerald'
                    : isActive
                      ? 'bg-brand-500 text-white shadow-orange'
                      : isFuture
                        ? 'bg-stone-100 text-stone-400'
                        : 'bg-brand-50 text-brand-600'
                }`}
              >
                {isDone ? (
                  <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.4} d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  index + 1
                )}
              </div>
              <span
                className={`hidden text-xs font-semibold sm:block ${
                  isDone ? 'text-emerald-600' : isActive ? 'text-brand-600' : 'text-stone-400'
                }`}
              >
                {step.name}
              </span>
              <span
                className={`text-[11px] font-semibold sm:hidden ${
                  isDone ? 'text-emerald-600' : isActive ? 'text-brand-600' : 'text-stone-400'
                }`}
              >
                {step.shortName}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function App() {
  const [uploadedImage, setUploadedImage] = useState(null);
  const [summary, setSummary] = useState('');
  const [pipeline, setPipeline] = useState('optimize');
  const [isLoading, setIsLoading] = useState(false);
  const [currentResult, setCurrentResult] = useState(null);
  const [currentStatus, setCurrentStatus] = useState(null);
  const [selectedHistoryId, setSelectedHistoryId] = useState(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [showHistory, setShowHistory] = useState(false);
  const [demoHistory, setDemoHistory] = useState([]);
  const inferenceTimersRef = useRef([]);
  const localImageUrlsRef = useRef([]);

  const clearInferenceTimers = useCallback(() => {
    inferenceTimersRef.current.forEach((timer) => window.clearTimeout(timer));
    inferenceTimersRef.current = [];
  }, []);

  useEffect(() => clearInferenceTimers, [clearInferenceTimers]);

  useEffect(() => () => {
    localImageUrlsRef.current.forEach((url) => URL.revokeObjectURL(url));
    localImageUrlsRef.current = [];
  }, []);

  const handleUpload = useCallback(async (file) => {
    try {
      setIsLoading(true);
      const imageUrl = URL.createObjectURL(file);
      localImageUrlsRef.current.push(imageUrl);
      setUploadedImage({
        url: imageUrl,
        path: `local:${file.name}`,
        originalName: file.name,
      });
      setSummary(SAMPLE_ORIGINAL_SUMMARY);
      setCurrentResult(null);
      setCurrentStatus(null);
      setSelectedHistoryId(null);
    } catch (error) {
      alert('Upload failed: ' + error.message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleSubmit = useCallback(async () => {
    if (!uploadedImage || !summary.trim() || !pipeline) return;

    try {
      clearInferenceTimers();
      setIsLoading(true);
      setCurrentResult(null);
      setCurrentStatus('parsing');
      setSelectedHistoryId(null);

      INFERENCE_TIMELINE.forEach(({ status, delay }) => {
        const timer = window.setTimeout(() => {
          if (status !== 'completed') {
            setCurrentStatus(status);
            return;
          }

          setCurrentStatus('completed');
          setCurrentResult(DEMO_RESULT);
          setIsLoading(false);
          setDemoHistory(items => [
            {
              id: `analysis-${Date.now()}`,
              image_path: uploadedImage.path,
              image_url: uploadedImage.url,
              image_filename: uploadedImage.originalName,
              summary: summary.trim(),
              pipeline,
              result: DEMO_RESULT,
              total_score: Object.values(DEMO_RESULT.scores).reduce((sum, score) => sum + score, 0),
              status: 'completed',
              created_at: new Date().toISOString(),
            },
            ...items,
          ]);
          setRefreshTrigger(t => t + 1);
          inferenceTimersRef.current = [];
        }, delay);

        inferenceTimersRef.current.push(timer);
      });
    } catch (error) {
      alert('Analysis failed: ' + error.message);
      setIsLoading(false);
      setCurrentStatus('error');
    }
  }, [clearInferenceTimers, uploadedImage, summary, pipeline]);

  const handleHistorySelect = useCallback((item) => {
    setSelectedHistoryId(item.id);
    setCurrentResult(item.result);
    setCurrentStatus(item.status);
    setPipeline(item.pipeline);
    setSummary(item.summary);
    setUploadedImage({
      url: item.image_url || `/uploads/${item.image_filename}`,
      path: item.image_path,
      originalName: item.image_filename,
    });
  }, []);

  const handleNewAnalysis = useCallback(() => {
    clearInferenceTimers();
    setUploadedImage(null);
    setSummary('');
    setPipeline('optimize');
    setCurrentResult(null);
    setCurrentStatus(null);
    setSelectedHistoryId(null);
    setShowHistory(false);
    setIsLoading(false);
  }, [clearInferenceTimers]);

  const activeStep = getActiveStep(currentStatus, uploadedImage, currentResult);
  const title = isLoading || currentStatus === 'pending' || currentStatus === 'processing'
    ? 'Analyzing the figure...'
    : currentResult
      ? 'Analysis report is ready'
      : 'Figure summary evaluation';

  return (
    <div className="min-h-screen app-grid-bg bg-stone-50 text-stone-900">
      <Sidebar showHistory={showHistory} setShowHistory={setShowHistory} onNewAnalysis={handleNewAnalysis}>
        <HistoryList
          onSelect={handleHistorySelect}
          selectedId={selectedHistoryId}
          refreshTrigger={refreshTrigger}
          itemsOverride={demoHistory}
        />
      </Sidebar>

      <header className="sticky top-0 z-30 border-b border-stone-200 bg-white/86 backdrop-blur-xl lg:hidden">
        <div className="flex h-16 items-center justify-between px-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-500 text-sm font-bold text-white">
              A
            </div>
            <div>
              <h1 className="text-base font-bold tracking-tight text-stone-950">AgentGER</h1>
              <p className="text-xs font-medium text-stone-500">Figure Intelligence</p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => setShowHistory(!showHistory)}
            className="rounded-lg border border-stone-200 bg-white p-2 text-stone-700 shadow-sm transition hover:bg-stone-50"
            aria-label="Open history"
          >
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </button>
        </div>
      </header>

      <main className="lg:pl-64">
        <div className="mx-auto min-h-screen max-w-6xl px-4 py-8 sm:px-6 lg:px-10">
          <section className="pt-2 text-center sm:pt-4">
            <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-brand-200 bg-brand-50 px-4 py-2 text-xs font-semibold text-brand-600">
              <span className={`h-2 w-2 rounded-full ${isLoading ? 'animate-pulse bg-brand-500' : 'bg-emerald-500'}`} />
              {isLoading ? 'Analyzing your figure' : 'Ready for figure analysis'}
            </div>
            <h2 className="text-3xl font-extrabold tracking-tight text-stone-950 sm:text-4xl">{title}</h2>
            <p className="mx-auto mt-3 max-w-2xl text-sm leading-6 text-stone-500 sm:text-base">
              Upload a chart, evaluate an existing summary, and generate an AgentGER evaluation-refinement report.
            </p>
          </section>

          <div className="mt-8">
            <ProcessStepper activeStep={activeStep} />
          </div>

          <section className="mt-8 grid gap-5 xl:grid-cols-[minmax(0,0.92fr)_minmax(420px,1.08fr)]">
            <ImageUpload
              onUpload={handleUpload}
              uploadedImage={uploadedImage}
              isLoading={isLoading}
            />
            <PipelineForm
              summary={summary}
              setSummary={setSummary}
              pipeline={pipeline}
              setPipeline={setPipeline}
              onSubmit={handleSubmit}
              isLoading={isLoading}
              uploadedImage={uploadedImage}
            />
          </section>

          {(currentStatus || currentResult) && (
            <section className="mt-6 animate-slide-up">
              <ResultDisplay
                result={currentResult}
                status={currentStatus}
                pipeline={pipeline}
              />
            </section>
          )}

          <section className="mt-6 rounded-xl border border-stone-200 bg-white/78 p-4 shadow-panel lg:hidden">
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-sm font-bold text-stone-900">Recent Projects</h3>
              <button
                onClick={() => setShowHistory(!showHistory)}
                className="text-xs font-semibold text-brand-600"
              >
                View all
              </button>
            </div>
            <HistoryList
              onSelect={handleHistorySelect}
              selectedId={selectedHistoryId}
              refreshTrigger={refreshTrigger}
              itemsOverride={demoHistory}
            />
          </section>
        </div>
      </main>

      {showHistory && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div 
            className="absolute inset-0 bg-stone-950/35 backdrop-blur-sm"
            onClick={() => setShowHistory(false)}
          />
          <div className="absolute right-0 top-0 bottom-0 w-80 border-l border-stone-200 bg-white shadow-2xl animate-slide-in-right">
            <div className="p-4">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold text-stone-950">Recent Projects</h2>
                <button
                  onClick={() => setShowHistory(false)}
                  className="p-2 rounded-lg text-stone-500 hover:bg-stone-100 transition-colors"
                  aria-label="Close history"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              <div className="max-h-[calc(100vh-8rem)] overflow-y-auto">
                <HistoryList
                  onSelect={(item) => {
                    handleHistorySelect(item);
                    setShowHistory(false);
                  }}
                  selectedId={selectedHistoryId}
                  refreshTrigger={refreshTrigger}
                  itemsOverride={demoHistory}
                />
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
