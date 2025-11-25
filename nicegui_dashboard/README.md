# NiceGUI Dashboard for Cyberian

A simplified, single-file dashboard for managing agentapi servers using NiceGUI.

## Features

✅ **Single Python File** - No separate frontend/backend
✅ **No CORS Issues** - Everything runs in one process
✅ **Auto-Refresh** - Updates every 5 seconds
✅ **Direct Integration** - Uses subprocess directly
✅ **Dark Mode** - Built-in dark theme
✅ **Responsive Grid** - Auto-adjusting card layout

## Installation

```bash
# Install dashboard dependencies (nicegui)
uv sync --group dashboard
```

## Usage

```bash
# Run the dashboard
uv run python nicegui_dashboard/dashboard.py
```

Then open http://localhost:8080 in your browser.

## Features

### Server Management
- **View** all running agentapi servers
- **Start** new servers with directory picker
- **Stop** servers with one click
- **Auto-discovery** of running servers

### Server Monitoring
- Live status indicators (ready, thinking, responding, error)
- Message count display
- Last message preview
- Auto-refresh every 5 seconds

### Quick Messaging
- Send messages directly from each card
- No need to open full chat interface
- See responses in message preview

### Server Controls
- **Open Chat** - Opens full agentapi interface in new tab
- **Stop** - Terminates the server process
- **Start Server** - Launch new servers with:
  - Directory selection (required)
  - Auto-generated name from directory
  - Auto-assigned port (4800-4900)
  - Agent type selection

## Comparison with React Dashboard

### Advantages
- **Single file** (~400 lines) vs complex React/TypeScript/FastAPI setup
- **No build process** - Just run the Python file
- **No CORS/proxy issues** - Direct HTTP calls
- **Built-in auto-refresh** - No WebSocket complexity
- **Simpler deployment** - One Python process

### Limitations
- No drag-and-drop card rearrangement
- No layout persistence (yet)
- Less fancy animations
- Server-side rendering only

## Architecture

```
┌─────────────────┐
│   NiceGUI App   │
│   (Port 8080)   │
│                 │
│  ┌───────────┐  │
│  │  Dashboard │  │───── ps auxwww ──────> [Process List]
│  │    UI      │  │
│  └───────────┘  │───── HTTP calls ─────> [AgentAPI Servers]
│                 │                         (Ports 4800-4900)
└─────────────────┘
```

## Customization

### Change Port
```python
ui.run(port=8080)  # Change to any port
```

### Adjust Refresh Rate
```python
await asyncio.sleep(5)  # Change to desired seconds in auto_refresh()
```

### Modify Grid Layout
```python
ui.grid(columns='repeat(auto-fill, minmax(350px, 1fr))')  # Adjust 350px for card width
```

## Troubleshooting

### Dashboard won't start
- Check port 8080 is free: `lsof -i :8080`
- Install dependencies: `uv sync --group dashboard`

### Servers not showing
- Verify servers are running: `ps aux | grep agentapi`
- Check server ports are in expected range (4800-4900)

### Can't send messages
- Ensure servers are running on localhost
- Check firewall isn't blocking local connections

### Start server fails
- Verify directory exists and is accessible
- Check agentapi is in PATH
- Ensure ports 4800-4900 are available

## Development

### Running in development mode
```bash
# With auto-reload on file changes
uv run python nicegui_dashboard/dashboard.py --reload
```

### Adding features
The entire dashboard is in `dashboard.py`. Key functions:
- `parse_servers()` - Discovers running servers
- `create_server_card()` - Creates UI for each server
- `refresh_servers()` - Updates the display
- `start_new_server()` - Launches new servers

## Future Enhancements

Potential improvements:
- [ ] Layout persistence in localStorage
- [ ] Server grouping/filtering
- [ ] Bulk operations (stop all, restart all)
- [ ] Message history view
- [ ] Server resource monitoring
- [ ] Export/import configurations
- [ ] Custom themes