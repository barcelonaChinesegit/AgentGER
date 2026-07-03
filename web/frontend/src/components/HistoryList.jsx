import { useState, useEffect } from 'react';
import { getHistory } from '../api';

function formatDate(dateString) {
  if (!dateString) return '';
  let dateStr = dateString;
  if (!dateStr.includes('Z') && !dateStr.includes('+')) {
    dateStr = dateStr.replace(' ', 'T') + 'Z';
  }
  const date = new Date(dateStr);
  const now = new Date();
  const diff = now - date;
  
  if (diff < 0) return 'Just now';
  
  if (diff < 60000) return 'Just now';
  if (diff < 3600000) return `${Math.floor(diff / 60000)} min ago`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} hr ago`;
  if (diff < 604800000) return `${Math.floor(diff / 86400000)} days ago`;
  
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function StatusBadge({ status }) {
  const configs = {
    completed: { text: 'Completed', color: 'bg-emerald-50 text-emerald-600 border-emerald-100' },
    pending: { text: 'Pending', color: 'bg-amber-50 text-amber-600 border-amber-100' },
    processing: { text: 'Processing', color: 'bg-sky-50 text-sky-600 border-sky-100' },
    failed: { text: 'Failed', color: 'bg-red-50 text-red-600 border-red-100' },
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
            src={item.image_url || `/uploads/${item.image_filename}`}
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

export default function HistoryList({ onSelect, selectedId, refreshTrigger, itemsOverride = null }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const displayHistory = itemsOverride || history;

  const fetchHistory = async () => {
    if (itemsOverride) {
      setLoading(false);
      setError(null);
      return;
    }

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
  }, [refreshTrigger, itemsOverride]);

  useEffect(() => {
    if (itemsOverride) return undefined;

    const interval = setInterval(fetchHistory, 10000);
    return () => clearInterval(interval);
  }, [itemsOverride]);

  if (loading && displayHistory.length === 0) {
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
          Retry
        </button>
      </div>
    );
  }

  if (displayHistory.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="mb-4 inline-flex h-14 w-14 items-center justify-center rounded-full bg-stone-100">
          <svg className="h-7 w-7 text-stone-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <p className="font-semibold text-stone-500">No history yet</p>
        <p className="mt-1 text-sm text-stone-400">Analyses will appear here after you run them</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {displayHistory.map((item) => (
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
