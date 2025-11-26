import React, { useState, useEffect } from 'react';
import { Server, Activity, MessageSquare, Send, XCircle, Zap, Clock, Eye, Info, GripVertical } from 'lucide-react';
import { ServerInfo, AgentStatus, Message } from '../types';
import { getAgentStatus, getMessages, sendMessage, stopServer } from '../api';
import { MessageTooltip } from './MessageTooltip';
import clsx from 'clsx';

interface ServerCardProps {
  server: ServerInfo;
  onClick: () => void;
}

export const ServerCard: React.FC<ServerCardProps> = ({ server, onClick }) => {
  const [agentStatus, setAgentStatus] = useState<AgentStatus>({ status: 'ready' });
  const [messageCount, setMessageCount] = useState(0);
  const [lastMessage, setLastMessage] = useState<Message | null>(null);
  const [quickMessage, setQuickMessage] = useState('');
  const [sending, setSending] = useState(false);
  const [stopping, setStopping] = useState(false);

  useEffect(() => {
    fetchServerData();
    const interval = setInterval(fetchServerData, 5000); // Update every 5 seconds
    return () => clearInterval(interval);
  }, [server.port]);

  const fetchServerData = async () => {
    try {
      // Fetch status
      const status = await getAgentStatus(server.port);
      setAgentStatus(status);

      // Fetch messages
      const msgs = await getMessages(server.port, 10); // Get last 10 messages
      setMessageCount(msgs.length);

      // Get last user/assistant message
      const lastMsg = msgs.filter(m => m.role !== 'system').pop();
      setLastMessage(lastMsg || null);
    } catch (error) {
      console.error(`Error fetching data for server ${server.port}:`, error);
      // Don't crash - just set error status
      setAgentStatus({ status: 'error', message: 'Failed to fetch data' });
    }
  };

  const handleSendQuickMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!quickMessage.trim() || sending) return;

    setSending(true);
    try {
      await sendMessage(server.port, quickMessage);
      setQuickMessage('');
      // Refresh data after sending
      setTimeout(fetchServerData, 500);
    } catch (error: any) {
      console.error('Failed to send message:', error);
      // More descriptive error message
      const errorMsg = error.response?.data?.detail ||
                       error.response?.data?.message ||
                       error.message ||
                       'Failed to send message';
      alert(`Error sending to port ${server.port}: ${errorMsg}`);
    } finally {
      setSending(false);
    }
  };

  const handleStop = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm(`Stop server on port ${server.port}?`)) return;

    setStopping(true);
    try {
      await stopServer(server.port);
    } catch (error) {
      console.error('Failed to stop server:', error);
      alert('Failed to stop server');
    }
    setStopping(false);
  };

  const statusColor = {
    ready: 'bg-green-500',
    thinking: 'bg-yellow-500',
    responding: 'bg-blue-500',
    error: 'bg-red-500'
  }[agentStatus.status];

  const statusText = {
    ready: 'Ready',
    thinking: 'Thinking...',
    responding: 'Responding...',
    error: 'Error'
  }[agentStatus.status];

  return (
    <div className="h-full bg-gray-800 border border-gray-700 rounded-lg overflow-hidden flex flex-col group">
      {/* Drag Handle Indicator */}
      <div className="flex items-center bg-gray-750 px-2 py-1 border-b border-gray-700 cursor-move">
        <GripVertical className="w-4 h-4 text-gray-500 group-hover:text-gray-400 transition-colors" />
        <span className="text-xs text-gray-500 ml-1 group-hover:text-gray-400 transition-colors">
          Drag to reorder
        </span>
      </div>

      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-700 bg-gray-750">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <Server className="w-4 h-4 text-blue-400" />
            <span className="font-semibold">
              {server.name || `Port ${server.port}`}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <div className={clsx('w-2 h-2 rounded-full', statusColor)} />
            <span className="text-xs text-gray-400">{statusText}</span>
          </div>
        </div>

        <div className="flex items-center gap-3 text-xs text-gray-400">
          <span className="flex items-center gap-1">
            <Activity className="w-3 h-3" />
            PID: {server.pid}
          </span>
          <span>•</span>
          <span>:{server.port}</span>
          {agentStatus.model && (
            <>
              <span>•</span>
              <span className="text-blue-400">{agentStatus.model}</span>
            </>
          )}
        </div>
      </div>

      {/* Status Section */}
      <div className="flex-1 p-4 space-y-3 bg-gray-850">
        {/* Message Stats */}
        <div className="bg-gray-800 rounded p-3">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <MessageSquare className="w-4 h-4 text-gray-400" />
              <span className="text-sm font-medium">Messages</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-2xl font-bold text-blue-400">{messageCount}</span>
              {agentStatus.status === 'error' && (
                <button
                  onClick={() => {
                    setAgentStatus({ status: 'ready' });
                    fetchServerData();
                  }}
                  className="text-xs px-2 py-1 bg-yellow-600 hover:bg-yellow-700 rounded"
                  title="Retry connection"
                >
                  Retry
                </button>
              )}
            </div>
          </div>

          {/* Last Message Preview */}
          {lastMessage && (
            <div className="mt-2 pt-2 border-t border-gray-700">
              <div className="flex items-center gap-1 text-xs text-gray-500 mb-1">
                <Clock className="w-3 h-3" />
                <span>Last {lastMessage.role === 'user' ? 'User' : 'Assistant'} Message:</span>
                <span title="Hover over message to see full text">
                  <Info className="w-3 h-3 ml-auto text-gray-600" />
                </span>
              </div>
              <MessageTooltip
                message={lastMessage.content}
                role={lastMessage.role}
                truncated={
                  <p className="text-xs text-gray-300 line-clamp-2 hover:text-gray-100 transition-colors">
                    {lastMessage.content}
                  </p>
                }
              />
            </div>
          )}

          {messageCount === 0 && (
            <p className="text-xs text-gray-500 mt-2">No messages yet</p>
          )}
        </div>

        {/* Conversation Status */}
        {agentStatus.conversation_id && (
          <div className="bg-gray-800 rounded p-2">
            <div className="flex items-center gap-2 text-xs text-gray-400">
              <Zap className="w-3 h-3" />
              <span>Conversation ID:</span>
              <code className="text-blue-400">{agentStatus.conversation_id.slice(0, 8)}...</code>
            </div>
          </div>
        )}

        {/* Quick Message Input */}
        <form onSubmit={handleSendQuickMessage} className="flex gap-2">
          <input
            type="text"
            value={quickMessage}
            onChange={(e) => setQuickMessage(e.target.value)}
            placeholder="Quick message..."
            className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded text-sm placeholder-gray-400 focus:outline-none focus:border-blue-500"
            disabled={sending}
          />
          <button
            type="submit"
            disabled={sending || !quickMessage.trim()}
            className="px-3 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:text-gray-500 rounded transition-colors"
            title="Send message"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>

      {/* Footer Controls */}
      <div className="px-4 py-2 border-t border-gray-700 bg-gray-750">
        <div className="flex items-center justify-between">
          <button
            onClick={(e) => {
              e.stopPropagation();
              onClick();
            }}
            className="flex items-center gap-2 text-xs px-3 py-1.5 bg-blue-600 hover:bg-blue-700 active:bg-blue-800 rounded transition-colors font-medium"
            type="button"
          >
            <Eye className="w-3 h-3" />
            Full Chat View
          </button>
          <button
            onClick={handleStop}
            disabled={stopping}
            className="text-xs px-3 py-1.5 bg-red-600 hover:bg-red-700 rounded transition-colors disabled:opacity-50 flex items-center gap-1"
          >
            <XCircle className="w-3 h-3" />
            {stopping ? 'Stopping...' : 'Stop'}
          </button>
        </div>
      </div>
    </div>
  );
};