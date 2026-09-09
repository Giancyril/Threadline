import React, { useState, useCallback } from 'react';
import { Search, Trash2, Edit2, Brain, PauseCircle, PlayCircle, RotateCcw, Clock, Infinity, Folder, Zap, History } from 'lucide-react';
import { MemoryItem, LongevityTier, MemorySnapshot, MemoryDiff } from '../../lib/types';
import { VersionHistoryModal } from './VersionHistoryModal';

interface MemoryViewProps {
  memories: MemoryItem[];
  onDeleteMemory: (id: string) => void;
  onEditMemory: (id: string, newContent: string) => void;
  memoryStatus: 'active' | 'paused';
  onToggleStatus: () => void;
  onResetAll: () => void;
}

const TIER_CONFIG: Record<LongevityTier, { label: string; color: string; bg: string; icon: React.ReactNode; description: string }> = {
  ephemeral: {
    label: 'Ephemeral',
    color: 'text-amber-700',
    bg: 'bg-amber-50 border-amber-200',
    icon: <Zap className="w-3 h-3" />,
    description: 'Expires in ~24 hours'
  },
  project_bound: {
    label: 'Project',
    color: 'text-blue-700',
    bg: 'bg-blue-50 border-blue-200',
    icon: <Folder className="w-3 h-3" />,
    description: 'Expires in ~30 days'
  },
  permanent: {
    label: 'Permanent',
    color: 'text-emerald-700',
    bg: 'bg-emerald-50 border-emerald-200',
    icon: <Infinity className="w-3 h-3" />,
    description: 'Never expires'
  }
};

function getExpiryCountdown(expiresAt: string | null | undefined): string | null {
  if (!expiresAt) return null;
  const now = Date.now();
  const expiry = new Date(expiresAt).getTime();
  const diffMs = expiry - now;
  if (diffMs <= 0) return 'Expired';
  const hours = Math.floor(diffMs / 3600000);
  const days = Math.floor(hours / 24);
  if (days > 1) return `Expires in ${days}d`;
  if (hours > 1) return `Expires in ${hours}h`;
  const minutes = Math.floor(diffMs / 60000);
  return `Expires in ${minutes}m`;
}

