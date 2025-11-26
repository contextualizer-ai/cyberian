#!/usr/bin/env python3
"""NiceGUI-based dashboard for managing agentapi servers.

To run:
    uv sync --group dashboard
    uv run python nicegui_dashboard/dashboard.py
"""

import asyncio
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import httpx
from nicegui import ui

# Import cyberian utilities (no more duplication!)
from cyberian.server_utils import (
    get_running_servers,
    find_available_port,
    start_agentapi_server,
    stop_server_by_port
)
from cyberian.agent_client import (
    get_agent_status,
    get_agent_messages,
    send_agent_message
)
from cyberian.dashboard_config import (
    load_dashboard_config,
    save_dashboard_config,
    sync_config_with_running_servers,
    reorder_server_in_config
)
from cyberian.models import ServerConfig

# Store server cards and their UI elements for updates
server_cards: Dict[int, dict] = {}
auto_refresh_task = None


class ServerInfo:
    """Information about a running agentapi server."""

    def __init__(self, pid: str, port: int, name: Optional[str] = None, command: str = ""):
        self.pid = pid
        self.port = port
        self.name = name or f"Port {port}"
        self.command = command
        self.status = "checking"
        self.message_count = 0
        self.last_message = ""
        self.last_update = time.time()
        self.last_message_time = None  # Timestamp of last message


def parse_servers() -> List[ServerInfo]:
    """Get servers in config order with runtime info.

    Uses cyberian utilities - no more ps parsing duplication!
    """
    try:
        # Load config (creates if missing)
        config = load_dashboard_config()

        # Get running servers from ps
        running = get_running_servers()

        # Sync: remove stopped servers, add new ones
        config = sync_config_with_running_servers(config)
        save_dashboard_config(config)

        # Build ServerInfo objects in config order
        servers = []
        running_by_port = {s['port']: s for s in running}

        for server_cfg in config.servers:
            ps_info = running_by_port.get(server_cfg.port)
            if ps_info:
                servers.append(ServerInfo(
                    pid=ps_info['pid'],
                    port=server_cfg.port,
                    name=server_cfg.name or f"Port {server_cfg.port}",
                    command=ps_info['command']
                ))

        return servers

    except Exception as e:
        print(f"Error in parse_servers: {e}")
        # Fallback: just use ps output directly
        try:
            running = get_running_servers()
            return [
                ServerInfo(
                    pid=s['pid'],
                    port=s['port'],
                    name=s.get('name') or f"Port {s['port']}",
                    command=s['command']
                )
                for s in running
            ]
        except Exception:
            return []


async def check_server_status(server: ServerInfo):
    """Check the status and messages of a server using cyberian utilities."""
    try:
        # Check status using agent_client utility
        try:
            status_data = await asyncio.to_thread(get_agent_status, server.port)
            server.status = status_data.get('status', 'ready')
        except Exception:
            server.status = 'unreachable'

        # Get messages using agent_client utility
        try:
            messages = await asyncio.to_thread(get_agent_messages, server.port)
            server.message_count = len(messages)

            # Get last non-system message
            user_messages = [m for m in messages if m.get('role') != 'system']
            if user_messages:
                last = user_messages[-1]
                content = last.get('content', '')
                # Truncate long messages
                if len(content) > 100:
                    content = content[:100] + '...'
                server.last_message = f"[{last.get('role', 'unknown')}] {content}"
                server.last_message_time = datetime.now()
            else:
                server.last_message = ""
                server.last_message_time = None
        except Exception:
            pass

    except Exception as e:
        server.status = 'error'
        print(f"Error checking server {server.port}: {e}")


