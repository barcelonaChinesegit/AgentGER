/**
 * API 接口封装
 */

const API_BASE = '/api';

/**
 * 上传图片
 */
export async function uploadImage(file) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '上传失败');
  }

  return response.json();
}

/**
 * 运行 Pipeline
 */
export async function runPipeline(imagePath, summary, pipeline) {
  const formData = new FormData();
  formData.append('image_path', imagePath);
  formData.append('summary', summary);
  formData.append('pipeline', pipeline);

  const response = await fetch(`${API_BASE}/run`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '运行失败');
  }

  return response.json();
}

/**
 * 获取任务状态
 */
export async function getTaskStatus(recordId) {
  const response = await fetch(`${API_BASE}/status/${recordId}`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '获取状态失败');
  }

  return response.json();
}

/**
 * 获取历史记录列表
 */
export async function getHistory(limit = 50, offset = 0) {
  const response = await fetch(`${API_BASE}/history?limit=${limit}&offset=${offset}`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '获取历史记录失败');
  }

  return response.json();
}

/**
 * 获取单条记录详情
 */
export async function getHistoryDetail(recordId) {
  const response = await fetch(`${API_BASE}/history/${recordId}`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '获取记录详情失败');
  }

  return response.json();
}

/**
 * 轮询任务状态直到完成
 */
export function pollTaskStatus(recordId, onUpdate, interval = 2000) {
  const poll = async () => {
    try {
      const status = await getTaskStatus(recordId);
      onUpdate(status);

      if (status.status === 'pending' || status.status === 'processing') {
        setTimeout(poll, interval);
      }
    } catch (error) {
      onUpdate({ status: 'error', error: error.message });
    }
  };

  poll();
}

