import axios from 'axios';
import { ServerInfo, ServerStatusResponse, AgentStatus, Message } from './types';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 5000,
});

// Dashboard API endpoints
export const fetchServers = async (): Promise<ServerInfo[]> => {
  const response = await api.get<ServerInfo[]>('/api/servers');
  return response.data;
};

export const checkServerStatus = async (port: number): Promise<ServerStatusResponse> => {
  const response = await api.get<ServerStatusResponse>(`/api/server/${port}/status`);
  return response.data;
};

export const stopServer = async (port: number): Promise<{ status: string; port: number; pid: string }> => {
  const response = await api.post(`/api/server/${port}/stop`);
  return response.data;
};

export interface ServerStartConfig {
  directory: string;
  name?: string;
  port?: number;
  model?: string;
}

export const startServer = async (config: ServerStartConfig): Promise<any> => {
  const response = await api.post('/api/server/start', config);
  return response.data;
};

// Proxied agentapi endpoints (through backend to avoid CORS)
export const getAgentStatus = async (port: number): Promise<AgentStatus> => {
  try {
    const response = await api.get(`/api/server/${port}/agent-status`);
    return response.data;
  } catch (error) {
    return {
      status: 'error',
      message: 'Server unreachable',
      conversation_id: null
    };
  }
};

export const getMessages = async (port: number, last?: number): Promise<Message[]> => {
  try {
    const url = last ?
      `/api/server/${port}/messages?last=${last}` :
      `/api/server/${port}/messages`;
    const response = await api.get(url);
    return response.data.messages || [];
  } catch (error) {
    return [];
  }
};

export const sendMessage = async (port: number, content: string): Promise<any> => {
  try {
    const response = await api.post(
      `/api/server/${port}/message`,
      {
        content: content,
        type: 'user'  // Add the required type field
      },
      {
        timeout: 30000,
        headers: {
          'Content-Type': 'application/json'
        }
      }
    );
    return response.data;
  } catch (error: any) {
    console.error('Error sending message:', error.response?.data || error.message);
    throw error;
  }
};