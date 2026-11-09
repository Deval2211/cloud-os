import axios, { AxiosInstance, AxiosError, AxiosResponse } from 'axios';
import { useAuthStore } from '@/stores/authStore';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  meta?: Record<string, any>;
}

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: `${API_BASE_URL}/api/v1`,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor - add auth token
    this.client.interceptors.request.use((config) => {
      const token = useAuthStore.getState().token;
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Response interceptor - handle errors
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Token expired - attempt refresh
          try {
            const refreshToken = useAuthStore.getState().refreshToken;
            if (refreshToken) {
              const response = await axios.post(
                `${API_BASE_URL}/api/v1/auth/refresh`,
                { refreshToken }
              );
              const { token } = response.data;
              useAuthStore.getState().setToken(token);
              
              // Retry original request
              if (error.config) {
                return this.client(error.config);
              }
            }
          } catch {
            // Refresh failed - logout user
            useAuthStore.getState().logout();
          }
        }
        return Promise.reject(error);
      }
    );
  }

  // Auth endpoints
  async getGithubAuthUrl(): Promise<ApiResponse<{ url: string; state: string }>> {
    return this.client.get('/auth/github');
  }

  async githubCallback(code: string, state: string): Promise<ApiResponse> {
    return this.client.post('/auth/github/callback', { code, state });
  }

  async getCurrentUser(): Promise<ApiResponse> {
    return this.client.get('/auth/me');
  }

  async logout(): Promise<void> {
    await this.client.post('/auth/logout');
  }

  // Workspace endpoints
  async getWorkspaces(): Promise<ApiResponse> {
    return this.client.get('/workspaces');
  }

  async createWorkspace(name: string, description?: string): Promise<ApiResponse> {
    return this.client.post('/workspaces', { name, description });
  }

  async getWorkspace(id: string): Promise<ApiResponse> {
    return this.client.get(`/workspaces/${id}`);
  }

  async updateWorkspace(id: string, data: Record<string, any>): Promise<ApiResponse> {
    return this.client.patch(`/workspaces/${id}`, data);
  }

  async deleteWorkspace(id: string): Promise<void> {
    await this.client.delete(`/workspaces/${id}`);
  }

  // Session endpoints
  async startSession(
    workspaceId: string,
    config: Record<string, any>
  ): Promise<ApiResponse> {
    return this.client.post(`/workspaces/${workspaceId}/sessions`, config);
  }

  async getSessions(workspaceId: string): Promise<ApiResponse> {
    return this.client.get(`/workspaces/${workspaceId}/sessions`);
  }

  async getSession(workspaceId: string, sessionId: string): Promise<ApiResponse> {
    return this.client.get(`/workspaces/${workspaceId}/sessions/${sessionId}`);
  }

  async stopSession(workspaceId: string, sessionId: string): Promise<void> {
    await this.client.post(`/workspaces/${workspaceId}/sessions/${sessionId}/stop`);
  }

  async getSessionLogs(workspaceId: string, sessionId: string, lines?: number): Promise<ApiResponse> {
    const params = lines ? `?lines=${lines}` : '';
    return this.client.get(`/workspaces/${workspaceId}/sessions/${sessionId}/logs${params}`);
  }

  // Workflow endpoints
  async getWorkflows(workspaceId: string): Promise<ApiResponse> {
    return this.client.get(`/workflows?workspace_id=${workspaceId}`);
  }

  async createWorkflow(
    workspaceId: string,
    name: string,
    definition: Record<string, any>
  ): Promise<ApiResponse> {
    return this.client.post('/workflows', {
      workspaceId,
      name,
      definition,
    });
  }

  async executeWorkflow(workflowId: string): Promise<ApiResponse> {
    return this.client.post(`/workflows/${workflowId}/execute`);
  }

  // Provider endpoints
  async getProviders(): Promise<ApiResponse> {
    return this.client.get('/providers');
  }

  async getProviderCredentials(provider: string): Promise<ApiResponse> {
    return this.client.get(`/providers/${provider}/credentials`);
  }

  async setProviderCredentials(
    provider: string,
    credentials: Record<string, any>
  ): Promise<ApiResponse> {
    return this.client.post(`/providers/${provider}/credentials`, credentials);
  }

  async getAvailableGPUs(provider?: string): Promise<ApiResponse> {
    const params = provider ? `?provider=${provider}` : '';
    return this.client.get(`/providers/gpus${params}`);
  }

  // Storage endpoints
  async uploadFile(workspaceId: string, file: File): Promise<ApiResponse> {
    const formData = new FormData();
    formData.append('file', file);
    return this.client.post(
      `/storage/upload?workspace_id=${workspaceId}`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
  }

  async downloadFile(fileId: string): Promise<Blob> {
    const response = await this.client.get(`/storage/download/${fileId}`, {
      responseType: 'blob',
    });
    return response.data;
  }

  // Metrics endpoints
  async getSessionMetrics(sessionId: string, timeRange?: string): Promise<ApiResponse> {
    const params = timeRange ? `?time_range=${timeRange}` : '';
    return this.client.get(`/metrics/session/${sessionId}${params}`);
  }

  // Health check
  async health(): Promise<ApiResponse> {
    return this.client.get('/health', { baseURL: API_BASE_URL });
  }
}

export const apiClient = new ApiClient();
