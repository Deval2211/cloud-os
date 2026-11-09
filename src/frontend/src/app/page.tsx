'use client';

import { useEffect, useState } from 'react';
import { useDesktopStore } from '@/stores/desktopStore';
import { useAuthStore } from '@/stores/authStore';
import { useSessionStore } from '@/stores/sessionStore';
import { apiClient } from '@/api/client';
import WorkspaceWindow from '@/components/workspace/WorkspaceWindow';
import DesktopTaskbar from '@/components/taskbar/DesktopTaskbar';
import AuthPage from '@/components/auth/AuthPage';
import { Window } from '@/stores/desktopStore';
import './page.css';

export default function Home() {
  const { windows, focusedWindowId, addWindow, removeWindow, focusWindow } = useDesktopStore();
  const { user, isAuthenticated, setUser, setToken } = useAuthStore();
  const { setCurrentSession } = useSessionStore();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Initialize app - check authentication
  useEffect(() => {
    const initializeApp = async () => {
      try {
        // Check if user is already authenticated
        const token = localStorage.getItem('access_token');
        if (token) {
          setToken(token);
          const response = await apiClient.getCurrentUser();
          if (response.data) {
            setUser(response.data);
          }
        }
      } catch (err) {
        console.error('Failed to initialize app:', err);
      } finally {
        setIsLoading(false);
      }
    };

    initializeApp();
  }, [setUser, setToken]);

  // Show loading screen
  if (isLoading) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner" />
        <p>Initializing Cloud OS...</p>
      </div>
    );
  }

  // Show auth page if not authenticated
  if (!isAuthenticated) {
    return (
      <div className="auth-redirect">
        <AuthPage />
      </div>
    );
  }

  // Main desktop environment
  return (
    <div className="desktop-container">
      <div className="windows-container">
        {windows.map((window) => (
          <div
            key={window.id}
            className={`window-pane ${window.isFocused ? 'focused' : ''}`}
            style={{
              left: `${window.x}px`,
              top: `${window.y}px`,
              width: `${window.width}px`,
              height: `${window.height}px`,
              '--z-index': window.isFocused ? 100 : 1,
            } as React.CSSProperties}
            onClick={() => focusWindow(window.id)}
          >
            <WorkspaceWindow
              window={window}
              onClose={() => removeWindow(window.id)}
              onFocus={() => focusWindow(window.id)}
            />
          </div>
        ))}

        {windows.length === 0 && (
          <div className="empty-desktop">
            <div className="empty-state">
              <div className="empty-icon">
                <svg
                  width="64"
                  height="64"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                >
                  <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" />
                  <polyline points="13 2 13 9 20 9" />
                </svg>
              </div>
              <h2>Welcome to Cloud OS</h2>
              <p>Open a workspace to get started</p>
            </div>
          </div>
        )}
      </div>

      <DesktopTaskbar windows={windows} onWindowClick={focusWindow} onNewWindow={addWindow} />
    </div>
  );
}
