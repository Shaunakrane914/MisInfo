import http.server
import socketserver
import os

# Standardized port 8080 for frontend
PORT = 8080

# Change to the frontend directory
frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend')
if os.path.exists(frontend_dir) and os.path.isdir(frontend_dir):
    os.chdir(frontend_dir)
    print(f"Changed to frontend directory: {frontend_dir}")
else:
    print(f"Frontend directory not found at: {frontend_dir}")
    print("Serving from current directory")

Handler = http.server.SimpleHTTPRequestHandler

try:
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Frontend server running at http://localhost:{PORT}/")
        print("Press Ctrl+C to stop the server")
        httpd.serve_forever()
except OSError as e:
    if e.errno == 10048:
        print(f"Port {PORT} is already in use. Please close the application using this port or change the PORT variable in serve_frontend.py")
    else:
        print(f"Error starting server: {e}")
except KeyboardInterrupt:
    print("\nServer stopped.")