export type MemoryCategory = 'preferences' | 'biographical' | 'projects' | 'communication_style';
export type LongevityTier = 'ephemeral' | 'project_bound' | 'permanent';

export interface MemoryMetadata {
  longevity_tier?: LongevityTier;
  expires_at?: string | null;
  decay_half_life_days?: number;
  is_archived?: boolean;
  [key: string]: unknown;
}

export interface MemoryItem {
  id: string;
  content: string;
  category: MemoryCategory;
  source_agent?: string;
  session_id?: string;
  created_at: string;
  updated_at?: string;
  score?: number;
  metadata?: MemoryMetadata;
  topic_key?: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  memories_used?: MemoryItem[];
}

export interface MemorySnapshot {
  snapshot_id: string;
  memory_id: string;
  version: number;
  content: string;
  trigger: string;
  triggered_by: string;
  snapshot_at: string;
}

export interface MemoryDiff {
  diff_id: string;
  memory_id: string;
  from_version: number;
  to_version: number;
  previous_content: string;
  new_content: string;
  contradiction_confidence: number;
  contradiction_severity: 'none' | 'low' | 'medium' | 'high';
  explanation: string;
  diff_at: string;
}

export interface KnowledgeNode {
  id: string;
  label: string;
  entity_type: string;
  canonical_name: string;
}

export interface KnowledgeEdge {
  id: string;
  source_id: string;
  target_id: string;
  relation: string;
  weight: number;
}

export interface GraphData {
  nodes: KnowledgeNode[];
  edges: KnowledgeEdge[];
}
