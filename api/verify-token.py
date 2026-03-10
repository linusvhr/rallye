from http.server import BaseHTTPRequestHandler
import json
import os
import psycopg2
import secrets

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
            vorname = data.get('vorname', '').strip()
            nachname = data.get('nachname', '').strip()

            if not vorname or not nachname:
                self.wfile.write(json.dumps({
                    'error': 'Vorname und Nachname dürfen nicht leer sein.'
                }).encode('utf-8'))
                return

            if not DATABASE_URL:
                raise Exception("POSTGRES_URL Umgebungsvariable nicht gesetzt")

            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()

            # Tabelle anlegen, falls nicht vorhanden (mit token-Spalte)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS signups (
                    id SERIAL PRIMARY KEY,
                    vorname TEXT NOT NULL,
                    nachname TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW(),
                    token VARCHAR(32) UNIQUE
                )
            """)

            # Prüfen, ob bereits ein Eintrag mit diesem Namen existiert
            cur.execute(
                "SELECT token FROM signups WHERE vorname = %s AND nachname = %s",
                (vorname, nachname)
            )
            existing = cur.fetchone()

            if existing:
                # existierender Token
                token = existing[0]
                message = f"Willkommen zurück, {vorname} {nachname}!"
            else:
                # neuen Token generieren und einfügen
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

            response = {
                'status': 'ok',
                'token': token,
                'message': message
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))

        except Exception as e:
            self.wfile.write(json.dumps({
                'error': f'Interner Serverfehler: {str(e)}'
            }).encode('utf-8'))
        return

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
