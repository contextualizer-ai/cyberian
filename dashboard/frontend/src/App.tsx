import React, { useState, useEffect, useRef } from 'react';
import GridLayout from 'react-grid-layout';
import { ServerCard } from './components/ServerCard';
import { ServerModal } from './components/ServerModal';
import { ServerStartModal, ServerStartConfig } from './components/ServerStartModal';
import { useWebSocket } from './hooks/useWebSocket';
import { ServerInfo } from './types';
import { fetchServers, startServer } from './api';
import { Plus } from 'lucide-react';
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';
import './App.css';

function App() {
  const [servers, setServers] = useState<ServerInfo[]>([]);
  const [selectedServer, setSelectedServer] = useState<ServerInfo | null>(null);
  const [showStartModal, setShowStartModal] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [containerWidth, setContainerWidth] = useState(1200);

  // Use WebSocket for real-time updates (optional - can work without it)
  useWebSocket('ws://localhost:8000/ws', (message) => {
    if (message.type === 'server_list') {
      setServers(message.servers);
      setLoading(false);
      setError(null); // Clear error on successful update
    } else if (message.action === 'server_started') {
      // Server was started, refresh the list
      console.log('New server started:', message);
      setTimeout(() => loadServers(), 1000);
    }
  });

  // Initial load
  useEffect(() => {
    loadServers();

    // Update container width on resize
    const handleResize = () => {
      if (containerRef.current) {
        setContainerWidth(containerRef.current.offsetWidth);
      }
    };

    window.addEventListener('resize', handleResize);
    handleResize();

    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const loadServers = async () => {
    try {
      setError(null);
      const data = await fetchServers();
      setServers(data);
      setLoading(false);
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail ||
                       err.message ||
                       'Failed to load servers. Make sure agentapi servers are running.';
      setError(errorMsg);
      setLoading(false);
      console.error('Error loading servers:', err);
    }
  };

  const handleServerClick = (server: ServerInfo) => {
    setSelectedServer(server);
  };

  const handleCloseModal = () => {
    setSelectedServer(null);
  };

  const handleStartServer = async (config: ServerStartConfig) => {
    try {
      const result = await startServer(config);
      console.log('Server started:', result);
      // Reload servers after a short delay to allow server to initialize
      setTimeout(() => loadServers(), 2000);
    } catch (error) {
      console.error('Failed to start server:', error);
      throw error; // Let the modal handle the error display
    }
  };

  // Load saved layout from localStorage
  const loadSavedLayout = () => {
    try {
      const saved = localStorage.getItem('dashboard-layout');
      if (saved) {
        return JSON.parse(saved);
      }
    } catch (e) {
      console.error('Failed to load saved layout:', e);
    }
    return null;
  };

  // Generate or load grid layout
  const generateLayout = () => {
    const savedLayout = loadSavedLayout();
    const cols = Math.max(1, Math.floor(containerWidth / 350));

    return servers.map((server, index) => {
      const itemKey = `server-${server.port}`;

      // Check if we have a saved position for this server
      const savedItem = savedLayout?.find((item: any) => item.i === itemKey);

      if (savedItem) {
        // Use saved position but ensure it fits in current grid
        return {
          ...savedItem,
          minW: 1,
          maxW: 2,  // Allow some resizing
          minH: 1,
          maxH: 2
        };
      }

      // Default position for new servers
      return {
        i: itemKey,
        x: (index % cols),
        y: Math.floor(index / cols),
        w: 1,
        h: 1,
        minW: 1,
        maxW: 2,
        minH: 1,
        maxH: 2
      };
    });
  };

  // Save layout when it changes
  const handleLayoutChange = (newLayout: any) => {
    try {
      localStorage.setItem('dashboard-layout', JSON.stringify(newLayout));
    } catch (e) {
      console.error('Failed to save layout:', e);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-900">
        <div className="text-white text-xl">Loading servers...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-900">
        <div className="text-center">
          <div className="text-red-500 text-xl mb-4">{error}</div>
          <button
            onClick={() => {
              setLoading(true);
              setError(null);
              loadServers();
            }}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
          >
            Retry
          </button>
          <div className="mt-4 text-gray-400 text-sm">
            <p>Make sure agentapi servers are running:</p>
            <code className="bg-gray-800 px-2 py-1 rounded mt-2 inline-block">
              agentapi server --port 4800
            </code>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <header className="bg-gray-800 border-b border-gray-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Cyberian Dashboard</h1>
          <div className="flex items-center gap-4">
            <span className="text-gray-400">
              {servers.length} server{servers.length !== 1 ? 's' : ''} running
            </span>
            <button
              onClick={() => setShowStartModal(true)}
              className="px-3 py-2 bg-green-600 hover:bg-green-700 rounded-lg transition-colors flex items-center gap-2"
              title="Start a new agentapi server"
            >
              <Plus className="w-4 h-4" />
              Start Server
            </button>
            <button
              onClick={() => {
                localStorage.removeItem('dashboard-layout');
                window.location.reload();
              }}
              className="px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors text-sm"
              title="Reset card positions to default"
            >
              Reset Layout
            </button>
            <button
              onClick={loadServers}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
            >
              Refresh
            </button>
          </div>
        </div>
      </header>

      <main className="p-6" ref={containerRef}>
        {servers.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-400 text-lg mb-4">No servers are currently running</p>
            <p className="text-gray-500">
              Start servers using: <code className="bg-gray-800 px-2 py-1 rounded">
                agentapi server --port 4800
              </code>
            </p>
          </div>
        ) : (
          <GridLayout
            className="layout"
            layout={generateLayout()}
            cols={Math.max(1, Math.floor(containerWidth / 350))}
            rowHeight={440}  // Increased height for drag handle and content
            width={containerWidth}
            isDraggable={true}  // Enable drag-and-drop
            isResizable={true}  // Enable resizing
            compactType={null}  // Allow free positioning
            margin={[20, 20]}
            containerPadding={[0, 0]}
            useCSSTransforms={true}
            onLayoutChange={handleLayoutChange}
          >
            {servers.map((server) => (
              <div key={`server-${server.port}`}>
                <ServerCard
                  server={server}
                  onClick={() => handleServerClick(server)}
                />
              </div>
            ))}
          </GridLayout>
        )}
      </main>

      {selectedServer && (
        <ServerModal
          server={selectedServer}
          onClose={handleCloseModal}
        />
      )}

      <ServerStartModal
        isOpen={showStartModal}
        onClose={() => setShowStartModal(false)}
        onStart={handleStartServer}
      />
    </div>
  );
}

export default App;