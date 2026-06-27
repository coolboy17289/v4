'use client';

import { useState } from 'react';

interface ChatInputProps {
  onSend: (message: string) => Promise<void>;
}

export const ChatInput = ({ onSend }: ChatInputProps) => {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [files, setFiles] = useState<FileList | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() === '' && (!files || files.length === 0)) return;
    setLoading(true);
    // For now, we only send text; files could be appended to message or sent separately
    await onSend(input);
    setInput('');
    setFiles(null);
    setLoading(false);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFiles(e.target.files);
  };

  return (
    <div className="flex gap-3">
      <form onSubmit={handleSubmit} className="flex-1">
        <div className="flex gap-2 items-start">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type a message..."
            className="flex-1 min-h-[60px] rounded-lg border border-gray-300 bg-white px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
            disabled={loading}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSubmit(e as React.FormEvent);
              }
            }}
          />
          <div className="flex space-x-2 mt-2">
            <button
              type="button"
              onClick={() => document.getElementById('file-input')?.click()}
              disabled={loading}
              className={`px-3 py-2 rounded-lg border border-gray-300 bg-white hover:bg-gray-50 disabled:opacity-50`}
            >
              📎
            </button>
            <input
              type="file"
              id="file-input"
              accept=".txt,.pdf,.png,.jpg,.jpeg,.csv,.json"
              multiple
              onChange={handleFileChange}
              className="hidden"
            />
            {files && files.length > 0 && (
              <span className="text-xs text-gray-500">{files.length} file(s) selected</span>
            )}
          </div>
        </div>
      </form>
      <button
        onClick={handleSubmit}
        disabled={loading || (input.trim() === '' && (!files || files.length === 0))}
        className={`px-6 py-2 rounded-lg bg-blue-600 text-white font-medium hover:bg-blue-700 transition-colors disabled:opacity-50`}
      >
        {loading ? 'Sending...' : 'Send'}
      </button>
    </div>
  );
};
