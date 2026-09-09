import React from 'react';
import { MessageSquare, Brain, Sliders, ShieldCheck } from 'lucide-react';

interface SidebarProps {
  activeTab: 'chat' | 'memory' | 'settings';
  setActiveTab: (tab: 'chat' | 'memory' | 'settings') => void;
  memoryCount: number;
  memoryStatus: 'active' | 'paused';
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  memoryCount,
  memoryStatus
}) => {
  return (
    <aside className="w-64 border-r border-slate-200 bg-white flex flex-col justify-between h-screen shrink-0 select-none">
      <div>
        <div className="p-5 border-b border-slate-100 flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-indigo-600 flex items-center justify-center text-white shadow-sm shadow-indigo-200">
            <Brain className="w-5 h-5" />
          </div>
          <div>
            <h1 className="font-bold text-sm tracking-tight text-slate-900">Memoria AI</h1>
            <p className="text-[11px] text-slate-500 font-medium">Assistant with Long-term Memory</p>
          </div>
        </div>

        <nav className="p-3 space-y-1">
          <button
            type="button"
            onClick={() => setActiveTab('chat')}
            className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              activeTab === 'chat'
                ? 'bg-indigo-50 text-indigo-700 font-bold'
                : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
            }`}
          >
            <div className="flex items-center gap-2.5">
              <MessageSquare className="w-4 h-4" />
              <span>Conversation</span>
            </div>
            <span className="text-[10px] bg-slate-100 text-slate-500 px-1.5 py-0.5 rounded font-mono">v1</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('memory')}
            className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              activeTab === 'memory'
                ? 'bg-indigo-50 text-indigo-700 font-bold'
                : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
            }`}
          >
            <div className="flex items-center gap-2.5">
              <Brain className="w-4 h-4" />
              <span>Memory Bank</span>
            </div>
            <span className="text-[11px] bg-indigo-100 text-indigo-700 px-2 py-0.5 rounded-full font-bold">
              {memoryCount}
            </span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('settings')}
            className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              activeTab === 'settings'
                ? 'bg-indigo-50 text-indigo-700 font-bold'
                : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
            }`}
          >
            <div className="flex items-center gap-2.5">
              <Sliders className="w-4 h-4" />
              <span>Persona & Style</span>
            </div>
          </button>
        </nav>
      </div>

      <div className="p-4 border-t border-slate-100 bg-slate-50/50 space-y-3">
        <div className="flex items-center justify-between text-xs">
          <span className="text-slate-500 font-medium">Memory Engine:</span>
          <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-bold ${
            memoryStatus === 'active' ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700'
          }`}>
            <span className={`w-1.5 h-1.5 rounded-full ${memoryStatus === 'active' ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'}`} />
            {memoryStatus === 'active' ? 'Active' : 'Paused'}
          </span>
        </div>

        <div className="flex items-center gap-2 text-[11px] text-slate-400">
          <ShieldCheck className="w-3.5 h-3.5 text-slate-500" />
          <span>Explicit user governance enabled</span>
        </div>
      </div>
    </aside>
  );
};
