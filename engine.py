"""
CSC200 - Data Structures & Algorithms
Solitaire (Klondike) Core Engine (Phase 2, Phase 3 & Bonus Features)

Integrates:
- 1. Stack: Foundation piles (LIFO), Waste pile, Undo/Redo history stacks
- 2. Queue: Stockpile draw management (FIFO)
- 3. DoublyLinkedList: Tableau columns with O(1) sub-stack splitting/splicing
- 4. Array/List: Initial deck representation & Fisher-Yates shuffle
- 5. CardHashMap: O(1) card registry tracking location, depth, and face-up state
- Bonus 1: Robust Undo/Redo System using Stacks
- Bonus 2: Intelligent Multi-level Hint System
- Bonus 3: Scoring system, move counting, and game performance tracking
"""

import time
import json
import os
from typing import List, Optional, Tuple, Dict, Any

from structures import Stack, Queue, DoublyLinkedList, DListNode, CardHashMap, CardMetadata
from card import Card, Deck, Suit, Rank


class MoveAction:
    """Records full state delta of a move for exact Undo and Redo execution."""
    def __init__(
        self,
        action_type: str,
        source: Tuple[str, int],       # ('tableau', idx), ('waste', 0), ('foundation', idx), ('stock', 0)
        target: Tuple[str, int],       # ('tableau', idx), ('foundation', idx), ('waste', 0), ('stock', 0)
        cards: List[Card],             # Cards moved in order
        uncovered_card: Optional[Card] = None,  # Card that was flipped face-up as a result
        score_delta: int = 0,
        extra_data: Optional[Dict[str, Any]] = None
    ):
        self.action_type = action_type
        self.source = source
        self.target = target
        self.cards = list(cards)
        self.uncovered_card = uncovered_card
        self.score_delta = score_delta
        self.extra_data = extra_data or {}

    def __repr__(self) -> str:
        return (f"MoveAction({self.action_type}, {self.source}->{self.target}, "
                f"cards={[c.rank_name + c.symbol for c in self.cards]}, "
                f"uncovered={self.uncovered_card}, score_delta={self.score_delta})")


class Hint:
    """Represents a suggested legal move with human-readable rationale."""
    def __init__(self, source: Tuple[str, int], target: Tuple[str, int], card: Card, description: str, priority: int):
        self.source = source
        self.target = target
        self.card = card
        self.description = description
        self.priority = priority  # Higher number = more strategically favorable

    def __repr__(self) -> str:
        return f"Hint(priority={self.priority}, {self.description})"


