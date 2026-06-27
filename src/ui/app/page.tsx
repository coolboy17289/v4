import { useState, useEffect, useRef } from 'react';
import Image from 'next/image';

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const sendMessage = async () => {
    if (input.trim() === '') return;
    setLoading(true);
    const userMessage: Message = {
      id: Date.now().toString(),
      text: input,
      sender: 'user'
    };
    setMessages(prev => [...prev, userMessage]);
    setInput('');

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage.text,
          session_id: 'default', // In a real app, you would manage sessions
          context: {},
        }),
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const data: ChatResponse = await response.json();
      const botMessage: Message = {
        id: Date.now().toString() + 'b',
        text: data.response,
        sender: 'bot'
      };
      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      console.error('Error:', error);
      const botMessage: Message = {
        id: Date.now().toString() + 'b',
        text: 'Sorry, something went wrong. Please try again.',
        sender: 'bot'
      };
      setMessages(prev => [...prev, botMessage]);
    } finally {
      setLoading(false);
    }
  };

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-white shadow-sm">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <h1 className="text-2xl font-bold text-gray-800">AI Assistant</h1>
          <p className="mt-Name="mt-1 text-sm text-gray-500">Chat with your AI assistant</p>
        </div>
      </header>
      <main className="flex-1 overflow-y-auto px-4 py-8 max-w-4xl mx-auto">
        <div className="text-sm text-gray-500">Chat with your AI assistant</p>
        </div>
      </header>
      <main className="flex-1 overflow-y-auto px-4 py-8 max-w-4xl mx-auto">
        <div className="space-y-4">
          {messages.map((message) => (
            <div key={message.id} className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] rounded-lg px-4 py-2 ${
                message.sender === 'user'
                  ? 'bg-blue-500 text-white ml-4'
                  : 'bg-gray-200 text-gray-800 mr-4'
              }`}>
                <p className="whitespace-pre-wrap">{message.text}</p>
              </div>
            </div>
          ))}
          {loading && (
            <div className="flex justify-start">
              <div className="w-4 h-4 border-2 border-t-2 border-l-2 border-b-transparent border-r-transparent rounded-full animate-spin border-blue-500"></div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </main>
      <footer className="bg-white border-t">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex gap-3">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Type a message..."
              className="flex-1 min-h-[60px] rounded-lg border border-gray-300 bg-white px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
              disabled={loading}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  sendMessage();
                }
              }}
            />
            <button
              onClick={sendMessage}
              disabled={loading || input.trim() === ''}
              className={`px-6 py-2 rounded-lg bg-blue-600 text-white font-medium hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center`}
            >
              {loading ? 'Sending...' : 'Send'}
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
}

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'bot';
}

interface ChatResponse {
  response: string;
  session_id: string;
  confidence: number;
  sources: any[];
  metadata: any;
}