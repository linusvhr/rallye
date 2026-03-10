from http.server import BaseHTTPRequestHandler
import json
import os
import psycopg2

DATABASE_URL = os.environ.get('POSTGRES_URL')

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)

        try:
            data = json.loads(post_data.decode('utf-8'))
            token = data.get('token', '').strip()

            if not token:
                self.wfile.write(json.dumps({'valid': False}).encode('utf-8'))
                return

            if not DATABASE_URL:
                raise Exception("POSTGRES_URL nicht gesetzt")

            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()
            cur.execute("SELECT id FROM signups WHERE token = %s", (token,))
            exists = cur.fetchone() is not None
            cur.close()
            conn.close()

            self.wfile.write(json.dumps({'valid': exists}).encode('utf-8'))

        except Exception as e:
            self.wfile.write(json.dumps({'valid': False, 'error': str(e)}).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
