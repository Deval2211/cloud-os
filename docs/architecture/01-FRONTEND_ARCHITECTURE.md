# Frontend Architecture

**Document**: Frontend System Design
**Version**: 1.0
**Status**: Design Phase

## Overview

The frontend is a **React-based desktop operating system** running in the browser. It provides:

1. **Desktop Environment** - Windows, taskbar, workspace management
2. **IDE Integration** - Embedded VSCode (code-server)
3. **Terminal** - xterm.js-based terminal emulator
4. **Workflow Builder** - Visual node-based programming
5. **GPU Monitor** - Real-time metrics dashboard
6. **Notification System** - Toast notifications and alerts

**Tech Stack:**
- **Framework**: Next.js 14+ (with App Router)
- **UI Library**: React 18+
- **Styling**: TailwindCSS + custom CSS
- **State Management**: Zustand
- **Real-time**: Socket.io client
- **Animations**: Framer Motion
- **HTTP Client**: TanStack Query (React Query) + Axios
- **Code Editor**: Monaco Editor / Ace
- **Terminal**: xterm.js
- **Icons**: Heroicons + custom SVGs
- **Form Handling**: React Hook Form + Zod validation

## Directory Structure

```
src/frontend/
├── app/                           # Next.js App Router
│   ├── layout.tsx                 # Root layout
│   ├── page.tsx                   # Home/landing
│   ├── dashboard/
│   │   ├── layout.tsx
│   │   ├── page.tsx               # Desktop shell
│   │   └── [workspace]/
│   │       └── page.tsx
│   └── auth/
│       ├── callback/              # OAuth callback
│       └── logout/
├── components/
│   ├── Desktop/
│   │   ├── Desktop.tsx            # Main desktop container
│   │   ├── Taskbar.tsx            # Bottom taskbar
│   │   ├── WindowManager.tsx      # Window management
│   │   ├── WorkspaceSwitcher.tsx  # Workspace selector
│   │   └── NotificationCenter.tsx
│   ├── Windows/
│   │   ├── IDEWindow.tsx          # VSCode window
│   │   ├── TerminalWindow.tsx     # Terminal window
│   │   ├── NotebookWindow.tsx     # Jupyter window
│   │   ├── WorkflowWindow.tsx     # Workflow builder
│   │   └── FileExplorerWindow.tsx
│   ├── Workflow/
│   │   ├── WorkflowCanvas.tsx     # Canvas rendering
│   │   ├── WorkflowNode.tsx       # Node component
│   │   ├── NodePalette.tsx        # Node selection
│   │   └── WorkflowProperties.tsx
│   ├── GPU/
│   │   ├── GPUMonitor.tsx         # GPU stats display
│   │   ├── GPUGauge.tsx           # Individual GPU
│   │   └── MetricsChart.tsx       # Historical charts
│   ├── Storage/
│   │   ├── StorageExplorer.tsx
│   │   └── FileBrowser.tsx
│   └── Common/
│       ├── Button.tsx
│       ├── Modal.tsx
│       ├── Sidebar.tsx
│       └── Toast.tsx
├── hooks/
│   ├── useDesktop.ts              # Desktop state
│   ├── useWorkspaces.ts           # Workspace management
│   ├── useSessions.ts             # Session state
│   ├── useGPUMetrics.ts           # GPU metrics streaming
│   ├── useWebSocket.ts            # WebSocket connection
│   ├── useTerminal.ts             # Terminal state
│   └── useWorkflow.ts             # Workflow state
├── lib/
│   ├── api.ts                     # API client
│   ├── websocket.ts               # WebSocket manager
│   ├── storage.ts                 # Local storage helper
│   ├── utils.ts                   # Utilities
│   └── window-manager.ts          # Window management logic
├── stores/
│   ├── desktopStore.ts            # Desktop Zustand store
│   ├── workspaceStore.ts
│   ├── sessionStore.ts
│   ├── workflowStore.ts
│   └── metricsStore.ts
├── types/
│   ├── index.ts
│   ├── api.ts
│   └── ui.ts
├── styles/
│   ├── globals.css
│   ├── animations.css
│   └── variables.css
└── config/
    └── constants.ts
```

