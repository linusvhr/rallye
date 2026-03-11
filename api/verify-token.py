from http.server import BaseHTTPRequestHandler
import json
import os
import psycopg2
from http.cookies import SimpleCookie

DATABASE_URL = os.environ.get('POSTGRES_URL')

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            cookie_header = self.headers.get('Cookie')
            token = None
            
            if cookie_header:
                cookie = SimpleCookie(cookie_header)
                if 'rallye_token' in cookie:
                    token = cookie['rallye_token'].value

            if not token:
                self._send_response(401, {'valid': False})
                return

            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()
            cur.execute("SELECT id FROM signups WHERE token = %s", (token,))
            exists = cur.fetchone() is not None
            cur.close()
            conn.close()

            if exists:
                self._send_response(200, {'valid': True})
            else:
                self._send_response(401, {'valid': False})

        except Exception:
            self._send_response(500, {'valid': False})

    def _send_response(self, status, data):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Cookie')
        self.end_headers()
