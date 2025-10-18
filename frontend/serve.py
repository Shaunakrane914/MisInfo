import http.server
import socketserver
import os

# Print current working directory for debugging
print("Current working directory:", os.getcwd())

# List files in current directory for debugging
print("Files in current directory:")
for file in os.listdir('.'):
    print(f"  {file}")

# Standardized port 8080 for frontend
PORT = 8080

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