from http.server import BaseHTTPRequestHandler
import json
import os
import psycopg2
import secrets
import sys

DATABASE_URL = os.environ.get('POSTGRES_URL')

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            vorname = data.get('vorname', '').strip()
            nachname = data.get('nachname', '').strip()

            if not vorname or not nachname:
                self._send_error(400, 'Vorname und Nachname dürfen nicht leer sein.')
                return

            if not DATABASE_URL:
                self._send_error(500, 'Datenbank-URL nicht konfiguriert.')
                return

            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()

            cur.execute("""
                CREATE TABLE IF NOT EXISTS signups (
                    id SERIAL PRIMARY KEY,
                    vorname TEXT NOT NULL,
                    nachname TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    token VARCHAR(32) UNIQUE
                )
            """)

            cur.execute("SELECT token FROM signups WHERE vorname = %s AND nachname = %s", (vorname, nachname))
            existing = cur.fetchone()

            if existing:
                token = existing[0]
                message = f"Willkommen zurück, {vorname} {nachname}!"
            else:
                token = secrets.token_urlsafe(16)[:16]
                cur.execute("INSERT INTO signups (vorname, nachname, token) VALUES (%s, %s, %s) RETURNING token", (vorname, nachname, token))
                token = cur.fetchone()[0]
                message = f"{vorname} {nachname} wurde erfolgreich angemeldet!"

            conn.commit()
            cur.close()
            conn.close()

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Set-Cookie', f'rallye_token={token}; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=31536000')
            self.end_headers()
            
            self.wfile.write(json.dumps({'status': 'ok', 'message': message}).encode('utf-8'))

        except psycopg2.IntegrityError:
            self._send_error(400, 'Dieser Name ist bereits registriert (Integritätsfehler).')
        except Exception as e:
            print("Fehler in signup.py:", str(e), file=sys.stderr)
            self._send_error(500, 'Interner Serverfehler')

    def _send_error(self, status, message):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps({'error': message}).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
