import React, { useState } from 'react';
import { Layers, Tag, Database, Activity, CheckCircle, ChevronRight, Hash } from 'lucide-react';

export interface TopicClusterData {
  cluster_id: string;
  name: string;
  keywords: string[];
  memory_ids: string[];
  cohesion_score: number;
  created_at: string;
}

interface TopicClusterViewProps {
  clusters: TopicClusterData[];
  onSelectCluster?: (clusterId: string) => void;
}

export const TopicClusterView: React.FC<TopicClusterViewProps> = ({ clusters, onSelectCluster }) => {
  const [selectedClusterId, setSelectedClusterId] = useState<string | null>(
    clusters.length > 0 ? clusters[0].cluster_id : null
  );

  const selectedCluster = clusters.find(c => c.cluster_id === selectedClusterId);

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-50 overflow-hidden">
      {/* Header bar */}
      <div className="p-6 bg-white border-b border-slate-200 flex items-center justify-between">
        <div>
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Layers className="w-5 h-5 text-indigo-600" />
            Semantic Topic Clusters
          </h3>
          <p className="text-xs text-slate-500">
            Unsupervised density clustering grouping memories by conceptual domains
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200">
            {clusters.length} Active Clusters
          </span>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden p-6 gap-6 max-w-7xl mx-auto w-full">
        {/* Cluster List */}
        <div className="w-1/2 overflow-y-auto space-y-3 pr-2">
          {clusters.map((cluster) => {
            const isSelected = cluster.cluster_id === selectedClusterId;
            const cohesionPct = Math.round(cluster.cohesion_score * 100);

            return (
              <div
                key={cluster.cluster_id}
                onClick={() => {
                  setSelectedClusterId(cluster.cluster_id);
                  onSelectCluster?.(cluster.cluster_id);
                }}
                className={`p-4 rounded-xl border transition-all cursor-pointer ${
                  isSelected
                    ? 'bg-white border-indigo-600 shadow-md ring-2 ring-indigo-100'
                    : 'bg-white border-slate-200 hover:border-slate-300 shadow-xs'
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h4 className="text-sm font-bold text-slate-900">{cluster.name}</h4>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-[11px] text-slate-500 flex items-center gap-1">
                        <Database className="w-3 h-3 text-slate-400" />
                        {cluster.memory_ids.length} memories
                      </span>
                      <span className="text-slate-300">·</span>
                      <span className="text-[11px] font-semibold text-emerald-700 flex items-center gap-1">
                        <Activity className="w-3 h-3" />
                        {cohesionPct}% cohesion
                      </span>
                    </div>
                  </div>
                  <ChevronRight className={`w-4 h-4 transition-transform ${isSelected ? 'text-indigo-600 translate-x-1' : 'text-slate-400'}`} />
                </div>

                {/* Cohesion progress bar */}
                <div className="w-full bg-slate-100 h-1.5 rounded-full mt-3 overflow-hidden">
                  <div
                    className="bg-indigo-600 h-full rounded-full transition-all duration-500"
                    style={{ width: `${cohesionPct}%` }}
                  />
                </div>

                {/* Keywords */}
                <div className="flex flex-wrap gap-1.5 mt-3">
                  {cluster.keywords.map((kw, i) => (
                    <span
                      key={i}
                      className="px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 text-[10px] font-medium flex items-center gap-1"
                    >
                      <Hash className="w-2.5 h-2.5 text-slate-400" />
                      {kw}
                    </span>
                  ))}
                </div>
              </div>
            );
          })}
        </div>

        {/* Cluster Inspector Drawer */}
        <div className="w-1/2 bg-white rounded-2xl border border-slate-200 p-6 flex flex-col shadow-xs overflow-hidden">
          {selectedCluster ? (
            <div className="flex-1 flex flex-col overflow-hidden space-y-4">
              <div>
                <div className="flex items-center gap-2">
                  <Tag className="w-4 h-4 text-indigo-600" />
                  <span className="text-xs font-mono text-slate-400 uppercase tracking-wider">{selectedCluster.cluster_id}</span>
                </div>
                <h3 className="text-lg font-bold text-slate-900 mt-1">{selectedCluster.name}</h3>
              </div>

              <div className="p-4 bg-slate-50 border border-slate-100 rounded-xl space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-500 font-medium">Cluster Semantic Cohesion</span>
                  <span className="font-bold text-indigo-700">{Math.round(selectedCluster.cohesion_score * 100)}%</span>
                </div>
                <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                  <div
                    className="bg-indigo-600 h-full rounded-full"
                    style={{ width: `${Math.round(selectedCluster.cohesion_score * 100)}%` }}
                  />
                </div>
                <p className="text-[11px] text-slate-400">
                  Calculated by pairwise cosine distance of embedded member representations.
                </p>
              </div>

              <div className="flex-1 flex flex-col overflow-hidden">
                <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                  Member Memories ({selectedCluster.memory_ids.length})
                </h4>
                <div className="flex-1 overflow-y-auto space-y-2 pr-1">
                  {selectedCluster.memory_ids.map((memId, idx) => (
                    <div
                      key={idx}
                      className="p-3 bg-white border border-slate-200 rounded-lg text-xs text-slate-700 flex items-start gap-2.5 shadow-2xs"
                    >
                      <CheckCircle className="w-3.5 h-3.5 text-indigo-500 shrink-0 mt-0.5" />
                      <div>
                        <p className="font-mono text-[10px] text-slate-400 mb-0.5">{memId}</p>
                        <p className="font-sans leading-relaxed">Associated memory node in this cluster partition.</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="flex-1 flex items-center justify-center text-center p-8 text-slate-400 text-xs">
              Select a cluster to inspect its keywords and member memories
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
