import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Play, FileText, CheckCircle, AlertCircle } from 'lucide-react';
import Button from '../common/Button';
import { useWebSocket } from '../../hooks/useWebSocket';
import { projectsApi, ExecuteWorkflowRequest } from '../../services/api';

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'agent' | 'system';
  timestamp: Date;
  agent?: string;
  type?: 'message' | 'execution_start' | 'execution_complete' | 'stage_start' | 'file_created' | 'error';
  metadata?: any;
}

const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      content: 'Hallo! Ich bin dein KI-Assistent. Beschreibe dein Projekt, und ich helfe dir dabei, es umzusetzen.',
      sender: 'agent',
      timestamp: new Date(),
      agent: 'XTeam Assistant',
    },
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [currentProjectId, setCurrentProjectId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // WebSocket integration
  const { sendAgentCommand, isConnected } = useWebSocket({
    autoConnect: true,
    onAgentMessage: (message) => {
      const agentMessage: Message = {
        id: Date.now().toString(),
        content: message.data?.content || 'Agent response',
        sender: 'agent',
        timestamp: new Date(),
        agent: message.data?.agent || 'Agent',
        type: 'message',
      };
      setMessages(prev => [...prev, agentMessage]);
      setIsTyping(false);
    },
    onExecutionStart: (message) => {
      const systemMessage: Message = {
        id: Date.now().toString(),
        content: `🚀 Workflow gestartet mit ${message.data?.agents_count || 0} Agenten`,
        sender: 'system',
        timestamp: new Date(),
        type: 'execution_start',
        metadata: message.data,
      };
      setMessages(prev => [...prev, systemMessage]);
    },
    onExecutionComplete: (message) => {
      const systemMessage: Message = {
        id: Date.now().toString(),
        content: `✅ Workflow abgeschlossen!`,
        sender: 'system',
        timestamp: new Date(),
        type: 'execution_complete',
        metadata: message.data,
      };
      setMessages(prev => [...prev, systemMessage]);
      setIsTyping(false);
    },
    onStageStart: (message) => {
      const stageNames = {
        requirements_analysis: 'Anforderungsanalyse',
        system_design: 'Systemdesign',
        code_generation: 'Codegenerierung',
        testing: 'Tests',
      };
      const stageName = stageNames[message.data?.stage as keyof typeof stageNames] || message.data?.stage;
      const systemMessage: Message = {
        id: Date.now().toString(),
        content: `🔄 ${stageName} wird ausgeführt...`,
        sender: 'system',
        timestamp: new Date(),
        type: 'stage_start',
        metadata: message.data,
      };
      setMessages(prev => [...prev, systemMessage]);
    },
    onFileCreated: (message) => {
      const systemMessage: Message = {
        id: Date.now().toString(),
        content: `📄 Datei erstellt: ${message.data?.file_path}`,
        sender: 'system',
        timestamp: new Date(),
        type: 'file_created',
        metadata: message.data,
      };
      setMessages(prev => [...prev, systemMessage]);
    },
    onError: (message) => {
      const errorMessage: Message = {
        id: Date.now().toString(),
        content: `❌ Fehler: ${message.data?.error_message || 'Unbekannter Fehler'}`,
        sender: 'system',
        timestamp: new Date(),
        type: 'error',
        metadata: message.data,
      };
      setMessages(prev => [...prev, errorMessage]);
      setIsTyping(false);
    },
  });

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputMessage,
      sender: 'user',
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsTyping(true);

    // Check if this looks like a project description that should trigger workflow
    const isProjectDescription = inputMessage.length > 50 && 
      (inputMessage.toLowerCase().includes('projekt') || 
       inputMessage.toLowerCase().includes('build') || 
       inputMessage.toLowerCase().includes('create') ||
       inputMessage.toLowerCase().includes('develop'));

    if (isProjectDescription && currentProjectId) {
      // Start workflow execution
      try {
        await startWorkflow(inputMessage);
      } catch (error) {
        console.error('Failed to start workflow:', error);
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          content: '❌ Fehler beim Starten des Workflows. Bitte versuche es erneut.',
          sender: 'system',
          timestamp: new Date(),
          type: 'error',
        };
        setMessages(prev => [...prev, errorMessage]);
        setIsTyping(false);
      }
    } else {
      // Send regular message via WebSocket
      try {
        sendAgentCommand('process_message', {
          content: userMessage.content,
          timestamp: userMessage.timestamp.toISOString(),
        });
      } catch (error) {
        console.error('Failed to send message:', error);
        setIsTyping(false);
        // Fallback to mock response
        setTimeout(() => {
          const agentMessage: Message = {
            id: (Date.now() + 1).toString(),
            content: `Ich habe deine Anfrage erhalten: "${userMessage.content}". Ich werde jetzt mit der Analyse beginnen und dir gleich ein Update geben.`,
            sender: 'agent',
            timestamp: new Date(),
            agent: 'Product Manager',
          };
          setMessages(prev => [...prev, agentMessage]);
          setIsTyping(false);
        }, 2000);
      }
    }
  };

  const startWorkflow = async (prompt: string) => {
    if (!currentProjectId) {
      throw new Error('No project selected');
    }

    try {
      const response = await projectsApi.executeWorkflow(currentProjectId, {
        prompt,
        execution_type: 'full',
      });

      // Workflow started successfully - messages will come via WebSocket
      console.log('Workflow started:', response);
    } catch (error) {
      console.error('Failed to start workflow:', error);
      throw error;
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                message.sender === 'user'
                  ? 'bg-blue-600 text-white'
                  : message.sender === 'system'
                  ? 'bg-yellow-100 text-yellow-800 border border-yellow-200'
                  : 'bg-gray-100 text-gray-900'
              }`}
            >
              {message.sender === 'agent' && message.agent && (
                <div className="flex items-center mb-1">
                  <Bot className="w-4 h-4 mr-1" />
                  <span className="text-xs font-medium text-gray-600">
                    {message.agent}
                  </span>
                </div>
              )}
              {message.sender === 'system' && (
                <div className="flex items-center mb-1">
                  <AlertCircle className="w-4 h-4 mr-1" />
                  <span className="text-xs font-medium text-yellow-700">
                    System
                  </span>
                </div>
              )}
              {message.sender === 'user' && (
                <div className="flex items-center mb-1">
                  <User className="w-4 h-4 mr-1" />
                  <span className="text-xs font-medium text-blue-200">
                    Du
                  </span>
                </div>
              )}
              <p className="text-sm">{message.content}</p>
              <p className={`text-xs mt-1 ${
                message.sender === 'user' 
                  ? 'text-blue-200' 
                  : message.sender === 'system'
                  ? 'text-yellow-600'
                  : 'text-gray-500'
              }`}>
                {message.timestamp.toLocaleTimeString('de-DE', {
                  hour: '2-digit',
                  minute: '2-digit',
                })}
              </p>
            </div>
          </div>
        ))}

        {isTyping && (
          <div className="flex justify-start">
            <div className="bg-gray-100 px-4 py-2 rounded-lg">
              <div className="flex items-center">
                <Bot className="w-4 h-4 mr-1" />
                <span className="text-xs font-medium text-gray-600 mr-2">
                  Product Manager
                </span>
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-200 p-4">
        <div className="flex space-x-2">
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Beschreibe dein Projekt oder gib Anweisungen..."
            className="flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 resize-none"
            rows={1}
            style={{ minHeight: '40px', maxHeight: '120px' }}
            onInput={(e) => {
              const target = e.target as HTMLTextAreaElement;
              target.style.height = 'auto';
              target.style.height = Math.min(target.scrollHeight, 120) + 'px';
            }}
          />
          <Button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || isTyping}
            className="px-4 py-2"
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>
        <p className="text-xs text-gray-500 mt-2">
          Drücke Enter zum Senden, Shift+Enter für neue Zeile
        </p>
      </div>
    </div>
  );
};

export default ChatInterface;