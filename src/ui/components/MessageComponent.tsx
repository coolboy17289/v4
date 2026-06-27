import { useState } from 'react';

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

  return (
    <div
      className={`flex ${sender === 'user' ? 'justify-end' : 'justify-start'}`}
      onMouseEnter={() => setShowTime(true)}
      onMouseLeave={() => setShowTime(false)}
    >
      <div
        className={`max-w-[80%] rounded-lg px-4 py-2 ${
          sender === 'user'
            ? 'bg-blue-500 text-white ml-4'
            : 'bg-gray-200 text-gray-800 mr-4'
        } relative`}
      >
        <p className="whitespace-pre-wrap break-words">{text}</p>
        {showTime && (
          <span className="absolute bottom-0 right-0 text-xs text-gray-400 m-1">
            {formatTime(timestamp)}
          </span>
        )}
      </div>
    </div>
  );
};
