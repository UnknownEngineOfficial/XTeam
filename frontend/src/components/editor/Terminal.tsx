import React, { useState, useRef, useEffect } from 'react';
import { Terminal as TerminalIcon, Square, Trash2 } from 'lucide-react';
import Button from '../common/Button';

interface TerminalLine {
  id: string;
  content: string;
  type: 'input' | 'output' | 'error';
  timestamp: Date;
}

interface TerminalProps {
  onCommand: (command: string) => Promise<string>;
  className?: string;
  placeholder?: string;
}

const Terminal: React.FC<TerminalProps> = ({
  onCommand,
  className = '',
  placeholder = 'Enter command...',
}) => {
  const [lines, setLines] = useState<TerminalLine[]>([
    {
      id: '1',
      content: 'Welcome to XTeam Terminal',
      type: 'output',
      timestamp: new Date(),
    },
    {
      id: '2',
      content: 'Type "help" for available commands',
      type: 'output',
      timestamp: new Date(),
    },
  ]);
  const [currentCommand, setCurrentCommand] = useState('');
  const [isRunning, setIsRunning] = useState(false);
  const [commandHistory, setCommandHistory] = useState<string[]>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);

  const terminalRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    scrollToBottom();
  }, [lines]);

  const scrollToBottom = () => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  };

  const addLine = (content: string, type: 'input' | 'output' | 'error' = 'output') => {
    const newLine: TerminalLine = {
      id: Date.now().toString(),
      content,
      type,
      timestamp: new Date(),
    };
    setLines(prev => [...prev, newLine]);
  };

  const executeCommand = async (command: string) => {
    if (!command.trim()) return;

    // Add command to history
    setCommandHistory(prev => [...prev, command]);

    // Add input line
    addLine(`$ ${command}`, 'input');

    setIsRunning(true);

    try {
      const result = await onCommand(command);
      addLine(result, 'output');
    } catch (error) {
      addLine(`Error: ${error}`, 'error');
    } finally {
      setIsRunning(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const command = currentCommand.trim();
    if (!command || isRunning) return;

    await executeCommand(command);
    setCurrentCommand('');
    setHistoryIndex(-1);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      if (commandHistory.length > 0) {
        const newIndex = historyIndex === -1 ? commandHistory.length - 1 : Math.max(0, historyIndex - 1);
        setHistoryIndex(newIndex);
        setCurrentCommand(commandHistory[newIndex]);
      }
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      if (historyIndex >= 0) {
        const newIndex = historyIndex + 1;
        if (newIndex >= commandHistory.length) {
          setHistoryIndex(-1);
          setCurrentCommand('');
        } else {
          setHistoryIndex(newIndex);
          setCurrentCommand(commandHistory[newIndex]);
        }
      }
    } else if (e.key === 'Tab') {
      e.preventDefault();
      // Basic tab completion (could be enhanced)
      const suggestions = ['help', 'ls', 'cd', 'pwd', 'clear'];
      const matching = suggestions.filter(cmd => cmd.startsWith(currentCommand));
      if (matching.length === 1) {
        setCurrentCommand(matching[0]);
      }
    }
  };

  const clearTerminal = () => {
    setLines([]);
  };

  const stopCommand = () => {
    // This would need to be implemented with actual process management
    addLine('Command execution stopped', 'error');
    setIsRunning(false);
  };

  return (
    <div className={`flex flex-col h-full bg-gray-900 text-gray-100 ${className}`}>
      {/* Terminal Header */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700">
        <div className="flex items-center">
          <TerminalIcon className="w-4 h-4 mr-2" />
          <span className="text-sm font-medium">Terminal</span>
        </div>
        <div className="flex items-center space-x-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={clearTerminal}
            className="p-1 text-gray-400 hover:text-gray-200"
            title="Clear terminal"
          >
            <Trash2 className="w-4 h-4" />
          </Button>
          {isRunning && (
            <Button
              variant="ghost"
              size="sm"
              onClick={stopCommand}
              className="p-1 text-red-400 hover:text-red-200"
              title="Stop command"
            >
              <Square className="w-4 h-4" />
            </Button>
          )}
        </div>
      </div>

      {/* Terminal Content */}
      <div
        ref={terminalRef}
        className="flex-1 overflow-y-auto p-4 font-mono text-sm"
      >
        {lines.map((line) => (
          <div
            key={line.id}
            className={`mb-1 ${
              line.type === 'error'
                ? 'text-red-400'
                : line.type === 'input'
                ? 'text-green-400'
                : 'text-gray-300'
            }`}
          >
            <span className="text-gray-500 mr-2">
              {line.timestamp.toLocaleTimeString('en-US', {
                hour12: false,
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
              })}
            </span>
            <span>{line.content}</span>
          </div>
        ))}

        {/* Current command input */}
        <form onSubmit={handleSubmit} className="flex items-center">
          <span className="text-green-400 mr-2">$</span>
          <input
            ref={inputRef}
            type="text"
            value={currentCommand}
            onChange={(e) => setCurrentCommand(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={isRunning ? 'Command running...' : placeholder}
            disabled={isRunning}
            className="flex-1 bg-transparent border-none outline-none text-gray-100 placeholder-gray-500"
            autoFocus
          />
          {isRunning && (
            <div className="flex space-x-1 ml-2">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
            </div>
          )}
        </form>
      </div>
    </div>
  );
};

export default Terminal;
