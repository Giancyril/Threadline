import React, { useState } from 'react';
import { Search, Trash2, Edit2, Brain, PauseCircle, PlayCircle, RotateCcw } from 'lucide-react';
import { MemoryItem } from '../../lib/types';

interface MemoryViewProps {
  memories: MemoryItem[];
  onDeleteMemory: (id: string) => void;
  onEditMemory: (id: string, newContent: string) => void;
  memoryStatus: 'active' | 'paused';
  onToggleStatus: () => void;
  onResetAll: () => void;
}

export const MemoryView: React.FC<MemoryViewProps> = ({
  memories,
  onDeleteMemory,
  onEditMemory,
  memoryStatus,
  onToggleStatus,
  onResetAll
}) => {
  const [search, setSearch] = useState('');
  const [activeCategory, setActiveCategory] = useState<string>('all');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editText, setEditText] = useState('');

  const categories = [
    { id: 'all', label: 'All Context' },
    { id: 'preferences', label: 'Preferences' },
    { id: 'biographical', label: 'Biographical' },
    { id: 'projects', label: 'Projects' },
    { id: 'communication_style', label: 'Style & Tone' }
  ];

  const filteredMemories = memories.filter(m => {
    const matchesSearch = m.content.toLowerCase().includes(search.toLowerCase());
    const matchesCategory = activeCategory === 'all' || m.category === activeCategory;
    return matchesSearch && matchesCategory;
  });

  const startEdit = (m: MemoryItem) => {
    setEditingId(m.id);
    setEditText(m.content);
  };

  const saveEdit = (id: string) => {
    if (editText.trim()) {
      onEditMemory(id, editText.trim());
    }
    setEditingId(null);
  };

  return (
    <div className="flex-1 flex flex-col h-screen bg-slate-50 overflow-hidden">
      <header className="h-16 border-b border-slate-200 bg-white px-8 flex items-center justify-between shrink-0">
        <div>
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Brain className="w-5 h-5 text-indigo-600" />
            Memory Management Bank
          </h2>
          <p className="text-xs text-slate-500">Inspect, edit, or purge what your assistant remembers across sessions</p>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onToggleStatus}
            className={`px-3 py-1.5 rounded-lg border text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer ${
              memoryStatus === 'active'
                ? 'border-slate-200 text-slate-700 hover:bg-slate-50'
                : 'border-amber-200 bg-amber-50 text-amber-800'
            }`}
          >
            {memoryStatus === 'active' ? <PauseCircle className="w-4 h-4 text-slate-500" /> : <PlayCircle className="w-4 h-4 text-amber-600" />}
            {memoryStatus === 'active' ? 'Pause Learning' : 'Resume Learning'}
          </button>

          <button
            type="button"
            onClick={onResetAll}
            className="px-3 py-1.5 rounded-lg border border-red-200 bg-red-50 text-red-700 hover:bg-red-100 text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            Clear All Memories
          </button>
        </div>
      </header>

      <div className="p-6 pb-2 space-y-4 max-w-5xl mx-auto w-full">
        <div className="flex items-center gap-4">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search memories by keyword, topic, or person..."
              className="w-full pl-10 pr-4 py-2.5 bg-white border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500 shadow-xs"
            />
          </div>
        </div>

        <div className="flex items-center gap-1.5 border-b border-slate-200 pb-3">
          {categories.map((c) => (
            <button
              key={c.id}
              type="button"
              onClick={() => setActiveCategory(c.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                activeCategory === c.id
                  ? 'bg-indigo-600 text-white shadow-xs'
                  : 'text-slate-600 hover:bg-slate-200/60'
              }`}
            >
              {c.label}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-4 max-w-5xl mx-auto w-full space-y-3">
        {filteredMemories.length === 0 ? (
          <div className="p-12 text-center bg-white border border-dashed border-slate-300 rounded-2xl">
            <Brain className="w-8 h-8 text-slate-300 mx-auto mb-2" />
            <p className="text-sm font-semibold text-slate-700">No memories found</p>
            <p className="text-xs text-slate-400 mt-1">Chat with the assistant to let it extract durable context automatically.</p>
          </div>
        ) : (
          filteredMemories.map((m) => (
            <div key={m.id} className="p-4 bg-white border border-slate-200 rounded-xl shadow-xs hover:border-slate-300 transition-all flex items-start justify-between gap-4">
              <div className="flex-1 space-y-1.5">
                {editingId === m.id ? (
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      value={editText}
                      onChange={(e) => setEditText(e.target.value)}
                      className="flex-1 px-3 py-1.5 text-xs border border-indigo-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                    <button
                      type="button"
                      onClick={() => saveEdit(m.id)}
                      className="px-3 py-1.5 bg-indigo-600 text-white rounded-lg text-xs font-semibold cursor-pointer"
                    >
                      Save
                    </button>
                  </div>
                ) : (
                  <p className="text-xs font-medium text-slate-800 leading-relaxed">{m.content}</p>
                )}

                <div className="flex items-center gap-2 pt-1">
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 uppercase tracking-wider">
                    {m.category}
                  </span>
                  {m.source_agent && (
                    <span className="text-[10px] px-2 py-0.5 rounded bg-slate-100 text-slate-600 font-medium">
                      Agent: {m.source_agent}
                    </span>
                  )}
                  <span className="text-[10px] text-slate-400">Added {m.created_at}</span>
                </div>
              </div>

              <div className="flex items-center gap-1 shrink-0">
                <button
                  type="button"
                  onClick={() => startEdit(m)}
                  className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer"
                  title="Edit memory"
                >
                  <Edit2 className="w-3.5 h-3.5" />
                </button>
                <button
                  type="button"
                  onClick={() => onDeleteMemory(m.id)}
                  className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors cursor-pointer"
                  title="Delete memory"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
