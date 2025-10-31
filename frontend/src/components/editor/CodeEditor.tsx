import React, { useRef, useEffect, useState } from 'react';
import Loader from '../common/Loader';

interface CodeEditorProps {
  value: string;
  onChange: (value: string) => void;
  language?: string;
  theme?: 'light' | 'dark';
  readOnly?: boolean;
  className?: string;
}

const CodeEditor: React.FC<CodeEditorProps> = ({
  value,
  onChange,
  language = 'typescript',
  theme = 'light',
  readOnly = false,
  className = '',
}) => {
  const editorRef = useRef<HTMLDivElement>(null);
  const monacoRef = useRef<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let monaco: any = null;

    const initMonaco = async () => {
      try {
        // Dynamically import Monaco Editor
        const { editor } = await import('monaco-editor');

        if (!editorRef.current) return;

        // Create Monaco Editor instance
        monaco = editor.create(editorRef.current, {
          value,
          language,
          theme: theme === 'dark' ? 'vs-dark' : 'vs',
          readOnly,
          automaticLayout: true,
          minimap: { enabled: false },
          fontSize: 14,
          lineNumbers: 'on',
          roundedSelection: false,
          scrollBeyondLastLine: false,
          wordWrap: 'on',
          tabSize: 2,
          insertSpaces: true,
          detectIndentation: true,
          folding: true,
          lineDecorationsWidth: 10,
          lineNumbersMinChars: 3,
          renderWhitespace: 'selection',
          cursorBlinking: 'blink',
          cursorStyle: 'line',
          contextmenu: true,
          mouseWheelZoom: true,
          multiCursorModifier: 'ctrlCmd',
          accessibilitySupport: 'auto',
          suggestOnTriggerCharacters: true,
          acceptSuggestionOnEnter: 'on',
          quickSuggestions: {
            other: true,
            comments: true,
            strings: true,
          },
          parameterHints: {
            enabled: true,
          },
          hover: {
            enabled: true,
          },
          bracketPairColorization: {
            enabled: true,
          },
          guides: {
            bracketPairs: true,
            indentation: true,
          },
        });

        monacoRef.current = monaco;

        // Handle content changes
        monaco.onDidChangeModelContent(() => {
          const newValue = monaco.getValue();
          onChange(newValue);
        });

        setIsLoading(false);
      } catch (err) {
        console.error('Failed to load Monaco Editor:', err);
        setError('Failed to load code editor');
        setIsLoading(false);
      }
    };

    initMonaco();

    return () => {
      if (monaco) {
        monaco.dispose();
      }
    };
  }, [language, theme, readOnly]);

  // Update value when prop changes
  useEffect(() => {
    if (monacoRef.current && value !== monacoRef.current.getValue()) {
      monacoRef.current.setValue(value);
    }
  }, [value]);

  // Handle theme changes
  useEffect(() => {
    if (monacoRef.current) {
      const { editor } = require('monaco-editor');
      editor.setTheme(theme === 'dark' ? 'vs-dark' : 'vs');
    }
  }, [theme]);

  if (error) {
    return (
      <div className={`flex items-center justify-center h-full border border-red-300 rounded-md bg-red-50 ${className}`}>
        <div className="text-center">
          <div className="text-red-600 mb-2">⚠️</div>
          <p className="text-sm text-red-600">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`relative h-full ${className}`}>
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-50 z-10">
          <Loader size="sm" />
        </div>
      )}
      <div
        ref={editorRef}
        className="h-full w-full"
        style={{ minHeight: '200px' }}
      />
    </div>
  );
};

export default CodeEditor;