async def send_message(port: int, content: str, input_element=None):
    """Send a message to a server using cyberian utilities."""
    if not content.strip():
        return

    try:
        # Use agent_client utility to send message
        await asyncio.to_thread(send_agent_message, port, content)
        try:
            ui.notify(f"Message sent to port {port}", type='positive')
        except Exception:
            print(f"Message sent to port {port}")
        # Refresh the server status after a brief delay
        await asyncio.sleep(0.5)
        await refresh_servers()
    except Exception as e:
        try:
            ui.notify(f"Error sending message: {str(e)}", type='negative')
        except Exception:
            print(f"Error sending message: {str(e)}")


async def stop_server(server: ServerInfo):
    """Stop a server using cyberian utilities."""
    try:
        # Use server_utils to stop the server
        await asyncio.to_thread(stop_server_by_port, server.port)
        ui.notify(f"Stopped server on port {server.port}", type='positive')
        # Remove the card
        if server.port in server_cards:
            server_cards[server.port]['card'].delete()
            del server_cards[server.port]
        # Refresh after a brief delay
        await asyncio.sleep(0.5)
        await refresh_servers()
    except Exception as e:
        ui.notify(f"Error stopping server: {str(e)}", type='negative')


async def start_new_server(directory: str, name: str = "", agent_type: str = "claude", port: Optional[int] = None):
    """Start a new agentapi server using cyberian utilities."""

    # Validate directory exists
    if not os.path.isdir(directory):
        ui.notify(f"Directory does not exist: {directory}", type='negative')
        return

    # Generate name from directory if not provided
    if not name:
        dir_path = Path(directory)
        name = dir_path.name.replace('_', '-').replace(' ', '-').lower()
        name = re.sub(r'[^a-z0-9-]', '', name)
        if not name:
            name = "server"

    # Find available port if not provided
    if not port:
        try:
            port = await asyncio.to_thread(find_available_port)
        except Exception as e:
            ui.notify(str(e), type='negative')
            return

    try:
        # Start the server using server_utils
        process = await asyncio.to_thread(
            start_agentapi_server,
            agent_type=agent_type,
            port=port,
            directory=directory,
            name=name
        )

        # Wait a moment to check if process started successfully
        await asyncio.sleep(1)

        # Check if process is still running
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            error_msg = stderr or stdout or "Failed to start server"
            ui.notify(f"Server failed to start: {error_msg}", type='negative')
            return

        ui.notify(f"Started server '{name}' on port {port}", type='positive')

        # Add to dashboard config
        config = await asyncio.to_thread(load_dashboard_config)
        new_server = ServerConfig(
            name=name,
            agent_type=agent_type,
            port=port,
            directory=directory
        )
        config.servers.append(new_server)
        await asyncio.to_thread(save_dashboard_config, config)

        # Refresh the server list
        await asyncio.sleep(1)
        await refresh_servers()

    except Exception as e:
        ui.notify(f"Failed to start server: {str(e)}", type='negative')


def show_message_preview(port: int):
    """Show a preview of recent messages without full chat interface."""
    from nicegui import context

    # Get current client to create dialog at page level (not as child of card)
    client = context.client

    # Create dialog at client level to prevent it from being destroyed when cards refresh
    with client:
        with ui.dialog() as dialog, ui.card().classes('w-full max-w-2xl'):
            ui.label(f'Recent Messages - Port {port}').classes('text-xl font-bold mb-4')

            # Container for messages
            messages_container = ui.column().classes('w-full gap-2 max-h-96 overflow-y-auto')

            async def load_preview():
                """Load and display recent messages."""
                try:
                    # Use agent_client utility
                    messages = await asyncio.to_thread(get_agent_messages, port)

                    with messages_container:
                        if not messages:
                            ui.label('No messages yet').classes('text-gray-500 italic')
                        else:
                            # Show last 10 messages
                            for msg in messages[-10:]:
                                role = msg.get('role', 'user')
                                content = msg.get('content', '')

                                # Truncate very long messages
                                if len(content) > 200:
                                    content = content[:200] + '...'

                                with ui.card().classes('w-full'):
                                    ui.label(f"{role.upper()}:").classes('text-xs font-bold text-gray-500')
                                    ui.label(content).classes('text-sm')
                except Exception as e:
                    with messages_container:
                        ui.label(f'Error loading messages: {str(e)}').classes('text-red-500')

            # Load messages
            asyncio.create_task(load_preview())

            # Close button
            with ui.row().classes('w-full justify-end mt-4'):
                ui.button('Close', on_click=dialog.close)

    dialog.open()


