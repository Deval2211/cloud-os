/**
 * File browser component for workspace file navigation
 */
'use client';

import { useState } from 'react';

interface FileItem {
  name: string;
  type: 'file' | 'directory';
  size?: number;
  modified?: string;
}

interface FileBrowserProps {
  workspaceId: string;
  onSelectFile?: (path: string) => void;
  onClose?: () => void;
}

export function FileBrowser({ workspaceId, onSelectFile, onClose }: FileBrowserProps) {
  const [currentPath, setCurrentPath] = useState('/');
  const [expandedDirs, setExpandedDirs] = useState<Set<string>>(new Set(['/']));
  const [selectedFile, setSelectedFile] = useState<string | null>(null);

  // Mock file structure - in real app, would fetch from backend
  const mockFileStructure: Record<string, FileItem[]> = {
    '/': [
      { name: 'src', type: 'directory' },
      { name: 'README.md', type: 'file', size: 1024, modified: '2024-01-15' },
      { name: 'requirements.txt', type: 'file', size: 256, modified: '2024-01-15' },
    ],
    '/src': [
      { name: 'main.py', type: 'file', size: 2048, modified: '2024-01-15' },
      { name: 'utils', type: 'directory' },
      { name: 'models.py', type: 'file', size: 4096, modified: '2024-01-14' },
    ],
    '/src/utils': [
      { name: 'helpers.py', type: 'file', size: 1024, modified: '2024-01-15' },
      { name: 'validators.py', type: 'file', size: 1536, modified: '2024-01-14' },
    ],
  };

  const files = mockFileStructure[currentPath] || [];

  const toggleDirectory = (dirPath: string) => {
    const newExpanded = new Set(expandedDirs);
    if (newExpanded.has(dirPath)) {
      newExpanded.delete(dirPath);
    } else {
      newExpanded.add(dirPath);
    }
    setExpandedDirs(newExpanded);
  };

  const navigateTo = (path: string) => {
    setCurrentPath(path);
    setSelectedFile(null);
  };

  const handleFileSelect = (fileName: string) => {
    const filePath = currentPath === '/' ? `/${fileName}` : `${currentPath}/${fileName}`;
    setSelectedFile(filePath);
    if (onSelectFile) {
      onSelectFile(filePath);
    }
  };

  const formatSize = (bytes?: number) => {
    if (!bytes) return '-';
    if (bytes < 1024) return `${bytes}B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)}MB`;
  };

  const breadcrumbs = currentPath.split('/').filter(Boolean);

  return (
    <div className="flex flex-col h-full bg-gray-950 text-gray-100 border border-gray-700 rounded">
      {/* Header */}
      <div className="p-3 border-b border-gray-700 bg-gray-900 flex justify-between items-center">
        <h3 className="font-semibold">Files</h3>
        {onClose && (
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-200 text-lg leading-none"
          >
            ✕
          </button>
        )}
      </div>

      {/* Breadcrumb */}
      <div className="px-3 py-2 border-b border-gray-800 bg-gray-900 text-xs text-gray-400 flex items-center gap-1 overflow-x-auto">
        <button
          onClick={() => navigateTo('/')}
          className="hover:text-gray-300 whitespace-nowrap"
        >
          /
        </button>
        {breadcrumbs.map((crumb, idx) => {
          const path = '/' + breadcrumbs.slice(0, idx + 1).join('/');
          return (
            <div key={path} className="flex items-center gap-1">
              <span className="text-gray-700">/</span>
              <button
                onClick={() => navigateTo(path)}
                className="hover:text-gray-300 whitespace-nowrap"
              >
                {crumb}
              </button>
            </div>
          );
        })}
      </div>

      {/* File List */}
      <div className="flex-1 overflow-y-auto">
        {files.length === 0 ? (
          <div className="p-4 text-center text-gray-500">
            Empty directory
          </div>
        ) : (
          <div>
            {/* Parent Directory */}
            {currentPath !== '/' && (
              <button
                onClick={() => {
                  const parent = currentPath.substring(0, currentPath.lastIndexOf('/')) || '/';
                  navigateTo(parent);
                }}
                className="w-full px-3 py-2 text-left text-gray-400 hover:bg-gray-800 flex items-center gap-2 text-sm"
              >
                <span className="text-gray-600">📁</span>
                <span>..</span>
              </button>
            )}

            {/* Files and Directories */}
            {files.map((file) => {
              const fullPath = currentPath === '/' ? `/${file.name}` : `${currentPath}/${file.name}`;
              const isDirectory = file.type === 'directory';
              const isExpanded = expandedDirs.has(fullPath);

              return (
                <div key={file.name}>
                  <button
                    onClick={() => {
                      if (isDirectory) {
                        toggleDirectory(fullPath);
                      } else {
                        handleFileSelect(file.name);
                      }
                    }}
                    className={`w-full px-3 py-2 text-left flex items-center gap-2 text-sm transition-colors ${
                      selectedFile === fullPath
                        ? 'bg-sky-950 text-sky-200'
                        : 'text-gray-300 hover:bg-gray-800'
                    }`}
                  >
                    {isDirectory ? (
                      <>
                        <span className="text-gray-600 w-4 text-center">
                          {isExpanded ? '▼' : '▶'}
                        </span>
                        <span>📁</span>
                      </>
                    ) : (
                      <>
                        <span className="w-4"></span>
                        <span>📄</span>
                      </>
                    )}
                    <span className="flex-1">{file.name}</span>
                    {!isDirectory && (
                      <span className="text-xs text-gray-600">{formatSize(file.size)}</span>
                    )}
                  </button>

                  {/* Subdirectory Contents */}
                  {isDirectory && isExpanded && (
                    <div className="bg-gray-900 bg-opacity-50">
                      {(mockFileStructure[fullPath] || []).map((subfile) => (
                        <button
                          key={subfile.name}
                          onClick={() => {
                            if (subfile.type === 'directory') {
                              navigateTo(fullPath);
                            } else {
                              setSelectedFile(`${fullPath}/${subfile.name}`);
                            }
                          }}
                          className={`w-full px-6 py-2 text-left flex items-center gap-2 text-sm transition-colors ${
                            selectedFile === `${fullPath}/${subfile.name}`
                              ? 'bg-sky-950 text-sky-200'
                              : 'text-gray-400 hover:bg-gray-800'
                          }`}
                        >
                          <span>{subfile.type === 'directory' ? '📁' : '📄'}</span>
                          <span className="flex-1">{subfile.name}</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Status Bar */}
      {selectedFile && (
        <div className="px-3 py-2 border-t border-gray-700 bg-gray-900 text-xs text-gray-500">
          Selected: {selectedFile}
        </div>
      )}
    </div>
  );
}