## Component Architecture

### Desktop Container (Main App Shell)

```tsx
// components/Desktop/Desktop.tsx
export function Desktop() {
  return (
    <div className="desktop">
      <WindowManager />
      <Taskbar />
      <NotificationCenter />
      <WorkspaceSwitcher />
      <ContextMenus />
    </div>
  );
}
```

**Responsibilities:**
- Layout composition
- Theme management
- Route coordination
- Error boundaries

### Window Manager

```tsx
interface Window {
  id: string;
  type: 'ide' | 'terminal' | 'notebook' | 'workflow' | 'storage';
  title: string;
  position: { x: number; y: number };
  size: { width: number; height: number };
  zIndex: number;
  isMinimized: boolean;
  isMaximized: boolean;
  isDocked?: 'left' | 'right' | 'bottom';
  sessionId: string;
  state: Record<string, any>;
}

// WindowManager responsibilities:
// - Render multiple windows
// - Handle dragging/resizing
// - Manage focus/z-index
// - Persist layout state
// - Restore windows on refresh
```

**Window Features:**
- Draggable header
- Resize handles (8-directional)
- Minimize/maximize/close buttons
- Snap-to-grid positioning
- Auto-arrange when overlapping
- Persistent layout (saved to localStorage + backend)

### Taskbar

```tsx
// components/Desktop/Taskbar.tsx
export function Taskbar() {
  return (
    <div className="taskbar">
      <div className="taskbar-left">
        <AppLauncher />
        <WindowButtons />
      </div>
      <div className="taskbar-center">
        {/* Currently active workspace indicator */}
      </div>
      <div className="taskbar-right">
        <GPUMonitor />
        <SystemClock />
        <UserMenu />
      </div>
    </div>
  );
}
```

**GPU Monitor Display:**
```
RTX 4090 (GPU 0)
████████████░░ 80% VRAM
Temp: 45°C | Power: 320W

RTX 4090 (GPU 1)
██░░░░░░░░░░░░░ 15% VRAM
Temp: 38°C | Power: 50W

Active: Fine-tuning Llama 3
Status: Running 2h 45m
```

### IDE Integration (code-server)

```tsx
// components/Windows/IDEWindow.tsx
export function IDEWindow({ sessionId }: { sessionId: string }) {
  const ideUrl = `/api/v1/sessions/${sessionId}/ide`;
  
  return (
    <iframe
      src={ideUrl}
      className="ide-frame"
      sandbox="allow-same-origin allow-scripts"
    />
  );
}
```

**How it works:**
1. Backend exposes code-server on unique endpoint per session
2. Frontend embeds in iframe with proper sandbox attributes
3. WebSocket proxying for extensions/terminals in code-server
4. Session state persisted (open files, cursor position)

### Workflow Builder

```tsx
// components/Workflow/WorkflowCanvas.tsx
export function WorkflowCanvas({ workflowId }: { workflowId: string }) {
  const store = useWorkflowStore();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  
  // Canvas-based rendering (for performance)
  // or React Flow (for interactivity)
  
  return (
    <div className="workflow-builder">
      <NodePalette />
      <canvas ref={canvasRef} className="workflow-canvas" />
      <WorkflowProperties />
    </div>
  );
}
```

**Node Types:**
```
Input Nodes:
- DatasetNode: Select dataset
- ModelNode: Select model
- ImageInputNode: Upload image
- TextInputNode: Text input

Processing Nodes:
- PyTorchNode: Run Python code
- FineTuneNode: Fine-tune model
- InferenceNode: Run inference
- TransformNode: Transform data
- ScriptNode: Execute script

Output Nodes:
- SaveToStorageNode: Save results
- DeployInferenceNode: Deploy model
- NotifyNode: Send notification
- DownloadNode: Download files

Control Nodes:
- IfNode: Conditional branching
- LoopNode: Iterate over items
- ParallelNode: Run in parallel
- DelayNode: Wait/schedule
```

