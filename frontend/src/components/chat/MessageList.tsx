import React from 'react';
import { Bot, User } from 'lucide-react';

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'agent';
  timestamp: Date;
  agent?: string;
}

interface MessageListProps {
  messages: Message[];
}

const MessageList: React.FC<MessageListProps> = ({ messages }) => {
  return (
    <div className="space-y-4">
      {messages.map((message) => (
        <div
          key={message.id}
          className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
        >
          <div
            className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
              message.sender === 'user'
                ? 'bg-blue-600 text-white'
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
              message.sender === 'user' ? 'text-blue-200' : 'text-gray-500'
            }`}>
              {message.timestamp.toLocaleTimeString('de-DE', {
                hour: '2-digit',
                minute: '2-digit',
              })}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
};

export default MessageList;