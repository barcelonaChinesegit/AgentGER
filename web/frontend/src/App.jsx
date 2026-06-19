import { useState, useCallback } from 'react';
import ImageUpload from './components/ImageUpload';
import PipelineForm from './components/PipelineForm';
import ResultDisplay from './components/ResultDisplay';
import HistoryList from './components/HistoryList';
import { uploadImage, runPipeline, pollTaskStatus } from './api';

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

  const handleUpload = useCallback(async (file) => {
    try {
      setIsLoading(true);
      const result = await uploadImage(file);
      setUploadedImage({
        url: result.url,
        path: result.path,
        originalName: result.original_name,
      });
    } catch (error) {
      alert('上传失败: ' + error.message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleSubmit = useCallback(async () => {
    if (!uploadedImage || !summary.trim() || !pipeline) return;

    try {
      setIsLoading(true);
      setCurrentResult(null);
      setCurrentStatus('pending');
      setSelectedHistoryId(null);

      const result = await runPipeline(uploadedImage.path, summary, pipeline);
      
      // 开始轮询任务状态
      pollTaskStatus(result.record_id, (status) => {
        setCurrentStatus(status.status);
        if (status.status === 'completed' || status.status === 'failed') {
          setCurrentResult(status.result);
          setIsLoading(false);
          setRefreshTrigger(t => t + 1);
        }
      });
    } catch (error) {
      alert('执行失败: ' + error.message);
      setIsLoading(false);
      setCurrentStatus('error');
    }
  }, [uploadedImage, summary, pipeline]);

  const handleHistorySelect = useCallback((item) => {
    setSelectedHistoryId(item.id);
    setCurrentResult(item.result);
    setCurrentStatus(item.status);
    setPipeline(item.pipeline);
    setSummary(item.summary);
    // 尝试加载历史图片
    setUploadedImage({
      url: `/uploads/${item.image_filename}`,
      path: item.image_path,
      originalName: item.image_filename,
    });
  }, []);

  return (
    <div className="min-h-screen grid-bg">
      {/* 顶部导航 */}
      <header className="sticky top-0 z-50 glass border-b border-slate-700/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-xl bg-gradient-to-br from-brand-500 to-brand-700">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <div>
                <h1 className="font-display text-xl font-semibold gradient-text">图表总结评估</h1>
                <p className="text-xs text-slate-500 hidden sm:block">Figure Summary Evaluation</p>
              </div>
            </div>
            
            {/* 移动端历史记录按钮 */}
            <button
              onClick={() => setShowHistory(!showHistory)}
              className="lg:hidden p-2 rounded-lg glass-light hover:bg-slate-700/50 transition-colors"
            >
              <svg className="w-6 h-6 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </button>
          </div>
        </div>
      </header>

      {/* 主内容区 */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="lg:grid lg:grid-cols-12 lg:gap-8">
          {/* 左侧主要内容 */}
          <div className="lg:col-span-8 space-y-8">
            {/* 输入区域 */}
            <section className="glass rounded-2xl p-6 animate-fade-in">
              <div className="grid md:grid-cols-2 gap-6">
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
              </div>
            </section>

            {/* 结果展示 */}
            {(currentStatus || currentResult) && (
              <section className="animate-slide-up">
                <ResultDisplay
                  result={currentResult}
                  status={currentStatus}
                  pipeline={pipeline}
                />
              </section>
            )}
          </div>

          {/* 右侧历史记录 - 桌面端 */}
          <aside className="hidden lg:block lg:col-span-4">
            <div className="sticky top-24">
              <div className="glass rounded-2xl p-4">
                <h2 className="text-lg font-semibold text-slate-200 mb-4 flex items-center gap-2">
                  <svg className="w-5 h-5 text-brand-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  历史记录
                </h2>
                <div className="max-h-[calc(100vh-12rem)] overflow-y-auto pr-2 -mr-2">
                  <HistoryList
                    onSelect={handleHistorySelect}
                    selectedId={selectedHistoryId}
                    refreshTrigger={refreshTrigger}
                  />
                </div>
              </div>
            </div>
          </aside>
        </div>
      </main>

      {/* 移动端历史记录抽屉 */}
      {showHistory && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div 
            className="absolute inset-0 bg-slate-900/80 backdrop-blur-sm"
            onClick={() => setShowHistory(false)}
          />
          <div className="absolute right-0 top-0 bottom-0 w-80 glass border-l border-slate-700/50 animate-slide-in-right">
            <div className="p-4">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-slate-200">历史记录</h2>
                <button
                  onClick={() => setShowHistory(false)}
                  className="p-2 rounded-lg hover:bg-slate-700/50 transition-colors"
                >
                  <svg className="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 底部装饰 */}
      <div className="fixed bottom-0 left-0 right-0 h-32 pointer-events-none bg-gradient-to-t from-slate-950/50 to-transparent" />
    </div>
  );
}
