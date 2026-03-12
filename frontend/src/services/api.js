const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  return res.json();
}

/** แปลง UTC timestamp string → "DD/MM HH:MM" UTC+7
 *  รองรับทั้ง "2026-03-11T04:04:31" (no Z) และ "2026-03-11T04:04:31Z"
 *  datetime.utcnow() ใน Python ไม่มี Z → ต้องบวก +7 เอง
 */
export function toThai(utcStr) {
  if (!utcStr) return '';
  // บังคับให้เป็น UTC โดยใส่ Z ถ้าไม่มี
  const normalized = utcStr.endsWith('Z') || utcStr.includes('+') ? utcStr : utcStr + 'Z';
  const d = new Date(normalized);
  const local = new Date(d.getTime() + 7 * 60 * 60 * 1000);
  const dd  = String(local.getUTCDate()).padStart(2, '0');
  const mm  = String(local.getUTCMonth() + 1).padStart(2, '0');
  const hh  = String(local.getUTCHours()).padStart(2, '0');
  const min = String(local.getUTCMinutes()).padStart(2, '0');
  return `${dd}/${mm} ${hh}:${min}`;
}

/** แปลง UTC ISO string → "DD/MM/YYYY HH:MM" UTC+7 (สำหรับแสดงในตาราง) */
export function toThaiLong(utcStr) {
  if (!utcStr) return '—';
  const normalized = utcStr.endsWith('Z') || utcStr.includes('+') ? utcStr : utcStr + 'Z';
  const d = new Date(normalized);
  const local = new Date(d.getTime() + 7 * 60 * 60 * 1000);
  const dd   = String(local.getUTCDate()).padStart(2, '0');
  const mm   = String(local.getUTCMonth() + 1).padStart(2, '0');
  const yyyy = local.getUTCFullYear();
  const hh   = String(local.getUTCHours()).padStart(2, '0');
  const min  = String(local.getUTCMinutes()).padStart(2, '0');
  return `${dd}/${mm}/${yyyy} ${hh}:${min}`;
}

/** แปลง array of UTC label strings "MM/DD HH:MM" (จาก backend strftime) → UTC+7 */
export function shiftLabels(labels = []) {
  return labels.map(lbl => {
    const [datePart, timePart] = (lbl || '').split(' ');
    if (!datePart || !timePart) return lbl;
    const [mon, day] = datePart.split('/');
    const [hr, min]  = timePart.split(':');
    const d = new Date(Date.UTC(2000, parseInt(mon) - 1, parseInt(day), parseInt(hr), parseInt(min)));
    const local = new Date(d.getTime() + 7 * 60 * 60 * 1000);
    const mm2 = String(local.getUTCMonth() + 1).padStart(2, '0');
    const dd2 = String(local.getUTCDate()).padStart(2, '0');
    const hh2 = String(local.getUTCHours()).padStart(2, '0');
    const min2 = String(local.getUTCMinutes()).padStart(2, '0');
    return `${mm2}/${dd2} ${hh2}:${min2}`;
  });
}

export const api = {
  // Dashboard
  getDashboard:       () => request('/api/dashboard'),
  getVisualization:   () => request('/api/visualization'),
  getPerformance:     () => request('/api/performance'),

  // Prices
  fetchPrices:        () => request('/api/prices/fetch', { method: 'POST' }),
  getGoldHistory:     (hours = 168) => request(`/api/prices/gold/history?hours=${hours}`),
  getLatestGold:      () => request('/api/prices/gold/latest'),
  getLatestOil:       () => request('/api/prices/oil/latest'),

  // Predictions
  getLatestPrediction:  () => request('/api/predictions/latest'),
  getPredictionHistory: (limit = 50) => request(`/api/predictions/history?limit=${limit}`),
  getTrades:            (limit = 100) => request(`/api/predictions/trades?limit=${limit}`),
  getTradesChart:       (limit = 100) => request(`/api/trades/chart?limit=${limit}`),
  triggerPredict:       () => request('/api/predictions/predict', { method: 'POST' }),

  // Model
  triggerTraining:    () => request('/api/model/train', { method: 'POST' }),
  getTrainingLogs:    () => request('/api/model/training-logs'),
  listModels:         () => request('/api/model/list'),
  selectModel:        (filename) => request('/api/model/select', {
    method: 'POST',
    body: JSON.stringify({ filename }),
  }),
};