def show_chat_dialog(port: int):
    """Show a full chat interface with message history."""
    from nicegui import context

    # Get current client to create dialog at page level (not as child of card)
    client = context.client

    # Create dialog at client level to prevent it from being destroyed when cards refresh
    with client:
        with ui.dialog().props('maximized').style('background-color: rgba(0,0,0,0.8)') as dialog:
            with ui.column().classes('w-full h-full bg-gray-900 p-4'):
                    # Header
                    with ui.row().classes('w-full items-center justify-between mb-4'):
                        ui.label(f'Chat - Port {port}').classes('text-2xl font-bold text-white')
                        with ui.row().classes('gap-2'):
                            ui.link('Open in Tab', f'http://localhost:{port}/', new_tab=True).classes('bg-green-600 text-white px-4 py-2 rounded')
                            ui.button('Close', on_click=dialog.close, icon='close').classes('bg-red-600 text-white')

                    # Chat container - use flex column with proper spacing
                    with ui.column().classes('w-full h-full bg-white rounded-lg p-4').style('display: flex; flex-direction: column; gap: 1rem;'):
                        # Message display area - takes remaining space
                        scroll_area = ui.scroll_area().classes('w-full border-2 border-gray-300 rounded p-4').style('flex: 1; min-height: 0;')
                        with scroll_area:
                            messages_display = ui.column().classes('w-full gap-2')

                        # Input area - fixed at bottom
                        with ui.row().classes('w-full gap-2').style('flex-shrink: 0;'):
                            message_input = ui.input(label='Message', placeholder='Type a message...').classes('flex-grow text-black').props('color="black" input-style="color: black"')
                            send_button = ui.button('Send', icon='send').classes('bg-blue-500')

                        # Polling state and message tracking
                        polling_active = {'active': True}
                        last_message_count = {'count': 0}

                        # Function to load messages
                        async def load_messages(force_scroll: bool = False):
                            """Fetch and display messages from the server.

                            Args:
                                force_scroll: If True, always scroll to bottom. If False, only scroll if at bottom.
                            """
                            try:
                                # Use agent_client utility
                                messages = await asyncio.to_thread(get_agent_messages, port)

                                # Check if we have new messages
                                has_new_messages = len(messages) > last_message_count['count']
                                last_message_count['count'] = len(messages)

                                messages_display.clear()
                                with messages_display:
                                    if not messages:
                                        ui.label('No messages yet').classes('text-gray-500 italic')
                                    else:
                                        for msg in messages:
                                            msg_type = msg.get('type', 'user')
                                            content = msg.get('content', '')

                                            # Style based on message type
                                            if msg_type == 'user':
                                                with ui.row().classes('w-full justify-end'):
                                                    with ui.card().classes('bg-blue-100 max-w-4xl'):
                                                        ui.markdown(content).classes('text-blue-900')
                                            else:
                                                with ui.row().classes('w-full justify-start'):
                                                    with ui.card().classes('bg-gray-100 max-w-4xl'):
                                                        ui.markdown(content).classes('text-gray-900')

                                # Only auto-scroll if forced OR if we have new messages
                                if force_scroll or has_new_messages:
                                    await asyncio.sleep(0.1)
                                    scroll_area.scroll_to(pixels=999999)
                            except Exception as e:
                                messages_display.clear()
                                with messages_display:
                                    ui.label(f'Error loading messages: {str(e)}').classes('text-red-500')

                        # Polling loop to refresh messages
                        async def poll_messages():
                            """Poll for new messages every 2 seconds."""
                            while polling_active['active']:
                                await asyncio.sleep(2)
                                if polling_active['active']:
                                    await load_messages()

                        # Function to send message
                        async def send_handler():
                            """Send a message to the server."""
                            content = message_input.value
                            message_input.value = ''

                            if content and content.strip():
                                # Clean the content
                                cleaned_content = content.strip()

                                try:
                                    # Use agent_client utility
                                    await asyncio.to_thread(send_agent_message, port, cleaned_content)
                                    # Reload messages immediately after sending, force scroll
                                    await load_messages(force_scroll=True)
                                except Exception as e:
                                    try:
                                        ui.notify(f"Error sending message: {str(e)}", type='negative')
                                    except Exception:
                                        print(f"Error sending message: {str(e)}")

                        # Wire up the send button and Enter key
                        send_button.on_click(send_handler)
                        message_input.on('keydown.enter', lambda: asyncio.create_task(send_handler()))

                        # Load messages initially (force scroll on first load) and start polling
                        asyncio.create_task(load_messages(force_scroll=True))
                        asyncio.create_task(poll_messages())

                        # Stop polling when dialog closes
                        dialog.on('close', lambda: polling_active.update({'active': False}))

    dialog.open()


