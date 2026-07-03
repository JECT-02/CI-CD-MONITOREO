import http.server
import json
import os
import signal
import sys


class HealthHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "healthy"}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        sys.stderr.write("[%s] %s\n" % (self.log_date_time_string(), format % args))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8081"))
    server = http.server.HTTPServer(("0.0.0.0", port), HealthHandler)
    print("Server listening on port %d" % port, flush=True)

    def shutdown(sig, frame):
        server.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)
    server.serve_forever()
