import axios from 'axios';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/auth';
    }
    return Promise.reject(error);
  }
);

// ============================================================================
// Auth API
// ============================================================================

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  username: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    username: string;
  };
}

export interface UserResponse {
  id: string;
  email: string;
  username: string;
  created_at: string;
  updated_at: string;
}

export const authApi = {
  login: async (data: LoginRequest): Promise<AuthResponse> => {
    const response = await api.post('/auth/login', data);
    return response.data;
  },

  register: async (data: RegisterRequest): Promise<AuthResponse> => {
    const response = await api.post('/auth/register', data);
    return response.data;
  },

  getCurrentUser: async (): Promise<UserResponse> => {
    const response = await api.get('/auth/me');
    return response.data;
  },

  logout: () => {
    localStorage.removeItem('token');
  },
};

// ============================================================================
// Projects API
// ============================================================================

export interface Project {
  id: string;
  name: string;
  description?: string;
  requirements?: string;
  repository_url?: string;
  status: string;
  progress: number;
  workspace_path?: string;
  created_at: string;
  updated_at: string;
  owner_id: string;
}

export interface CreateProjectRequest {
  name: string;
  description?: string;
  requirements?: string;
  repository_url?: string;
}

export interface ProjectListResponse {
  projects: Project[];
  total: number;
  page: number;
  page_size: number;
}

export interface ExecuteWorkflowRequest {
  prompt: string;
  execution_type?: 'full' | 'incremental';
}

export interface ExecuteWorkflowResponse {
  message: string;
  project_id: string;
  execution_type: string;
  status: string;
}

export const projectsApi = {
  getProjects: async (params?: {
    page?: number;
    page_size?: number;
    status?: string;
    search?: string;
  }): Promise<ProjectListResponse> => {
    const response = await api.get('/projects', { params });
    return response.data;
  },

  createProject: async (data: CreateProjectRequest): Promise<Project> => {
    const response = await api.post('/projects', data);
    return response.data;
  },

  getProject: async (projectId: string): Promise<Project> => {
    const response = await api.get(`/projects/${projectId}`);
    return response.data;
  },

  updateProject: async (
    projectId: string,
    data: Partial<CreateProjectRequest>
  ): Promise<Project> => {
    const response = await api.patch(`/projects/${projectId}`, data);
    return response.data;
  },

  deleteProject: async (projectId: string): Promise<void> => {
    await api.delete(`/projects/${projectId}`);
  },

  executeWorkflow: async (
    projectId: string,
    data: ExecuteWorkflowRequest
  ): Promise<ExecuteWorkflowResponse> => {
    const response = await api.post(
      `/projects/${projectId}/execute`,
      {},
      { params: data }
    );
    return response.data;
  },
};

// ============================================================================
// Agents API
// ============================================================================

export interface AgentConfig {
  id: string;
  agent_role: string;
  agent_name?: string;
  llm_provider: string;
  llm_model: string;
  temperature: number;
  max_tokens: number;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateAgentConfigRequest {
  agent_role: string;
  llm_provider: string;
  llm_model: string;
  temperature?: number;
  max_tokens?: number;
  api_key?: string;
  organization?: string;
  endpoint?: string;
  deployment_name?: string;
  api_version?: string;
}

export interface AgentConfigListResponse {
  configs: AgentConfig[];
  total: number;
}

export const agentsApi = {
  getAgentConfigs: async (params?: {
    agent_role?: string;
    active_only?: boolean;
  }): Promise<AgentConfigListResponse> => {
    const response = await api.get('/agents/config', { params });
    return response.data;
  },

  createAgentConfig: async (
    data: CreateAgentConfigRequest
  ): Promise<AgentConfig> => {
    const response = await api.post('/agents/config', data);
    return response.data;
  },

  getAgentConfig: async (configId: string): Promise<AgentConfig> => {
    const response = await api.get(`/agents/config/${configId}`);
    return response.data;
  },

  updateAgentConfig: async (
    configId: string,
    data: Partial<CreateAgentConfigRequest>
  ): Promise<AgentConfig> => {
    const response = await api.put(`/agents/config/${configId}`, data);
    return response.data;
  },

  deleteAgentConfig: async (configId: string): Promise<void> => {
    await api.delete(`/agents/config/${configId}`);
  },

  setDefaultConfig: async (configId: string): Promise<AgentConfig> => {
    const response = await api.post(`/agents/config/${configId}/set-default`);
    return response.data;
  },
};

// ============================================================================
// WebSocket Events
// ============================================================================

export interface WebSocketEvent {
  event_type: string;
  data: any;
  timestamp: string;
  source: string;
  execution_id?: string;
  project_id?: string;
}

export interface AgentMessageEvent extends WebSocketEvent {
  event_type: 'agent_message';
  data: {
    agent: string;
    content: string;
  };
}

export interface ExecutionStartEvent extends WebSocketEvent {
  event_type: 'execution_start';
  data: {
    execution_id: string;
    agents_count: number;
  };
}

export interface ExecutionCompleteEvent extends WebSocketEvent {
  event_type: 'execution_complete';
  data: {
    execution_id: string;
    status: string;
    output: any;
  };
}

export interface StageStartEvent extends WebSocketEvent {
  event_type: 'stage_start';
  data: {
    stage: string;
    agent: string;
  };
}

export interface FileCreatedEvent extends WebSocketEvent {
  event_type: 'file_created';
  data: {
    file_path: string;
    size: number;
  };
}

export interface ErrorEvent extends WebSocketEvent {
  event_type: 'error';
  data: {
    error_message: string;
    error_type: string;
  };
}

export type WorkflowEvent =
  | AgentMessageEvent
  | ExecutionStartEvent
  | ExecutionCompleteEvent
  | StageStartEvent
  | FileCreatedEvent
  | ErrorEvent;

export default api;
