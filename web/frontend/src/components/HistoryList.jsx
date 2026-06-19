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
    completed: { text: '已完成', color: 'bg-emerald-500/20 text-emerald-400' },
    pending: { text: '等待中', color: 'bg-amber-500/20 text-amber-400' },
    processing: { text: '处理中', color: 'bg-blue-500/20 text-blue-400' },
    failed: { text: '失败', color: 'bg-red-500/20 text-red-400' },
  };
  
  const config = configs[status] || configs.pending;
  
  return (
    <span className={`px-2 py-0.5 text-xs rounded-full ${config.color}`}>
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
        w-full p-4 rounded-xl text-left transition-all duration-300
        ${isSelected 
          ? 'glass border-brand-500/50 glow-sm' 
          : 'glass-light hover:border-slate-500/30 border-transparent'
        }
      `}
    >
      <div className="flex items-start gap-3">
        {/* 缩略图 */}
        <div className="w-12 h-12 rounded-lg overflow-hidden bg-slate-700/50 flex-shrink-0">
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
            <span className="text-xs text-slate-500">
              {pipelineLabel}
            </span>
          </div>
          
          <p className="text-sm text-slate-300 truncate mb-1">
            {item.summary}
          </p>
          
          <div className="flex items-center justify-between">
            <span className="text-xs text-slate-500">
              {formatDate(item.created_at)}
            </span>
            {item.status === 'completed' && (
              <span className={`
                text-sm font-semibold
                ${totalScore >= 8 ? 'text-emerald-400' : 
                  totalScore >= 6 ? 'text-amber-400' : 'text-slate-400'}
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
        <div className="animate-spin w-6 h-6 border-2 border-brand-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <p className="text-red-400 text-sm">{error}</p>
        <button
          onClick={fetchHistory}
          className="mt-2 text-sm text-brand-400 hover:text-brand-300"
        >
          重试
        </button>
      </div>
    );
  }

  if (history.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-slate-800/50 mb-4">
          <svg className="w-8 h-8 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <p className="text-slate-400">暂无历史记录</p>
        <p className="text-sm text-slate-500 mt-1">开始分析后将在这里显示</p>
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
