"""
Dynamic Network Configuration Module
Auto-detects local IP address and provides centralized configuration
"""

import socket
import os
from typing import Optional


def get_local_ip() -> str:
    """
    Auto-detect the local IP address of the machine.
    Uses socket connection to Google DNS to determine the local network IP.
    
    Returns:
        str: Local IP address (e.g., '10.138.1.240') or '127.0.0.1' if detection fails
    """
    try:
        # Create a socket to determine local IP
        # This doesn't actually send data, just determines routing
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # Google DNS
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        print(f"⚠️  Warning: Could not auto-detect IP address: {e}")
        print(f"⚠️  Falling back to localhost (127.0.0.1)")
        return "127.0.0.1"


class Config:
    """
    Centralized configuration for the Patient Monitoring System backend.
    Automatically detects network settings on startup.
    """
    
    # Network Configuration
    HOST = os.getenv("BACKEND_HOST", "0.0.0.0")  # Bind to all interfaces
    PORT = int(os.getenv("BACKEND_PORT", "8000"))
    
    # Auto-detected local IP
    LOCAL_IP = get_local_ip()
    
    # Database Configuration (from existing .env)
    DATABASE_URL = os.getenv("DATABASE_URL")
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_PUBLISHABLE_KEY = os.getenv("SUPABASE_PUBLISHABLE_KEY")
    SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")
    
    # Hardware Configuration
    BAND_ID = os.getenv("BAND_ID", "BAND_01")
    BLE_PROXIMITY_THRESHOLD_RSSI = int(os.getenv("BLE_PROXIMITY_THRESHOLD_RSSI", "-70"))
    
    # Mode Configuration
    USE_HARDWARE = os.getenv("USE_HARDWARE", "false").lower() == "true"
    USE_MOCK_DATA = not USE_HARDWARE
    
    @classmethod
    def get_local_url(cls) -> str:
        """Get the localhost URL"""
        return f"http://localhost:{cls.PORT}"
    
    @classmethod
    def get_network_url(cls) -> str:
        """Get the network-accessible URL"""
        return f"http://{cls.LOCAL_IP}:{cls.PORT}"
    
    @classmethod
    def get_ws_local_url(cls) -> str:
        """Get the localhost WebSocket URL"""
        return f"ws://localhost:{cls.PORT}"
    
    @classmethod
    def get_ws_network_url(cls) -> str:
        """Get the network WebSocket URL"""
        return f"ws://{cls.LOCAL_IP}:{cls.PORT}"
    
    @classmethod
    def get_connection_info(cls) -> dict:
        """
        Get comprehensive connection information for all clients.
        
        Returns:
            dict: Connection URLs for local and network access
        """
        return {
            "local": {
                "http": cls.get_local_url(),
                "ws": cls.get_ws_local_url()
            },
            "network": {
                "http": cls.get_network_url(),
                "ws": cls.get_ws_network_url(),
                "ip": cls.LOCAL_IP,
                "port": cls.PORT
            },
            "endpoints": {
                "api_docs": f"{cls.get_network_url()}/docs",
                "health": f"{cls.get_network_url()}/api/health",
                "camera_stream": f"{cls.get_network_url()}/stream",
                "websocket": f"{cls.get_ws_network_url()}/ws"
            }
        }
    
    @classmethod
    def print_startup_banner(cls, include_qr: bool = True):
        """
        Print a beautiful startup banner with connection information.
        
        Args:
            include_qr: Whether to include QR code (requires qrcode library)
        """
        print("\n" + "=" * 60)
        print("🏥  PATIENT MONITORING SYSTEM - Backend Server")
        print("=" * 60)
        print(f"\n✅  Server started successfully!")
        print(f"\n📡 Connection Information:")
        print(f"   Local:   {cls.get_local_url()}")
        print(f"   Network: {cls.get_network_url()}")
        print(f"\n🌐 Network Details:")
        print(f"   IP Address: {cls.LOCAL_IP}")
        print(f"   Port:       {cls.PORT}")
        print(f"   Binding:    {cls.HOST} (all interfaces)")
        print(f"\n📚 API Documentation:")
        print(f"   {cls.get_network_url()}/docs")
        print(f"\n📹 Camera Stream:")
        print(f"   {cls.get_network_url()}/stream")
        print(f"\n🔌 WebSocket:")
        print(f"   {cls.get_ws_network_url()}/ws")
        
        if include_qr:
            try:
                cls.print_qr_code()
            except ImportError:
                print(f"\n💡 Tip: Install 'qrcode' for QR code display:")
                print(f"   pip install qrcode[pil]")
        
        print("\n" + "=" * 60)
        print("📱 Mobile App Setup:")
        print("   1. Open the Nurse Alarm App")
        print("   2. Go to Settings → Network Configuration")
        print("   3. Scan the QR code above OR")
        print(f"   4. Manually enter: {cls.get_network_url()}")
        print("=" * 60 + "\n")
    
    @classmethod
    def print_qr_code(cls):
        """
        Generate and print ASCII QR code for mobile app configuration.
        Requires qrcode library.
        """
        try:
            import qrcode
            
            # Create QR code with backend URL
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=1,
                border=1,
            )
            qr.add_data(cls.get_network_url())
            qr.make(fit=True)
            
            # Print ASCII QR code
            print(f"\n📱 Scan this QR code to configure mobile app:")
            print(f"   Backend URL: {cls.get_network_url()}\n")
            qr.print_ascii(invert=True)
            
        except ImportError:
            pass  # Silently skip if qrcode not installed
        except Exception as e:
            print(f"\n⚠️  Could not generate QR code: {e}")


# Export commonly used values
HOST = Config.HOST
PORT = Config.PORT
LOCAL_IP = Config.LOCAL_IP
USE_MOCK_DATA = Config.USE_MOCK_DATA
USE_HARDWARE = Config.USE_HARDWARE
