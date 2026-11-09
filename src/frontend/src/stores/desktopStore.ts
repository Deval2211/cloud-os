import { create } from 'zustand';

export interface Window {
  id: string;
  title: string;
  type: 'terminal' | 'editor' | 'workspace' | 'workflow' | 'metrics' | 'files' | 'settings';
  x: number;
  y: number;
  width: number;
  height: number;
  isMinimized: boolean;
  isFocused: boolean;
}

export interface DesktopState {
  windows: Window[];
  focusedWindowId: string | null;
  addWindow: (window: Window) => void;
  removeWindow: (id: string) => void;
  updateWindow: (id: string, updates: Partial<Window>) => void;
  focusWindow: (id: string) => void;
  minimizeWindow: (id: string) => void;
  maximizeWindow: (id: string) => void;
  closeAllWindows: () => void;
}

export const useDesktopStore = create<DesktopState>((set) => ({
  windows: [],
  focusedWindowId: null,

  addWindow: (window: Window) =>
    set((state) => ({
      windows: [...state.windows, window],
      focusedWindowId: window.id,
    })),

  removeWindow: (id: string) =>
    set((state) => ({
      windows: state.windows.filter((w) => w.id !== id),
      focusedWindowId: state.focusedWindowId === id ? null : state.focusedWindowId,
    })),

  updateWindow: (id: string, updates: Partial<Window>) =>
    set((state) => ({
      windows: state.windows.map((w) => (w.id === id ? { ...w, ...updates } : w)),
    })),

  focusWindow: (id: string) =>
    set((state) => ({
      windows: state.windows.map((w) => ({
        ...w,
        isFocused: w.id === id,
      })),
      focusedWindowId: id,
    })),

  minimizeWindow: (id: string) =>
    set((state) => ({
      windows: state.windows.map((w) =>
        w.id === id ? { ...w, isMinimized: !w.isMinimized } : w
      ),
    })),

  maximizeWindow: (id: string) =>
    set((state) => ({
      windows: state.windows.map((w) =>
        w.id === id
          ? { ...w, x: 0, y: 0, width: window.innerWidth, height: window.innerHeight }
          : w
      ),
    })),

  closeAllWindows: () =>
    set({
      windows: [],
      focusedWindowId: null,
    }),
}));