async def reorder_card(port: int, old_index: int, new_index: int):
    """Reorder a server card in the dashboard.

    Args:
        port: Port of the server to reorder
        old_index: Current 0-based index of the server
        new_index: Target 0-based index (where to move it)
    """
    try:
        # Load config
        config = await asyncio.to_thread(load_dashboard_config)

        # Reorder using dashboard_config utility
        config = await asyncio.to_thread(reorder_server_in_config, config, old_index, new_index)

        # Save updated config
        await asyncio.to_thread(save_dashboard_config, config)

        ui.notify(f'Moved server to position {new_index + 1}', type='positive')

        # Refresh to show new order
        await refresh_servers()

    except Exception as e:
        ui.notify(f'Error reordering card: {str(e)}', type='negative')


def create_server_card(server: ServerInfo, index: int) -> dict:
    """Create a card for a server and return dict with UI element references.

    Args:
        server: ServerInfo object with server details
        index: 0-based index of this server in the list
    """
    elements = {}

    with ui.card().classes('w-full') as card:
        # Header row with badge in top-right
        with ui.row().classes('w-full items-start justify-between'):
            # Left side: Server info with index
            with ui.column().classes('gap-0'):
                with ui.row().classes('gap-2 items-center'):
                    # Index input (1-based for users)
                    async def handle_index_change(e):
                        """Handle user changing the card index."""
                        try:
                            new_index = int(e.value) - 1  # Convert to 0-based
                            if new_index != index and new_index >= 0:
                                await reorder_card(server.port, index, new_index)
                        except ValueError:
                            # Invalid input - reset to current index
                            e.sender.value = str(index + 1)

                    ui.number(
                        value=index + 1,
                        min=1,
                        on_change=handle_index_change
                    ).classes('w-16').props('dense outlined')

                    elements['name'] = ui.label(server.name).classes('text-lg font-bold')

                with ui.row().classes('gap-2 text-sm text-gray-500'):
                    elements['port'] = ui.label(f'Port: {server.port}')
                    elements['pid'] = ui.label(f'PID: {server.pid}')

                # Timestamp - small font
                if server.last_message_time:
                    time_str = server.last_message_time.strftime('%H:%M:%S')
                    elements['timestamp'] = ui.label(f'Last: {time_str}').classes('text-xs text-gray-500 mt-1')
                else:
                    elements['timestamp'] = ui.label('No activity yet').classes('text-xs text-gray-500 mt-1')

            # Right side: Status and Message Count Badge
            with ui.column().classes('items-end gap-2'):
                # Status badge
                status_colors = {
                    'ready': 'green',
                    'thinking': 'yellow',
                    'responding': 'blue',
                    'error': 'red',
                    'unreachable': 'gray',
                    'checking': 'gray'
                }
                color = status_colors.get(server.status, 'gray')
                elements['status'] = ui.badge(server.status, color=color)

                # Message count badge (clickable)
                with ui.button(
                    on_click=lambda p=server.port: show_message_preview(p)
                ).props('dense flat').classes('bg-blue-600 text-white rounded-full px-3 py-1'):
                    elements['message_count'] = ui.label(str(server.message_count)).classes('text-sm font-bold')

        ui.separator()

        # Last message preview - compact
        with ui.column().classes('w-full'):
            if server.last_message:
                elements['last_message'] = ui.label(server.last_message).classes('text-xs text-gray-400 truncate')
            else:
                elements['last_message'] = ui.label('No messages yet').classes('text-xs text-gray-500 italic')

        ui.separator()

        # Quick message input
        with ui.row().classes('w-full gap-2'):
            message_input = ui.input(
                placeholder='Quick message...'
            ).classes('flex-grow')

            # Define send handler that clears immediately
            async def send_handler():
                content = message_input.value
                message_input.value = ''  # Clear immediately
                if content and content.strip():
                    await send_message(server.port, content, None)

            # Support Enter key to send
            message_input.on('keydown.enter', lambda: asyncio.create_task(send_handler()))

            ui.button(
                'Send',
                on_click=lambda: asyncio.create_task(send_handler())
            ).classes('bg-blue-500')

        # Control buttons
        with ui.row().classes('w-full gap-2 mt-2'):
            ui.button(
                'Open Chat',
                on_click=lambda p=server.port: show_chat_dialog(p)
            ).classes('flex-1 bg-blue-500')

            ui.button(
                'Stop',
                on_click=lambda s=server: asyncio.create_task(stop_server(s)),
                color='red'
            ).classes('flex-1')

    elements['card'] = card
    return elements


