import { useState, useEffect } from 'react';
import { getHistory } from '../api';

function formatDate(dateString) {
  if (!dateString) return '';
  // 处理时区问题 - 数据库存储的是 UTC 时间，需要转换为本地时间
  // 如果字符串不包含时区信息，添加 UTC 标记
  let dateStr = dateString;
  if (!dateStr.includes('Z') && !dateStr.includes('+')) {
    dateStr = dateStr.replace(' ', 'T') + 'Z';
  }
  const date = new Date(dateStr);
  const now = new Date();
  const diff = now - date;
  
  // 处理负数差值（未来时间或时区问题）
  if (diff < 0) return '刚刚';
  
  if (diff < 60000) return '刚刚';
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`;
  if (diff < 604800000) return `${Math.floor(diff / 86400000)} 天前`;
  
  return date.toLocaleDateString('zh-CN', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function StatusBadge({ status }) {
  const configs = {
    completed: { text: '已完成', color: 'bg-emerald-50 text-emerald-600 border-emerald-100' },
    pending: { text: '等待中', color: 'bg-amber-50 text-amber-600 border-amber-100' },
    processing: { text: '处理中', color: 'bg-sky-50 text-sky-600 border-sky-100' },
    failed: { text: '失败', color: 'bg-red-50 text-red-600 border-red-100' },
  };
  
  const config = configs[status] || configs.pending;
  
  return (
    <span className={`rounded-full border px-2 py-0.5 text-[11px] font-bold ${config.color}`}>
      {config.text}
    </span>
  );
}

function HistoryItem({ item, isSelected, onClick }) {
  const totalScore = item.total_score || 0;
  const pipelineLabel = item.pipeline === 'optimize' || item.pipeline === 'pipeline2' ? 'Ref' : 'Eva';
  
  return (
    <button
      onClick={onClick}
      className={`
        w-full rounded-lg border p-3 text-left transition-all duration-300
        ${isSelected 
          ? 'border-brand-300 bg-brand-50/75 shadow-sm'
          : 'border-stone-200 bg-white hover:border-stone-300 hover:bg-stone-50'
        }
      `}
    >
      <div className="flex items-start gap-3">
        <div className="h-12 w-12 flex-shrink-0 overflow-hidden rounded-lg border border-stone-200 bg-stone-100">
          <img
            src={`/uploads/${item.image_filename}`}
            alt=""
            className="w-full h-full object-cover"
            onError={(e) => {
              e.target.style.display = 'none';
            }}
          />
        </div>
        
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <StatusBadge status={item.status} />
            <span className="text-xs font-bold text-stone-400">
              {pipelineLabel}
            </span>
          </div>
          
          <p className="mb-1 truncate text-sm font-semibold text-stone-800">
            {item.summary}
          </p>
          
          <div className="flex items-center justify-between">
            <span className="text-xs text-stone-400">
              {formatDate(item.created_at)}
            </span>
            {item.status === 'completed' && (
              <span className={`
                text-sm font-extrabold
                ${totalScore >= 8 ? 'text-emerald-600' :
                  totalScore >= 6 ? 'text-amber-600' : 'text-stone-500'}
              `}>
                {totalScore.toFixed(1)}
              </span>
            )}
          </div>
        </div>
      </div>
    </button>
  );
}

export default function HistoryList({ onSelect, selectedId, refreshTrigger }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      const data = await getHistory(50, 0);
      setHistory(data.items);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, [refreshTrigger]);

  // 自动刷新（每10秒）
  useEffect(() => {
    const interval = setInterval(fetchHistory, 10000);
    return () => clearInterval(interval);
  }, []);

  if (loading && history.length === 0) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-brand-500 border-t-transparent" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <p className="text-sm text-red-600">{error}</p>
        <button
          onClick={fetchHistory}
          className="mt-2 text-sm font-bold text-brand-600 hover:text-brand-700"
        >
          重试
        </button>
      </div>
    );
  }

  if (history.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="mb-4 inline-flex h-14 w-14 items-center justify-center rounded-full bg-stone-100">
          <svg className="h-7 w-7 text-stone-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <p className="font-semibold text-stone-500">暂无历史记录</p>
        <p className="mt-1 text-sm text-stone-400">开始分析后将在这里显示</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {history.map((item) => (
        <HistoryItem
          key={item.id}
          item={item}
          isSelected={selectedId === item.id}
          onClick={() => onSelect(item)}
        />
      ))}
    </div>
  );
}
