// API Service for communicating with FastAPI backend
// ================================================

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

class ApiError extends Error {
  constructor(message, status, data) {
    super(message);
    this.status = status;
    this.data = data;
  }
}

class ApiService {
  constructor() {
    this.baseURL = API_BASE_URL;
    this.token = localStorage.getItem('token');
    this._refreshing = null; // deduplicate concurrent refresh calls
  }

  // Set authentication token
  setToken(token) {
    this.token = token;
    if (token) {
      localStorage.setItem('token', token);
    } else {
      localStorage.removeItem('token');
    }
  }

  // Get authentication token
  getToken() {
    return this.token || localStorage.getItem('token');
  }

  // Clear authentication
  clearAuth() {
    this.token = null;
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  }

  // Attempt to silently refresh an expired token.
  // Returns true if a new token was obtained, false if refresh failed.
  async _tryRefresh() {
    const token = this.getToken();
    if (!token) return false;

    // Deduplicate: if a refresh is already in flight, wait for it
    if (this._refreshing) {
      try { await this._refreshing; return true; } catch { return false; }
    }

    this._refreshing = (async () => {
      const response = await fetch(`${this.baseURL}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
      });
      if (!response.ok) throw new Error('Refresh failed');
      const data = await response.json();
      this.setToken(data.access_token);
    })();

    try {
      await this._refreshing;
      return true;
    } catch {
      this.clearAuth();
      return false;
    } finally {
      this._refreshing = null;
    }
  }

  // Make authenticated request
  async request(endpoint, options = {}, _isRetry = false) {
    const url = `${this.baseURL}${endpoint}`;
    const token = this.getToken();

    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    // Add authentication header if token exists
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, config);

      // On 401: try to refresh once, then replay
      if (response.status === 401 && !_isRetry && endpoint !== '/auth/refresh') {
        const refreshed = await this._tryRefresh();
        if (refreshed) {
          return this.request(endpoint, options, true);
        }
        // Refresh failed — redirect to login
        window.dispatchEvent(new CustomEvent('auth:expired'));
        throw new ApiError('Session expired. Please log in again.', 401, {});
      }

      // Handle 204 No Content as a special case for batch completion
      if (response.status === 204) {
        let errorData;
        try {
          const text = await response.text();
          if (text) {
            errorData = JSON.parse(text);
          } else {
            errorData = { detail: 'Batch completed - start new session' };
          }
        } catch {
          errorData = { detail: 'Batch completed - start new session' };
        }

        throw new ApiError(
          errorData.detail || 'Batch completed - start new session for next batch',
          response.status,
          { ...errorData, batchComplete: true }
        );
      }

      if (!response.ok) {
        let errorData;
        try {
          errorData = await response.json();
        } catch {
          errorData = { detail: 'Network error occurred' };
        }

        throw new ApiError(
          errorData.detail || `HTTP ${response.status}`,
          response.status,
          errorData
        );
      }

      // Handle empty responses
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        const result = await response.json();
        return result;
      }

      return null;
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      throw new ApiError('Network error occurred', 0, error);
    }
  }

  // GET request
  async get(endpoint) {
    return this.request(endpoint, { method: 'GET' });
  }

  // POST request
  async post(endpoint, data) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // PUT request
  async put(endpoint, data) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  // DELETE request
  async delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  }

  // PATCH request
  async patch(endpoint, data = null) {
    const options = { method: 'PATCH' };
    if (data) {
      options.body = JSON.stringify(data);
    }
    return this.request(endpoint, options);
  }

  // File upload
  async upload(endpoint, formData) {
    const token = this.getToken();
    const config = {
      method: 'POST',
      body: formData,
    };

    if (token) {
      config.headers = {
        Authorization: `Bearer ${token}`,
      };
    }

    const response = await fetch(`${this.baseURL}${endpoint}`, config);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Upload failed' }));
      throw new ApiError(errorData.detail, response.status, errorData);
    }

    return response.json();
  }

  // Authentication endpoints
  async register(userData) {
    const response = await this.post('/auth/register', userData);
    if (response.access_token) {
      this.setToken(response.access_token);
      localStorage.setItem('user', JSON.stringify(response.user));
    }
    return response;
  }

  async login(credentials) {
    const response = await this.post('/auth/login', credentials);
    if (response.access_token) {
      this.setToken(response.access_token);
      // Note: User data will be fetched separately by the AuthContext
    }
    return response;
  }

  async logout() {
    this.clearAuth();
  }

  async getCurrentUser() {
    try {
      return await this.get('/auth/me');
    } catch (error) {
      if (error.status === 401) {
        this.clearAuth();
      }
      throw error;
    }
  }

  // Dataset endpoints
  async getDatasets() {
    return this.get('/datasets/');
  }

  async getDataset(datasetId) {
    return this.get(`/datasets/${datasetId}`);
  }

  async createDataset(datasetData) {
    return this.post('/datasets/', datasetData);
  }

  async uploadDataset(file, metadata = {}) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('metadata', JSON.stringify(metadata));
    return this.upload('/datasets/upload', formData);
  }

  async deleteDataset(datasetId) {
    return this.delete(`/datasets/${datasetId}`);
  }

  async toggleDatasetStatus(datasetId) {
    return this.patch(`/datasets/${datasetId}/toggle`);
  }

  async getAllDatasets(includeInactive = false) {
    return this.get(`/datasets/?include_inactive=${includeInactive}`);
  }

  // Learning session endpoints
  async startSession(datasetId, forceReview = false, timerMode = 'disabled', timerDuration = 30) {
    return this.post('/sessions/start', { 
      dataset_id: datasetId,
      force_review: forceReview,
      timer_enabled: timerMode !== 'disabled',
      timer_seconds: timerDuration,
      timer_mode: timerMode
    });
  }

  async getNextFlashcard(learningSetId, forceReview = false) {
    const params = new URLSearchParams({
      learning_set_id: learningSetId,
      force_review: forceReview.toString()
    });
    return this.get(`/sessions/next?${params}`);
  }

  async submitAnswer(elementId, questionField, answerField, userAnswer, correctAnswer, isCorrect, timeSpent = null, timerExpired = false, wasTimed = false) {
    return this.post('/sessions/answer', {
      element_id: elementId,
      question_field: questionField,
      answer_field: answerField,
      user_answer: userAnswer,
      correct_answer: correctAnswer,
      is_correct: isCorrect,
      response_time_ms: timeSpent ? timeSpent * 1000 : null, // Convert seconds to milliseconds
      timer_expired: timerExpired,
      was_timed: wasTimed,
    });
  }

  async getSessionProgress(learningSetId) {
    const params = new URLSearchParams({
      learning_set_id: learningSetId
    });
    return this.get(`/sessions/progress?${params}`);
  }

  async getConfidenceStats(learningSetId) {
    return this.get(`/sessions/${learningSetId}/confidence-stats`);
  }

  async endSession(sessionId) {
    return this.post(`/sessions/${sessionId}/end`, {});
  }

  // User progress and dashboard endpoints
  async getUserProgress() {
    return this.get('/dashboard/progress');
  }

  async getUserStats() {
    return this.get('/dashboard/stats');
  }

  async getUserAchievements() {
    return this.get('/dashboard/achievements');
  }

  async getLeaderboard(datasetId = null) {
    const endpoint = datasetId ? `/dashboard/leaderboard?dataset_id=${datasetId}` : '/dashboard/leaderboard';
    return this.get(endpoint);
  }

  // Analytics endpoints
  async getProgressHistory(days = 30) {
    return this.get(`/dashboard/progress-history?days=${days}`);
  }

  async getAccuracyStats(datasetId = null) {
    const endpoint = datasetId ? `/dashboard/accuracy?dataset_id=${datasetId}` : '/dashboard/accuracy';
    return this.get(endpoint);
  }

  async getDatasetProgress() {
    return this.get('/dashboard/datasets');
  }

  async resetDatasetProgress(datasetId) {
    return this.post(`/dashboard/datasets/${datasetId}/reset`);
  }

  // Get public learning configuration for display
  async getLearningConfig() {
    return this.get('/admin/config/learning/public');
  }
}

// Create and export singleton instance
const apiService = new ApiService();
export default apiService;

// Export error class for component error handling
export { ApiError };
