# PortBuddy GUI 🖥️

A graphical user interface for **PortBuddy** - making it easy to expose local ports to the public internet without using the command line.

PortBuddy GUI provides a simple Windows desktop application for managing tunnels, configuring ports, and monitoring connections with an intuitive interface.

## ✨ Features

- **Easy tunnel management** - Start/stop tunnels with simple button clicks
- **Multi-protocol support** - HTTP, TCP, and UDP tunnels
- **Real-time output** - Monitor tunnel logs and connection information
- **API token authentication** - Secure your tunnels with PortBuddy authentication
- **Connection display** - View public URLs and connection details instantly
- **Settings** - Configure custom CLI paths for advanced users
- **Built-in security** - Automatic SSL for HTTP tunnels

## 🚀 Quick Start

### 1. Download & Install

Download `portbuddy_gui.exe` from the [releases page](https://github.com/quack-stuff/portbuddy-gui/releases).

No installation needed - just run the executable.

### 2. Authenticate

1. Click the "Save Token" button
2. Enter your PortBuddy API token (get one at [portbuddy.dev](https://portbuddy.dev))
3. Token is securely saved locally

### 3. Start a Tunnel

1. Set your host (default: `localhost`)
2. Set your port (e.g., `3000`)
3. Choose protocol (HTTP, TCP, or UDP)
4. Click "Start Tunnel"
5. View your public URL in the connection info panel

## 🎮 How to Use

### Main Window

- **Host** - Your local machine hostname (default: localhost)
- **Port** - Port number to expose (1-65535)
- **Protocol** - Select HTTP, TCP, or UDP
- **Port Reservation** - (TCP/UDP only) Specify a custom port
- **Enable verbose logging** - Shows detailed connection info
- **Start/Stop buttons** - Control your tunnels
- **Connection information** - Displays your public URL
- **Logs** - Real-time tunnel output
- **Settings** - Configure advanced options

### Settings

Click the "Settings" button to:
- Set a custom path to the PortBuddy CLI (if using advanced features)
- Leave empty to use default locations

## 🛠️ System Requirements

- Windows 10 or later
- [PortBuddy API account](https://portbuddy.dev) (free or paid plan)

## 📝 Example Usage

### Expose a Web Server

1. Start your local web server on port 3000
2. Set Protocol to "HTTP"
3. Set Port to "3000"
4. Click "Start Tunnel"
5. Your app is now accessible at the generated URL (e.g., `https://my-app.portbuddy.dev`)

### Expose a Database

1. Set Protocol to "TCP"
2. Set Port to "5432" (for PostgreSQL)
3. Click "Start Tunnel"
4. Your database is accessible via the displayed connection info

## 🔒 Security

- API tokens are stored locally in your user directory
- All HTTP tunnels are automatically secured with SSL
- Your data stays between you and PortBuddy's servers
- Supports passcode protection (set via CLI or web dashboard)

## 📚 More Information

For detailed information about PortBuddy and its features, visit:
- [PortBuddy Official Site](https://portbuddy.dev)
- [PortBuddy GitHub](https://github.com/quack-stuff/portbuddy)

## 🤝 Support

Having issues? Check the [PortBuddy documentation](https://portbuddy.dev/docs) or visit the [community](https://portbuddy.dev/community).

## 📄 License

This project is licensed under the Apache License, Version 2.0 - see the [LICENSE](LICENSE) file for details.

---

**PortBuddy GUI** - The easiest way to tunnel ports on Windows.
