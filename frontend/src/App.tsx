import React, { useState } from 'react';
import { Sidebar } from './components/Layout/Sidebar';
import { ChatView } from './components/Chat/ChatView';
import { MemoryView } from './components/MemoryPanel/MemoryView';
import { SettingsView } from './components/Settings/SettingsView';
import { ChatMessage, MemoryItem } from './lib/types';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'chat' | 'memory' | 'settings'>('chat');
  const [memoryStatus, setMemoryStatus] = useState<'active' | 'paused'>('active');

  // Initial demo memories to provide immediate visual feedback
  const [memories, setMemories] = useState<MemoryItem[]>([
    {
      id: 'mem-1',
      content: 'User prefers concise, bulleted explanations over lengthy introductory paragraphs.',
      category: 'preferences',
      source_agent: 'personal_assistant',
      created_at: 'Today, 2:15 PM'
    },
    {
      id: 'mem-2',
      content: 'Current primary project is AI Assistant With Memory using Mem0 and CrewAI.',
      category: 'projects',
      source_agent: 'personal_assistant',
      created_at: 'Today, 2:18 PM'
    },
    {
      id: 'mem-3',
      content: 'Operating environment is Windows with Python 3.14 and Node v24.',
      category: 'biographical',
      source_agent: 'system_surveyor',
      created_at: 'Today, 2:20 PM'
    }
  ]);

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'msg-1',
      role: 'assistant',
      content: 'Hello! I am your memory-augmented AI assistant. Every durable fact or preference from our conversations is categorized and stored in your Memory Bank, so you never have to repeat context.',
      timestamp: 'Just now',
      memories_used: [memories[0], memories[1]]
    }
  ]);

  const handleSendMessage = (text: string) => {
    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: 'Just now'
    };

    setMessages(prev => [...prev, userMsg]);

    // Simulated responsive turn with memory injection
    setTimeout(() => {
      const assistantMsg: ChatMessage = {
        id: `msg-${Date.now() + 1}`,
        role: 'assistant',
        content: `Got it! I\'ve noted that into your long-term memory. Since you prefer concise answers and are building the AI Assistant With Memory project, I will keep our next steps aligned to your roadmap.`,
        timestamp: 'Just now',
        memories_used: [memories[0], memories[1]]
      };
      setMessages(prev => [...prev, assistantMsg]);
    }, 600);
  };

  const handleDeleteMemory = (id: string) => {
    setMemories(prev => prev.filter(m => m.id !== id));
  };

  const handleEditMemory = (id: string, newContent: string) => {
    setMemories(prev => prev.map(m => m.id === id ? { ...m, content: newContent } : m));
  };

  const handleToggleStatus = () => {
    setMemoryStatus(prev => prev === 'active' ? 'paused' : 'active');
  };

  const handleResetAll = () => {
    if (window.confirm('Purge all stored memories? This cannot be undone.')) {
      setMemories([]);
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 font-sans">
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        memoryCount={memories.length}
        memoryStatus={memoryStatus}
      />
      <main className="flex-1 flex overflow-hidden">
        {activeTab === 'chat' && (
          <ChatView
            messages={messages}
            onSendMessage={handleSendMessage}
            isLoading={false}
          />
        )}
        {activeTab === 'memory' && (
          <MemoryView
            memories={memories}
            onDeleteMemory={handleDeleteMemory}
            onEditMemory={handleEditMemory}
            memoryStatus={memoryStatus}
            onToggleStatus={handleToggleStatus}
            onResetAll={handleResetAll}
          />
        )}
        {activeTab === 'settings' && <SettingsView />}
      </main>
    </div>
  );
};

export default App;
