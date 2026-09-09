import React, { useState, useEffect } from 'react';
import { Share2, RefreshCw, Layers, Compass, CheckCircle } from 'lucide-react';

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

const DEFAULT_NODES: GraphNode[] = [
  { id: 'n1', label: 'User', type: 'person' },
  { id: 'n2', label: 'FastAPI', type: 'framework' },
  { id: 'n3', label: 'Python 3.14', type: 'language' },
  { id: 'n4', label: 'Threadline', type: 'project' },
  { id: 'n5', label: 'Vector Store', type: 'database' },
  { id: 'n6', label: 'Concise Tone', type: 'preference' },
];

const DEFAULT_EDGES: GraphEdge[] = [
  { id: 'e1', source: 'n1', target: 'n4', relation: 'builds' },
  { id: 'e2', source: 'n4', target: 'n2', relation: 'powered_by' },
  { id: 'e3', source: 'n2', target: 'n3', relation: 'written_in' },
  { id: 'e4', source: 'n4', target: 'n5', relation: 'indexes_with' },
  { id: 'e5', source: 'n1', target: 'n6', relation: 'prefers' },
];

export const GraphVisualizer: React.FC<{ userId?: string }> = ({ userId = 'default_user' }) => {
  const [nodes, setNodes] = useState<GraphNode[]>(DEFAULT_NODES);
  const [edges, setEdges] = useState<GraphEdge[]>(DEFAULT_EDGES);
  const [loading, setLoading] = useState(false);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  const fetchGraph = async () => {
    setLoading(true);
    try {
      const res = await fetch(`http://localhost:8000/api/v1/graph/?user_id=${encodeURIComponent(userId)}`);
      if (res.ok) {
        const data = await res.json();
        if (data.nodes && data.nodes.length > 0) {
          setNodes(data.nodes);
          setEdges(data.edges || []);
        } else {
          setNodes(DEFAULT_NODES);
          setEdges(DEFAULT_EDGES);
        }
      } else {
        setNodes(DEFAULT_NODES);
        setEdges(DEFAULT_EDGES);
      }
    } catch {
      setNodes(DEFAULT_NODES);
      setEdges(DEFAULT_EDGES);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGraph();
  }, [userId]);

  const satelliteNodes = nodes.filter(n => n.label.toLowerCase() !== 'user').slice(0, 8);

  return (
    <div className="flex-1 flex flex-col h-screen bg-slate-50 text-slate-900 overflow-hidden">
      {/* Header bar - Clean White */}
      <header className="h-16 border-b border-slate-200 bg-white px-8 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
            <Share2 className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              Associative Knowledge Network
            </h2>
            <p className="text-xs text-slate-500">Multi-hop semantic connections extracted from long-term memory</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-slate-50 border border-slate-200 text-xs font-semibold text-slate-700 shadow-2xs">
            <Layers className="w-3.5 h-3.5 text-indigo-600" />
            <span>{nodes.length} Entities · {edges.length} Relationships</span>
          </div>
          <button
            type="button"
            onClick={fetchGraph}
            disabled={loading}
            className="p-2 rounded-lg bg-white hover:bg-slate-50 text-slate-600 transition-colors cursor-pointer border border-slate-200 shadow-2xs"
            title="Refresh Knowledge Graph"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-indigo-600' : ''}`} />
          </button>
        </div>
      </header>

      {/* Main Canvas Workspace */}
      <div className="flex-1 p-8 flex flex-col items-center justify-center relative overflow-hidden bg-slate-50/80">
        {/* Dynamic SVG Visualizer Canvas Card - Clean White with Slate borders */}
        <div className="w-full max-w-5xl h-[560px] bg-white rounded-2xl border border-slate-200 p-6 relative shadow-sm flex flex-col justify-between">
          <div className="flex items-center justify-between text-xs text-slate-500 border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2">
              <Compass className="w-4 h-4 text-indigo-600" />
              <span className="font-semibold text-slate-700">Entity-Relationship Graph Canvas</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-50 border border-emerald-200 text-[11px] font-semibold text-emerald-700">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                Live Graph Sync
              </span>
            </div>
          </div>

          <div className="flex-1 relative flex items-center justify-center overflow-hidden">
            <svg className="w-full h-full absolute inset-0 pointer-events-none">
              <defs>
                <linearGradient id="edgeGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#818cf8" stopOpacity="0.7" />
                  <stop offset="100%" stopColor="#c084fc" stopOpacity="0.5" />
                </linearGradient>
              </defs>
              {edges.slice(0, 10).map((edge, idx) => {
                const angle = (idx / Math.max(edges.length, 1)) * 2 * Math.PI;
                const x1 = 460;
                const y1 = 230;
                const x2 = 460 + Math.cos(angle) * 220;
                const y2 = 230 + Math.sin(angle) * 150;
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
                    <rect
                      x={(x1 + x2) / 2 - 28}
                      y={(y1 + y2) / 2 - 16}
                      width="56"
                      height="16"
                      rx="4"
                      fill="#ffffff"
                      stroke="#e2e8f0"
                      strokeWidth="1"
                    />
                    <text
                      x={(x1 + x2) / 2}
                      y={(y1 + y2) / 2 - 4}
                      fill="#64748b"
                      fontSize="9"
                      fontWeight="600"
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
            <div
              onClick={() => setSelectedNode(nodes.find(n => n.label.toLowerCase() === 'user') || { id: 'user', label: 'User', type: 'person' })}
              className="relative z-10 flex flex-col items-center cursor-pointer group"
            >
              <div className="w-20 h-20 rounded-2xl bg-indigo-600 text-white flex flex-col items-center justify-center font-bold text-sm shadow-lg shadow-indigo-200 border-2 border-indigo-400 group-hover:scale-105 transition-transform">
                <span>User</span>
              </div>
              <span className="text-[11px] font-bold text-indigo-700 mt-2 bg-indigo-50 px-2 py-0.5 rounded-full border border-indigo-200">
                Primary Entity
              </span>
            </div>

            {/* Orbiting Satellite Nodes */}
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              {satelliteNodes.map((node, idx) => {
                const total = Math.max(satelliteNodes.length, 1);
                const angle = (idx / total) * 2 * Math.PI;
                const x = Math.cos(angle) * 220;
                const y = Math.sin(angle) * 150;
                const isSelected = selectedNode?.id === node.id;

                return (
                  <div
                    key={node.id}
                    style={{ transform: `translate(${x}px, ${y}px)` }}
                    className="absolute pointer-events-auto flex flex-col items-center group cursor-pointer"
                    onClick={() => setSelectedNode(node)}
                  >
                    <div className={`px-4 py-2 rounded-xl text-xs font-bold transition-all shadow-xs ${isSelected
                      ? 'bg-indigo-600 text-white border-2 border-indigo-500 scale-105 ring-2 ring-indigo-200'
                      : 'bg-white border border-slate-200 text-slate-800 hover:border-indigo-400 hover:text-indigo-600 hover:shadow-md'
                      }`}>
                      {node.label}
                    </div>
                    <span className="text-[9px] font-semibold text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded mt-1 font-mono uppercase tracking-wider border border-slate-200">
                      {node.type}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Canvas Footer */}
          <div className="text-xs text-slate-500 border-t border-slate-100 pt-3 flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <CheckCircle className="w-3.5 h-3.5 text-indigo-600" />
              {selectedNode ? `Inspecting: ${selectedNode.label} (${selectedNode.type})` : 'Click any entity node to inspect associative connections'}
            </span>
            <span className="font-mono text-[11px] text-slate-400">
              Multi-hop Traversal: Max 2 Hops
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