function LongevityBadge({ tier, expiresAt }: { tier?: LongevityTier; expiresAt?: string | null }) {
  const resolvedTier: LongevityTier = tier || 'permanent';
  const config = TIER_CONFIG[resolvedTier];
  const countdown = getExpiryCountdown(expiresAt);

  return (
    <div className={`flex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full border ${config.bg} ${config.color}`}
         title={config.description}>
      {config.icon}
      <span>{config.label}</span>
      {countdown && resolvedTier !== 'permanent' && (
        <span className="ml-0.5 opacity-75">· {countdown}</span>
      )}
    </div>
  );
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
  const [activeTier, setActiveTier] = useState<string>('all');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editText, setEditText] = useState('');

  // History modal state
  const [historyMemory, setHistoryMemory] = useState<MemoryItem | null>(null);
  const [snapshots, setSnapshots] = useState<MemorySnapshot[]>([]);
  const [diffs, setDiffs] = useState<MemoryDiff[]>([]);
  // loading history

  const categories = [
    { id: 'all', label: 'All Context' },
    { id: 'preferences', label: 'Preferences' },
    { id: 'biographical', label: 'Biographical' },
    { id: 'projects', label: 'Projects' },
    { id: 'communication_style', label: 'Style & Tone' }
  ];

  const tiers = [
    { id: 'all', label: 'All Tiers' },
    { id: 'permanent', label: 'Permanent' },
    { id: 'project_bound', label: 'Project' },
    { id: 'ephemeral', label: 'Ephemeral' }
  ];

  const filteredMemories = memories.filter(m => {
    const matchesSearch = m.content.toLowerCase().includes(search.toLowerCase());
    const matchesCategory = activeCategory === 'all' || m.category === activeCategory;
    const memTier = (m.metadata?.longevity_tier as LongevityTier) || 'permanent';
    const matchesTier = activeTier === 'all' || memTier === activeTier;
    return matchesSearch && matchesCategory && matchesTier;
  });

  const startEdit = useCallback((m: MemoryItem) => {
    setEditingId(m.id);
    setEditText(m.content);
  }, []);

  const saveEdit = useCallback((id: string) => {
    if (editText.trim()) {
      onEditMemory(id, editText.trim());
    }
    setEditingId(null);
  }, [editText, onEditMemory]);

  const openHistory = async (memory: MemoryItem) => {
    setHistoryMemory(memory);
    
    try {
      const res = await fetch(`http://localhost:8000/api/v1/versioning/${memory.id}/history`);
      if (res.ok) {
        const data = await res.json();
        setSnapshots(data.snapshots || []);
        setDiffs(data.diffs || []);
      } else {
        // Fallback default snapshot
        setSnapshots([{
          snapshot_id: `snap_${memory.id}_1`,
          memory_id: memory.id,
          version: 1,
          content: memory.content,
          trigger: 'initial',
          triggered_by: 'system',
          snapshot_at: memory.created_at
        }]);
        setDiffs([]);
      }
    } catch {
      setSnapshots([{
        snapshot_id: `snap_${memory.id}_1`,
        memory_id: memory.id,
        version: 1,
        content: memory.content,
        trigger: 'initial',
        triggered_by: 'system',
        snapshot_at: memory.created_at
      }]);
      setDiffs([]);
    } finally {
      
    }
  };

  const handleRestore = async (memoryId: string, toVersion: number) => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/versioning/rollback`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ memory_id: memoryId, to_version: toVersion })
      });
      if (res.ok) {
        const data = await res.json();
        onEditMemory(memoryId, data.restored_content);
      }
    } catch (e) {
      console.error('Failed to rollback:', e);
    } finally {
      setHistoryMemory(null);
    }
  };

  // Stats
  const permanentCount = memories.filter(m => !m.metadata?.longevity_tier || m.metadata?.longevity_tier === 'permanent').length;
  const projectCount = memories.filter(m => m.metadata?.longevity_tier === 'project_bound').length;
  const ephemeralCount = memories.filter(m => m.metadata?.longevity_tier === 'ephemeral').length;

  return (
    <div className="flex-1 flex flex-col h-screen bg-slate-50 overflow-hidden">
      <header className="h-16 border-b border-slate-200 bg-white px-8 flex items-center justify-between shrink-0">
        <div>
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Brain className="w-5 h-5 text-indigo-600" />
            Memory Management Bank
          </h2>
          <p className="text-xs text-slate-500">Inspect, edit, version, or purge what your assistant remembers across sessions</p>
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={onToggleStatus}
            className={`px-3 py-1.5 rounded-lg border text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer ${
              memoryStatus === 'active'
                ? 'border-slate-200 bg-white text-slate-700 hover:bg-slate-50'
                : 'border-amber-200 bg-amber-50 text-amber-700 hover:bg-amber-100'
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

      {/* Tier Stats Bar */}
      <div className="px-8 py-2 bg-white border-b border-slate-100 flex items-center gap-4 text-xs text-slate-500">
        <Clock className="w-3.5 h-3.5 text-slate-400" />
        <span className="font-medium text-slate-700">Longevity Overview:</span>
        <span className="flex items-center gap-1 text-emerald-700 font-semibold">
          <Infinity className="w-3 h-3" /> {permanentCount} permanent
        </span>
        <span className="flex items-center gap-1 text-blue-700 font-semibold">
          <Folder className="w-3 h-3" /> {projectCount} project-bound
        </span>
        <span className="flex items-center gap-1 text-amber-700 font-semibold">
          <Zap className="w-3 h-3" /> {ephemeralCount} ephemeral
        </span>
      </div>

      <div className="p-6 pb-2 space-y-3 max-w-5xl mx-auto w-full">
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

        {/* Category Tabs */}
        <div className="flex items-center gap-1.5 border-b border-slate-200 pb-3">
          {categories.map((c) => (
            <button
              key={c.id}
              type="button"
              onClick={() => setActiveCategory(c.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                activeCategory === c.id
                  ? 'bg-indigo-600 text-white shadow-xs'
                  : 'text-slate-600 hover:bg-slate-100'
              }`}
            >
              {c.label}
            </button>
          ))}
        </div>

        {/* Tier Filter Tabs */}
        <div className="flex items-center gap-1.5">
          {tiers.map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => setActiveTier(t.id)}
              className={`px-3 py-1 rounded-lg text-[10px] font-semibold transition-all cursor-pointer ${
                activeTier === t.id
                  ? 'bg-slate-800 text-white'
                  : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'
              }`}
            >
              {t.label}
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
          filteredMemories.map((m) => {
            const tier = (m.metadata?.longevity_tier as LongevityTier) || 'permanent';
            const expiresAt = m.metadata?.expires_at as string | undefined;
            const isExpired = expiresAt ? new Date(expiresAt).getTime() < Date.now() : false;

            return (
              <div
                key={m.id}
                className={`p-4 bg-white border rounded-xl shadow-xs hover:border-slate-300 transition-all flex items-start justify-between gap-4 ${
                  isExpired ? 'opacity-60 bg-slate-50' : ''
                }`}
              >
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
                    <p className={`text-xs font-medium leading-relaxed ${isExpired ? 'line-through text-slate-400' : 'text-slate-800'}`}>
                      {m.content}
                    </p>
                  )}

                  <div className="flex items-center gap-2 pt-1 flex-wrap">
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 uppercase tracking-wider">
                      {m.category}
                    </span>
                    <LongevityBadge tier={tier} expiresAt={expiresAt} />
                    {m.source_agent && (
                      <span className="text-[10px] px-2 py-0.5 rounded bg-slate-100 text-slate-600 font-medium">
                        Agent: {m.source_agent}
                      </span>
                    )}
                    {isExpired && (
                      <span className="text-[10px] px-2 py-0.5 rounded bg-red-50 text-red-600 font-semibold border border-red-200">
                        Expired
                      </span>
                    )}
                    <span className="text-[10px] text-slate-400">Added {new Date(m.created_at).toLocaleDateString()}</span>
                  </div>
                </div>

                <div className="flex items-center gap-1 shrink-0">
                  <button
                    type="button"
                    onClick={() => openHistory(m)}
                    className="p-1.5 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors cursor-pointer"
                    title="Version History & Contradictions"
                  >
                    <History className="w-3.5 h-3.5" />
                  </button>
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
            );
          })
        )}
      </div>

      {/* Version History Modal */}
      {historyMemory && (
        <VersionHistoryModal
          memoryId={historyMemory.id}
          memoryContent={historyMemory.content}
          snapshots={snapshots}
          diffs={diffs}
          onClose={() => setHistoryMemory(null)}
          onRestore={handleRestore}
        />
      )}
    </div>
  );
};
