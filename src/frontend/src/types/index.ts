// Authentication
export interface User {
  id: string;
  username: string;
  email: string;
  displayName: string;
  avatarUrl?: string;
  isAdmin: boolean;
  createdAt: string;
}

export interface AuthToken {
  accessToken: string;
  refreshToken: string;
  expiresIn: number;
}

// Workspace
export interface Workspace {
  id: string;
  ownerId: string;
  name: string;
  description?: string;
  config: Record<string, any>;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

// Session
export interface WorkspaceSession {
  id: string;
  workspaceId: string;
  userId: string;
  provider: string;
  providerSessionId: string;
  status: 'pending' | 'running' | 'stopped' | 'error';
  gpuType: string;
  gpuCount: number;
  memoryGb: number;
  hourlyRate: number;
  currentCost: number;
  sessionConfig: Record<string, any>;
  startedAt?: string;
  endedAt?: string;
  createdAt: string;
  updatedAt: string;
}

// Checkpoint
export interface Checkpoint {
  id: string;
  workspaceId: string;
  sessionId: string;
  checkpointType: 'auto' | 'manual' | 'critical';
  s3Path: string;
  sizeBytes: number;
  checkpointData?: Record<string, any>;
  isLatest: boolean;
  createdAt: string;
  expiresAt?: string;
}

// Workflow
export interface Workflow {
  id: string;
  workspaceId: string;
  userId: string;
  name: string;
  description?: string;
  definition: WorkflowDAGNode[];
  isActive: boolean;
  version: number;
  createdAt: string;
  updatedAt: string;
}

export interface WorkflowDAGNode {
  id: string;
  type: string;
  label: string;
  position: { x: number; y: number };
  data: Record<string, any>;
  inputs?: string[];
  outputs?: string[];
}

// Workflow Run
export interface WorkflowRun {
  id: string;
  workflowId: string;
  userId: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  executionLog: Record<string, any>;
  result?: Record<string, any>;
  errorMessage?: string;
  startedAt?: string;
  completedAt?: string;
  createdAt: string;
}

// GPU & Provider
export interface GPU {
  id: string;
  provider: string;
  name: string;
  architecture: string;
  memoryGb: number;
  computeCapability: number;
  availableCount: number;
  pricePerHour: number;
  availability: number;
}

export interface Provider {
  id: string;
  name: string;
  type: string;
  isActive: boolean;
  config: Record<string, any>;
}

// Metrics
export interface SessionMetrics {
  gpuUsage: number;
  memoryUsage: number;
  cpuUsage: number;
  temperature: number;
  networkIn: number;
  networkOut: number;
  timestamp: string;
}

// API Response
export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  meta?: {
    total?: number;
    page?: number;
    pageSize?: number;
    timestamp: string;
  };
}

// Storage
export interface StorageMount {
  id: string;
  userId: string;
  workspaceId: string;
  storageType: string;
  mountName: string;
  mountPath: string;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}
