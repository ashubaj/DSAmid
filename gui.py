"""
CSC200 - Data Structures & Algorithms
Interactive & Responsive Solitaire (Klondike) Desktop GUI (Tkinter)

Features:
- Responsive canvas that dynamically scales card dimensions, margins, and pile layouts on window resize
- Smooth Drag-and-Drop of single cards and multi-card sub-stacks (DoublyLinkedList)
- One-click / Double-click / Right-click auto-move to Foundations and Tableaux
- Visual Hint indicator (glowing gold highlight on source and destination + action banner)
- Stack-based Undo and Redo with keyboard shortcuts (Ctrl+Z, Ctrl+Y)
- Stockpile draw with Draw-1 and Draw-3 modes, and recycle button
- Auto-Finish solver animation when all hidden cards are cleared
- Timer, Score tracking, Moves counter, High Score persistence
- Celebratory victory animation
"""

import tkinter as tk
from tkinter import messagebox
import time
import math
from typing import List, Optional, Tuple, Dict, Any

from engine import SolitaireEngine, Hint
from card import Card, Suit, Rank


class CardTheme:
    BG_FELT = "#0d4d22"
    BG_FELT_LIGHT = "#15632e"
    PANEL_BG = "#112211"
    TEXT_LIGHT = "#e8f5e9"
    ACCENT_GOLD = "#ffd700"
    HINT_GLOW = "#ffeb3b"
    CARD_BG = "#ffffff"
    CARD_BORDER = "#b0bec5"
    CARD_BACK_BG = "#1a365d"
    CARD_BACK_INNER = "#2b6cb0"
    CARD_BACK_PATTERN = "#4299e1"
    RED_SUIT = "#d32f2f"
    BLACK_SUIT = "#212121"
    SLOT_BORDER = "#1b5e20"
    SLOT_BG = "#0a3818"
    GHOST_COLOR = "#fff9c4"


class SolitaireGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("CSC200 Klondike Solitaire - DSA Midterm Project")
        self.root.geometry("1024x720")
        self.root.minsize(800, 600)
        self.root.configure(bg=CardTheme.BG_FELT)

        # Game Engine Instance
        self.engine = SolitaireEngine(draw_count=1)

        # Drag-and-drop state
        self.dragged_cards: List[Card] = []
        self.drag_source_type: Optional[str] = None  # 'tableau', 'waste', 'foundation'
        self.drag_source_idx: Optional[int] = None
        self.drag_start_x: int = 0
        self.drag_start_y: int = 0
        self.drag_offset_x: int = 0
        self.drag_offset_y: int = 0
        self.drag_item_ids: List[int] = []

        # Hint display state
        self.active_hint: Optional[Hint] = None
        self.hint_banner_text: str = ""

        # Layout dimensions (dynamically scaled in on_resize)
        self.canvas_width = 1024
        self.canvas_height = 660
        self.card_width = 90
        self.card_height = 126
        self.card_radius = 8
        self.margin_x = 24
        self.margin_y = 20
        self.gap_x = 18
        self.tableau_y = 170
        self.offset_face_down = 14
        self.offset_face_up = 26

        # Sound toggle (uses winsound on Windows if enabled)
        self.sound_enabled = True

        # Auto-finish animation running flag
        self.is_animating_autofinish = False

        self._build_ui()
        self._bind_events()
        self._update_timer_loop()
        self.render_all()

    # =========================================================================
    # UI SETUP & CONTROLS
    # =========================================================================

    def _build_ui(self):
        # 1. Top Control Bar
        self.top_bar = tk.Frame(self.root, bg=CardTheme.PANEL_BG, padx=12, pady=8)
        self.top_bar.pack(side=tk.TOP, fill=tk.X)

        # Left controls
        left_frame = tk.Frame(self.top_bar, bg=CardTheme.PANEL_BG)
        left_frame.pack(side=tk.LEFT)

        btn_style = {
            "bg": "#2e7d32", "fg": "white", "activebackground": "#388e3c",
            "activeforeground": "white", "font": ("Segoe UI", 9, "bold"),
            "relief": tk.FLAT, "padx": 10, "pady": 4, "cursor": "hand2"
        }

        self.btn_new = tk.Button(left_frame, text="✨ New Game", command=self.on_new_game, **btn_style)
        self.btn_new.pack(side=tk.LEFT, padx=3)

        self.btn_restart = tk.Button(left_frame, text="↺ Restart", command=self.on_restart, **btn_style)
        self.btn_restart.pack(side=tk.LEFT, padx=3)

        self.btn_undo = tk.Button(left_frame, text="⟲ Undo (Ctrl+Z)", command=self.on_undo, **btn_style)
        self.btn_undo.pack(side=tk.LEFT, padx=3)

        self.btn_redo = tk.Button(left_frame, text="⟳ Redo (Ctrl+Y)", command=self.on_redo, **btn_style)
        self.btn_redo.pack(side=tk.LEFT, padx=3)

        self.btn_hint = tk.Button(left_frame, text="💡 Hint (H)", command=self.on_hint, **btn_style)
        self.btn_hint.pack(side=tk.LEFT, padx=3)

        self.btn_draw_mode = tk.Button(left_frame, text="Draw: 1 Card", command=self.on_toggle_draw_mode, **btn_style)
        self.btn_draw_mode.pack(side=tk.LEFT, padx=3)

        self.btn_autofinish = tk.Button(
            left_frame, text="⚡ Auto-Finish", command=self.on_auto_finish,
            bg="#f57f17", fg="white", activebackground="#fbc02d",
            activeforeground="white", font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT, padx=10, pady=4, cursor="hand2"
        )
        self.btn_autofinish.pack(side=tk.LEFT, padx=3)

        # Right stats display
        right_frame = tk.Frame(self.top_bar, bg=CardTheme.PANEL_BG)
        right_frame.pack(side=tk.RIGHT)

        lbl_style = {"bg": CardTheme.PANEL_BG, "fg": CardTheme.TEXT_LIGHT, "font": ("Segoe UI", 10, "bold"), "padx": 8}

        self.lbl_score = tk.Label(right_frame, text="Score: 0", **lbl_style)
        self.lbl_score.pack(side=tk.LEFT)

        self.lbl_moves = tk.Label(right_frame, text="Moves: 0", **lbl_style)
        self.lbl_moves.pack(side=tk.LEFT)

        self.lbl_time = tk.Label(right_frame, text="Time: 00:00", **lbl_style)
        self.lbl_time.pack(side=tk.LEFT)

        self.lbl_highscore = tk.Label(right_frame, text=f"Best: {self.engine.get_high_score()}", fg=CardTheme.ACCENT_GOLD, bg=CardTheme.PANEL_BG, font=("Segoe UI", 10, "bold"), padx=8)
        self.lbl_highscore.pack(side=tk.LEFT)

        # 2. Hint Banner
        self.hint_bar = tk.Label(
            self.root, text="💡 Tip: Click or drag cards. Double-click to auto-move to foundation!",
            bg="#1b381e", fg="#e0f2f1", font=("Segoe UI", 10, "italic"), pady=4
        )
        self.hint_bar.pack(side=tk.TOP, fill=tk.X)

        # 3. Main Game Canvas (Interactive & Responsive)
        self.canvas = tk.Canvas(
            self.root, bg=CardTheme.BG_FELT, highlightthickness=0,
            cursor="arrow"
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

    def _bind_events(self):
        # Window resize event
        self.canvas.bind("<Configure>", self.on_resize)

        # Mouse interactions
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.canvas.bind("<Double-Button-1>", self.on_double_click)
        self.canvas.bind("<Button-3>", self.on_right_click)

        # Keyboard shortcuts
        self.root.bind("<Control-z>", lambda e: self.on_undo())
        self.root.bind("<Control-y>", lambda e: self.on_redo())
        self.root.bind("<Control-Z>", lambda e: self.on_undo())
        self.root.bind("<Control-Y>", lambda e: self.on_redo())
        self.root.bind("<h>", lambda e: self.on_hint())
        self.root.bind("<H>", lambda e: self.on_hint())
        self.root.bind("<n>", lambda e: self.on_new_game())
        self.root.bind("<N>", lambda e: self.on_new_game())

    # =========================================================================
    # RESPONSIVE SCALING & POSITION CALCULATION
    # =========================================================================

    def on_resize(self, event):
        """Dynamically scales cards, margins, and gaps when window is resized."""
        w = max(event.width, 760)
        h = max(event.height, 500)
        self.canvas_width = w
        self.canvas_height = h

        # Calculate responsive card dimensions
        # 7 columns with 8 gaps
        available_w = w - 40
        card_w = max(60, min(120, int(available_w / 7.8)))
        card_h = int(card_w * 1.4)

        gap_x = max(10, min(24, int((w - (7 * card_w)) / 8)))
        margin_x = gap_x

        self.card_width = card_w
        self.card_height = card_h
        self.gap_x = gap_x
        self.margin_x = margin_x
        self.margin_y = 16
        self.tableau_y = self.margin_y + card_h + 24
        self.offset_face_down = max(10, min(20, int(card_h * 0.14)))
        self.offset_face_up = max(18, min(34, int(card_h * 0.24)))

        self.render_all()

    def get_stock_pos(self) -> Tuple[int, int]:
        return (self.margin_x, self.margin_y)

    def get_waste_pos(self) -> Tuple[int, int]:
        return (self.margin_x + self.card_width + self.gap_x, self.margin_y)

    def get_foundation_pos(self, idx: int) -> Tuple[int, int]:
        # Right aligned foundations (cols 3, 4, 5, 6)
        x = self.margin_x + (3 + idx) * (self.card_width + self.gap_x)
        return (x, self.margin_y)

    def get_tableau_pos(self, col_idx: int) -> Tuple[int, int]:
        x = self.margin_x + col_idx * (self.card_width + self.gap_x)
        return (x, self.tableau_y)

    # =========================================================================
    # RENDERING ENGINE (VECTOR CARDS & BOARD)
    # =========================================================================

    def render_all(self):
        """Full re-render of the canvas board state."""
        self.canvas.delete("all")

        # 1. Background felt texture / border line
        self.canvas.create_line(
            0, self.tableau_y - 12, self.canvas_width, self.tableau_y - 12,
            fill="#0b401c", width=2
        )

        # 2. Render Slots (Stock, Waste, Foundations, Tableau bases)
        self._render_slots()

        # 3. Render Stock Pile
        self._render_stock()

        # 4. Render Waste Pile
        self._render_waste()

        # 5. Render Foundation Piles
        self._render_foundations()

        # 6. Render Tableau Columns
        self._render_tableau()

        # 7. Render Hint Highlight if active
        self._render_hint_highlight()

        # 8. Update UI controls state (Undo/Redo button availability)
        self._update_controls_state()

    def _render_slots(self):
        # Stock Slot outline
        sx, sy = self.get_stock_pos()
        self._draw_slot_box(sx, sy, label="↺" if self.engine.stock.is_empty() else "")

        # Waste Slot outline
        wx, wy = self.get_waste_pos()
        self._draw_slot_box(wx, wy, label="")

        # 4 Foundation Slot outlines with suit watermarks
        suit_symbols = ["♥", "♦", "♣", "♠"]
        for i in range(4):
            fx, fy = self.get_foundation_pos(i)
            symbol = suit_symbols[i]
            color = "#a33" if i < 2 else "#444"
            self._draw_slot_box(fx, fy, label=symbol, label_color=color)

        # 7 Tableau Column Slot bases
        for i in range(7):
            tx, ty = self.get_tableau_pos(i)
            self._draw_slot_box(tx, ty, label="K", label_color="#185025")

    def _draw_slot_box(self, x: int, y: int, label: str = "", label_color: str = "#226633"):
        w = self.card_width
        h = self.card_height
        r = self.card_radius

        # Rounded rectangle outline
        self._create_rounded_rect(
            x, y, x + w, y + h, radius=r,
            fill=CardTheme.SLOT_BG, outline=CardTheme.SLOT_BORDER, width=2
        )
        if label:
            font_size = max(14, int(w * 0.28))
            self.canvas.create_text(
                x + w // 2, y + h // 2, text=label,
                font=("Segoe UI", font_size, "bold"), fill=label_color
            )

    def _render_stock(self):
        sx, sy = self.get_stock_pos()
        stock_size = self.engine.stock.size()
        if stock_size > 0:
            # Draw stacked card appearance if more than 1
            if stock_size > 3:
                self._draw_card_back(sx - 3, sy - 3)
            if stock_size > 1:
                self._draw_card_back(sx - 1, sy - 1)
            # Top card
            card_item_id = self._draw_card_back(sx, sy)
            self.canvas.addtag_withtag(f"stock_top", card_item_id)
        else:
            # Draw recycle icon
            self.canvas.create_text(
                sx + self.card_width // 2, sy + self.card_height // 2,
                text="↺\nRecycle", font=("Segoe UI", 11, "bold"),
                fill="#81c784", justify=tk.CENTER
            )

    def _render_waste(self):
        wx, wy = self.get_waste_pos()
        waste_cards = self.engine.waste.to_list()
        if not waste_cards:
            return

        # Show up to 3 cascading cards in waste if draw_count == 3
        count_to_show = min(3, len(waste_cards)) if self.engine.draw_count == 3 else 1
        start_idx = len(waste_cards) - count_to_show
        shift_x = 18

        for offset, idx in enumerate(range(start_idx, len(waste_cards))):
            card = waste_cards[idx]
            curr_x = wx + offset * shift_x
            is_top = (idx == len(waste_cards) - 1)
            # Skip drawing top card if currently dragging it
            if is_top and self.drag_source_type == 'waste':
                continue
            self._draw_card_face(curr_x, wy, card, tag=f"waste_{idx}")

    def _render_foundations(self):
        for i, foundation in enumerate(self.engine.foundations):
            fx, fy = self.get_foundation_pos(i)
            top_card = foundation.peek()
            if top_card:
                if self.drag_source_type == 'foundation' and self.drag_source_idx == i:
                    # Currently dragging top card; draw card underneath if any
                    f_list = foundation.to_list()
                    if len(f_list) > 1:
                        self._draw_card_face(fx, fy, f_list[-2], tag=f"foundation_{i}")
                else:
                    self._draw_card_face(fx, fy, top_card, tag=f"foundation_{i}")

    def _render_tableau(self):
        for col_idx, col in enumerate(self.engine.tableau):
            tx, ty = self.get_tableau_pos(col_idx)
            cards = col.to_list()
            curr_y = ty

            for c_idx, card in enumerate(cards):
                # If this column is the drag source and card is being dragged, stop rendering here
                if self.drag_source_type == 'tableau' and self.drag_source_idx == col_idx:
                    if card in self.dragged_cards:
                        break

                if card.is_face_up:
                    self._draw_card_face(tx, curr_y, card, tag=f"tableau_{col_idx}_{c_idx}")
                    curr_y += self.offset_face_up
                else:
                    self._draw_card_back(tx, curr_y, tag=f"tableau_{col_idx}_{c_idx}")
                    curr_y += self.offset_face_down

    def _render_hint_highlight(self):
        """Draws glowing golden outline on suggested cards / piles."""
        if self.active_hint is None:
            return

        hint = self.active_hint
        # Source highlight
        src_type, src_idx = hint.source
        sx, sy = 0, 0
        if src_type == 'waste':
            sx, sy = self.get_waste_pos()
        elif src_type == 'stock':
            sx, sy = self.get_stock_pos()
        elif src_type == 'tableau':
            col = self.engine.tableau[src_idx]
            cards = col.to_list()
            tx, ty = self.get_tableau_pos(src_idx)
            curr_y = ty
            for c in cards:
                if c.id == hint.card.id:
                    sx, sy = tx, curr_y
                    break
                curr_y += self.offset_face_up if c.is_face_up else self.offset_face_down

        # Draw glowing animated-style rectangle around source
        self._create_rounded_rect(
            sx - 4, sy - 4, sx + self.card_width + 4, sy + self.card_height + 4,
            radius=self.card_radius + 2, outline=CardTheme.HINT_GLOW, width=4
        )

        # Destination highlight
        dst_type, dst_idx = hint.target
        dx, dy = 0, 0
        if dst_type == 'foundation':
            dx, dy = self.get_foundation_pos(dst_idx)
        elif dst_type == 'tableau':
            col = self.engine.tableau[dst_idx]
            tx, ty = self.get_tableau_pos(dst_idx)
            if col.is_empty():
                dx, dy = tx, ty
            else:
                curr_y = ty
                for c in col:
                    curr_y += self.offset_face_up if c.is_face_up else self.offset_face_down
                dx, dy = tx, curr_y - self.offset_face_up

        self._create_rounded_rect(
            dx - 4, dy - 4, dx + self.card_width + 4, dy + self.card_height + 4,
            radius=self.card_radius + 2, outline="#80d8ff", width=4
        )

    # =========================================================================
    # CARD DRAWING HELPERS (HIGH QUALITY VECTOR GRAPHICS)
    # =========================================================================

    def _create_rounded_rect(self, x1, y1, x2, y2, radius=8, **kwargs):
        """Creates a smooth rounded rectangle on Tkinter canvas."""
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1
        ]
        return self.canvas.create_polygon(points, smooth=True, **kwargs)

    def _draw_card_face(self, x: int, y: int, card: Card, tag: str = "") -> int:
        """Draws a crisp face-up playing card with rank and suit symbols."""
        w = self.card_width
        h = self.card_height
        r = self.card_radius

        # Drop shadow
        self._create_rounded_rect(x + 2, y + 2, x + w + 2, y + h + 2, radius=r, fill="#07220e", outline="")

        # Card Body
        body_id = self._create_rounded_rect(x, y, x + w, y + h, radius=r, fill=CardTheme.CARD_BG, outline=CardTheme.CARD_BORDER, width=1)
        if tag:
            self.canvas.addtag_withtag(tag, body_id)

        color = CardTheme.RED_SUIT if card.color == "RED" else CardTheme.BLACK_SUIT
        rank_str = card.rank_name
        suit_str = card.symbol

        # Corner font size
        corner_font_size = max(10, int(w * 0.16))
        corner_font = ("Segoe UI", corner_font_size, "bold")

        # Top-Left corner (Rank & Suit)
        self.canvas.create_text(x + 10, y + 12, text=rank_str, font=corner_font, fill=color, anchor=tk.CENTER)
        self.canvas.create_text(x + 10, y + 26, text=suit_str, font=corner_font, fill=color, anchor=tk.CENTER)

        # Bottom-Right corner (Rank & Suit inverted)
        self.canvas.create_text(x + w - 10, y + h - 26, text=suit_str, font=corner_font, fill=color, anchor=tk.CENTER)
        self.canvas.create_text(x + w - 10, y + h - 12, text=rank_str, font=corner_font, fill=color, anchor=tk.CENTER)

        # Center Graphic / Emblem
        center_font_size = max(16, int(w * 0.38))
        if card.rank in [Rank.JACK, Rank.QUEEN, Rank.KING]:
            # Royal card inner box
            inset = max(14, int(w * 0.20))
            self.canvas.create_rectangle(
                x + inset, y + inset + 4, x + w - inset, y + h - inset - 4,
                fill="#fffde7", outline="#cfd8dc", width=1
            )
            # Center Rank & Suit
            self.canvas.create_text(
                x + w // 2, y + h // 2 - 8, text=card.rank_name,
                font=("Segoe UI", int(center_font_size * 0.9), "bold"), fill=color
            )
            self.canvas.create_text(
                x + w // 2, y + h // 2 + 14, text=suit_str,
                font=("Segoe UI", int(center_font_size * 0.7)), fill=color
            )
        else:
            # Number / Ace card center suit
            self.canvas.create_text(
                x + w // 2, y + h // 2, text=suit_str,
                font=("Segoe UI", center_font_size), fill=color
            )

        return body_id

    def _draw_card_back(self, x: int, y: int, tag: str = "") -> int:
        """Draws an authentic casino-style card back with diamond cross-hatch pattern."""
        w = self.card_width
        h = self.card_height
        r = self.card_radius

        # Drop shadow
        self._create_rounded_rect(x + 2, y + 2, x + w + 2, y + h + 2, radius=r, fill="#07220e", outline="")

        # Card Back Body
        back_id = self._create_rounded_rect(
            x, y, x + w, y + h, radius=r,
            fill=CardTheme.CARD_BACK_BG, outline="#ffffff", width=1
        )
        if tag:
            self.canvas.addtag_withtag(tag, back_id)

        # Inner border
        pad = max(4, int(w * 0.06))
        self._create_rounded_rect(
            x + pad, y + pad, x + w - pad, y + h - pad, radius=max(2, r - 3),
            fill=CardTheme.CARD_BACK_INNER, outline="#ffffff", width=1
        )

        # Diamond pattern in center
        cx = x + w // 2
        cy = y + h // 2
        d_size = int(w * 0.22)
        diamond_pts = [cx, cy - d_size, cx + d_size, cy, cx, cy + d_size, cx - d_size, cy]
        self.canvas.create_polygon(diamond_pts, fill=CardTheme.CARD_BACK_PATTERN, outline="#ffffff", width=1)
        self.canvas.create_oval(cx - 4, cy - 4, cx + 4, cy + 4, fill="#ffffff", outline="")

        return back_id

    # =========================================================================
    # MOUSE EVENT HANDLERS (CLICK & DRAG-AND-DROP)
    # =========================================================================

    def on_mouse_down(self, event):
        """Handles initial mouse press to initiate drag or click stock."""
        self.active_hint = None  # Dismiss hint when user interacts
        x, y = event.x, event.y

        # 1. Check Stock Click
        sx, sy = self.get_stock_pos()
        if sx <= x <= sx + self.card_width and sy <= y <= sy + self.card_height:
            self.engine.draw_from_stock()
            self._play_sound("deal")
            self.render_all()
            return

        # 2. Check Waste Card Drag
        if not self.engine.waste.is_empty():
            wx, wy = self.get_waste_pos()
            shift_x = 18 if (self.engine.draw_count == 3 and self.engine.waste.size() > 1) else 0
            waste_count = min(3, self.engine.waste.size()) if self.engine.draw_count == 3 else 1
            top_x = wx + (waste_count - 1) * shift_x
            if top_x <= x <= top_x + self.card_width and wy <= y <= wy + self.card_height:
                self.dragged_cards = [self.engine.waste.peek()]
                self.drag_source_type = 'waste'
                self.drag_source_idx = 0
                self.drag_start_x = top_x
                self.drag_start_y = wy
                self.drag_offset_x = x - top_x
                self.drag_offset_y = y - wy
                return

        # 3. Check Foundation Drag
        for f_idx in range(4):
            fx, fy = self.get_foundation_pos(f_idx)
            if fx <= x <= fx + self.card_width and fy <= y <= fy + self.card_height:
                top_card = self.engine.foundations[f_idx].peek()
                if top_card:
                    self.dragged_cards = [top_card]
                    self.drag_source_type = 'foundation'
                    self.drag_source_idx = f_idx
                    self.drag_start_x = fx
                    self.drag_start_y = fy
                    self.drag_offset_x = x - fx
                    self.drag_offset_y = y - fy
                    return

        # 4. Check Tableau Drag (Single card or Multi-card sub-stack)
        for t_idx in range(7):
            tx, ty = self.get_tableau_pos(t_idx)
            col = self.engine.tableau[t_idx]
            cards = col.to_list()
            if not cards:
                continue

            curr_y = ty
            for c_idx, card in enumerate(cards):
                is_last = (c_idx == len(cards) - 1)
                step = self.offset_face_up if card.is_face_up else self.offset_face_down
                card_bottom = (curr_y + self.card_height) if is_last else (curr_y + step)

                if tx <= x <= tx + self.card_width and curr_y <= y <= card_bottom:
                    if card.is_face_up:
                        # Pick up this card and all subsequent cards in the column
                        self.dragged_cards = cards[c_idx:]
                        self.drag_source_type = 'tableau'
                        self.drag_source_idx = t_idx
                        self.drag_start_x = tx
                        self.drag_start_y = curr_y
                        self.drag_offset_x = x - tx
                        self.drag_offset_y = y - curr_y
                        self.render_all()
                        self._draw_drag_ghost(x, y)
                        return
                    else:
                        # Clicked a face-down card at the top of pile (if uncovered)
                        if is_last:
                            card.is_face_up = True
                            self.render_all()
                            return
                curr_y += step

    def on_mouse_drag(self, event):
        """Updates position of dragged cards."""
        if not self.dragged_cards:
            return
        self._draw_drag_ghost(event.x, event.y)

    def _draw_drag_ghost(self, mouse_x: int, mouse_y: int):
        """Draws the currently dragged cards following the mouse cursor."""
        self.canvas.delete("drag_ghost")
        gx = mouse_x - self.drag_offset_x
        gy = mouse_y - self.drag_offset_y

        curr_y = gy
        for card in self.dragged_cards:
            # Draw ghost card with glow tag
            w = self.card_width
            h = self.card_height
            r = self.card_radius

            # Shadow
            self._create_rounded_rect(
                gx + 4, curr_y + 4, gx + w + 4, curr_y + h + 4,
                radius=r, fill="#041207", outline="", tags="drag_ghost"
            )
            # Body
            self._create_rounded_rect(
                gx, curr_y, gx + w, curr_y + h,
                radius=r, fill=CardTheme.CARD_BG, outline=CardTheme.HINT_GLOW, width=2,
                tags="drag_ghost"
            )
            # Rank & Suit
            color = CardTheme.RED_SUIT if card.color == "RED" else CardTheme.BLACK_SUIT
            cfont = ("Segoe UI", max(10, int(w * 0.16)), "bold")
            self.canvas.create_text(gx + 10, curr_y + 12, text=card.rank_name, font=cfont, fill=color, tags="drag_ghost")
            self.canvas.create_text(gx + 10, curr_y + 26, text=card.symbol, font=cfont, fill=color, tags="drag_ghost")
            self.canvas.create_text(gx + w // 2, curr_y + h // 2, text=card.symbol, font=("Segoe UI", max(16, int(w * 0.36))), fill=color, tags="drag_ghost")

            curr_y += self.offset_face_up

    def on_mouse_up(self, event):
        """Handles drop of dragged card(s) onto destination pile."""
        if not self.dragged_cards:
            return

        self.canvas.delete("drag_ghost")
        x, y = event.x, event.y
        moved = False

        # Attempt to drop onto Foundation (Only single card can drop onto foundation)
        if len(self.dragged_cards) == 1:
            for f_idx in range(4):
                fx, fy = self.get_foundation_pos(f_idx)
                # Generous drop zone
                if (fx - 15 <= x <= fx + self.card_width + 15) and (fy - 15 <= y <= fy + self.card_height + 25):
                    card = self.dragged_cards[0]
                    if self.drag_source_type == 'waste':
                        moved = self.engine.move_waste_to_foundation(f_idx)
                    elif self.drag_source_type == 'tableau':
                        moved = self.engine.move_tableau_to_foundation(self.drag_source_idx, f_idx)
                    if moved:
                        self._play_sound("foundation")
                        break

        # Attempt to drop onto Tableau
        if not moved:
            for t_idx in range(7):
                tx, ty = self.get_tableau_pos(t_idx)
                col = self.engine.tableau[t_idx]
                target_top_y = ty + (len(col) * self.offset_face_up)
                hit_x = (tx - 15 <= x <= tx + self.card_width + 15)
                hit_y = (ty - 15 <= y <= target_top_y + self.card_height + 30)

                if hit_x and hit_y:
                    if self.drag_source_type == 'waste':
                        moved = self.engine.move_waste_to_tableau(t_idx)
                    elif self.drag_source_type == 'foundation':
                        moved = self.engine.move_foundation_to_tableau(self.drag_source_idx, t_idx)
                    elif self.drag_source_type == 'tableau':
                        if self.drag_source_idx != t_idx:
                            start_card_id = self.dragged_cards[0].id
                            moved = self.engine.move_tableau_to_tableau(
                                self.drag_source_idx, t_idx, start_card_id=start_card_id
                            )
                    if moved:
                        self._play_sound("snap")
                        break

        # Reset drag state
        self.dragged_cards = []
        self.drag_source_type = None
        self.drag_source_idx = None

        self.render_all()
        self._check_game_status()

    def on_double_click(self, event):
        """Intelligent double click: automatically moves clicked card to foundation or tableau."""
        self._handle_auto_play_at(event.x, event.y)

    def on_right_click(self, event):
        """Right click also triggers intelligent auto-move for convenience."""
        self._handle_auto_play_at(event.x, event.y)

    def _handle_auto_play_at(self, x: int, y: int):
        # 1. Check Waste
        wx, wy = self.get_waste_pos()
        if not self.engine.waste.is_empty():
            shift_x = 18 if (self.engine.draw_count == 3 and self.engine.waste.size() > 1) else 0
            waste_count = min(3, self.engine.waste.size()) if self.engine.draw_count == 3 else 1
            top_x = wx + (waste_count - 1) * shift_x
            if top_x <= x <= top_x + self.card_width and wy <= y <= wy + self.card_height:
                card = self.engine.waste.peek()
                if self.engine.auto_play_card(card.id):
                    self._play_sound("snap")
                    self.render_all()
                    self._check_game_status()
                return

        # 2. Check Tableau
        for t_idx in range(7):
            tx, ty = self.get_tableau_pos(t_idx)
            col = self.engine.tableau[t_idx]
            cards = col.to_list()
            curr_y = ty
            for c_idx, card in enumerate(cards):
                is_last = (c_idx == len(cards) - 1)
                step = self.offset_face_up if card.is_face_up else self.offset_face_down
                card_bottom = (curr_y + self.card_height) if is_last else (curr_y + step)
                if tx <= x <= tx + self.card_width and curr_y <= y <= card_bottom:
                    if card.is_face_up:
                        if self.engine.auto_play_card(card.id):
                            self._play_sound("snap")
                            self.render_all()
                            self._check_game_status()
                        return
                curr_y += step

    # =========================================================================
    # BUTTON ACTIONS & BONUS FEATURES
    # =========================================================================

    def on_new_game(self):
        """Starts a fresh game with new random seed."""
        self.engine.start_new_game()
        self.active_hint = None
        self.hint_bar.config(text="✨ New game started. Good luck!")
        self.render_all()

    def on_restart(self):
        """Restarts current deal."""
        self.engine.restart_game()
        self.active_hint = None
        self.hint_bar.config(text="↺ Game restarted with the same deal.")
        self.render_all()

    def on_undo(self):
        """Executes undo using undo_stack."""
        if self.engine.can_undo():
            self.engine.undo()
            self._play_sound("undo")
            self.render_all()
            self.hint_bar.config(text="⟲ Move undone.")

    def on_redo(self):
        """Executes redo using redo_stack."""
        if self.engine.can_redo():
            self.engine.redo()
            self._play_sound("undo")
            self.render_all()
            self.hint_bar.config(text="⟳ Move redone.")

    def on_hint(self):
        """Bonus Feature 2: Finds and visually highlights best strategic move."""
        hint = self.engine.get_best_hint()
        if hint is not None:
            self.active_hint = hint
            self.hint_bar.config(text=f"💡 Hint: {hint.description}")
            self.render_all()
        else:
            self.hint_bar.config(text="No legal moves available! Try drawing from stockpile.")

    def on_toggle_draw_mode(self):
        """Toggles between Draw 1 and Draw 3 cards."""
        new_mode = 3 if self.engine.draw_count == 1 else 1
        self.engine.draw_count = new_mode
        self.btn_draw_mode.config(text=f"Draw: {new_mode} Card{'s' if new_mode > 1 else ''}")
        self.hint_bar.config(text=f"Mode switched to Draw {new_mode}. Starting new game...")
        self.on_new_game()

    def on_auto_finish(self):
        """Bonus Feature: Auto completes the game when all cards are face-up."""
        if not self.engine.can_auto_finish():
            messagebox.showinfo(
                "Auto-Finish",
                "Auto-Finish becomes available when all cards in the tableau are revealed and the stock is cleared!"
            )
            return

        self._run_auto_finish_step()

    def _run_auto_finish_step(self):
        """Step-by-step animation moving cards to foundations."""
        if self.engine.is_game_won:
            self.render_all()
            self._check_game_status()
            return

        progress = False
        for t_idx in range(7):
            if not self.engine.tableau[t_idx].is_empty():
                if self.engine.move_tableau_to_foundation(t_idx):
                    progress = True
                    break

        if progress:
            self.render_all()
            self._play_sound("snap")
            self.root.after(80, self._run_auto_finish_step)
        else:
            self._check_game_status()

    # =========================================================================
    # TIMERS, STATS & WIN CELEBRATION
    # =========================================================================

    def _update_timer_loop(self):
        """Periodic 1-second update for timer and stats."""
        self.lbl_time.config(text=f"Time: {self.engine.get_formatted_time()}")
        self.lbl_score.config(text=f"Score: {self.engine.score}")
        self.lbl_moves.config(text=f"Moves: {self.engine.moves_count}")
        self.lbl_highscore.config(text=f"Best: {self.engine.get_high_score()}")

        # Auto-finish button visibility / pulse
        if self.engine.can_auto_finish():
            self.btn_autofinish.config(bg="#ff9800", text="⚡ Auto-Finish Available!")
        else:
            self.btn_autofinish.config(bg="#555555", text="⚡ Auto-Finish")

        self.root.after(1000, self._update_timer_loop)

    def _update_controls_state(self):
        """Updates Undo and Redo buttons disabled/enabled state."""
        self.btn_undo.config(state=tk.NORMAL if self.engine.can_undo() else tk.DISABLED)
        self.btn_redo.config(state=tk.NORMAL if self.engine.can_redo() else tk.DISABLED)

    def _check_game_status(self):
        """Checks if player won and displays victory animation."""
        if self.engine.check_win_condition():
            self._play_sound("win")
            self._celebrate_win()

    def _celebrate_win(self):
        """Victory banner and celebratory card fireworks."""
        time_str = self.engine.get_formatted_time()
        score = self.engine.score
        moves = self.engine.moves_count

        # Overlay victory banner on canvas
        cw = self.canvas_width
        ch = self.canvas_height
        self.canvas.create_rectangle(
            cw // 2 - 240, ch // 2 - 120, cw // 2 + 240, ch // 2 + 120,
            fill="#112211", outline=CardTheme.ACCENT_GOLD, width=4
        )
        self.canvas.create_text(
            cw // 2, ch // 2 - 60, text="🎉 CONGRATULATIONS! 🎉",
            font=("Segoe UI", 20, "bold"), fill=CardTheme.ACCENT_GOLD
        )
        self.canvas.create_text(
            cw // 2, ch // 2 - 10, text="YOU WON THE GAME!",
            font=("Segoe UI", 16, "bold"), fill="#ffffff"
        )
        self.canvas.create_text(
            cw // 2, ch // 2 + 35,
            text=f"Final Score: {score}  |  Time: {time_str}  |  Moves: {moves}",
            font=("Segoe UI", 12), fill="#c8e6c9"
        )
        self.canvas.create_text(
            cw // 2, ch // 2 + 75,
            text="Press 'New Game' or 'N' to play again!",
            font=("Segoe UI", 11, "italic"), fill="#81c784"
        )

    def _play_sound(self, sound_type: str):
        """Plays subtle sound cues on Windows."""
        if not self.sound_enabled:
            return
        try:
            import winsound
            if sound_type == "deal":
                winsound.Beep(880, 25)
            elif sound_type == "snap":
                winsound.Beep(1174, 30)
            elif sound_type == "foundation":
                winsound.Beep(1567, 45)
            elif sound_type == "undo":
                winsound.Beep(587, 30)
            elif sound_type == "win":
                for freq in [523, 659, 783, 1046]:
                    winsound.Beep(freq, 70)
        except Exception:
            pass
