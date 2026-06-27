'use client';

import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Avatar } from './Avatar';

interface MessageComponentProps {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

export const MessageComponent = ({
  id,
  text,
  sender,
  timestamp,
}: MessageComponentProps) => {
  const [showTime, setShowTime] = useState(false);

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const isUser = sender === 'user';
  const avatarName = isUser ? 'You' : 'AI Assistant';
  const avatarColor = isUser ? '#3b82f6' : '#10b981';

  return (
    <div
      className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
      onMouseEnter={() => setShowTime(true)}
      onMouseLeave={() => setShowTime(false)}
    >
      <div className={`flex items-end space-x-3 ${!isUser && 'order-first'}`}>
        {!isUser && (
          <Avatar name={avatarName} size={32} color={avatarColor} />
        )}
        <div className={`max-w-[80%] ${isUser ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-900'} rounded-lg p-3 relative`}>
          <div className="flex justify-between mb-1">
            <span className="font-medium">{avatarName}</span>
            {showTime && (
              <span className="text-xs text-opacity-60">
                {formatTime(timestamp)}
              </span>
            )}
          </div>
          <ReactMarkdown
            components={{
              code: ({ inline, className, children, ...props }) => {
                const match = /language-(\w+)/.exec(className || '');
                return (
                  <pre className={className} {...props}>
                    <code className={match ? `language-${match[1]}` : ''}>
                      {children}
                    </code>
                  </pre>
                );
              },
            }}
            plugins={[remarkGfm]}
          >
            {text}
          </ReactMarkdown>
        </div>
        {isUser && (
          <Avatar name={avatarName} size={32} color={avatarColor} />
        )}
      </div>
    </div>
  );
};
