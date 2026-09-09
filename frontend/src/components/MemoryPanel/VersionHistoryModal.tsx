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
  initial: 'Initial',
  user_update: 'User Update',
  auto_contradiction: 'Auto-Detected',
  manual_edit: 'Manual Edit',
  rollback: 'Rollback'
};

export const VersionHistoryModal: React.FC<VersionHistoryModalProps> = ({
  memoryId,
  memoryContent,
  snapshots,
  diffs,
  onClose,
  onRestore,
}) => {
  const [activeTab, setActiveTab] = useState<'timeline' | 'diffs'>('timeline');
  const [restoringVersion, setRestoringVersion] = useState<number | null>(null);

  const sortedSnapshots = [...snapshots].sort((a, b) => b.version - a.version);
  const latestVersion = sortedSnapshots.length > 0 ? sortedSnapshots[0].version : 1;

  const handleRestore = (ver: number) => {
    setRestoringVersion(ver);
    onRestore(memoryId, ver);
  };

  return (
    <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 max-w-2xl w-full flex flex-col max-h-[85vh] overflow-hidden">
        {/* Header */}
        <div className="p-6 border-b border-slate-200 flex items-center justify-between bg-slate-50/50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
              <GitBranch className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-slate-900">Version History & Audit Trail</h3>
              <p className="text-xs text-slate-500 font-mono">ID: {memoryId}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Current Live Memory Preview */}
        <div className="px-6 py-3 bg-indigo-50/60 border-b border-indigo-100 flex items-start gap-2">
          <span className="text-[10px] font-bold text-indigo-600 bg-indigo-100 px-2 py-0.5 rounded shrink-0 uppercase">
            Current
          </span>
          <p className="text-xs text-indigo-950 font-medium line-clamp-2">{memoryContent}</p>
        </div>

        {/* Tab Buttons */}
        <div className="px-6 pt-3 flex items-center gap-2 border-b border-slate-200">
          <button
            type="button"
            onClick={() => setActiveTab('timeline')}
            className={`px-3 py-2 text-xs font-semibold border-b-2 transition-all cursor-pointer ${
              activeTab === 'timeline'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            Snapshots Timeline ({snapshots.length})
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('diffs')}
            className={`px-3 py-2 text-xs font-semibold border-b-2 transition-all cursor-pointer ${
              activeTab === 'diffs'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            Contradiction Diffs ({diffs.length})
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-4 flex-1">
          {activeTab === 'timeline' && (
            <div className="relative pl-6 space-y-6 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
              {sortedSnapshots.map((snap) => {
                const isCurrent = snap.version === latestVersion;
                return (
                  <div key={snap.snapshot_id} className="relative group">
                    {/* Circle */}
                    <div className={`absolute -left-[23px] top-1 w-3.5 h-3.5 rounded-full border-2 bg-white ${
                      isCurrent ? 'border-indigo-600 ring-2 ring-indigo-100' : 'border-slate-400'
                    }`} />

                    <div className="bg-slate-50 hover:bg-white border border-slate-200 rounded-xl p-3.5 transition-all">
                      <div className="flex items-center justify-between mb-1.5">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold text-slate-800">Version {snap.version}</span>
                          {isCurrent && (
                            <span className="text-[10px] font-semibold text-indigo-600 bg-indigo-50 px-1.5 py-0.5 rounded">
                              Live
                            </span>
                          )}
                          <span className="text-[10px] text-slate-500">
                            {TRIGGER_LABELS[snap.trigger] || snap.trigger}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] text-slate-400 flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {new Date(snap.snapshot_at).toLocaleString()}
                          </span>
                          {!isCurrent && (
                            <button
                              type="button"
                              onClick={() => handleRestore(snap.version)}
                              disabled={restoringVersion === snap.version}
                              className="px-2 py-0.5 text-[11px] font-medium text-indigo-600 hover:bg-indigo-50 rounded border border-indigo-200 flex items-center gap-1 transition-colors cursor-pointer"
                              title="Revert to this version"
                            >
                              <RotateCcw className="w-3 h-3" />
                              {restoringVersion === snap.version ? 'Restoring...' : 'Restore'}
                            </button>
                          )}
                        </div>
                      </div>
                      <p className="text-xs text-slate-700 leading-relaxed font-sans">{snap.content}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {activeTab === 'diffs' && (
            <div className="space-y-4">
              {diffs.length === 0 ? (
                <p className="text-center text-xs text-slate-400 py-8">
                  No contradiction diffs recorded for this memory yet.
                </p>
              ) : (
                diffs.map((d) => {
                  const sev = SEVERITY_CONFIG[d.contradiction_severity] || SEVERITY_CONFIG.none;
                  return (
                    <div key={d.diff_id} className="border border-slate-200 rounded-xl p-4 space-y-3 bg-white">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2 text-xs font-semibold text-slate-700">
                          <span>v{d.from_version}</span>
                          <ArrowRight className="w-3.5 h-3.5 text-slate-400" />
                          <span>v{d.to_version}</span>
                        </div>
                        <div className={`flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold ${sev.bg} ${sev.color}`}>
                          {sev.icon}
                          <span>{sev.label} ({(d.contradiction_confidence * 100).toFixed(0)}%)</span>
                        </div>
                      </div>

                      <div className="text-xs space-y-1.5 font-mono">
                        <div className="p-2 bg-red-50 border border-red-200 rounded text-red-700">
                          - {d.previous_content}
                        </div>
                        <div className="p-2 bg-emerald-50 border border-emerald-200 rounded text-emerald-700">
                          + {d.new_content}
                        </div>
                      </div>

                      {d.explanation && (
                        <p className="text-[11px] text-slate-500 italic bg-slate-50 p-2 rounded border border-slate-100">
                          Note: {d.explanation}
                        </p>
                      )}
                    </div>
                  );
                })
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-200 bg-slate-50 flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
