import React from 'react';
import { X, ExternalLink, Server, Activity } from 'lucide-react';
import { ServerInfo } from '../types';

interface ServerModalProps {
  server: ServerInfo;
  onClose: () => void;
}

export const ServerModal: React.FC<ServerModalProps> = ({ server, onClose }) => {
  const handleOpenInNewTab = () => {
    window.open(`http://localhost:${server.port}/`, '_blank');
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-lg w-full max-w-7xl h-[90vh] flex flex-col">
        {/* Modal Header */}
        <div className="px-6 py-4 border-b border-gray-700 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Server className="w-5 h-5 text-blue-400" />
              <h2 className="text-xl font-semibold">
                {server.name || `Server on Port ${server.port}`}
              </h2>
            </div>
            <div className="flex items-center gap-2 text-sm text-gray-400">
              <Activity className="w-4 h-4" />
              <span>PID: {server.pid}</span>
              <span>•</span>
              <span>Port: {server.port}</span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleOpenInNewTab}
              className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
              title="Open in new tab"
            >
              <ExternalLink className="w-5 h-5" />
            </button>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
              title="Close"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Body - Full iframe */}
        <div className="flex-1 bg-gray-900">
          <iframe
            src={`http://localhost:${server.port}/`}
            className="w-full h-full border-0 modal-iframe"
            title={`Server ${server.port} - Full View`}
            sandbox="allow-same-origin allow-scripts allow-forms"
          />
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-3 border-t border-gray-700 bg-gray-750">
          <div className="flex items-center justify-between">
            <div className="text-xs text-gray-400">
              Command: <code className="bg-gray-800 px-2 py-1 rounded ml-2">
                {server.command.substring(0, 80)}{server.command.length > 80 ? '...' : ''}
              </code>
            </div>
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors text-sm"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};