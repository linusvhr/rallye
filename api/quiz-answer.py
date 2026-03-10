from http.server import BaseHTTPRequestHandler
import json
import os
import psycopg2

DATABASE_URL = os.environ.get('POSTGRES_URL')

# Musterlösungen (für Test)
CORRECT_ANSWERS = {
    1: "B",      # Multiple Choice
    2: "42",     # Texteingabe
    3: "ja",     # Ja/Nein
    4: "Berlin", # Stadt
    5: "3",      # Zahl
    6: "rot",    # Farbe
    7: "Montag", # Wochentag
    8: "true",   # Wahr/Falsch
    9: "Schule", # Wort
    10: "QR-Code" # letzte Frage
}

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            token = data.get('token', '').strip()
            question = data.get('question')  # 1-10
            answer = data.get('answer', '').strip().lower()

            if not token or not question:
                self.wfile.write(json.dumps({'error': 'Token und Frage erforderlich'}).encode('utf-8'))
                return

            if question not in CORRECT_ANSWERS:
                self.wfile.write(json.dumps({'error': 'Ungültige Frage'}).encode('utf-8'))
                return

            # Prüfen, ob vorherige Fragen bereits richtig sind
            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()

            # Status der vorherigen Fragen abrufen
            prev_cols = [f"q{i}_correct" for i in range(1, question)]
            if prev_cols:
                cur.execute(f"SELECT {', '.join(prev_cols)} FROM signups WHERE token = %s", (token,))
                prev_status = cur.fetchone()
                if not prev_status:
                    self.wfile.write(json.dumps({'error': 'User nicht gefunden'}).encode('utf-8'))
                    return
                if not all(prev_status):  # eine vorherige ist falsch
                    self.wfile.write(json.dumps({'error': 'Vorherige Fragen nicht abgeschlossen'}).encode('utf-8'))
                    return

            # Antwort prüfen
            correct = (answer == CORRECT_ANSWERS[question].lower())

            if correct:
                # Spalte für diese Frage auf TRUE setzen
                cur.execute(f"UPDATE signups SET q{question}_correct = TRUE WHERE token = %s", (token,))
                conn.commit()
                next_question = question + 1
                next_url = f"/quiz-{next_question}-{get_slug_for_question(next_question)}" if next_question <= 10 else "/tutorial"  # oder /ende
            else:
                next_url = None

            cur.close()
            conn.close()

            self.wfile.write(json.dumps({
                'correct': correct,
                'next': next_url,
                'message': 'Richtig!' if correct else 'Leider falsch. Versuche es noch einmal.'
            }).encode('utf-8'))

        except Exception as e:
            self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def get_slug_for_question(q):
    # Hier später echte lange Strings einfügen
    slugs = [
        "8f7a3b9c", "d4e5f6a7", "1a2b3c4d", "5e6f7g8h", "9i0j1k2l",
        "3m4n5o6p", "7q8r9s0t", "1u2v3w4x", "5y6z7a8b", "9c0d1e2f"
    ]
    return slugs[q-1]
