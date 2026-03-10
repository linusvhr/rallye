from http.server import BaseHTTPRequestHandler
import json
import os
import psycopg2
import secrets

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
                self._send_error(500, 'Datenbankkonfiguration fehlt.')
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

            cur.execute(
                "SELECT token FROM signups WHERE vorname = %s AND nachname = %s",
                (vorname, nachname)
            )
            existing = cur.fetchone()

            if existing:
                token = existing[0]
                message = f"Willkommen zurück, {vorname} {nachname}!"
            else:
                token = secrets.token_urlsafe(16)[:16]
                cur.execute(
                    "INSERT INTO signups (vorname, nachname, token) VALUES (%s, %s, %s) RETURNING token",
                    (vorname, nachname, token)
                )
                token = cur.fetchone()[0]
                message = f"{vorname} {nachname} wurde erfolgreich angemeldet!"

            conn.commit()
            cur.close()
            conn.close()

            self._send_response(200, {'status': 'ok', 'token': token, 'message': message})

        except psycopg2.IntegrityError:
            self._send_error(409, 'Dieser Name ist bereits registriert.')
        except Exception as e:
            self._send_error(500, f'Interner Serverfehler: {str(e)}')

    def _send_response(self, status, data):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def _send_error(self, status, message):
        self._send_response(status, {'error': message})

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
