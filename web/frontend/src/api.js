/**
 * API helpers
 */

const API_BASE = '/api';

/**
 * Upload image
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
    throw new Error(error.detail || 'Upload failed');
  }

  return response.json();
}

/**
 * Run pipeline
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
    throw new Error(error.detail || 'Run failed');
  }

  return response.json();
}

/**
 * Get task status
 */
export async function getTaskStatus(recordId) {
  const response = await fetch(`${API_BASE}/status/${recordId}`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to get task status');
  }

  return response.json();
}

/**
 * Get history list
 */
export async function getHistory(limit = 50, offset = 0) {
  const response = await fetch(`${API_BASE}/history?limit=${limit}&offset=${offset}`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to get history');
  }

  return response.json();
}

/**
 * Get history detail
 */
export async function getHistoryDetail(recordId) {
  const response = await fetch(`${API_BASE}/history/${recordId}`);

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to get history detail');
  }

  return response.json();
}

/**
 * Poll task status until completion
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
