from http.server import BaseHTTPRequestHandler
import json
import os
import psycopg2
from urllib.parse import parse_qs
import sys

# Datenbankverbindung aus Umgebungsvariable
DATABASE_URL = os.environ.get('POSTGRES_URL')

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # CORS-Header für Anfragen vom Frontend
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        # Länge der POST-Daten ermitteln
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            # JSON parsen
            data = json.loads(post_data.decode('utf-8'))
            vorname = data.get('vorname', '').strip()
            nachname = data.get('nachname', '').strip()

            if not vorname or not nachname:
                self.wfile.write(json.dumps({
                    'error': 'Vorname und Nachname dürfen nicht leer sein.'
                }).encode('utf-8'))
                return

            # In Datenbank speichern
            if not DATABASE_URL:
                raise Exception("POSTGRES_URL Umgebungsvariable nicht gesetzt")

            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()
            
            # Tabelle anlegen, falls nicht vorhanden
            cur.execute("""
                CREATE TABLE IF NOT EXISTS signups (
                    id SERIAL PRIMARY KEY,
                    vorname TEXT NOT NULL,
                    nachname TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            cur.execute(
                "INSERT INTO signups (vorname, nachname) VALUES (%s, %s)",
                (vorname, nachname)
            )
            conn.commit()
            cur.close()
            conn.close()

            response = {
                'status': 'ok',
                'message': f'{vorname} {nachname} wurde erfolgreich angemeldet! 🎉'
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))

        except Exception as e:
            self.wfile.write(json.dumps({
                'error': f'Interner Serverfehler: {str(e)}'
            }).encode('utf-8'))
        return

    # OPTIONS-Anfragen für CORS erlauben
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
