"""
CSC200 - Data Structures & Algorithms
Solitaire Web Server (Built-in Python http.server, zero dependencies)

Provides:
- Static file serving for web interface (HTML, CSS, JS)
- JSON REST API interfacing directly with the Python SolitaireEngine
  (using custom Stack, Queue, DoublyLinkedList, and CardHashMap)
"""

import http.server
import socketserver
import json
import urllib.parse
import os
import sys

from engine import SolitaireEngine
from card import Rank, Suit

PORT = 8080
WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")

# Shared Game Engine Instance for web session
engine = SolitaireEngine(draw_count=1)


class SolitaireAPIHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def _send_json_response(self, data: dict, status_code: int = 200):
        response_bytes = json.dumps(data).encode('utf-8')
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(response_bytes)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/state":
            self._send_json_response(self._get_engine_state())
        elif path == "/api/hints":
            hints = engine.get_hints()
            hint_list = [
                {
                    "source": h.source,
                    "target": h.target,
                    "card_id": h.card.id,
                    "description": h.description,
                    "priority": h.priority
                } for h in hints
            ]
            self._send_json_response({"hints": hint_list})
        else:
            # Fall back to serving static files from web/
            super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get('Content-Length', 0))
        post_body = self.rfile.read(content_length) if content_length > 0 else b"{}"
        try:
            payload = json.loads(post_body.decode('utf-8'))
        except Exception:
            payload = {}

        success = False
        message = ""

        if path == "/api/new_game":
            draw_count = payload.get("draw_count", engine.draw_count)
            engine.draw_count = draw_count
            engine.start_new_game()
            success = True
            message = "New game started"

        elif path == "/api/restart":
            engine.restart_game()
            success = True
            message = "Game restarted"

        elif path == "/api/draw":
            success = engine.draw_from_stock()
            message = "Stock drawn" if success else "No cards to draw"

        elif path == "/api/move":
            move_type = payload.get("type")
            if move_type == "waste_to_tableau":
                t_idx = payload.get("tableau_idx")
                success = engine.move_waste_to_tableau(t_idx)
            elif move_type == "waste_to_foundation":
                f_idx = payload.get("foundation_idx")
                success = engine.move_waste_to_foundation(f_idx)
            elif move_type == "tableau_to_tableau":
                src = payload.get("source_idx")
                dst = payload.get("target_idx")
                card_id = payload.get("card_id")
                success = engine.move_tableau_to_tableau(src, dst, start_card_id=card_id)
            elif move_type == "tableau_to_foundation":
                src = payload.get("source_idx")
                f_idx = payload.get("foundation_idx")
                success = engine.move_tableau_to_foundation(src, f_idx)
            elif move_type == "foundation_to_tableau":
                f_idx = payload.get("foundation_idx")
                t_idx = payload.get("tableau_idx")
                success = engine.move_foundation_to_tableau(f_idx, t_idx)

        elif path == "/api/auto_play":
            card_id = payload.get("card_id")
            success = engine.auto_play_card(card_id)
            message = "Auto-play executed" if success else "No valid move"

        elif path == "/api/auto_finish":
            success = engine.auto_finish_if_possible()
            message = "Auto-finish executed" if success else "Cannot auto finish yet"

        elif path == "/api/undo":
            success = engine.undo()
            message = "Move undone" if success else "Cannot undo"

        elif path == "/api/redo":
            success = engine.redo()
            message = "Move redone" if success else "Cannot redo"

        response = {
            "success": success,
            "message": message,
            "state": self._get_engine_state()
        }
        self._send_json_response(response)

    def _get_engine_state(self) -> dict:
        def serialize_card(c):
            if c is None:
                return None
            return {
                "id": c.id,
                "suit": c.suit,
                "rank": c.rank,
                "rank_name": c.rank_name,
                "symbol": c.symbol,
                "color": c.color,
                "is_face_up": c.is_face_up
            }

        return {
            "tableau": [[serialize_card(c) for c in col] for col in engine.tableau],
            "foundations": [[serialize_card(c) for c in f.to_list()] for f in engine.foundations],
            "stock_count": engine.stock.size(),
            "waste": [serialize_card(c) for c in engine.waste.to_list()],
            "score": engine.score,
            "moves": engine.moves_count,
            "elapsed_time": engine.get_formatted_time(),
            "can_undo": engine.can_undo(),
            "can_redo": engine.can_redo(),
            "can_auto_finish": engine.can_auto_finish(),
            "is_game_won": engine.is_game_won,
            "draw_count": engine.draw_count,
            "high_score": engine.get_high_score()
        }


def run_server(port=PORT):
    os.makedirs(WEB_DIR, exist_ok=True)
    with socketserver.TCPServer(("", port), SolitaireAPIHandler) as httpd:
        print(f"Solitaire Web Server running at http://localhost:{port}")
        httpd.serve_forever()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    run_server(port)
