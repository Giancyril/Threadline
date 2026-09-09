import React, { useState, useEffect, useCallback } from 'react';
import { Sidebar } from './components/Layout/Sidebar';
import { ChatView } from './components/Chat/ChatView';
import { MemoryView } from './components/MemoryPanel/MemoryView';
import { SettingsView } from './components/Settings/SettingsView';
import { GraphVisualizer } from './components/Graph/GraphVisualizer';
import { SemanticDriftView } from './components/Analytics/SemanticDriftView';
import { FederationHub } from './components/Federation/FederationHub';
import { ChatMessage, MemoryItem, MemoryCategory } from './lib/types';
import * as api from './lib/api';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'chat' | 'memory' | 'graph' | 'analytics' | 'federation' | 'settings'>('chat');
  const [memoryStatus, setMemoryStatus] = useState<'active' | 'paused'>('active');
  const [userId] = useState<string>('default_user');
  const [sessionId] = useState<string>('session_main');
  const [isLoading, setIsLoading] = useState<boolean>(false);

  // Initial memories
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
      content: 'Current primary project is AI Assistant With Memory using Mem0 and Qdrant.',
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

  // Load from backend on mount
  const refreshMemories = useCallback(async () => {
    const remote = await api.fetchMemories(userId);
    if (remote && remote.length > 0) {
      setMemories(remote);
    }
    const learningActive = await api.getLearningStatus(userId);
    setMemoryStatus(learningActive ? 'active' : 'paused');
  }, [userId]);

  useEffect(() => {
    refreshMemories();
  }, [refreshMemories]);

  const handleSendMessage = async (text: string) => {
    const userMsg: ChatMessage = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);

    const learnEnabled = memoryStatus === 'active';
    const response = await api.sendChatMessage(
      text,
      userId,
      sessionId,
      messages,
      true,
      learnEnabled
    );

    if (response) {
      const assistantMsg: ChatMessage = {
        id: `msg-${Date.now() + 1}`,
        role: 'assistant',
        content: response.reply,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        memories_used: (response.injected_memories || []).map((m: any) => ({
          id: m.id,
          content: m.content,
          category: m.category as MemoryCategory,
          created_at: 'Recalled context',
          score: m.score,
        })),
      };
      setMessages(prev => [...prev, assistantMsg]);

      // Refresh memory list if new facts were learned
      if (response.newly_learned_memories && response.newly_learned_memories.length > 0) {
        refreshMemories();
      }
    } else {
      setTimeout(() => {
        const assistantMsg: ChatMessage = {
          id: `msg-${Date.now() + 1}`,
          role: 'assistant',
          content: `Noted! I've retained your message: "${text}". Memory learning is ${memoryStatus}.`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          memories_used: [memories[0]],
        };
        setMessages(prev => [...prev, assistantMsg]);
      }, 500);
    }
    setIsLoading(false);
  };

  const handleDeleteMemory = async (id: string) => {
    await api.deleteMemory(id);
    setMemories(prev => prev.filter(m => m.id !== id));
  };

  const handleEditMemory = async (id: string, newContent: string) => {
    const existing = memories.find(m => m.id === id);
    if (existing) {
      await api.updateMemory(id, newContent, existing.category);
    }
    setMemories(prev => prev.map(m => m.id === id ? { ...m, content: newContent } : m));
  };

  const handleToggleStatus = async () => {
    const nextStatus = memoryStatus === 'active' ? 'paused' : 'active';
    const ok = await api.setLearningStatus(nextStatus === 'active', userId);
    setMemoryStatus(ok ? 'active' : 'paused');
  };

  const handleResetAll = async () => {
    if (window.confirm('Purge all stored memories? This cannot be undone.')) {
      await api.purgeAllMemories(userId);
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
            isLoading={isLoading}
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
        {activeTab === 'graph' && <GraphVisualizer userId={userId} />}
        {activeTab === 'analytics' && <SemanticDriftView />}
        {activeTab === 'federation' && <FederationHub />}
        {activeTab === 'settings' && <SettingsView />}
      </main>
    </div>
  );
};

export default App;
