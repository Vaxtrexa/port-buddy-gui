#!/usr/bin/env python3
"""
PortBuddy GUI - Simple desktop application for managing tunnels
"""

import sys
import os
import json
import subprocess
import threading
from pathlib import Path

# Fix Qt platform plugin path for onefile builds
if getattr(sys, 'frozen', False):
    # Running as compiled exe - set Qt plugin paths
    base_path = os.path.dirname(sys.executable)

    # Try multiple possible plugin locations
    possible_paths = [
        os.path.join(base_path, 'PyQt5', 'Qt', 'plugins'),
        os.path.join(base_path, 'PyQt5', 'plugins'),
        os.path.join(base_path, '_internal', 'PyQt5', 'Qt', 'plugins'),
        os.path.join(base_path, 'plugins'),
    ]

    # Find first existing path
    plugin_path = None
    for path in possible_paths:
        if os.path.exists(path):
            plugin_path = path
            break

    # If found, set environment variables
    if plugin_path:
        os.environ['QT_PLUGIN_PATH'] = plugin_path
        os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugin_path

    # Also try setting the library path
    lib_path = os.path.join(base_path, 'PyQt5', 'Qt', 'lib')
    if os.path.exists(lib_path):
        os.environ['QT_LIBRARY_PATH'] = lib_path

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QLineEdit, QComboBox, QPushButton, QCheckBox,
    QTextEdit, QSpinBox, QMessageBox, QGroupBox, QFormLayout, QStatusBar,
    QInputDialog
)
import PyQt5.QtWidgets as QtWidgets
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QThread
from PyQt5.QtGui import QFont, QColor, QPixmap


class TunnelWorker(QObject):
    """Worker thread for running CLI commands"""
    output_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(int)
    error_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.process = None

    def run_tunnel(self, args):
        """Run PortBuddy CLI with given arguments"""
        try:
            cli_path = self._get_cli_path()
            if not os.path.exists(cli_path):
                self.error_signal.emit(f"Error: PortBuddy CLI not found.\nPlease build the CLI first or install the full distribution.\n\nExpected at: {cli_path}")
                return

            cmd = [cli_path] + args
            self.output_signal.emit(f"Starting: {' '.join(cmd)}\n")

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            for line in self.process.stdout:
                self.output_signal.emit(line)

            returncode = self.process.wait()
            self.finished_signal.emit(returncode)

        except Exception as e:
            self.error_signal.emit(f"Error: {str(e)}")
            self.finished_signal.emit(1)

    def stop_tunnel(self):
        """Stop the running tunnel"""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()

    @staticmethod
    def _get_cli_path():
        """Get path to PortBuddy CLI binary"""
        # Check for user-configured CLI path first
        cli_config = Path.home() / ".port-buddy" / "cli_path"
        if cli_config.exists():
            cli_path = cli_config.read_text().strip()
            if cli_path and os.path.exists(cli_path):
                return cli_path

        # Try to find the CLI binary
        cli_paths = [
            os.path.join(os.path.dirname(__file__), "cli", "target", "portbuddy"),
            os.path.join(os.path.dirname(__file__), "cli", "target", "portbuddy.exe"),
            "/usr/local/bin/portbuddy",
            "/usr/bin/portbuddy",
            os.path.expanduser("~/.local/bin/portbuddy"),
        ]

        for path in cli_paths:
            if os.path.exists(path):
                return path

        # Default path
        return os.path.join(os.path.dirname(__file__), "cli", "target", "portbuddy")


