export interface ServerInfo {
  pid: string;
  port: number;
  name: string | null;
  command: string;
  status: string;
  url: string;
}

export interface ServerStatusResponse {
  port: number;
  status: 'healthy' | 'unhealthy' | 'unreachable';
  response_time?: number;
  error?: string;
}

export interface WebSocketMessage {
  type: 'server_list' | 'server_stopped';
  servers?: ServerInfo[];
  port?: number;
}

export interface AgentStatus {
  status: 'ready' | 'thinking' | 'responding' | 'error';
  message?: string;
  conversation_id?: string | null;
  model?: string;
}

export interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp?: string;
  id?: string;
}