async def refresh_servers():
    """Refresh the server list and update the UI.

    Cards are recreated in config order to support reordering.
    """
    servers = parse_servers()

    # Check status for each server
    await asyncio.gather(*[check_server_status(server) for server in servers])

    # Clear all existing cards
    for port in list(server_cards.keys()):
        server_cards[port]['card'].delete()
        del server_cards[port]

    # Recreate all cards in config order
    servers_container.clear()
    with servers_container:
        for index, server in enumerate(servers):
            server_cards[server.port] = create_server_card(server, index)


async def auto_refresh():
    """Auto-refresh the server list every 5 seconds."""
    while True:
        await asyncio.sleep(5)
        try:
            await refresh_servers()
        except Exception as e:
            print(f"Error during auto-refresh: {e}")


def show_search_dialog(search_term: str):
    """Show search results across all servers."""
    with ui.dialog() as dialog, ui.card().classes('w-full max-w-4xl'):
        ui.label(f'Search Results for: "{search_term}"').classes('text-xl font-bold mb-4')

        results_container = ui.column().classes('w-full gap-4 max-h-96 overflow-y-auto')

        async def perform_search():
            """Search all servers for the search term."""
            servers = parse_servers()
            found_results = False

            for server in servers:
                try:
                    async with httpx.AsyncClient() as client:
                        response = await client.get(
                            f"http://localhost:{server.port}/messages",
                            timeout=5.0
                        )
                        if response.status_code == 200:
                            data = response.json()
                            messages = data.get('messages', [])

                            # Filter messages containing search term (case-insensitive)
                            matching_messages = [
                                msg for msg in messages
                                if search_term.lower() in msg.get('content', '').lower()
                            ]

                            if matching_messages:
                                found_results = True
                                with results_container:
                                    # Server header
                                    ui.label(f"{server.name} (Port {server.port})").classes('text-lg font-bold text-blue-400 mt-2')

                                    # Show matching messages
                                    for msg in matching_messages:
                                        role = msg.get('role', 'user')
                                        content = msg.get('content', '')

                                        # Highlight the search term (simple approach)
                                        # Truncate very long messages
                                        if len(content) > 300:
                                            content = content[:300] + '...'

                                        with ui.card().classes('w-full bg-gray-800'):
                                            ui.label(f"{role.upper()}:").classes('text-xs font-bold text-gray-400')
                                            ui.label(content).classes('text-sm')
                except Exception as e:
                    print(f"Error searching server {server.port}: {e}")
                    continue

            if not found_results:
                with results_container:
                    ui.label('No results found').classes('text-gray-500 italic text-center mt-8')

        # Perform search
        asyncio.create_task(perform_search())

        # Close button
        with ui.row().classes('w-full justify-end mt-4'):
            ui.button('Close', on_click=dialog.close)

    dialog.open()