**Workflow Execution:**
```
1. User creates DAG of nodes
2. Click "Run" → serialize to JSON
3. POST /api/v1/workflows/{id}/run
4. Backend validates DAG
5. Celery task processes workflow
6. Emit progress updates via WebSocket
7. User sees step-by-step execution
```

### Terminal Emulator

```tsx
// components/Windows/TerminalWindow.tsx
export function TerminalWindow({ sessionId }: { sessionId: string }) {
  const terminalRef = useRef<HTMLDivElement>(null);
  const terminalRef = useRef<Terminal>();
  
  useEffect(() => {
    const term = new Terminal();
    term.open(terminalRef.current);
    
    // WebSocket connection to backend
    const ws = new WebSocket(`wss://.../terminals/${sessionId}`);
    
    term.onData(data => ws.send(data));
    ws.onmessage = msg => term.write(msg.data);
    
    return () => {
      term.dispose();
      ws.close();
    };
  }, [sessionId]);
  
  return <div ref={terminalRef} className="terminal" />;
}
```

## State Management (Zustand Stores)

### Desktop Store

```typescript
// stores/desktopStore.ts
interface DesktopState {
  // Windows
  windows: Window[];
  activeWindowId: string | null;
  addWindow: (window: Window) => void;
  removeWindow: (id: string) => void;
  focusWindow: (id: string) => void;
  updateWindow: (id: string, updates: Partial<Window>) => void;
  
  // Workspaces
  workspaces: Workspace[];
  activeWorkspaceId: string;
  switchWorkspace: (id: string) => void;
  
  // Notifications
  notifications: Notification[];
  addNotification: (notif: Notification) => void;
  removeNotification: (id: string) => void;
  
  // Theme
  theme: 'dark' | 'light';
  setTheme: (theme: 'dark' | 'light') => void;
}

export const useDesktopStore = create<DesktopState>()(
  persist(
    (set) => ({
      // Implementation
    }),
    {
      name: 'desktop-storage',
      partialize: (state) => ({
        workspaces: state.workspaces,
        activeWorkspaceId: state.activeWorkspaceId,
        theme: state.theme,
      }),
    }
  )
);
```

### Session Store

```typescript
// stores/sessionStore.ts
interface SessionState {
  sessions: Session[];
  activeSessionId: string | null;
  
  // CRUD
  createSession: (workspace: Workspace) => Promise<void>;
  getSession: (id: string) => Session | undefined;
  updateSessionMetrics: (id: string, metrics: Metrics) => void;
  terminateSession: (id: string) => Promise<void>;
  
  // Recovery
  requestCheckpoint: (sessionId: string) => Promise<void>;
  recoverSession: (sessionId: string) => Promise<void>;
}
```

### Metrics Store

```typescript
// stores/metricsStore.ts
interface MetricsState {
  metrics: Map<string, GPUMetrics[]>;
  subscribe: (sessionId: string) => void;
  unsubscribe: (sessionId: string) => void;
  addMetric: (sessionId: string, metric: GPUMetrics) => void;
  getHistoricalMetrics: (sessionId: string, range: TimeRange) => GPUMetrics[];
}
```

## Real-time Communication

### WebSocket Events

```typescript
// lib/websocket.ts
export class WebSocketManager {
  private socket: Socket;
  
  connect(token: string) {
    this.socket = io(`${BACKEND_URL}`, {
      auth: { token },
      reconnection: true,
      reconnectionDelay: 1000,
    });
    
    this.socket.on('metrics:update', (data) => {
      useMetricsStore.setState(state => ({
        metrics: new Map(state.metrics).set(data.sessionId, data.value)
      }));
    });
    
    this.socket.on('session:status', (data) => {
      useSessionStore.setState(state => ({
        sessions: state.sessions.map(s => 
          s.id === data.sessionId ? { ...s, status: data.status } : s
        )
      }));
    });
    
    this.socket.on('workflow:step_completed', (data) => {
      // Update workflow run
    });
  }
  
