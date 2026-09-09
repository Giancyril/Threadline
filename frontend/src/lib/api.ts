import { ChatMessage, MemoryItem, MemoryCategory } from './types';

const API_BASE = 'http://localhost:8000/api/v1';

export async function sendChatMessage(
  message: string,
  userId: string = 'default_user',
  sessionId: string = 'session_1',
  history: ChatMessage[] = [],
  useMemory: boolean = true,
  learnMemory: boolean = true
) {
  try {
    const res = await fetch(`${API_BASE}/chat/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: userId,
        session_id: sessionId,
        message,
        history: history.map(h => ({ role: h.role, content: h.content })),
        use_memory: useMemory,
        learn_memory: learnMemory,
      }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('Backend offline or unreachable, falling back to client simulation:', err);
    return null;
  }
}

export async function fetchMemories(userId: string = 'default_user', category?: string, search?: string) {
  try {
    let url = `${API_BASE}/memories/?user_id=${encodeURIComponent(userId)}`;
    if (category && category !== 'all') url += `&category=${encodeURIComponent(category)}`;
    if (search) url += `&search=${encodeURIComponent(search)}`;

    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    return data.memories as MemoryItem[];
  } catch (err) {
    console.warn('Backend fetchMemories failed, using local fallback:', err);
    return null;
  }
}

export async function createMemory(content: string, category: MemoryCategory, userId: string = 'default_user') {
  try {
    const res = await fetch(`${API_BASE}/memories/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content, category, user_id: userId }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('Backend createMemory failed:', err);
    return null;
  }
}

export async function updateMemory(id: string, content: string, category?: MemoryCategory) {
  try {
    const res = await fetch(`${API_BASE}/memories/${encodeURIComponent(id)}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content, category }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.warn('Backend updateMemory failed:', err);
    return null;
  }
}

export async function deleteMemory(id: string) {
  try {
    const res = await fetch(`${API_BASE}/memories/${encodeURIComponent(id)}`, {
      method: 'DELETE',
    });
    return res.ok;
  } catch (err) {
    console.warn('Backend deleteMemory failed:', err);
    return false;
  }
}

export async function purgeAllMemories(userId: string = 'default_user') {
  try {
    const res = await fetch(`${API_BASE}/memories/purge/all?user_id=${encodeURIComponent(userId)}`, {
      method: 'DELETE',
    });
    return res.ok;
  } catch (err) {
    console.warn('Backend purgeAllMemories failed:', err);
    return false;
  }
}

export async function getLearningStatus(userId: string = 'default_user') {
  try {
    const res = await fetch(`${API_BASE}/memories/learning/status?user_id=${encodeURIComponent(userId)}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    return data.learning_enabled as boolean;
  } catch (err) {
    console.warn('Backend getLearningStatus failed:', err);
    return true;
  }
}

export async function setLearningStatus(enabled: boolean, userId: string = 'default_user') {
  try {
    const res = await fetch(`${API_BASE}/memories/learning/status?user_id=${encodeURIComponent(userId)}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ learning_enabled: enabled }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    return data.learning_enabled as boolean;
  } catch (err) {
    console.warn('Backend setLearningStatus failed:', err);
    return enabled;
  }
}
