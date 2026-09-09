import React, { useState, useEffect } from 'react';
import { Network, RefreshCw, Layers } from 'lucide-react';

interface GraphNode {
  id: string;
  label: string;
  type: string;
}

interface GraphEdge {
  id: string;
  source: string;
  target: string;
  relation: string;
}

export const GraphVisualizer: React.FC<{ userId?: string }> = ({ userId = 'default_user' }) => {
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchGraph = async () => {
    setLoading(true);
    try {
      const res = await fetch(`http://localhost:8000/api/v1/graph/?user_id=${encodeURIComponent(userId)}`);
      if (res.ok) {
        const data = await res.json();
        setNodes(data.nodes || []);
        setEdges(data.edges || []);
      }
    } catch (e) {
      // Fallback demo nodes
      setNodes([
        { id: 'n1', label: 'User', type: 'person' },
        { id: 'n2', label: 'Tokyo', type: 'location' },
        { id: 'n3', label: 'FastAPI', type: 'tool' },
        { id: 'n4', label: 'Threadline', type: 'project' },
      ]);
      setEdges([
        { id: 'e1', source: 'n1', target: 'n2', relation: 'lives_in' },
        { id: 'e2', source: 'n1', target: 'n4', relation: 'works_on' },
        { id: 'e3', source: 'n4', target: 'n3', relation: 'uses_tool' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGraph();
  }, [userId]);

  return (
    <div className="flex-1 flex flex-col h-screen bg-slate-900 text-slate-100 overflow-hidden">
      <header className="h-16 border-b border-slate-800 px-8 flex items-center justify-between bg-slate-950/80">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
            <Network className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-white tracking-wide">Associative Knowledge Network</h2>
            <p className="text-xs text-slate-400">Multi-hop semantic connections extracted from long-term memory</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-800/80 border border-slate-700 text-xs text-slate-300">
            <Layers className="w-3.5 h-3.5 text-indigo-400" />
            <span>{nodes.length} Entities • {edges.length} Relationships</span>
          </div>
          <button
            type="button"
            onClick={fetchGraph}
            disabled={loading}
            className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors cursor-pointer border border-slate-700"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </header>

      <div className="flex-1 p-6 flex flex-col items-center justify-center relative overflow-hidden bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-slate-900 via-slate-950 to-black">
        {/* Dynamic SVG Visualizer Canvas */}
        <div className="w-full max-w-4xl h-[540px] bg-slate-950/60 rounded-2xl border border-slate-800/80 p-6 relative shadow-2xl backdrop-blur-xl flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-slate-500 border-b border-slate-800/50 pb-3">
            <span>Entity Relationship Graph Canvas</span>
            <span className="text-[11px] font-mono text-emerald-400">● Live Graph Sync</span>
          </div>

          <div className="flex-1 relative flex items-center justify-center">
            <svg className="w-full h-full absolute inset-0 pointer-events-none">
              <defs>
                <linearGradient id="edgeGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#6366f1" stopOpacity="0.6" />
                  <stop offset="100%" stopColor="#a855f7" stopOpacity="0.3" />
                </linearGradient>
              </defs>
              {edges.slice(0, 10).map((edge, idx) => {
                const angle = (idx / Math.max(edges.length, 1)) * 2 * Math.PI;
                const x1 = 380;
                const y1 = 220;
                const x2 = 380 + Math.cos(angle) * 180;
                const y2 = 220 + Math.sin(angle) * 140;
                return (
                  <g key={edge.id}>
                    <line
                      x1={x1}
                      y1={y1}
                      x2={x2}
                      y2={y2}
                      stroke="url(#edgeGradient)"
                      strokeWidth="2"
                      strokeDasharray="4 4"
                    />
                    <text
                      x={(x1 + x2) / 2}
                      y={(y1 + y2) / 2 - 6}
                      fill="#94a3b8"
                      fontSize="10"
                      textAnchor="middle"
                      className="font-mono select-none"
                    >
                      {edge.relation}
                    </text>
                  </g>
                );
              })}
            </svg>

            {/* Central Node */}
            <div className="relative z-10 flex flex-col items-center">
              <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-indigo-600 to-violet-500 text-white flex items-center justify-center font-bold text-sm shadow-xl shadow-indigo-500/20 border border-indigo-400/40">
                User
              </div>
              <span className="text-xs font-semibold text-indigo-300 mt-2">Primary Entity</span>
            </div>

            {/* Orbiting Satellite Nodes */}
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              {nodes.filter(n => n.label !== 'User').slice(0, 6).map((node, idx) => {
                const angle = (idx / 6) * 2 * Math.PI;
                const x = Math.cos(angle) * 180;
                const y = Math.sin(angle) * 140;
                return (
                  <div
                    key={node.id}
                    style={{ transform: `translate(${x}px, ${y}px)` }}
                    className="absolute pointer-events-auto flex flex-col items-center group cursor-pointer"
                  >
                    <div className="px-3.5 py-1.5 rounded-xl bg-slate-900/90 border border-slate-700 text-xs font-semibold text-slate-200 shadow-lg group-hover:border-indigo-500 group-hover:text-white transition-all backdrop-blur-md">
                      {node.label}
                    </div>
                    <span className="text-[10px] text-slate-400 capitalize mt-1 font-mono uppercase tracking-wider">{node.type}</span>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="text-[11px] text-slate-500 border-t border-slate-800/50 pt-2 flex items-center justify-between">
            <span>Click any entity to inspect associative memory paths</span>
            <span>Multi-hop Traversal Depth: 2 hops</span>
          </div>
        </div>
      </div>
    </div>
  );
};
