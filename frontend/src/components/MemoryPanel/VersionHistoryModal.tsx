import React, { useState } from 'react';
import { X, RotateCcw, Clock, AlertTriangle, CheckCircle, ArrowRight, GitBranch } from 'lucide-react';

interface Snapshot {
  snapshot_id: string;
  version: number;
  content: string;
  trigger: string;
  triggered_by: string;
  snapshot_at: string;
}

interface Diff {
  diff_id: string;
  from_version: number;
  to_version: number;
  previous_content: string;
  new_content: string;
  contradiction_confidence: number;
  contradiction_severity: 'none' | 'low' | 'medium' | 'high';
  explanation: string;
  diff_at: string;
}

interface VersionHistoryModalProps {
  memoryId: string;
  memoryContent: string;
  snapshots: Snapshot[];
  diffs: Diff[];
  onClose: () => void;
  onRestore: (memoryId: string, toVersion: number) => void;
}

const SEVERITY_CONFIG = {
  none: { color: 'text-slate-500', bg: 'bg-slate-50', icon: <CheckCircle className="w-3.5 h-3.5" />, label: 'No Conflict' },
  low: { color: 'text-yellow-600', bg: 'bg-yellow-50', icon: <AlertTriangle className="w-3.5 h-3.5" />, label: 'Low Conflict' },
  medium: { color: 'text-orange-600', bg: 'bg-orange-50', icon: <AlertTriangle className="w-3.5 h-3.5" />, label: 'Medium Conflict' },
  high: { color: 'text-red-600', bg: 'bg-red-50', icon: <AlertTriangle className="w-3.5 h-3.5" />, label: 'High Conflict' },
};

const TRIGGER_LABELS: Record<string, string> = {
  initial: '🌱 Initial',
  user_update: '✏️ User Update',
  auto_contradiction: '⚡ Auto-Detected',
  manual_edit: '🖊️ Manual Edit',
  rollback: '↩️ Rollback',
};

function ConflictBar({ confidence }: { confidence: number }) {
  const pct = Math.round(confidence * 100);
  const color = pct >= 80 ? 'bg-red-500' : pct >= 40 ? 'bg-orange-400' : 'bg-emerald-400';
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
        <div className={h-full rounded-full } style={{ width: ${pct}% }} />
      </div>
      <span className="text-[10px] font-mono text-slate-500 w-8 text-right">{pct}%</span>
    </div>
  );
}

export const VersionHistoryModal: React.FC<VersionHistoryModalProps> = ({
  memoryId,
  memoryContent,
  snapshots,
  diffs,
  onClose,
  onRestore,
}) => {
  const [restoring, setRestoring] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState<'timeline' | 'diffs'>('timeline');

  const handleRestore = async (version: number) => {
    setRestoring(version);
    await onRestore(memoryId, version);
    setRestoring(null);
  };

  const getDiffForVersion = (toVersion: number): Diff | undefined =>
    diffs.find(d => d.to_version === toVersion);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl mx-4 flex flex-col max-h-[85vh]">
        {/* Header */}
        <div className="p-5 border-b border-slate-200 flex items-start justify-between shrink-0">
          <div>
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <GitBranch className="w-4 h-4 text-indigo-600" />
              Version History
            </h3>
            <p className="text-xs text-slate-500 mt-0.5 max-w-md line-clamp-2">{memoryContent}</p>
          </div>
          <button onClick={onClose} className="p-1.5 hover:bg-slate-100 rounded-lg transition-colors cursor-pointer">
            <X className="w-4 h-4 text-slate-500" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 px-5 pt-3 border-b border-slate-100 shrink-0">
          {(['timeline', 'diffs'] as const).map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={px-3 py-1.5 text-xs font-semibold rounded-t-lg capitalize transition-all cursor-pointer }
            >
              {tab === 'timeline' ? 📋 Timeline () : 🔀 Diffs ()}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-5 space-y-3">
          {activeTab === 'timeline' ? (
            [...snapshots].reverse().map((snap) => {
              const diff = getDiffForVersion(snap.version);
              const isLatest = snap.version === snapshots.length;
              const severity = (diff?.contradiction_severity as keyof typeof SEVERITY_CONFIG) || 'none';
              const sevConfig = SEVERITY_CONFIG[severity];

              return (
                <div key={snap.snapshot_id} className={p-4 border rounded-xl }>
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center gap-2">
                        <span className={	ext-[10px] font-bold px-2 py-0.5 rounded-full }>
                          v{snap.version}
                        </span>
                        <span className="text-[10px] text-slate-500">
                          {TRIGGER_LABELS[snap.trigger] || snap.trigger}
                        </span>
                        {diff && (
                          <div className={lex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full  }>
                            {sevConfig.icon}
                            {sevConfig.label}
                          </div>
                        )}
                      </div>
                      <p className="text-xs text-slate-800 font-medium leading-relaxed">{snap.content}</p>
                      {diff && (
                        <div className="pt-1">
                          <p className="text-[10px] text-slate-400 mb-1">Contradiction confidence</p>
                          <ConflictBar confidence={diff.contradiction_confidence} />
                          {diff.explanation && (
                            <p className="text-[10px] text-slate-500 mt-1 italic">{diff.explanation}</p>
                          )}
                        </div>
                      )}
                      <p className="text-[10px] text-slate-400">
                        <Clock className="w-3 h-3 inline mr-1" />
                        {new Date(snap.snapshot_at).toLocaleString()}
                      </p>
                    </div>

                    {!isLatest && (
                      <button
                        onClick={() => handleRestore(snap.version)}
                        disabled={restoring === snap.version}
                        className="shrink-0 px-3 py-1.5 bg-slate-800 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 hover:bg-slate-700 transition-colors cursor-pointer disabled:opacity-50"
                      >
                        <RotateCcw className="w-3 h-3" />
                        {restoring === snap.version ? 'Restoring...' : 'Restore'}
                      </button>
                    )}
                    {isLatest && (
                      <span className="shrink-0 text-[10px] font-semibold text-indigo-600 bg-indigo-50 px-2 py-1 rounded-lg">Current</span>
                    )}
                  </div>
                </div>
              );
            })
          ) : (
            diffs.length === 0 ? (
              <div className="text-center py-12 text-slate-400">
                <GitBranch className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No diffs yet. Update the memory to generate change records.</p>
              </div>
            ) : (
              [...diffs].reverse().map(diff => {
                const severity = (diff.contradiction_severity as keyof typeof SEVERITY_CONFIG);
                const sevConfig = SEVERITY_CONFIG[severity];
                return (
                  <div key={diff.diff_id} className={p-4 border rounded-xl }>
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-[10px] font-bold text-slate-600">v{diff.from_version}</span>
                      <ArrowRight className="w-3 h-3 text-slate-400" />
                      <span className="text-[10px] font-bold text-slate-600">v{diff.to_version}</span>
                      <div className={lex items-center gap-1 text-[10px] font-semibold px-2 py-0.5 rounded-full border  }>
                        {sevConfig.icon}
                        {sevConfig.label}
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div>
                        <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-0.5">Before</p>
                        <p className="text-xs text-slate-600 line-through opacity-70">{diff.previous_content}</p>
                      </div>
                      <div>
                        <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-0.5">After</p>
                        <p className="text-xs text-slate-800 font-medium">{diff.new_content}</p>
                      </div>
                      <ConflictBar confidence={diff.contradiction_confidence} />
                      {diff.explanation && <p className="text-[10px] text-slate-500 italic">{diff.explanation}</p>}
                    </div>
                  </div>
                );
              })
            )
          )}
        </div>
      </div>
    </div>
  );
};
