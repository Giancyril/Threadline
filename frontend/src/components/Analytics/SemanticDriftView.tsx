import React, { useState, useEffect } from 'react';
import { TrendingUp, AlertTriangle, CheckCircle, Compass, Zap, ArrowRight, Activity, ShieldAlert } from 'lucide-react';
import { TopicClusterView, TopicClusterData } from './TopicClusterView';

interface DriftPoint {
  timestamp: string;
  window_label: string;
  drift_distance: number;
  drift_velocity: number;
  active_cluster_count: number;
  divergence_score: number;
  dominant_topic?: string;
}

interface DivergenceAlert {
  alert_id: string;
  topic: string;
  previous_preference: string;
  current_preference: string;
  divergence_score: number;
  severity: string;
  recommendation: string;
  acknowledged: boolean;
}

interface DriftAnalysisSummary {
  total_memories: number;
  clusters: TopicClusterData[];
  drift_points: DriftPoint[];
  divergence_alerts: DivergenceAlert[];
  overall_drift_status: 'stable' | 'drifting' | 'volatile';
  mean_velocity: number;
}

export const SemanticDriftView: React.FC = () => {
  const [subTab, setSubTab] = useState<'drift' | 'clusters'>('drift');
  const [data, setData] = useState<DriftAnalysisSummary | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchDriftData = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/v1/analytics/drift');
      if (res.ok) {
        const json = await res.json();
        setData(json);
      }
    } catch {
      // Offline fallback state for demo
      setData({
        total_memories: 6,
        clusters: [
          {
            cluster_id: 'cluster_1',
            name: 'Preferences: Fastapi, Python',
            keywords: ['fastapi', 'python', 'async', 'backend'],
            memory_ids: ['mem_1', 'mem_2'],
            cohesion_score: 0.88,
            created_at: new Date().toISOString()
          },
          {
            cluster_id: 'cluster_2',
            name: 'Projects: Vector, AI',
            keywords: ['chromadb', 'embeddings', 'memory'],
            memory_ids: ['mem_3', 'mem_4'],
            cohesion_score: 0.92,
            created_at: new Date().toISOString()
          }
        ],
        drift_points: [
          { timestamp: new Date(Date.now() - 21 * 86400000).toISOString(), window_label: 'Week 1', drift_distance: 0.0, drift_velocity: 0.0, active_cluster_count: 2, divergence_score: 0.0, dominant_topic: 'FastAPI' },
          { timestamp: new Date(Date.now() - 14 * 86400000).toISOString(), window_label: 'Week 2', drift_distance: 0.22, drift_velocity: 0.22, active_cluster_count: 3, divergence_score: 0.33, dominant_topic: 'Vector DBs' },
          { timestamp: new Date(Date.now() - 7 * 86400000).toISOString(), window_label: 'Week 3', drift_distance: 0.45, drift_velocity: 0.45, active_cluster_count: 4, divergence_score: 0.67, dominant_topic: 'Memory Arch' },
          { timestamp: new Date().toISOString(), window_label: 'Week 4', drift_distance: 0.68, drift_velocity: 0.68, active_cluster_count: 4, divergence_score: 0.85, dominant_topic: 'Rust & Federation' }
        ],
        divergence_alerts: [
          {
            alert_id: 'alert_1',
            topic: 'Programming Language',
            previous_preference: 'User prefers Python and FastAPI for all backend development.',
            current_preference: 'Transitioning all performance-critical services from Python to Rust.',
            divergence_score: 0.85,
            severity: 'high',
            recommendation: 'User shifted programming language preference from Python to Rust. Suggest deprecating historical Python memory.',
            acknowledged: false
          }
        ],
        overall_drift_status: 'drifting',
        mean_velocity: 0.338
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDriftData();
  }, []);

  const acknowledgeAlert = async (alertId: string) => {
    try {
      await fetch(`http://localhost:8000/api/v1/analytics/alerts/${alertId}/acknowledge`, { method: 'POST' });
    } catch {
      // Ignore
    }
    if (data) {
      setData({
        ...data,
        divergence_alerts: data.divergence_alerts.map(a =>
          a.alert_id === alertId ? { ...a, acknowledged: true } : a
        )
      });
    }
  };

  if (loading || !data) {
    return (
      <div className="flex-1 flex items-center justify-center bg-slate-50 text-xs text-slate-400">
        <Activity className="w-5 h-5 animate-spin mr-2 text-indigo-600" />
        Calculating semantic drift vectors & topic topology...
      </div>
    );
  }

  const statusColors = {
    stable: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    drifting: 'bg-amber-50 text-amber-700 border-amber-200',
    volatile: 'bg-red-50 text-red-700 border-red-200',
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-50 overflow-hidden">
      {/* Top Header */}
      <header className="h-16 border-b border-slate-200 bg-white px-8 flex items-center justify-between shrink-0">
        <div>
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-indigo-600" />
            Semantic Drift & Topic Topology
          </h2>
          <p className="text-xs text-slate-500">Monitor temporal centroid trajectory and intent divergence over time</p>
        </div>

        {/* Tab switch */}
        <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-xl">
          <button
            type="button"
            onClick={() => setSubTab('drift')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              subTab === 'drift' ? 'bg-white text-indigo-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Drift Velocity & Alerts
          </button>
          <button
            type="button"
            onClick={() => setSubTab('clusters')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              subTab === 'clusters' ? 'bg-white text-indigo-700 shadow-xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Topic Clusters ({data.clusters.length})
          </button>
        </div>
      </header>

      {subTab === 'clusters' ? (
        <TopicClusterView clusters={data.clusters} />
      ) : (
        <div className="flex-1 overflow-y-auto p-8 space-y-6 max-w-6xl mx-auto w-full">
          {/* Key Metric Cards */}
          <div className="grid grid-cols-4 gap-4">
            <div className="p-4 bg-white border border-slate-200 rounded-2xl shadow-xs">
              <span className="text-slate-500 text-xs font-medium flex items-center gap-1.5">
                <Compass className="w-3.5 h-3.5 text-indigo-600" /> Drift Status
              </span>
              <div className="mt-2 flex items-center gap-2">
                <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full border uppercase tracking-wider ${statusColors[data.overall_drift_status]}`}>
                  {data.overall_drift_status}
                </span>
              </div>
              <p className="text-[11px] text-slate-400 mt-2">Centroid movement variance</p>
            </div>

            <div className="p-4 bg-white border border-slate-200 rounded-2xl shadow-xs">
              <span className="text-slate-500 text-xs font-medium flex items-center gap-1.5">
                <Zap className="w-3.5 h-3.5 text-amber-600" /> Drift Velocity
              </span>
              <div className="mt-2 text-xl font-extrabold text-slate-900">
                {data.mean_velocity.toFixed(3)} <span className="text-xs text-slate-400 font-normal">dist/day</span>
              </div>
              <p className="text-[11px] text-slate-400 mt-2">Rate of semantic shift</p>
            </div>

            <div className="p-4 bg-white border border-slate-200 rounded-2xl shadow-xs">
              <span className="text-slate-500 text-xs font-medium flex items-center gap-1.5">
                <Activity className="w-3.5 h-3.5 text-blue-600" /> Active Clusters
              </span>
              <div className="mt-2 text-xl font-extrabold text-slate-900">
                {data.clusters.length}
              </div>
              <p className="text-[11px] text-slate-400 mt-2">Across {data.total_memories} memories</p>
            </div>

            <div className="p-4 bg-white border border-slate-200 rounded-2xl shadow-xs">
              <span className="text-slate-500 text-xs font-medium flex items-center gap-1.5">
                <ShieldAlert className="w-3.5 h-3.5 text-rose-600" /> Divergence Alerts
              </span>
              <div className="mt-2 text-xl font-extrabold text-slate-900">
                {data.divergence_alerts.filter(a => !a.acknowledged).length}
              </div>
              <p className="text-[11px] text-slate-400 mt-2">Requires review</p>
            </div>
          </div>

          {/* Temporal Drift Trend Graph */}
          <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-900">Centroid Trajectory Over Time</h3>
                <p className="text-xs text-slate-500">Sliding-window cosine distance from initial baseline embedding</p>
              </div>
              <span className="text-xs text-indigo-600 font-mono font-semibold">4 Temporal Windows</span>
            </div>

            {/* SVG Trend Line Chart */}
            <div className="h-44 w-full relative pt-4">
              <svg className="w-full h-full overflow-visible" viewBox="0 0 500 120">
                {/* Horizontal Grid lines */}
                <line x1="0" y1="20" x2="500" y2="20" stroke="#f1f5f9" strokeWidth="1" />
                <line x1="0" y1="60" x2="500" y2="60" stroke="#f1f5f9" strokeWidth="1" />
                <line x1="0" y1="100" x2="500" y2="100" stroke="#f1f5f9" strokeWidth="1" />

                {/* SVG Polyline */}
                {data.drift_points.length > 1 && (
                  <>
                    <polyline
                      fill="none"
                      stroke="#6366f1"
                      strokeWidth="3"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      points={data.drift_points.map((p, idx) => {
                        const x = 30 + (idx * (440 / (data.drift_points.length - 1)));
                        const y = 100 - (p.drift_distance * 90);
                        return `${x},${y}`;
                      }).join(' ')}
                    />
                    {data.drift_points.map((p, idx) => {
                      const x = 30 + (idx * (440 / (data.drift_points.length - 1)));
                      const y = 100 - (p.drift_distance * 90);
                      return (
                        <g key={idx}>
                          <circle cx={x} cy={y} r="5" fill="#ffffff" stroke="#4f46e5" strokeWidth="3" />
                          <text x={x} y="118" fontSize="9" fill="#94a3b8" textAnchor="middle" fontFamily="sans-serif">
                            {p.window_label}
                          </text>
                          <text x={x} y={y - 8} fontSize="9" fontWeight="bold" fill="#4f46e5" textAnchor="middle" fontFamily="sans-serif">
                            {p.drift_distance.toFixed(2)}
                          </text>
                        </g>
                      );
                    })}
                  </>
                )}
              </svg>
            </div>
          </div>

          {/* Divergence Alerts Panel */}
          <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-4">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-600" />
              Preference Shift & Divergence Notifications
            </h3>

            {data.divergence_alerts.length === 0 ? (
              <p className="text-xs text-slate-400 text-center py-4">No preference shifts detected across memory history.</p>
            ) : (
              <div className="space-y-3">
                {data.divergence_alerts.map((alert) => (
                  <div
                    key={alert.alert_id}
                    className={`p-4 rounded-xl border transition-all flex items-start justify-between gap-4 ${
                      alert.acknowledged
                        ? 'bg-slate-50/70 border-slate-200 opacity-60'
                        : 'bg-amber-50/40 border-amber-200 shadow-xs'
                    }`}
                  >
                    <div className="space-y-2 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-bold uppercase tracking-wider bg-amber-100 text-amber-800 px-2 py-0.5 rounded">
                          {alert.topic}
                        </span>
                        <span className="text-[10px] font-semibold text-rose-600">
                          {(alert.divergence_score * 100).toFixed(0)}% Divergence
                        </span>
                      </div>

                      <div className="flex items-center gap-3 text-xs">
                        <span className="line-through text-slate-400 bg-white px-2 py-1 rounded border border-slate-200">
                          {alert.previous_preference}
                        </span>
                        <ArrowRight className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                        <span className="font-semibold text-slate-800 bg-white px-2 py-1 rounded border border-amber-200">
                          {alert.current_preference}
                        </span>
                      </div>

                      <p className="text-[11px] text-slate-600 bg-white/80 p-2 rounded border border-slate-100 italic">
                        {alert.recommendation}
                      </p>
                    </div>

                    {!alert.acknowledged && (
                      <button
                        type="button"
                        onClick={() => acknowledgeAlert(alert.alert_id)}
                        className="px-3 py-1.5 text-xs font-semibold text-indigo-700 bg-indigo-50 border border-indigo-200 rounded-lg hover:bg-indigo-100 transition-colors flex items-center gap-1 cursor-pointer shrink-0"
                      >
                        <CheckCircle className="w-3.5 h-3.5" />
                        Acknowledge
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
