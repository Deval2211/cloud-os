'use client';

import { useRef, useState } from 'react';
import { useDesktopStore, Window } from '@/stores/desktopStore';
import { useSessionStore } from '@/stores/sessionStore';
import { TerminalWindow } from '@/components/windows/TerminalWindow';
import { EditorWindow } from '@/components/windows/EditorWindow';
import { MetricsDashboard } from '@/components/windows/MetricsDashboard';
import { FileBrowser } from '@/components/windows/FileBrowser';
import { WorkflowBuilder } from '@/components/windows/WorkflowBuilder';
import './window.css';

interface WorkspaceWindowProps {
  window: Window;
  onClose: () => void;
  onFocus: () => void;
}

export default function WorkspaceWindow({
  window: initialWindow,
  onClose,
  onFocus,
}: WorkspaceWindowProps) {
  const updateWindow = useDesktopStore((state) => state.updateWindow);
  const currentSession = useSessionStore((state) => state.currentSession);
  const [isDragging, setIsDragging] = useState(false);
  const [isResizing, setIsResizing] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const windowRef = useRef<HTMLDivElement>(null);

  const handleMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    if ((e.target as HTMLElement).closest('.window-controls')) return;

    setIsDragging(true);
    setDragOffset({
      x: e.clientX - initialWindow.x,
      y: e.clientY - initialWindow.y,
    });
    onFocus();
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (isDragging) {
      updateWindow(initialWindow.id, {
        x: e.clientX - dragOffset.x,
        y: e.clientY - dragOffset.y,
      });
    }

    if (isResizing) {
      const newWidth = Math.max(300, e.clientX - initialWindow.x);
      const newHeight = Math.max(200, e.clientY - initialWindow.y);
      updateWindow(initialWindow.id, {
        width: newWidth,
        height: newHeight,
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
    setIsResizing(false);
  };

  const handleResizeStart = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
    onFocus();
  };

  return (
    <div
      ref={windowRef}
      className={`window ${initialWindow.isFocused ? 'focused' : ''}`}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      {/* Header */}
      <div
        className="window-header"
        onMouseDown={handleMouseDown}
        style={{ cursor: isDragging ? 'grabbing' : 'grab' }}
      >
        <div className="window-title-section">
          <span className="window-icon">
            {initialWindow.type === 'terminal' && '⌨️'}
            {initialWindow.type === 'editor' && '📝'}
            {initialWindow.type === 'workflow' && '🔄'}
            {initialWindow.type === 'workspace' && '📁'}
            {initialWindow.type === 'metrics' && '📊'}
            {initialWindow.type === 'files' && '🗂️'}
            {initialWindow.type === 'settings' && '⚙️'}
          </span>
          <h3 className="window-title">{initialWindow.title}</h3>
        </div>

        <div className="window-controls">
          <button
            className="window-button minimize"
            onClick={() =>
              updateWindow(initialWindow.id, { isMinimized: !initialWindow.isMinimized })
            }
            title="Minimize"
          >
            _
          </button>
          <button
            className="window-button maximize"
            onClick={() =>
              updateWindow(initialWindow.id, {
                x: 0,
                y: 0,
                width: window.innerWidth,
                height: window.innerHeight - 64,
              })
            }
            title="Maximize"
          >
            □
          </button>
          <button
            className="window-button close"
            onClick={onClose}
            title="Close"
          >
            ✕
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="window-content">
        {initialWindow.type === 'terminal' && (
          <TerminalWindow 
            sessionId={currentSession?.id || null}
            onClose={onClose}
          />
        )}
        {initialWindow.type === 'editor' && (
          <EditorWindow 
            filename="untitled.txt"
            onClose={onClose}
          />
        )}
        {initialWindow.type === 'metrics' && (
          <MetricsDashboard 
            sessionId={currentSession?.id || null}
            onClose={onClose}
          />
        )}
        {initialWindow.type === 'files' && (
          <FileBrowser 
            workspaceId="workspace-123"
            onClose={onClose}
          />
        )}
        {initialWindow.type === 'workflow' && (
          <WorkflowBuilder 
            onClose={onClose}
          />
        )}
        {initialWindow.type === 'workspace' && (
          <div className="placeholder-content">
            <p>Workspace Manager</p>
          </div>
        )}
        {initialWindow.type === 'settings' && (
          <div className="placeholder-content">
            <p>Settings</p>
          </div>
        )}
      </div>

      {/* Resize Handle */}
      <div
        className="window-resize-handle"
        onMouseDown={handleResizeStart}
        style={{ cursor: isResizing ? 'nwse-resize' : 'pointer' }}
      />
    </div>
  );
}
