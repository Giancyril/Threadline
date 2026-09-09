export type MemoryCategory = 'preferences' | 'biographical' | 'projects' | 'communication_style';

export interface MemoryItem {
  id: string;
  content: string;
  category: MemoryCategory;
  source_agent?: string;
  session_id?: string;
  created_at: string;
  updated_at?: string;
  score?: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  memories_used?: MemoryItem[];
}
