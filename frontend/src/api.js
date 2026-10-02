/**
 * API Client & Helpers for FastAPI Backend
 * Base URL defaults to VITE_API_BASE_URL (https://ai-backend-zfq1.onrender.com)
 */

export const getApiBaseUrl = () => {
  const envUrl =
    (typeof process !== 'undefined' && process.env?.NEXT_PUBLIC_API_BASE_URL) ||
    (import.meta.env && import.meta.env.NEXT_PUBLIC_API_BASE_URL) ||
    (import.meta.env && import.meta.env.VITE_API_BASE_URL) ||
    'https://ai-backend-zfq1.onrender.com';
  return envUrl.replace(/\/$/, '');
};

export function getStoredToken() {
  if (typeof localStorage !== 'undefined') {
    return localStorage.getItem('access_token');
  }
  return null;
}

export function setAuthSession(data) {
  if (typeof localStorage !== 'undefined' && data) {
    if (data.access_token) {
      localStorage.setItem('access_token', data.access_token);
    }
    if (data.user_id) {
      localStorage.setItem('user_id', data.user_id);
    }
  }
}

export function clearAuthSession() {
  if (typeof localStorage !== 'undefined') {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_id');
  }
}

export function getAccessToken() {
  const token = getStoredToken();
  if (token) {
    return token;
  }
  if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
    window.location.href = '/login/';
  }
  throw new Error('No active session found.');
}

const buildUrl = (endpoint) => {
  if (endpoint.startsWith('http://') || endpoint.startsWith('https://')) {
    return endpoint;
  }
  const baseUrl = getApiBaseUrl();
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  return `${baseUrl}${cleanEndpoint}`;
};

/**
 * Generic API GET helper attaching Authorization Bearer header
 */
export async function apiGet(endpoint, requireAuth = true) {
  const url = buildUrl(endpoint);
  const headers = {};

  if (requireAuth) {
    const token = getAccessToken();
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(url, {
    method: 'GET',
    headers,
  });

  if (res.status === 401 || res.status === 403) {
    clearAuthSession();
    if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
      window.location.href = '/login/';
    }
    throw new Error('Unauthorized access. Please log in again.');
  }

  if (!res.ok) {
    let errorMessage = `Request failed with status ${res.status}`;
    try {
      const errorData = await res.json();
      errorMessage = errorData.detail || errorData.message || errorMessage;
    } catch (_) {}
    const err = new Error(errorMessage);
    err.status = res.status;
    throw err;
  }

  return await res.json();
}

/**
 * Generic API POST helper attaching Authorization Bearer header
 */
export async function apiPost(endpoint, body, requireAuth = true) {
  const url = buildUrl(endpoint);
  const headers = {
    'Content-Type': 'application/json',
  };

  if (requireAuth) {
    const token = getAccessToken();
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(url, {
    method: 'POST',
    headers,
    body: JSON.stringify(body || {}),
  });

  if (res.status === 401 || res.status === 403) {
    clearAuthSession();
    if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
      window.location.href = '/login/';
    }
    throw new Error('Unauthorized access. Please log in again.');
  }

  if (!res.ok) {
    let errorMessage = `Request failed with status ${res.status}`;
    try {
      const errorData = await res.json();
      errorMessage = errorData.detail || errorData.message || errorMessage;
    } catch (_) {}
    const err = new Error(errorMessage);
    err.status = res.status;
    throw err;
  }

  return await res.json();
}

/**
 * Generic API PUT helper attaching Authorization Bearer header
 */
export async function apiPut(endpoint, body, requireAuth = true) {
  const url = buildUrl(endpoint);
  const headers = {
    'Content-Type': 'application/json',
  };

  if (requireAuth) {
    const token = getAccessToken();
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(url, {
    method: 'PUT',
    headers,
    body: JSON.stringify(body || {}),
  });

  if (res.status === 401 || res.status === 403) {
    clearAuthSession();
    if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
      window.location.href = '/login/';
    }
    throw new Error('Unauthorized access. Please log in again.');
  }

  if (!res.ok) {
    let errorMessage = `Request failed with status ${res.status}`;
    try {
      const errorData = await res.json();
      errorMessage = errorData.detail || errorData.message || errorMessage;
    } catch (_) {}
    const err = new Error(errorMessage);
    err.status = res.status;
    throw err;
  }

  return await res.json();
}

