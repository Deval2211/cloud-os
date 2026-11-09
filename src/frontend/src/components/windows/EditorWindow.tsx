/**
 * Code editor window component
 */
'use client';

import { useState, useRef, useEffect } from 'react';

interface EditorWindowProps {
  filename?: string;
  onClose?: () => void;
  onSave?: (content: string) => Promise<void>;
}

const LANGUAGE_EXTENSIONS: Record<string, string> = {
  '.py': 'python',
  '.js': 'javascript',
  '.ts': 'typescript',
  '.jsx': 'jsx',
  '.tsx': 'tsx',
  '.json': 'json',
  '.yml': 'yaml',
  '.yaml': 'yaml',
  '.md': 'markdown',
  '.html': 'html',
  '.css': 'css',
  '.sql': 'sql',
  '.sh': 'bash',
};

export function EditorWindow({ filename = 'untitled.txt', onClose, onSave }: EditorWindowProps) {
  const [content, setContent] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [isDirty, setIsDirty] = useState(false);
  const [lineNumbers, setLineNumbers] = useState<string[]>(['1']);
  const editorRef = useRef<HTMLTextAreaElement>(null);
  const lineNumbersRef = useRef<HTMLDivElement>(null);

  const getLanguage = () => {
    for (const [ext, lang] of Object.entries(LANGUAGE_EXTENSIONS)) {
      if (filename.endsWith(ext)) return lang;
    }
    return 'plaintext';
  };

  const updateLineNumbers = () => {
    if (!editorRef.current) return;
    const lines = content.split('\n').length;
    setLineNumbers(Array.from({ length: lines }, (_, i) => String(i + 1)));
  };

  useEffect(() => {
    updateLineNumbers();
  }, [content]);

  const handleScroll = () => {
    if (!editorRef.current || !lineNumbersRef.current) return;
    lineNumbersRef.current.scrollTop = editorRef.current.scrollTop;
  };

  const handleSave = async () => {
    if (!onSave) return;
    try {
      setIsSaving(true);
      await onSave(content);
      setIsDirty(false);
    } catch (err) {
      console.error('Failed to save:', err);
    } finally {
      setIsSaving(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 's') {
      e.preventDefault();
      handleSave();
    } else if (e.key === 'Tab') {
      e.preventDefault();
      const start = editorRef.current!.selectionStart;
      const end = editorRef.current!.selectionEnd;
      const newContent = content.substring(0, start) + '\t' + content.substring(end);
      setContent(newContent);
      setTimeout(() => {
        editorRef.current!.selectionStart = editorRef.current!.selectionEnd = start + 1;
      }, 0);
    }
  };

  return (
    <div className="flex flex-col h-full bg-gray-950 text-gray-100 border border-gray-700 rounded overflow-hidden">
      {/* Header */}
      <div className="p-3 border-b border-gray-700 bg-gray-900 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-gray-600"></div>
          <span className="font-mono text-sm">{filename}</span>
          {isDirty && <span className="text-xs text-yellow-400">●</span>}
          <span className="text-xs text-gray-500 ml-2">{getLanguage()}</span>
        </div>
        <div className="flex gap-2">
          {onSave && (
            <button
              onClick={handleSave}
              disabled={isSaving || !isDirty}
              title="Save (Ctrl+S)"
              className="text-xs px-3 py-1 rounded bg-sky-600 hover:bg-sky-700 disabled:bg-gray-700 text-white transition"
            >
              {isSaving ? 'Saving...' : 'Save'}
            </button>
          )}
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

      {/* Editor */}
      <div className="flex-1 flex overflow-hidden">
        {/* Line Numbers */}
        <div
          ref={lineNumbersRef}
          className="bg-gray-900 border-r border-gray-800 text-right pr-4 pl-3 py-4 text-xs text-gray-600 font-mono overflow-hidden select-none"
          style={{ width: '50px', maxHeight: '100%', overflowY: 'hidden' }}
        >
          {lineNumbers.map((num) => (
            <div key={num}>{num}</div>
          ))}
        </div>

        {/* Text Area */}
        <textarea
          ref={editorRef}
          value={content}
          onChange={(e) => {
            setContent(e.target.value);
            setIsDirty(true);
          }}
          onKeyDown={handleKeyDown}
          onScroll={handleScroll}
          placeholder="Start typing... (or paste code)"
          className="flex-1 p-4 bg-gray-950 text-gray-100 font-mono text-sm resize-none outline-none placeholder-gray-700"
          spellCheck="false"
        />
      </div>

      {/* Status Bar */}
      <div className="px-4 py-2 border-t border-gray-700 bg-gray-900 text-xs text-gray-500 flex justify-between">
        <span>{content.length} characters</span>
        <span>
          Ln {lineNumbers.length}, Col 1 | {getLanguage()}
        </span>
      </div>
    </div>
  );
}