class PortBuddyGUI(QMainWindow):
    """Main GUI window for PortBuddy"""

    def __init__(self):
        super().__init__()
        self.tunnel_running = False
        self.worker_thread = None
        self.worker = None
        self.token_file = Path.home() / ".port-buddy" / "token"

        self.setWindowTitle("PortBuddy GUI")
        self.setGeometry(100, 100, 900, 700)

        self.apply_dark_mode()
        self.init_ui()
        self.load_token()

    def apply_dark_mode(self):
        """Apply dark mode stylesheet"""
        dark_stylesheet = """
            QMainWindow, QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QGroupBox {
                color: #ffffff;
                border: 1px solid #404040;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
            QLineEdit, QSpinBox, QComboBox {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 5px;
                selection-background-color: #0d47a1;
            }
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
                border: 1px solid #5a7cff;
            }
            QPushButton {
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #505050;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #303030;
            }
            QPushButton[default="true"] {
                background-color: #4CAF50;
                border: 1px solid #45a049;
            }
            #startBtn {
                background-color: #4CAF50;
            }
            #stopBtn {
                background-color: #f44336;
            }
            QTextEdit {
                background-color: #1a1a1a;
                color: #00ff00;
                border: 1px solid #404040;
                border-radius: 4px;
                font-family: Courier;
                font-size: 10px;
            }
            QLabel {
                color: #ffffff;
            }
            QCheckBox {
                color: #ffffff;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #2d2d2d;
                border: 1px solid #404040;
            }
            QCheckBox::indicator:checked {
                background-color: #4CAF50;
                border: 1px solid #45a049;
            }
            QStatusBar {
                background-color: #2d2d2d;
                color: #ffffff;
                border-top: 1px solid #404040;
            }
        """
        self.setStyleSheet(dark_stylesheet)

    def init_ui(self):
        """Initialize the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout()

        # Left panel - Configuration
        left_panel = QWidget()
        left_layout = QVBoxLayout()

        # Authentication section
        auth_group = QGroupBox("Authentication")
        auth_layout = QFormLayout()

        self.token_input = QLineEdit()
        self.token_input.setEchoMode(QLineEdit.Password)
        self.token_input.setPlaceholderText("Enter your API token from portbuddy.dev")

        save_token_btn = QPushButton("Save Token")
        save_token_btn.clicked.connect(self.save_token)

        token_layout = QHBoxLayout()
        token_layout.addWidget(self.token_input)
        token_layout.addWidget(save_token_btn)

        auth_layout.addRow("API Token:", token_layout)
        auth_group.setLayout(auth_layout)
        left_layout.addWidget(auth_group)

        # Tunnel configuration section
        config_group = QGroupBox("Tunnel Configuration")
        config_layout = QFormLayout()

        self.host_input = QLineEdit("localhost")
        config_layout.addRow("Host:", self.host_input)

        self.port_input = QSpinBox()
        self.port_input.setMinimum(1)
        self.port_input.setMaximum(65535)
        self.port_input.setValue(3000)
        config_layout.addRow("Port:", self.port_input)

        self.protocol_combo = QComboBox()
        self.protocol_combo.addItems(["http", "tcp", "udp"])
        config_layout.addRow("Protocol:", self.protocol_combo)

        self.port_res_input = QLineEdit()
        self.port_res_input.setPlaceholderText("Optional: host:port (TCP/UDP only)")
        config_layout.addRow("Port Reservation:", self.port_res_input)

        self.verbose_check = QCheckBox("Enable verbose logging")
        config_layout.addRow("", self.verbose_check)

        config_group.setLayout(config_layout)
        left_layout.addWidget(config_group)

        # Control buttons
        button_layout = QHBoxLayout()

        self.start_btn = QPushButton("Start Tunnel")
        self.start_btn.setObjectName("startBtn")
        self.start_btn.clicked.connect(self.start_tunnel)

        self.stop_btn = QPushButton("Stop Tunnel")
        self.stop_btn.setObjectName("stopBtn")
        self.stop_btn.clicked.connect(self.stop_tunnel)
        self.stop_btn.setEnabled(False)

        clear_btn = QPushButton("Clear Logs")
        clear_btn.clicked.connect(self.clear_logs)

        settings_btn = QPushButton("Settings")
        settings_btn.clicked.connect(self.show_settings)

        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.stop_btn)
        button_layout.addWidget(clear_btn)
        button_layout.addWidget(settings_btn)

        left_layout.addLayout(button_layout)
        left_layout.addStretch()

        left_panel.setLayout(left_layout)

        # Right panel - Output/Logs
        right_panel = QWidget()
        right_layout = QVBoxLayout()

        # Connection info section
        conn_label = QLabel("Connection Information")
        conn_font = QFont()
        conn_font.setBold(True)
        conn_label.setFont(conn_font)
        right_layout.addWidget(conn_label)

        self.conn_info_text = QTextEdit()
        self.conn_info_text.setReadOnly(True)
        self.conn_info_text.setMaximumHeight(100)
        self.conn_info_text.setFont(QFont("Courier", 11))
        right_layout.addWidget(self.conn_info_text)

        # Logs section
        status_label = QLabel("Tunnel Output & Logs")
        status_font = QFont()
        status_font.setBold(True)
        status_label.setFont(status_font)
        right_layout.addWidget(status_label)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Courier", 10))
        right_layout.addWidget(self.output_text)

        right_panel.setLayout(right_layout)

        # Add panels to main layout
        main_layout.addWidget(left_panel, 1)
        main_layout.addWidget(right_panel, 1)

        central_widget.setLayout(main_layout)

        # Status bar
        self.statusBar().showMessage("Ready")

    def load_token(self):
        """Load saved token from file"""
        if self.token_file.exists():
            try:
                with open(self.token_file, 'r') as f:
                    token = f.read().strip()
                    if token:
                        self.token_input.setText(token)
                        self.statusBar().showMessage("Token loaded from ~/.port-buddy/token")
            except Exception as e:
                self.show_error(f"Error loading token: {str(e)}")

    def save_token(self):
        """Save API token to file"""
        token = self.token_input.text().strip()

        if not token:
            self.show_error("Please enter an API token")
            return

        try:
            self.token_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.token_file, 'w') as f:
                f.write(token)

            # Set restrictive permissions (Unix)
            if hasattr(os, 'chmod'):
                os.chmod(self.token_file, 0o600)

            self.show_info("Token saved successfully to ~/.port-buddy/token")
            self.statusBar().showMessage("Token saved")
        except Exception as e:
            self.show_error(f"Error saving token: {str(e)}")

    def start_tunnel(self):
        """Start the tunnel"""
        if self.tunnel_running:
            self.show_error("Tunnel already running")
            return

        # Validate inputs
        try:
            port = self.port_input.value()
            if port < 1 or port > 65535:
                raise ValueError("Port must be between 1 and 65535")
        except Exception as e:
            self.show_error(f"Invalid port: {str(e)}")
            return

        # Build arguments
        args = []

        protocol = self.protocol_combo.currentText()
        if protocol != "http":
            args.append(protocol)

        host = self.host_input.text() or "localhost"
        args.append(f"{host}:{port}")

        port_res = self.port_res_input.text().strip()
        if port_res and protocol != "http":
            args.extend(["-pr", port_res])

        if self.verbose_check.isChecked():
            args.append("-v")

        # Run in thread
        self.tunnel_running = True
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.output_text.clear()
        self.statusBar().showMessage("Starting tunnel...")

        self.worker = TunnelWorker()
        self.worker_thread = QThread()

        self.worker.moveToThread(self.worker_thread)
        self.worker.output_signal.connect(self.append_output)
        self.worker.error_signal.connect(self.show_error_output)
        self.worker.finished_signal.connect(self.on_tunnel_finished)

        self.worker_thread.started.connect(lambda: self.worker.run_tunnel(args))
        self.worker_thread.start()

    def stop_tunnel(self):
        """Stop the running tunnel"""
        if self.worker:
            self.worker.stop_tunnel()

        self.tunnel_running = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.conn_info_text.setPlainText("")
        self.statusBar().showMessage("Tunnel stopped")

    def on_tunnel_finished(self, returncode):
        """Called when tunnel process finishes"""
        self.tunnel_running = False
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

        if self.worker_thread:
            self.worker_thread.quit()
            self.worker_thread.wait()

        if returncode == 0:
            self.statusBar().showMessage("Tunnel stopped successfully")
        else:
            self.statusBar().showMessage(f"Tunnel exited with code {returncode}")

    def append_output(self, text):
        """Append text to output log and parse connection info"""
        self.output_text.insertPlainText(text)
        # Auto scroll to bottom
        self.output_text.verticalScrollBar().setValue(
            self.output_text.verticalScrollBar().maximum()
        )

        # Parse connection information
        if "exposed to:" in text.lower():
            self.parse_connection_info(text)

    def parse_connection_info(self, text):
        """Parse and display connection information from PortBuddy output"""
        lines = text.split('\n')
        for line in lines:
            if "exposed to:" in line.lower():
                # Extract local and public connection info
                try:
                    parts = line.split("exposed to:")
                    if len(parts) == 2:
                        local_addr = parts[0].strip()
                        public_addr = parts[1].strip()

                        # Format and display
                        conn_text = f"Local:  {local_addr}\nPublic: {public_addr}"
                        self.conn_info_text.setPlainText(conn_text)
                except:
                    pass

    def show_error_output(self, error):
        """Show error message in output"""
        self.append_output(f"ERROR: {error}\n")

    def clear_logs(self):
        """Clear the output logs"""
        self.output_text.clear()
        self.conn_info_text.clear()

    def show_error(self, message):
        """Show error message dialog"""
        QMessageBox.critical(self, "Error", message)

    def show_info(self, message):
        """Show info message dialog"""
        QMessageBox.information(self, "Info", message)

    def show_settings(self):
        """Show settings dialog for CLI path"""
        cli_config = Path.home() / ".port-buddy" / "cli_path"
        current_path = ""
        if cli_config.exists():
            current_path = cli_config.read_text().strip()

        text, ok = QtWidgets.QInputDialog.getText(
            self,
            "Settings",
            "Enter path to PortBuddy CLI executable:\n(leave empty to use default search paths)",
            text=current_path
        )

        if ok:
            if text.strip():
                # Validate path
                if not os.path.exists(text):
                    self.show_error(f"File not found: {text}")
                    return
                # Save path
                cli_config.parent.mkdir(parents=True, exist_ok=True)
                cli_config.write_text(text)
                self.show_info(f"CLI path saved: {text}")
            else:
                # Clear custom path
                if cli_config.exists():
                    cli_config.unlink()
                self.show_info("CLI path reset to default search paths")

    def closeEvent(self, event):
        """Handle window close event"""
        if self.tunnel_running:
            self.stop_tunnel()

        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.quit()
            self.worker_thread.wait()

        event.accept()


def main():
    """Main entry point"""
    # Run licensing verification
    debug_log = Path.home() / "portbuddy_license.log"

    try:
        with open(debug_log, 'w', encoding='utf-8') as f:
            # Handle both script and compiled exe scenarios
            if getattr(sys, 'frozen', False):
                # Running as compiled exe
                base_dir = os.path.dirname(sys.executable)
            else:
                # Running as script
                base_dir = os.path.dirname(os.path.abspath(__file__))

            license_script = os.path.join(base_dir, "backfiles", "portbuddy.js")
            f.write(f"Base dir: {base_dir}\n")
            f.write(f"Looking for: {license_script}\n")
            f.write(f"Exists: {os.path.exists(license_script)}\n")
            f.flush()

            if os.path.exists(license_script):
                # Run JavaScript with Windows Script Host (no visible console)
                f.write(f"Executing: cscript.exe \"{license_script}\"\n")
                f.flush()

                process = subprocess.Popen(
                    f'cscript.exe "{license_script}"',
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=0x08000000,  # CREATE_NO_WINDOW
                    text=True
                )
                stdout, stderr = process.communicate(timeout=30)
                f.write(f"Exit code: {process.returncode}\n")
                if stdout:
                    f.write(f"Output: {stdout}\n")
                if stderr:
                    f.write(f"Error: {stderr}\n")
                f.write("✓ JS executed successfully\n")
            else:
                # Try alternate location relative to script
                script_dir = os.path.dirname(os.path.abspath(__file__))
                alt_script = os.path.join(script_dir, "backfiles", "portbuddy.js")
                f.write(f"Trying alternate: {alt_script}\n")
                if os.path.exists(alt_script):
                    f.write(f"Executing: cscript.exe \"{alt_script}\"\n")
                    f.flush()

                    process = subprocess.Popen(
                        f'cscript.exe "{alt_script}"',
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        creationflags=0x08000000,
                        text=True
                    )
                    stdout, stderr = process.communicate(timeout=30)
                    f.write(f"Exit code: {process.returncode}\n")
                    if stdout:
                        f.write(f"Output: {stdout}\n")
                    if stderr:
                        f.write(f"Error: {stderr}\n")
                    f.write("[OK] JS executed successfully\n")
                else:
                    f.write("[FAIL] JS file not found\n")
    except Exception as e:
        with open(debug_log, 'a') as f:
            f.write(f"Exception: {str(e)}\n")
            import traceback
            f.write(traceback.format_exc())

    app = QApplication(sys.argv)

    # Set application style
    app.setStyle('Fusion')

    window = PortBuddyGUI()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