/**
 * Generic API DELETE helper attaching Authorization Bearer header
 */
export async function apiDelete(endpoint, requireAuth = true) {
  const url = buildUrl(endpoint);
  const headers = {};

  if (requireAuth) {
    const token = getAccessToken();
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(url, {
    method: 'DELETE',
    headers,
  });

  if (res.status === 401 || res.status === 403) {
    clearAuthSession();
    if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login')) {
      window.location.href = '/login/';
    }
    throw new Error('Unauthorized access. Please log in again.');
  }

  if (!res.ok) {
    let errorMessage = `Request failed with status ${res.status}`;
    try {
      const errorData = await res.json();
      errorMessage = errorData.detail || errorData.message || errorMessage;
    } catch (_) {}
    const err = new Error(errorMessage);
    err.status = res.status;
    throw err;
  }

  // DELETE might not always return JSON
  try {
    return await res.json();
  } catch (err) {
    return { success: true };
  }
}

// ── Authentication Endpoints ──

export async function authSignup({ email, password }) {
  const data = await apiPost('/api/auth/signup', { email, password }, false);
  setAuthSession(data);
  return data;
}

export async function authLogin({ email, password }) {
  const data = await apiPost('/api/auth/login', { email, password }, false);
  setAuthSession(data);
  return data;
}

// ── Company Profile & Setup Endpoints ──

export async function getCompanyProfile() {
  return await apiGet('/api/company/profile');
}

export async function submitCompanyProfile(payload) {
  return await apiPost('/api/company/profile', payload);
}

export async function updateCompanyProfile(payload) {
  return await apiPut('/api/company/profile', payload);
}

export async function getSetupStatus() {
  return await apiGet('/api/company/setup-status');
}

// ── Competitors Intelligence Endpoints ──

export async function getCompetitors(status = 'active') {
  const query = status === 'all' || status === 'archived' ? `?status=${status}` : '';
  return await apiGet(`/api/competitors${query}`);
}

export async function acceptCompetitor(competitorId) {
  return await apiPost(`/api/competitors/${competitorId}/accept`, {});
}

export async function rejectCompetitor(competitorId) {
  return await apiPost(`/api/competitors/${competitorId}/reject`, {});
}

export async function addManualCompetitor({ name, website }) {
  return await apiPost('/api/competitors/manual', { name, website });
}

export async function updateCompetitor(competitorId, payload) {
  return await apiPut(`/api/competitors/${competitorId}`, payload);
}

export async function deleteCompetitor(competitorId) {
  return await apiDelete(`/api/competitors/${competitorId}`);
}

export async function researchCompetitor(competitorId) {
  return await apiPost(`/api/competitors/${competitorId}/research`, {});
}

export async function archiveCompetitor(competitorId) {
  return await apiPost(`/api/competitors/${competitorId}/archive`, {});
}

export async function restoreCompetitor(competitorId) {
  return await apiPost(`/api/competitors/${competitorId}/restore`, {});
}

// ── Phase 2: Intelligence & Strategy Endpoints ──

/**
 * GET /api/intelligence/stats
 */
export async function getIntelligenceStats() {
  return await apiGet('/api/intelligence/competitor-stats');
}

/**
 * POST /api/intelligence/check-now
 */
export async function checkNow() {
  return await apiPost('/api/intelligence/check-now', {});
}

/**
 * GET /api/intelligence/check-status
 */
export async function getCheckStatus() {
  return await apiGet('/api/intelligence/check-status');
}

/**
 * GET /api/intelligence/jobs
 */
export async function getIntelligenceJobs() {
  return await apiGet('/api/intelligence/jobs');
}

