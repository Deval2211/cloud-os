'use client';

import { useState } from 'react';
import { Window } from '@/stores/desktopStore';
import './taskbar.css';

interface DesktopTaskbarProps {
  windows: Window[];
  onWindowClick: (id: string) => void;
  onNewWindow: (window: Window) => void;
}

export default function DesktopTaskbar({
  windows,
  onWindowClick,
  onNewWindow,
}: DesktopTaskbarProps) {
  const [showMenu, setShowMenu] = useState(false);

  const addNewWindow = (type: Window['type']) => {
    const titleMap: Record<Window['type'], string> = {
      terminal: 'Terminal',
      editor: 'Code Editor',
      workflow: 'Workflow Canvas',
      workspace: 'Workspace',
      metrics: 'Metrics Dashboard',
      files: 'File Browser',
      settings: 'Settings',
    };

    const newWindow: Window = {
      id: `window-${Date.now()}`,
      title: titleMap[type],
      type,
      x: 100 + Math.random() * 200,
      y: 100 + Math.random() * 200,
      width: 800,
      height: 600,
      isMinimized: false,
      isFocused: true,
    };
    onNewWindow(newWindow);
    setShowMenu(false);
  };

  return (
    <div className="taskbar-container">
      <div className="taskbar-content">
        <div className="taskbar-left">
          <div className="taskbar-app-menu">
            <button
              className="app-menu-button"
              onClick={() => setShowMenu(!showMenu)}
              title="Applications"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <rect x="3" y="3" width="4" height="4" />
                <rect x="10" y="3" width="4" height="4" />
                <rect x="17" y="3" width="4" height="4" />
                <rect x="3" y="10" width="4" height="4" />
                <rect x="10" y="10" width="4" height="4" />
                <rect x="17" y="10" width="4" height="4" />
                <rect x="3" y="17" width="4" height="4" />
                <rect x="10" y="17" width="4" height="4" />
                <rect x="17" y="17" width="4" height="4" />
              </svg>
            </button>

            {showMenu && (
              <div className="app-menu-dropdown">
                <button onClick={() => addNewWindow('workspace')}>
                  📁 Workspace
                </button>
                <button onClick={() => addNewWindow('editor')}>
                  📝 Code Editor
                </button>
                <button onClick={() => addNewWindow('terminal')}>
                  ⌨️ Terminal
                </button>
                <button onClick={() => addNewWindow('metrics')}>
                  📊 Metrics
                </button>
                <button onClick={() => addNewWindow('files')}>
                  🗂️ Files
                </button>
                <button onClick={() => addNewWindow('workflow')}>
                  🔄 Workflow
                </button>
              </div>
            )}
          </div>
        </div>

        <div className="taskbar-center">
          {windows.length > 0 && (
            <div className="taskbar-windows">
              {windows.map((window) => (
                <button
                  key={window.id}
                  className={`taskbar-item ${window.isFocused ? 'active' : ''}`}
                  onClick={() => onWindowClick(window.id)}
                  title={window.title}
                >
                  <span className="taskbar-item-icon">
                    {window.type === 'terminal' && '⌨️'}
                    {window.type === 'editor' && '📝'}
                    {window.type === 'workflow' && '🔄'}
                    {window.type === 'workspace' && '📁'}
                    {window.type === 'metrics' && '📊'}
                    {window.type === 'files' && '🗂️'}
                    {window.type === 'settings' && '⚙️'}
                  </span>
                  <span className="taskbar-item-label">{window.title}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="taskbar-right">
          <div className="taskbar-stats">
            <div className="stat-item">
              <span className="stat-label">GPU</span>
              <span className="stat-value">0%</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Memory</span>
              <span className="stat-value">0GB</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Cost</span>
              <span className="stat-value">$0.00</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
