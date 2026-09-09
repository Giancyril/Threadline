import React, { useState } from 'react';
import { Send, Brain, User, Bot } from 'lucide-react';
import { ChatMessage } from '../../lib/types';

interface ChatViewProps {
  messages: ChatMessage[];
  onSendMessage: (text: string) => void;
  isLoading: boolean;
}

export const ChatView: React.FC<ChatViewProps> = ({
  messages,
  onSendMessage,
  isLoading
}) => {
  const [input, setInput] = useState('');
  const [expandedMemories, setExpandedMemories] = useState<Record<string, boolean>>({});

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    onSendMessage(input);
    setInput('');
  };

  const toggleMemoryPill = (msgId: string) => {
    setExpandedMemories(prev => ({ ...prev, [msgId]: !prev[msgId] }));
  };

  return (
    <div className="flex-1 flex flex-col h-screen bg-slate-50 overflow-hidden">
      <header className="h-14 border-b border-slate-200 bg-white px-6 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h2 className="text-sm font-bold text-slate-800">Live Context Session</h2>
          <span className="text-[11px] font-medium text-slate-400">• Persistent Cross-Session Memory</span>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <span className="w-2 h-2 rounded-full bg-emerald-500" />
          <span>Mem0 Engine Ready</span>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto p-6 space-y-5">
        {messages.map((msg) => (
          <div key={msg.id} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
            <div className={`flex items-start gap-3 max-w-2xl ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
              <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
                msg.role === 'user' ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-white shadow-xs'
              }`}>
                {msg.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
              </div>

              <div className="space-y-1.5">
                <div className={`p-4 rounded-2xl text-sm leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-indigo-600 text-white rounded-tr-xs shadow-sm'
                    : 'bg-white border border-slate-200 text-slate-800 rounded-tl-xs shadow-xs'
                }`}>
                  {msg.content}
                </div>

                {msg.role === 'assistant' && msg.memories_used && msg.memories_used.length > 0 && (
                  <div>
                    <button
                      type="button"
                      onClick={() => toggleMemoryPill(msg.id)}
                      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-indigo-50 border border-indigo-100 text-indigo-700 text-[11px] font-semibold hover:bg-indigo-100/70 transition-colors cursor-pointer"
                    >
                      <Brain className="w-3 h-3 text-indigo-600" />
                      <span>Informed by {msg.memories_used.length} remembered facts</span>
                    </button>

                    {expandedMemories[msg.id] && (
                      <div className="mt-2 p-3 bg-white border border-indigo-100 rounded-xl shadow-xs space-y-1.5 max-w-lg animate-in fade-in duration-150">
                        <p className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Context Injected from Memory Bank:</p>
                        {msg.memories_used.map((mem) => (
                          <div key={mem.id} className="text-xs bg-slate-50 p-2 rounded-lg border border-slate-100 flex items-center justify-between">
                            <span className="text-slate-700 font-medium">"{mem.content}"</span>
                            <span className="text-[10px] px-1.5 py-0.5 rounded bg-indigo-100 text-indigo-800 font-semibold uppercase">{mem.category}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="p-4 bg-white border-t border-slate-200">
        <form onSubmit={handleSend} className="max-w-3xl mx-auto flex items-center gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Talk with the assistant (facts are extracted into memory)..."
            className="flex-1 px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:bg-white transition-all"
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="px-5 py-3 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white rounded-xl text-sm font-semibold flex items-center gap-2 transition-all cursor-pointer shadow-sm shadow-indigo-200"
          >
            <span>Send</span>
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
};