def show_start_dialog():
    """Show dialog to start a new server."""
    with ui.dialog() as dialog, ui.card().classes('w-96'):
        ui.label('Start New Server').classes('text-xl font-bold mb-4')

        directory_input = ui.input(
            'Working Directory *',
            placeholder='/path/to/project'
        ).classes('w-full')

        name_input = ui.input(
            'Server Name',
            placeholder='Auto-generated from directory'
        ).classes('w-full')

        agent_select = ui.select(
            label='Agent Type',
            options=['claude', 'openai', 'aider', 'amazonq', 'amp', 'auggie', 'codex'],
            value='claude'
        ).classes('w-full')

        port_input = ui.input(
            'Port',
            placeholder='Auto-assign (4800-4900)'
        ).classes('w-full')

        with ui.row().classes('w-full gap-2 mt-4'):
            ui.button('Cancel', on_click=dialog.close).classes('flex-1')

            async def start():
                if not directory_input.value.strip():
                    ui.notify('Directory is required', type='negative')
                    return

                port = None
                if port_input.value.strip():
                    try:
                        port = int(port_input.value)
                    except ValueError:
                        ui.notify('Invalid port number', type='negative')
                        return

                await start_new_server(
                    directory=directory_input.value.strip(),
                    name=name_input.value.strip(),
                    agent_type=agent_select.value,
                    port=port
                )
                dialog.close()

            ui.button(
                'Start Server',
                on_click=start
            ).classes('flex-1 bg-green-500')

    dialog.open()


# Build the UI
ui.dark_mode().enable()

with ui.header().classes('bg-gray-800'):
    with ui.row().classes('w-full items-center'):
        ui.label('Cyberian Dashboard').classes('text-2xl font-bold')
        ui.space()

        # Search input (middle)
        search_input = ui.input(placeholder='Search all messages...').classes('w-64')

        def perform_search():
            """Trigger search when user presses Enter."""
            search_term = search_input.value
            if search_term and search_term.strip():
                show_search_dialog(search_term.strip())

        search_input.on('keydown.enter', perform_search)

        ui.button(
            'Search',
            on_click=perform_search,
            icon='search'
        ).classes('bg-purple-500')

        ui.space()

        # Right side controls
        with ui.row().classes('gap-2'):
            ui.button(
                'Start Server',
                on_click=show_start_dialog,
                icon='add'
            ).classes('bg-green-500')

            ui.button(
                'Refresh',
                on_click=lambda: asyncio.create_task(refresh_servers()),
                icon='refresh'
            )

# Main container for server cards
servers_container = ui.grid(columns='repeat(auto-fill, minmax(350px, 1fr))').classes('w-full gap-4 p-4')

# Initial load and auto-refresh
async def startup_tasks():
    """Run startup tasks after the UI is ready."""
    await refresh_servers()
    asyncio.create_task(auto_refresh())

# Schedule startup tasks to run after UI is ready
ui.timer(0.1, lambda: asyncio.create_task(startup_tasks()), once=True)

# Run the app
ui.run(
    port=8080,
    title='Cyberian Dashboard',
    favicon='🤖',
    reload=False
)