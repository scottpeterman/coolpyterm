"""
Backend Factory - integrates Windows terminal backends with your existing SSH backend
Drop-in replacement for your current backend creation logic
"""


def create_backend(connection_config, parent_widget):
    """
    Factory function to create appropriate backend based on connection type

    Args:
        connection_config: Dict with connection parameters
        parent_widget: Parent widget for the backend

    Returns:
        Backend instance (SSHBackend or WindowsTerminalBackend)
    """
    connection_type = connection_config.get('connection_type', 'ssh')

    if connection_type == 'ssh':
        # Use your existing SSH backend
        from coolpyterm.ssh_backend import SSHBackend

        return SSHBackend(
            host=connection_config['hostname'],
            username=connection_config['username'],
            password=connection_config.get('password'),
            port=connection_config.get('port', 22),
            key_path=connection_config.get('key_path'),
            parent_widget=parent_widget
        )

    elif connection_type in ['cmd', 'powershell', 'wsl']:
        # Use new Windows terminal backend
        try:
            from coolpyterm.winptyshellreader import WindowsTerminalBackend

            return WindowsTerminalBackend(
                shell_path=connection_config.get('shell_path', 'cmd.exe'),
                working_dir=connection_config.get('working_dir'),
                env_vars=connection_config.get('env_vars', {}),
                startup_command=connection_config.get('startup_command'),
                parent_widget=parent_widget
            )
        except ImportError as e:
            raise Exception(f"Windows terminal support not available: {e}")

    else:
        raise ValueError(f"Unsupported connection type: {connection_type}")


def get_backend_requirements(connection_type):
    """
    Get the requirements for a specific backend type

    Args:
        connection_type: 'ssh', 'cmd', 'powershell', or 'wsl'

    Returns:
        Dict with requirement info
    """
    requirements = {
        'ssh': {
            'available': True,  # SSH is always available
            'dependencies': ['paramiko'],
            'platforms': ['Windows', 'Linux', 'Darwin'],
            'description': 'SSH connections to remote servers'
        },
        'cmd': {
            'available': False,
            'dependencies': ['pywinpty'],
            'platforms': ['Windows'],
            'description': 'Windows Command Prompt'
        },
        'powershell': {
            'available': False,
            'dependencies': ['pywinpty'],
            'platforms': ['Windows'],
            'description': 'Windows PowerShell'
        },
        'wsl': {
            'available': False,
            'dependencies': ['pywinpty'],
            'platforms': ['Windows'],
            'description': 'Windows Subsystem for Linux'
        }
    }

    req = requirements.get(connection_type, {})

    # Check if backend is actually available
    if connection_type == 'ssh':
        try:
            import paramiko
            req['available'] = True
        except ImportError:
            req['available'] = False
            req['error'] = 'paramiko not installed'

    elif connection_type in ['cmd', 'powershell', 'wsl']:
        import platform
        if platform.system() != 'Windows':
            req['available'] = False
            req['error'] = 'Windows terminal backends only available on Windows'
        else:
            try:
                import winpty
                req['available'] = True
            except ImportError:
                req['available'] = False
                req['error'] = 'pywinpty not installed. Install with: pip install pywinpty'

    return req


def check_all_backend_availability():
    """
    Check availability of all backend types

    Returns:
        Dict mapping backend type to availability info
    """
    backend_types = ['ssh', 'cmd', 'powershell', 'wsl']
    availability = {}

    for backend_type in backend_types:
        availability[backend_type] = get_backend_requirements(backend_type)

    return availability


def get_available_connection_types():
    """
    Get list of available connection types for the current platform

    Returns:
        List of available connection type strings
    """
    availability = check_all_backend_availability()
    available_types = []

    for conn_type, info in availability.items():
        if info['available']:
            available_types.append(conn_type)

    return available_types


# Integration example for your main application:
"""
# In your main terminal application (cpt.py or similar), replace your current
# backend creation with this factory:

# OLD CODE:
# backend = SSHBackend(host, username, password, ...)

# NEW CODE:
connection_config = {
    'connection_type': 'ssh',  # or 'cmd', 'powershell', 'wsl'
    'hostname': host,
    'username': username,
    'password': password,
    # ... other config
}

try:
    backend = create_backend(connection_config, parent_widget)
    # Backend will emit the same signals regardless of type:
    # - connection_established
    # - connection_failed
    # - send_output

    # Connect signals same way as before:
    backend.send_output.connect(your_terminal_widget.handle_output)
    backend.connection_established.connect(your_on_connected_handler)
    backend.connection_failed.connect(your_on_error_handler)

except Exception as e:
    print(f"Failed to create backend: {e}")
"""


# Compatibility functions for existing code
def create_ssh_backend(host, username, password=None, port=22, key_path=None, parent_widget=None):
    """
    Compatibility function for existing SSH backend creation
    """
    connection_config = {
        'connection_type': 'ssh',
        'hostname': host,
        'username': username,
        'password': password,
        'port': port,
        'key_path': key_path
    }
    return create_backend(connection_config, parent_widget)


def create_windows_terminal_backend(shell_path='cmd.exe', working_dir=None, parent_widget=None):
    """
    Convenience function for creating Windows terminal backends
    """
    # Map shell paths to connection types
    shell_type_map = {
        'cmd.exe': 'cmd',
        'cmd': 'cmd',
        'powershell.exe': 'powershell',
        'powershell': 'powershell',
        'pwsh.exe': 'powershell',
        'pwsh': 'powershell',
        'wsl.exe': 'wsl',
        'wsl': 'wsl'
    }

    connection_type = shell_type_map.get(shell_path.lower(), 'cmd')

    connection_config = {
        'connection_type': connection_type,
        'shell_path': shell_path,
        'working_dir': working_dir,
        'env_vars': {},
        'startup_command': None
    }

    return create_backend(connection_config, parent_widget)