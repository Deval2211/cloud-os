/**
 * Terminal window component for SSH/command execution
 */
'use client';

import { useEffect, useRef, useState } from 'react';
import { useTerminal } from '@/hooks/useSessions';

interface TerminalProps {
  sessionId: string | null;
  onClose?: () => void;
}

export function TerminalWindow({ sessionId, onClose }: TerminalProps) {
  const { output, history, sendCommand, clearOutput } = useTerminal(sessionId);
  const [input, setInput] = useState('');
  const [historyIndex, setHistoryIndex] = useState(-1);
  const outputRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll output to bottom
  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [output]);

  const handleCommand = (command: string) => {
    if (!command.trim()) return;
    if (!sessionId) return;

    sendCommand(command);
    setInput('');
    setHistoryIndex(-1);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      handleCommand(input);
      e.preventDefault();
    } else if (e.key === 'ArrowUp') {
      // Navigate history up
      const nextIndex = Math.min(historyIndex + 1, history.length - 1);
      if (nextIndex >= 0) {
        setHistoryIndex(nextIndex);
        setInput(history[history.length - 1 - nextIndex]);
      }
      e.preventDefault();
    } else if (e.key === 'ArrowDown') {
      // Navigate history down
      const nextIndex = historyIndex - 1;
      if (nextIndex >= 0) {
        setHistoryIndex(nextIndex);
        setInput(history[history.length - 1 - nextIndex]);
      } else if (nextIndex < 0) {
        setHistoryIndex(-1);
        setInput('');
      }
      e.preventDefault();
    } else if (e.key === 'l' && e.ctrlKey) {
      // Clear screen (Ctrl+L)
      clearOutput();
      e.preventDefault();
    }
  };

  if (!sessionId) {
    return (
      <div className="flex flex-col h-full bg-gray-950 text-gray-100 border border-gray-700 rounded">
        <div className="p-4 border-b border-gray-700 flex justify-between items-center">
          <h3 className="font-semibold">Terminal</h3>
          {onClose && (
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-200"
            >
              ✕
            </button>
          )}
        </div>
        <div className="flex-1 flex items-center justify-center">
          <div className="text-gray-500">Start a session to use terminal</div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-gray-950 text-gray-100 border border-gray-700 rounded font-mono text-sm">
      {/* Header */}
      <div className="p-3 border-b border-gray-700 flex justify-between items-center bg-gray-900">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-green-500"></div>
          <h3 className="font-semibold">Terminal</h3>
        </div>
        <div className="flex gap-2">
          <button
            onClick={clearOutput}
            title="Clear screen (Ctrl+L)"
            className="text-xs px-2 py-1 rounded bg-gray-800 hover:bg-gray-700 text-gray-300 transition"
          >
            Clear
          </button>
          {onClose && (
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-200 text-lg leading-none"
            >
              ✕
            </button>
          )}
        </div>
      </div>

      {/* Output Area */}
      <div
        ref={outputRef}
        className="flex-1 overflow-y-auto p-4 bg-gray-950 whitespace-pre-wrap break-words text-gray-300"
      >
        {output || (
          <div className="text-gray-600">
            $ Welcome to Cloud OS Terminal
            <br />$ Type commands and press Enter
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="p-3 border-t border-gray-700 bg-gray-900">
        <div className="flex items-center gap-2">
          <span className="text-green-400">$</span>
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Enter command..."
            className="flex-1 bg-transparent outline-none text-gray-100 placeholder-gray-600"
            autoFocus
          />
        </div>
      </div>

      {/* Status Bar */}
      <div className="px-3 py-1 text-xs border-t border-gray-700 bg-gray-900 text-gray-500 flex justify-between">
        <span>Commands: {history.length}</span>
        <span>Session: {sessionId.slice(0, 12)}...</span>
      </div>
    </div>
  );
}