class SolitaireEngine:
    """
    Main Game Controller orchestrating all rules, data structures, and features.
    """
    def __init__(self, draw_count: int = 1, seed: Optional[int] = None):
        self.draw_count = draw_count  # 1 or 3
        self.seed = seed

        # Required Data Structures:
        # 1. Tableau: 7 columns, each implemented via DoublyLinkedList for sublist slicing
        self.tableau: List[DoublyLinkedList[Card]] = [
            DoublyLinkedList[Card](name=f"Tableau_{i+1}") for i in range(7)
        ]

        # 2. Foundation: 4 piles, each implemented via Stack (LIFO)
        self.foundations: List[Stack[Card]] = [
            Stack[Card](name=f"Foundation_{i+1}") for i in range(4)
        ]

        # 3. Stockpile: Implemented via Queue (FIFO) for sequential card drawing
        self.stock: Queue[Card] = Queue[Card](name="StockQueue")

        # 4. Waste pile: Implemented via Stack (LIFO)
        self.waste: Stack[Card] = Stack[Card](name="WasteStack")

        # 5. Card Registry: HashMap for O(1) state and location tracking
        self.registry: CardHashMap = CardHashMap(capacity=64)

        # Bonus 1: Undo and Redo Stacks (LIFO)
        self.undo_stack: Stack[MoveAction] = Stack[MoveAction](name="UndoStack")
        self.redo_stack: Stack[MoveAction] = Stack[MoveAction](name="RedoStack")

        # Bonus 3: Scoring and Statistics
        self.score: int = 0
        self.moves_count: int = 0
        self.start_time: float = time.time()
        self.is_game_won: bool = False
        self.stock_recycles: int = 0

        # Start initial game
        self.start_new_game()

    # =========================================================================
    # INITIALIZATION & SETUP
    # =========================================================================

    def start_new_game(self, seed: Optional[int] = None) -> None:
        """Initializes a new game according to Klondike Solitaire rules."""
        if seed is not None:
            self.seed = seed

        # Clear all structures
        for col in self.tableau:
            col.clear()
        for f in self.foundations:
            f.clear()
        self.stock.clear()
        self.waste.clear()
        self.registry.clear()
        self.undo_stack.clear()
        self.redo_stack.clear()

        self.score = 0
        self.moves_count = 0
        self.start_time = time.time()
        self.is_game_won = False
        self.stock_recycles = 0

        # 1. Create 52-card deck using Array/List and shuffle with Fisher-Yates
        deck = Deck(seed=self.seed)
        deck.shuffle()

        # 2. Deal Tableau: Pile i gets (i + 1) cards (1 to 7)
        for i in range(7):
            num_cards = i + 1
            for j in range(num_cards):
                card = deck.deal()
                if card is None:
                    break
                # Only the last (topmost) card is face-up
                card.is_face_up = (j == num_cards - 1)
                self.tableau[i].append(card)

        # 3. Remaining 24 cards go into the Stock Queue (face-down)
        while not deck.is_empty():
            card = deck.deal()
            if card:
                card.is_face_up = False
                self.stock.enqueue(card)

        # 4. Synchronize HashMap Registry
        self._sync_registry()

    def restart_game(self) -> None:
        """Restarts the same game layout from the original seed."""
        self.start_new_game(seed=self.seed)

    def _sync_registry(self) -> None:
        """Updates the CardHashMap with current locations and states of all cards."""
        self.registry.clear()

        # Stock cards
        stock_list = self.stock.to_list()
        for idx, card in enumerate(stock_list):
            self.registry.put(card.id, CardMetadata(card.id, 'stock', 0, idx, card.is_face_up))

        # Waste cards
        waste_list = self.waste.to_list()
        for idx, card in enumerate(waste_list):
            self.registry.put(card.id, CardMetadata(card.id, 'waste', 0, idx, card.is_face_up))

        # Foundation cards
        for f_idx, foundation in enumerate(self.foundations):
            f_list = foundation.to_list()
            for idx, card in enumerate(f_list):
                self.registry.put(card.id, CardMetadata(card.id, 'foundation', f_idx, idx, card.is_face_up))

        # Tableau cards
        for t_idx, col in enumerate(self.tableau):
            t_list = col.to_list()
            for idx, card in enumerate(t_list):
                self.registry.put(card.id, CardMetadata(card.id, 'tableau', t_idx, idx, card.is_face_up))

    # =========================================================================
    # CORE GAMEPLAY MOVES & VALIDATION
    # =========================================================================

    def draw_from_stock(self) -> bool:
        """
        Draws 1 (or draw_count) cards from Stock Queue and places them onto Waste Stack.
        If stock is empty, recycles all cards from Waste Stack back into Stock Queue.
        """
        if self.stock.is_empty() and self.waste.is_empty():
            return False  # No cards to draw or recycle

        if self.stock.is_empty():
            # Recycle Waste back to Stock
            # Cards in waste are popped LIFO and enqueued back to Stock Queue
            cards_recycled = []
            while not self.waste.is_empty():
                c = self.waste.pop()
                c.is_face_up = False
                self.stock.enqueue(c)
                cards_recycled.append(c)

            self.stock_recycles += 1
            # Penalty for recycling in Klondike (optional penalty)
            penalty = -20 if self.draw_count == 1 else -0
            self.score = max(0, self.score + penalty)
            self.moves_count += 1

            action = MoveAction(
                action_type="RECYCLE_WASTE_TO_STOCK",
                source=('waste', 0),
                target=('stock', 0),
                cards=cards_recycled,
                score_delta=penalty
            )
            self.undo_stack.push(action)
            self.redo_stack.clear()
            self._sync_registry()
            return True

        # Normal Draw from Stock Queue
        drawn_cards = []
        count = min(self.draw_count, self.stock.size())
        for _ in range(count):
            card = self.stock.dequeue()
            card.is_face_up = True
            self.waste.push(card)
            drawn_cards.append(card)

        self.moves_count += 1
        action = MoveAction(
            action_type="STOCK_TO_WASTE",
            source=('stock', 0),
            target=('waste', 0),
            cards=drawn_cards,
            score_delta=0
        )
        self.undo_stack.push(action)
        self.redo_stack.clear()
        self._sync_registry()
        return True

    def move_waste_to_tableau(self, tableau_idx: int) -> bool:
        """Moves the top card of the waste pile to a tableau column."""
        if not (0 <= tableau_idx < 7):
            return False
        if self.waste.is_empty():
            return False

        card = self.waste.peek()
        target_col = self.tableau[tableau_idx]
        target_top = target_col.peek_tail()

        if not card.can_stack_on_tableau(target_top):
            return False

        # Execute move
        moved_card = self.waste.pop()
        target_col.append(moved_card)

        score_gain = 5  # Waste to Tableau: +5 pts
        self.score += score_gain
        self.moves_count += 1

        action = MoveAction(
            action_type="WASTE_TO_TABLEAU",
            source=('waste', 0),
            target=('tableau', tableau_idx),
            cards=[moved_card],
            score_delta=score_gain
        )
        self.undo_stack.push(action)
        self.redo_stack.clear()
        self._sync_registry()
        self.check_win_condition()
        return True

    def move_waste_to_foundation(self, foundation_idx: Optional[int] = None) -> bool:
        """
        Moves the top card of the waste pile to a foundation pile.
        If foundation_idx is None, automatically finds a matching foundation.
        """
        if self.waste.is_empty():
            return False

        card = self.waste.peek()

        if foundation_idx is None:
            # Auto-find valid foundation
            foundation_idx = self._find_valid_foundation_index(card)
            if foundation_idx is None:
                return False
        else:
            if not (0 <= foundation_idx < 4):
                return False
            target_f = self.foundations[foundation_idx]
            if not card.can_stack_on_foundation(target_f.peek()):
                return False

        # Execute move
        moved_card = self.waste.pop()
        self.foundations[foundation_idx].push(moved_card)

        score_gain = 10  # Waste to Foundation: +10 pts
        self.score += score_gain
        self.moves_count += 1

        action = MoveAction(
            action_type="WASTE_TO_FOUNDATION",
            source=('waste', 0),
            target=('foundation', foundation_idx),
            cards=[moved_card],
            score_delta=score_gain
        )
        self.undo_stack.push(action)
        self.redo_stack.clear()
        self._sync_registry()
        self.check_win_condition()
        return True

    def move_tableau_to_tableau(self, source_idx: int, target_idx: int, start_card_id: Optional[str] = None) -> bool:
        """
        Moves a sub-stack of cards from source tableau to target tableau.
        Uses DoublyLinkedList O(1) detach and append!
        """
        if source_idx == target_idx:
            return False
        if not (0 <= source_idx < 7 and 0 <= target_idx < 7):
            return False

        src_col = self.tableau[source_idx]
        dst_col = self.tableau[target_idx]

        if src_col.is_empty():
            return False

        # Determine start node
        if start_card_id is None:
            # Default to top card
            start_node = src_col.peek_tail_node()
        else:
            # Find node matching card id
            curr = src_col.head
            start_node = None
            while curr is not None:
                if curr.data.id == start_card_id:
                    start_node = curr
                    break
                curr = curr.next

        if start_node is None:
            return False

        # The starting card must be face-up to move
        if not start_node.data.is_face_up:
            return False

        # Validate legality against target pile's top card
        target_top = dst_col.peek_tail()
        if not start_node.data.can_stack_on_tableau(target_top):
            return False

        # Execute DoublyLinkedList pointer detach & splice!
        sublist = src_col.detach_sublist_from_node(start_node)
        cards_moved = sublist.to_list()
        dst_col.append_sublist(sublist)

        # Check if the newly exposed top card of source column needs to be flipped face-up
        uncovered_card = None
        new_top = src_col.peek_tail()
        score_gain = 0
        if new_top is not None and not new_top.is_face_up:
            new_top.is_face_up = True
            uncovered_card = new_top
            score_gain += 5  # Uncovering a tableau card: +5 pts
            self.score += 5

        self.moves_count += 1
        action = MoveAction(
            action_type="TABLEAU_TO_TABLEAU",
            source=('tableau', source_idx),
            target=('tableau', target_idx),
            cards=cards_moved,
            uncovered_card=uncovered_card,
            score_delta=score_gain
        )
        self.undo_stack.push(action)
        self.redo_stack.clear()
        self._sync_registry()
        self.check_win_condition()
        return True

    def move_tableau_to_foundation(self, source_idx: int, foundation_idx: Optional[int] = None) -> bool:
        """
        Moves the top card of a tableau column to a foundation pile.
        """
        if not (0 <= source_idx < 7):
            return False
        src_col = self.tableau[source_idx]
        if src_col.is_empty():
            return False

        card = src_col.peek_tail()
        if card is None or not card.is_face_up:
            return False

        if foundation_idx is None:
            foundation_idx = self._find_valid_foundation_index(card)
            if foundation_idx is None:
                return False
        else:
            if not (0 <= foundation_idx < 4):
                return False
            target_f = self.foundations[foundation_idx]
            if not card.can_stack_on_foundation(target_f.peek()):
                return False

        # Pop from tableau
        moved_card = src_col.pop_tail()
        self.foundations[foundation_idx].push(moved_card)

        # Check if newly exposed top card needs to be flipped face-up
        uncovered_card = None
        new_top = src_col.peek_tail()
        score_gain = 10  # Tableau to Foundation: +10 pts
        if new_top is not None and not new_top.is_face_up:
            new_top.is_face_up = True
            uncovered_card = new_top
            score_gain += 5  # Turning over hidden card: +5 pts

        self.score += score_gain
        self.moves_count += 1

        action = MoveAction(
            action_type="TABLEAU_TO_FOUNDATION",
            source=('tableau', source_idx),
            target=('foundation', foundation_idx),
            cards=[moved_card],
            uncovered_card=uncovered_card,
            score_delta=score_gain
        )
        self.undo_stack.push(action)
        self.redo_stack.clear()
        self._sync_registry()
        self.check_win_condition()
        return True

    def move_foundation_to_tableau(self, foundation_idx: int, tableau_idx: int) -> bool:
        """
        Moves the top card of a foundation pile back down to a tableau column.
        (Allowed in standard Klondike rules with -15 score penalty).
        """
        if not (0 <= foundation_idx < 4 and 0 <= tableau_idx < 7):
            return False

        f_pile = self.foundations[foundation_idx]
        if f_pile.is_empty():
            return False

        card = f_pile.peek()
        dst_col = self.tableau[tableau_idx]
        target_top = dst_col.peek_tail()

        if not card.can_stack_on_tableau(target_top):
            return False

        moved_card = f_pile.pop()
        dst_col.append(moved_card)

        score_penalty = -15  # Standard Klondike penalty
        self.score = max(0, self.score + score_penalty)
        self.moves_count += 1

        action = MoveAction(
            action_type="FOUNDATION_TO_TABLEAU",
            source=('foundation', foundation_idx),
            target=('tableau', tableau_idx),
            cards=[moved_card],
            score_delta=score_penalty
        )
        self.undo_stack.push(action)
        self.redo_stack.clear()
        self._sync_registry()
        return True

    def auto_play_card(self, card_id: str) -> bool:
        """
        Intelligent one-click / double-click helper:
        Attempts to automatically move the card to the Foundation first,
        or to the best valid Tableau pile if Foundation is not possible.
        """
        meta = self.registry.get(card_id)
        if meta is None or not meta.is_face_up:
            return False

        # Case 1: Waste card
        if meta.pile_type == 'waste':
            # Try Foundation first
            if self.move_waste_to_foundation():
                return True
            # Try Tableau
            for t_idx in range(7):
                if self.move_waste_to_tableau(t_idx):
                    return True
            return False

        # Case 2: Tableau card
        if meta.pile_type == 'tableau':
            col_idx = meta.pile_index
            col = self.tableau[col_idx]
            # Only top card can go to Foundation
            if col.peek_tail() and col.peek_tail().id == card_id:
                if self.move_tableau_to_foundation(col_idx):
                    return True
            # Try moving sub-stack to another Tableau column
            for t_idx in range(7):
                if t_idx != col_idx:
                    if self.move_tableau_to_tableau(col_idx, t_idx, start_card_id=card_id):
                        return True
            return False

        # Case 3: Foundation card to Tableau
        if meta.pile_type == 'foundation':
            f_idx = meta.pile_index
            for t_idx in range(7):
                if self.move_foundation_to_tableau(f_idx, t_idx):
                    return True
            return False

        return False

    def auto_finish_if_possible(self) -> bool:
        """
        Checks if the game is in an 'auto-win' state:
        Stock is empty, Waste is empty, and all cards in the Tableau are face-up.
        If true, automatically moves all cards to foundations sequentially.
        """
        if not self.stock.is_empty() or not self.waste.is_empty():
            return False

        for col in self.tableau:
            for card in col:
                if not card.is_face_up:
                    return False

        # Game is guaranteed won! Perform automatic resolution
        progress = True
        while progress and not self.is_game_won:
            progress = False
            for t_idx in range(7):
                if not self.tableau[t_idx].is_empty():
                    if self.move_tableau_to_foundation(t_idx):
                        progress = True
                        break
        return self.is_game_won

    def can_auto_finish(self) -> bool:
        """Returns True if the game is currently eligible for Auto-Finish."""
        if not self.stock.is_empty() or not self.waste.is_empty():
            return False
        for col in self.tableau:
            for card in col:
                if not card.is_face_up:
                    return False
        return not self.is_game_won

    # =========================================================================
    # BONUS 1: UNDO & REDO SYSTEM (STACK-BASED)
    # =========================================================================

    def can_undo(self) -> bool:
        return not self.undo_stack.is_empty()

    def can_redo(self) -> bool:
        return not self.redo_stack.is_empty()

    def undo(self) -> bool:
        """
        Reverses the last action using the undo_stack (LIFO).
        Pushes reversed action onto redo_stack.
        """
        if self.undo_stack.is_empty():
            return False

        action = self.undo_stack.pop()

        # Revert score
        self.score = max(0, self.score - action.score_delta)
        self.moves_count += 1

        # Re-cover the card if it was flipped face-up by this move
        if action.uncovered_card is not None:
            action.uncovered_card.is_face_up = False

        # Execute inverse move based on action type
        if action.action_type == "STOCK_TO_WASTE":
            # Cards were popped from stock queue into waste stack.
            # To revert: pop from waste stack and enqueue back to the FRONT of stock queue.
            # (Or recreate stock queue order)
            for _ in range(len(action.cards)):
                c = self.waste.pop()
                c.is_face_up = False
            # Reconstruct stock queue: put undone cards back at the front
            all_stock = action.cards + self.stock.to_list()
            self.stock.clear()
            for c in all_stock:
                self.stock.enqueue(c)

        elif action.action_type == "RECYCLE_WASTE_TO_STOCK":
            # Revert recycling: empty stock queue, push cards back onto waste stack face-up
            self.stock.clear()
            for c in reversed(action.cards):
                c.is_face_up = True
                self.waste.push(c)
            self.stock_recycles = max(0, self.stock_recycles - 1)

        elif action.action_type == "WASTE_TO_TABLEAU":
            # Pop card from tableau and push back onto waste
            t_idx = action.target[1]
            c = self.tableau[t_idx].pop_tail()
            self.waste.push(c)

        elif action.action_type == "WASTE_TO_FOUNDATION":
            # Pop card from foundation and push back onto waste
            f_idx = action.target[1]
            c = self.foundations[f_idx].pop()
            self.waste.push(c)

        elif action.action_type == "TABLEAU_TO_FOUNDATION":
            # Pop card from foundation and append back to source tableau
            src_t_idx = action.source[1]
            f_idx = action.target[1]
            c = self.foundations[f_idx].pop()
            self.tableau[src_t_idx].append(c)

        elif action.action_type == "FOUNDATION_TO_TABLEAU":
            # Pop card from tableau and push back to foundation
            src_f_idx = action.source[1]
            dst_t_idx = action.target[1]
            c = self.tableau[dst_t_idx].pop_tail()
            self.foundations[src_f_idx].push(c)

        elif action.action_type == "TABLEAU_TO_TABLEAU":
            # Move sublist from target tableau back to source tableau
            src_t_idx = action.source[1]
            dst_t_idx = action.target[1]
            count = len(action.cards)

            # Detach the last 'count' cards from dst_col
            dst_col = self.tableau[dst_t_idx]
            src_col = self.tableau[src_t_idx]

            # Find the starting node of the sublist in dst_col
            curr = dst_col.head
            target_start_card_id = action.cards[0].id
            while curr is not None:
                if curr.data.id == target_start_card_id:
                    break
                curr = curr.next

            if curr is not None:
                sub = dst_col.detach_sublist_from_node(curr)
                src_col.append_sublist(sub)

        # Push action onto redo stack
        self.redo_stack.push(action)
        self._sync_registry()
        self.is_game_won = False
        return True

    def redo(self) -> bool:
        """
        Re-applies the last undone action using the redo_stack (LIFO).
        """
        if self.redo_stack.is_empty():
            return False

        action = self.redo_stack.pop()

        # Re-apply score
        self.score += action.score_delta
        self.moves_count += 1

        if action.action_type == "STOCK_TO_WASTE":
            count = len(action.cards)
            for _ in range(count):
                c = self.stock.dequeue()
                c.is_face_up = True
                self.waste.push(c)

        elif action.action_type == "RECYCLE_WASTE_TO_STOCK":
            while not self.waste.is_empty():
                c = self.waste.pop()
                c.is_face_up = False
                self.stock.enqueue(c)
            self.stock_recycles += 1

        elif action.action_type == "WASTE_TO_TABLEAU":
            t_idx = action.target[1]
            c = self.waste.pop()
            self.tableau[t_idx].append(c)

        elif action.action_type == "WASTE_TO_FOUNDATION":
            f_idx = action.target[1]
            c = self.waste.pop()
            self.foundations[f_idx].push(c)

        elif action.action_type == "TABLEAU_TO_FOUNDATION":
            src_t_idx = action.source[1]
            f_idx = action.target[1]
            c = self.tableau[src_t_idx].pop_tail()
            self.foundations[f_idx].push(c)

        elif action.action_type == "FOUNDATION_TO_TABLEAU":
            src_f_idx = action.source[1]
            dst_t_idx = action.target[1]
            c = self.foundations[src_f_idx].pop()
            self.tableau[dst_t_idx].append(c)

        elif action.action_type == "TABLEAU_TO_TABLEAU":
            src_t_idx = action.source[1]
            dst_t_idx = action.target[1]
            src_col = self.tableau[src_t_idx]
            dst_col = self.tableau[dst_t_idx]

            curr = src_col.head
            target_start_card_id = action.cards[0].id
            while curr is not None:
                if curr.data.id == target_start_card_id:
                    break
                curr = curr.next

            if curr is not None:
                sub = src_col.detach_sublist_from_node(curr)
                dst_col.append_sublist(sub)

        # Re-flip uncovered card if applicable
        if action.uncovered_card is not None:
            action.uncovered_card.is_face_up = True

        self.undo_stack.push(action)
        self._sync_registry()
        self.check_win_condition()
        return True

    # =========================================================================
    # BONUS 2: HINT SYSTEM
    # =========================================================================

    def get_hints(self) -> List[Hint]:
        """
        Examines the entire game state and returns all valid moves sorted by
        strategic priority.
        Priority tiers:
          10: Move to Foundation (Aces and 2s are completely safe; higher ranks when safe)
          8: Tableau move that uncovers a hidden face-down card
          7: Move King to empty tableau space to unlock a column
          6: Waste to Foundation
          5: Waste to Tableau
          4: Tableau to Tableau consolidation
          2: Draw from Stock
        """
        hints: List[Hint] = []

        # 1. Check Tableau to Foundation
        for t_idx, col in enumerate(self.tableau):
            top_card = col.peek_tail()
            if top_card and top_card.is_face_up:
                f_idx = self._find_valid_foundation_index(top_card)
                if f_idx is not None:
                    # Priority is higher for lower ranks or if safe
                    prio = 10 if top_card.rank <= 2 else 7
                    hints.append(Hint(
                        source=('tableau', t_idx),
                        target=('foundation', f_idx),
                        card=top_card,
                        description=f"Move {top_card.rank_name}{top_card.symbol} from Tableau {t_idx+1} to Foundation {f_idx+1}",
                        priority=prio
                    ))

        # 2. Check Waste to Foundation
        if not self.waste.is_empty():
            w_card = self.waste.peek()
            f_idx = self._find_valid_foundation_index(w_card)
            if f_idx is not None:
                prio = 9 if w_card.rank <= 2 else 6
                hints.append(Hint(
                    source=('waste', 0),
                    target=('foundation', f_idx),
                    card=w_card,
                    description=f"Move {w_card.rank_name}{w_card.symbol} from Waste to Foundation {f_idx+1}",
                    priority=prio
                ))

        # 3. Check Tableau to Tableau
        for src_idx, src_col in enumerate(self.tableau):
            # Scan for all face-up cards in src_col
            curr = src_col.head
            node_idx = 0
            while curr is not None:
                card = curr.data
                if card.is_face_up:
                    # Can we move this card to another tableau?
                    for dst_idx, dst_col in enumerate(self.tableau):
                        if dst_idx == src_idx:
                            continue
                        dst_top = dst_col.peek_tail()

                        if card.can_stack_on_tableau(dst_top):
                            # Avoid meaningless moving King from empty to empty
                            if dst_top is None and curr.prev is None:
                                continue

                            # Calculate strategic priority
                            # If moving this card uncovers a face-down card behind it:
                            uncovers_hidden = (curr.prev is not None and not curr.prev.data.is_face_up)
                            if uncovers_hidden:
                                prio = 8
                            elif dst_top is None and card.rank == Rank.KING:
                                prio = 7
                            else:
                                prio = 4

                            hints.append(Hint(
                                source=('tableau', src_idx),
                                target=('tableau', dst_idx),
                                card=card,
                                description=f"Move {card.rank_name}{card.symbol} from Tableau {src_idx+1} onto {dst_top.rank_name + dst_top.symbol if dst_top else 'Empty Space'} in Tableau {dst_idx+1}",
                                priority=prio
                            ))
                curr = curr.next
                node_idx += 1

        # 4. Check Waste to Tableau
        if not self.waste.is_empty():
            w_card = self.waste.peek()
            for dst_idx, dst_col in enumerate(self.tableau):
                dst_top = dst_col.peek_tail()
                if w_card.can_stack_on_tableau(dst_top):
                    prio = 5 if dst_top is not None else 6  # King into empty space is good
                    hints.append(Hint(
                        source=('waste', 0),
                        target=('tableau', dst_idx),
                        card=w_card,
                        description=f"Move {w_card.rank_name}{w_card.symbol} from Waste onto {dst_top.rank_name + dst_top.symbol if dst_top else 'Empty Space'} in Tableau {dst_idx+1}",
                        priority=prio
                    ))

        # 5. Stock draw suggestion
        if not self.stock.is_empty() or not self.waste.is_empty():
            hints.append(Hint(
                source=('stock', 0),
                target=('waste', 0),
                card=Card(Suit.SPADES, 1, is_face_up=False),  # placeholder
                description="Draw card(s) from Stockpile" if not self.stock.is_empty() else "Recycle Waste into Stockpile",
                priority=2
            ))

        # Sort hints by descending priority
        hints.sort(key=lambda h: h.priority, reverse=True)
        return hints

    def get_best_hint(self) -> Optional[Hint]:
        """Returns the highest priority hint or None if no moves exist."""
        hints = self.get_hints()
        return hints[0] if hints else None

    # =========================================================================
    # HELPERS & WIN CONDITION
    # =========================================================================

    def _find_valid_foundation_index(self, card: Card) -> Optional[int]:
        """Finds an index (0-3) of a foundation pile where this card legally fits."""
        # Check existing non-empty foundations with matching suit
        for idx, f in enumerate(self.foundations):
            if not f.is_empty():
                top = f.peek()
                if card.can_stack_on_foundation(top):
                    return idx

        # If card is Ace, look for an empty foundation
        if card.rank == Rank.ACE:
            for idx, f in enumerate(self.foundations):
                if f.is_empty():
                    return idx
        return None

    def check_win_condition(self) -> bool:
        """
        Game is won when all 4 foundations have 13 cards (total 52 cards).
        """
        total = sum(f.size() for f in self.foundations)
        if total == 52:
            self.is_game_won = True
            # Award win bonus score based on time
            elapsed = self.get_elapsed_time()
            time_bonus = max(0, 1000 - int(elapsed) * 2)
            self.score += time_bonus
            self.save_high_score()
            return True
        return False

    def get_elapsed_time(self) -> float:
        """Returns elapsed time in seconds."""
        return time.time() - self.start_time

    def get_formatted_time(self) -> str:
        """Returns elapsed time formatted as MM:SS."""
        secs = int(self.get_elapsed_time())
        mins = secs // 60
        secs = secs % 60
        return f"{mins:02d}:{secs:02d}"

    def save_high_score(self, filepath: str = "high_scores.json") -> None:
        """Persists high scores to a JSON file."""
        data = {
            "high_score": self.score,
            "best_time": self.get_formatted_time(),
            "best_moves": self.moves_count
        }
        try:
            existing = {}
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    existing = json.load(f)
            if self.score > existing.get("high_score", 0):
                existing["high_score"] = self.score
            if existing.get("best_moves") is None or self.moves_count < existing.get("best_moves", 999999):
                existing["best_moves"] = self.moves_count
            with open(filepath, 'w') as f:
                json.dump(existing, f, indent=2)
        except Exception:
            pass

    def get_high_score(self, filepath: str = "high_scores.json") -> int:
        """Reads high score from JSON."""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    return data.get("high_score", 0)
        except Exception:
            pass
        return 0