  emit(event: string, data: any) {
    this.socket.emit(event, data);
  }
}
```

## React Query Integration

```typescript
// lib/api.ts
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,  // 5 minutes
      gcTime: 1000 * 60 * 30,      // 30 minutes
      retry: 2,
      refetchOnWindowFocus: true,
    },
  },
});

// Custom hooks
export function useWorkspaces() {
  return useQuery({
    queryKey: ['workspaces'],
    queryFn: async () => api.get('/api/v1/workspaces'),
  });
}

export function useSessionMetrics(sessionId: string) {
  return useQuery({
    queryKey: ['metrics', sessionId],
    queryFn: async () => api.get(`/api/v1/sessions/${sessionId}/metrics`),
    refetchInterval: 1000,  // 1 second
  });
}
```

## UI/UX Design

### Visual Theme

```css
/* styles/variables.css */
:root {
  /* Colors */
  --primary: #6366f1;           /* Indigo */
  --primary-dark: #4f46e5;
  --accent: #ec4899;            /* Pink */
  --background: #0f172a;        /* Slate-900 */
  --surface: #1e293b;           /* Slate-800 */
  --surface-light: #334155;     /* Slate-700 */
  
  /* GPU Status Colors */
  --gpu-idle: #6366f1;          /* Blue */
  --gpu-medium: #f59e0b;        /* Amber */
  --gpu-high: #ef4444;          /* Red */
  
  /* Success/Warning/Error */
  --success: #10b981;
  --warning: #f59e0b;
  --error: #ef4444;
  
  /* Spacing */
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
  --spacing-xl: 2rem;
  
  /* Border Radius */
  --radius-sm: 0.375rem;
  --radius-md: 0.5rem;
  --radius-lg: 0.75rem;
  
  /* Shadows */
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
}
```

### Component Library

**Button:**
```tsx
<Button 
  variant="primary" 
  size="md"
  disabled={false}
  onClick={handleClick}
>
  Create Workspace
</Button>
```

**Modal:**
```tsx
<Modal isOpen={isOpen} onClose={onClose} title="Create Session">
  <form onSubmit={handleSubmit}>
    <Input name="workspace" />
    <Select name="provider" options={providers} />
    <Button type="submit">Create</Button>
  </form>
</Modal>
```

**Toast:**
```tsx
toast.success("Workspace created!");
toast.error("Failed to provision GPU");
toast.info("GPU session initializing...");
```

## Performance Optimization

### Code Splitting

```typescript
// Dynamic imports for large components
const WorkflowBuilder = dynamic(() => import('@/components/Workflow/WorkflowCanvas'), {
  loading: () => <LoadingSpinner />,
  ssr: false,
});
```

### Image Optimization

```tsx
import Image from 'next/image';

<Image
  src="/gpu-icon.png"
  alt="GPU"
  width={32}
  height={32}
  priority
/>
```

### Memoization

```tsx
const GPUMonitor = React.memo(function GPUMonitor({ sessionId }: { sessionId: string }) {
  // Component only re-renders if sessionId changes
});
```

## Accessibility

```tsx
// Semantic HTML
<button aria-label="Close window" onClick={handleClose}>
  ✕
</button>

// ARIA roles
<div role="tablist" aria-label="Workspace tabs">
  {/* Tab content */}
</div>

// Keyboard navigation
useEffect(() => {
  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Escape') closeWindow();
    if (e.ctrlKey && e.key === 'Tab') switchWorkspace();
  };
  
  window.addEventListener('keydown', handleKeyDown);
  return () => window.removeEventListener('keydown', handleKeyDown);
}, []);
```

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Requires WebGL 2.0 for workflow canvas

## Next Steps

- Proceed to [Backend Architecture](02-BACKEND_ARCHITECTURE.md)
- Review [Database Schema](../design/DATABASE_SCHEMA.md)
- See [API Specifications](../api/API_SPECIFICATIONS.md)
