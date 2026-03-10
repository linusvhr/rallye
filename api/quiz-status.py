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

        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads post_data.decode('utf-8')
            token = data.get('token', '').strip()

            if not token:
                self.wfile.write(json.dumps({'error': 'Kein Token'}).encode('utf-8'))
                return

            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()
            cur.execute("""
                SELECT q1_correct, q2_correct, q3_correct, q4_correct, q5_correct,
                       q6_correct, q7_correct, q8_correct, q9_correct, q10_correct
                FROM signups WHERE token = %s
            """, (token,))
            row = cur.fetchone()
            cur.close()
            conn.close()

            if not row:
                self.wfile.write(json.dumps({'error': 'User nicht gefunden'}).encode('utf-8'))
                return

            # Letzte bestandene Frage ermitteln (0 = keine)
            last_correct = 0
            for i in range(10):
                if row[i]:
                    last_correct = i + 1

            self.wfile.write(json.dumps({
                'status': [bool(row[i]) for i in range(10)],
                'last_correct': last_correct
            }).encode('utf-8'))

        except Exception as e:
            self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
