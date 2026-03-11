from http.server import BaseHTTPRequestHandler
import json
import os
import psycopg2

DATABASE_URL = os.environ.get('POSTGRES_URL')

CORRECT_ANSWERS = {
    1: "B",          
    2: "16",         
    3: "ja",         
    4: "rhein",      
    5: "gold,rot,schwarz",
    6: "1989-11-09",
    7: "71",         
    8: "test@beispiel.de",
    9: "49",
    10: "qr-code"
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
            question = data.get('question')
            answer = data.get('answer', '').strip().lower()

            if not token or not question:
                self.wfile.write(json.dumps({'error': 'Token und Frage erforderlich'}).encode('utf-8'))
                return

            if question not in CORRECT_ANSWERS:
                self.wfile.write(json.dumps({'error': 'Ungültige Frage'}).encode('utf-8'))
                return

            conn = psycopg2.connect(DATABASE_URL)
            cur = conn.cursor()

            if question > 1:
                prev_cols = [f"q{i}_correct" for i in range(1, question)]
                cur.execute(f"SELECT {', '.join(prev_cols)} FROM signups WHERE token = %s", (token,))
                prev_status = cur.fetchone()
                if not prev_status or not all(prev_status):
                    self.wfile.write(json.dumps({'error': 'Vorherige Fragen nicht abgeschlossen'}).encode('utf-8'))
                    return

            correct = (answer == CORRECT_ANSWERS[question].lower())

            if correct:
                cur.execute(f"UPDATE signups SET q{question}_correct = TRUE WHERE token = %s", (token,))
                conn.commit()

            cur.close()
            conn.close()

            self.wfile.write(json.dumps({'correct': correct}).encode('utf-8'))

        except Exception as e:
            self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