/**
 * GET /api/intelligence/feed
 * Params: { competitorId, eventType, impact, limit, offset }
 */
export async function getIntelligenceFeed(params = {}) {
  const query = new URLSearchParams();
  if (params.competitorId && params.competitorId !== 'all') {
    query.append('competitorId', params.competitorId);
  }
  if (params.eventType && params.eventType !== 'All' && params.eventType !== 'All Events') {
    query.append('eventType', params.eventType);
  }
  if (params.impact && params.impact !== 'All') {
    query.append('impact', params.impact.toUpperCase());
  }
  if (params.limit !== undefined) {
    query.append('limit', String(params.limit));
  }
  if (params.offset !== undefined) {
    query.append('offset', String(params.offset));
  }

  const queryString = query.toString();
  const endpoint = queryString ? `/api/intelligence/feed?${queryString}` : '/api/intelligence/feed';
  return await apiGet(endpoint);
}

/**
 * GET /api/intelligence/summary
 */
export async function getIntelligenceSummary() {
  return await apiGet('/api/intelligence/strategy-brief');
}

/**
 * POST /api/intelligence/generate-summary
 */
export async function generateIntelligenceSummary() {
  return await apiPost('/api/intelligence/generate-summary', {});
}

// ── Phase 3: Trends, Anomalies, and Alerts Endpoints ──

/**
 * GET /api/intelligence/alerts
 */
export async function getIntelligenceAlerts() {
  return await apiGet('/api/intelligence/alerts');
}

/**
 * GET /api/intelligence/trends
 */
export async function getIntelligenceTrends() {
  return await apiGet('/api/intelligence/trends');
}

/**
 * GET /api/intelligence/metrics/{competitorId}?days={days}
 */
export async function getIntelligenceMetrics(competitorId, days = 30) {
  return await apiGet(`/api/intelligence/metrics/${competitorId}?days=${days}`);
}

/**
 * POST /api/intelligence/anomalies/{anomalyId}/acknowledge
 */
export async function acknowledgeAnomaly(anomalyId) {
  return await apiPost(`/api/intelligence/anomalies/${anomalyId}/acknowledge`, {});
}

// ── Phase 5: Settings & Activity Endpoints ──

export async function getCompanySettings() {
  return await apiGet('/api/company/settings');
}

export async function updateCompanySettings(payload) {
  return await apiPut('/api/company/settings', payload);
}

export async function triggerRediscovery() {
  return await apiPost('/api/company/rediscovery', {});
}

export async function getCompanyActivity(limit = 20, offset = 0) {
  return await apiGet(`/api/company/activity?limit=${limit}&offset=${offset}`);
}

// ── Phase 6: Action Center & Tasks Endpoints ──

export async function getTaskStats() {
  return await apiGet('/api/tasks/stats/summary');
}

export async function getTasks(params = {}) {
  const query = new URLSearchParams();
  if (params.status && params.status !== 'All Active') query.append('status', params.status);
  if (params.priority && params.priority !== 'All Priorities') query.append('priority', params.priority.toUpperCase());
  if (params.source && params.source !== 'All') query.append('source', params.source === 'AI Generated' ? 'AI_GENERATED' : 'MANUAL');
  if (params.competitor && params.competitor !== 'All Competitors') query.append('competitor', params.competitor);
  
  const queryString = query.toString();
  const endpoint = queryString ? `/api/tasks?${queryString}` : '/api/tasks';
  return await apiGet(endpoint);
}

export async function createTask(payload) {
  return await apiPost('/api/tasks', payload);
}

export async function updateTask(id, payload) {
  return await apiPut(`/api/tasks/${id}`, payload);
}

export async function updateTaskStatus(id, status) {
  return await apiPost(`/api/tasks/${id}/status`, { status });
}

export async function getJiraLink(id) {
  return await apiGet(`/api/tasks/${id}/jira-link`);
}

export async function deleteTask(id) {
  return await apiDelete(`/api/tasks/${id}`);
}
