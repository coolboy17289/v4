'use client';

import { useState, useEffect, useRef } from 'react';
import Image from 'next/image';
import { MessageComponent } from '@/components/MessageComponent';
import { ChatInput } from '@/components/ChatInput';

export default function Home() {
  const [messages, setMessages] = useState<{
    id: string;
    text: string;
    sender: 'user' | 'bot';
    timestamp: Date;
  }[]>([]);
  const [input, setInput] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const sendMessage = async () => {
    if (input.trim() === '') return;
    setLoading(true);
    const userMessage = {
      id: Date.now().toString(),
      text: input,
      sender: 'user',
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);
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

      const data: { response: string; session_id: string; confidence: number; sources?: any[]; metadata?: any } = await response.json();
      const botMessage = {
        id: Date.now().toString() + 'b',
        text: data.response,
        sender: 'bot',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error('Error:', error);
      const botMessage = {
        id: Date.now().toString() + 'b',
        text: 'Sorry, something went wrong. Please try again.',
        sender: 'bot',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, botMessage]);
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
          <p className="mt-2 text-sm text-gray-500">
            Chat with your AI assistant
          </p>
        </div>
      </header>
      <main className="flex-1 overflow-y-auto px-4 py-8 max-w-4xl mx-auto">
        <div className="space-y-4">
          {messages.map((message) => (
            <MessageComponent
              key={message.id}
              id={message.id}
              text={message.text}
              sender={message.sender}
              timestamp={message.timestamp}
            />
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
            <ChatInput onSend={sendMessage} />
          </div>
        </div>
      </footer>
    </div>
  );
}
