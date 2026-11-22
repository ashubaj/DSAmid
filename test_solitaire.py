"""
CSC200 - Data Structures & Algorithms
Comprehensive Unit Tests & Verification Suite for Solitaire Project

Tests:
1. Stack (LIFO) operations
2. Queue (FIFO) operations
3. DoublyLinkedList operations (append, detach sublist, append sublist)
4. CardHashMap (O(1) dictionary operations)
5. Card & Deck logic (Fisher-Yates shuffle, suit/rank rules)
6. Game Engine Mechanics (Initialization, Tableau, Foundations, Moves, Flipping)
7. Undo and Redo Mechanics (Stack-based history reversal)
8. Hint System Validation
9. Win Condition & Auto-Finish Verification
"""

import unittest
from structures import Stack, Queue, DoublyLinkedList, CardHashMap, CardMetadata
from card import Card, Deck, Suit, Rank
from engine import SolitaireEngine


class TestDataStructures(unittest.TestCase):
    def test_stack_lifo(self):
        s = Stack[int]("TestStack")
        self.assertTrue(s.is_empty())
        s.push(10)
        s.push(20)
        s.push(30)
        self.assertEqual(s.size(), 3)
        self.assertEqual(s.peek(), 30)
        self.assertEqual(s.pop(), 30)
        self.assertEqual(s.pop(), 20)
        self.assertEqual(s.pop(), 10)
        self.assertTrue(s.is_empty())
        with self.assertRaises(IndexError):
            s.pop()

    def test_queue_fifo(self):
        q = Queue[str]("TestQueue")
        self.assertTrue(q.is_empty())
        q.enqueue("First")
        q.enqueue("Second")
        q.enqueue("Third")
        self.assertEqual(q.size(), 3)
        self.assertEqual(q.peek(), "First")
        self.assertEqual(q.dequeue(), "First")
        self.assertEqual(q.dequeue(), "Second")
        self.assertEqual(q.dequeue(), "Third")
        self.assertTrue(q.is_empty())
        with self.assertRaises(IndexError):
            q.dequeue()

    def test_doubly_linked_list_splicing(self):
        dll1 = DoublyLinkedList[int]("DLL1")
        for i in [1, 2, 3, 4, 5]:
            dll1.append(i)
        self.assertEqual(dll1.to_list(), [1, 2, 3, 4, 5])
        self.assertEqual(dll1.size(), 5)

        # Detach sublist starting at node with value 3
        node_3 = dll1.find_node(3)
        self.assertIsNotNone(node_3)
        sublist = dll1.detach_sublist_from_node(node_3)

        self.assertEqual(dll1.to_list(), [1, 2])
        self.assertEqual(dll1.size(), 2)
        self.assertEqual(dll1.peek_tail(), 2)
        self.assertEqual(sublist.to_list(), [3, 4, 5])
        self.assertEqual(sublist.size(), 3)

        # Append sublist onto another DLL
        dll2 = DoublyLinkedList[int]("DLL2")
        dll2.append(100)
        dll2.append_sublist(sublist)
        self.assertEqual(dll2.to_list(), [100, 3, 4, 5])
        self.assertEqual(dll2.size(), 4)
        self.assertEqual(dll2.peek_tail(), 5)

    def test_card_hash_map(self):
        hmap = CardHashMap(capacity=16)
        meta1 = CardMetadata("H_1", "tableau", 2, 0, True)
        meta2 = CardMetadata("S_13", "stock", 0, 5, False)

        hmap.put("H_1", meta1)
        hmap.put("S_13", meta2)

        self.assertEqual(hmap.size(), 2)
        self.assertTrue(hmap.contains("H_1"))
        self.assertEqual(hmap.get("H_1").pile_type, "tableau")
        self.assertEqual(hmap.get("S_13").depth, 5)

        # Update
        meta1_updated = CardMetadata("H_1", "foundation", 0, 0, True)
        hmap.put("H_1", meta1_updated)
        self.assertEqual(hmap.get("H_1").pile_type, "foundation")
        self.assertEqual(hmap.size(), 2)

        # Remove
        self.assertTrue(hmap.remove("H_1"))
        self.assertIsNone(hmap.get("H_1"))
        self.assertEqual(hmap.size(), 1)


class TestCardAndDeck(unittest.TestCase):
    def test_deck_creation_and_shuffle(self):
        deck = Deck(seed=42)
        self.assertEqual(deck.size(), 52)
        initial_order = [c.id for c in deck.cards]

        deck.shuffle()
        shuffled_order = [c.id for c in deck.cards]
        self.assertEqual(len(shuffled_order), 52)
        # Verify it shuffled
        self.assertNotEqual(initial_order, shuffled_order)

    def test_card_legality_rules(self):
        black_8 = Card(Suit.SPADES, 8, is_face_up=True)
        red_7 = Card(Suit.HEARTS, 7, is_face_up=True)
        black_7 = Card(Suit.CLUBS, 7, is_face_up=True)
        red_8 = Card(Suit.DIAMONDS, 8, is_face_up=True)
        black_king = Card(Suit.SPADES, 13, is_face_up=True)
        red_ace = Card(Suit.HEARTS, 1, is_face_up=True)
        red_2 = Card(Suit.HEARTS, 2, is_face_up=True)

        # Tableau stacking: alternating colors and descending rank
        self.assertTrue(red_7.can_stack_on_tableau(black_8))
        self.assertFalse(black_7.can_stack_on_tableau(black_8))  # Same color
        self.assertFalse(red_8.can_stack_on_tableau(black_8))  # Same rank
        self.assertTrue(black_king.can_stack_on_tableau(None))  # King on empty
        self.assertFalse(red_7.can_stack_on_tableau(None))      # Non-King on empty

        # Foundation stacking: same suit and ascending rank
        self.assertTrue(red_ace.can_stack_on_foundation(None))  # Ace on empty
        self.assertFalse(red_2.can_stack_on_foundation(None))   # 2 on empty
        self.assertTrue(red_2.can_stack_on_foundation(red_ace)) # 2 on Ace same suit
        spade_2 = Card(Suit.SPADES, 2, is_face_up=True)
        self.assertFalse(spade_2.can_stack_on_foundation(red_ace)) # Different suit


class TestSolitaireEngine(unittest.TestCase):
    def setUp(self):
        # Use a fixed seed for reproducible test results
        self.engine = SolitaireEngine(draw_count=1, seed=123)

    def test_initial_board_setup(self):
        # 7 tableau columns with sizes 1 to 7
        for i in range(7):
            col = self.engine.tableau[i]
            self.assertEqual(col.size(), i + 1)
            # Only top card is face up
            cards = col.to_list()
            for c_idx, card in enumerate(cards):
                if c_idx == len(cards) - 1:
                    self.assertTrue(card.is_face_up)
                else:
                    self.assertFalse(card.is_face_up)

        # 4 Foundations should be empty
        for f in self.engine.foundations:
            self.assertTrue(f.is_empty())

        # Waste should be empty
        self.assertTrue(self.engine.waste.is_empty())

        # Stock should contain 52 - (1+2+3+4+5+6+7) = 24 cards
        self.assertEqual(self.engine.stock.size(), 24)

        # Registry should have 52 entries
        self.assertEqual(self.engine.registry.size(), 52)

    def test_draw_from_stock_and_recycle(self):
        initial_stock_size = self.engine.stock.size()
        self.assertTrue(self.engine.draw_from_stock())
        self.assertEqual(self.engine.stock.size(), initial_stock_size - 1)
        self.assertEqual(self.engine.waste.size(), 1)
        self.assertTrue(self.engine.waste.peek().is_face_up)

        # Draw all remaining cards
        while not self.engine.stock.is_empty():
            self.engine.draw_from_stock()

        self.assertEqual(self.engine.stock.size(), 0)
        self.assertEqual(self.engine.waste.size(), 24)

        # Draw again -> triggers recycle
        self.assertTrue(self.engine.draw_from_stock())
        self.assertEqual(self.engine.stock.size(), 24)
        self.assertEqual(self.engine.waste.size(), 0)

    def test_undo_and_redo_stock_draw(self):
        self.assertEqual(self.engine.stock.size(), 24)
        self.assertEqual(self.engine.waste.size(), 0)

        # Draw
        self.engine.draw_from_stock()
        self.assertEqual(self.engine.stock.size(), 23)
        self.assertEqual(self.engine.waste.size(), 1)

        # Undo
        self.assertTrue(self.engine.can_undo())
        self.engine.undo()
        self.assertEqual(self.engine.stock.size(), 24)
        self.assertEqual(self.engine.waste.size(), 0)

        # Redo
        self.assertTrue(self.engine.can_redo())
        self.engine.redo()
        self.assertEqual(self.engine.stock.size(), 23)
        self.assertEqual(self.engine.waste.size(), 1)

    def test_tableau_move_and_card_flip(self):
        # Manually configure a specific scenario
        col0 = self.engine.tableau[0]
        col1 = self.engine.tableau[1]

        col0.clear()
        col1.clear()

        # col0: [Hidden card, Black 8]
        hidden_card = Card(Suit.SPADES, 10, is_face_up=False)
        black_8 = Card(Suit.SPADES, 8, is_face_up=True)
        col0.append(hidden_card)
        col0.append(black_8)

        # col1: [Red 9]
        red_9 = Card(Suit.HEARTS, 9, is_face_up=True)
        col1.append(red_9)

        self.engine._sync_registry()

        # Move Black 8 from col0 to col1
        success = self.engine.move_tableau_to_tableau(0, 1)
        self.assertTrue(success)

        # Verify col1 now has [Red 9, Black 8]
        self.assertEqual(col1.size(), 2)
        self.assertEqual(col1.peek_tail().id, black_8.id)

        # Verify col0 now has 1 card, and hidden_card was flipped face-up!
        self.assertEqual(col0.size(), 1)
        self.assertTrue(hidden_card.is_face_up)

        # Undo move!
        self.engine.undo()
        self.assertEqual(col0.size(), 2)
        self.assertEqual(col1.size(), 1)
        # hidden_card must be reverted back to face-down!
        self.assertFalse(hidden_card.is_face_up)

    def test_foundation_move(self):
        # Clear foundation 0
        f0 = self.engine.foundations[0]
        f0.clear()

        # Place Ace in Waste
        ace = Card(Suit.HEARTS, 1, is_face_up=True)
        self.engine.waste.push(ace)
        self.engine._sync_registry()

        success = self.engine.move_waste_to_foundation(0)
        self.assertTrue(success)
        self.assertEqual(f0.size(), 1)
        self.assertEqual(f0.peek().id, ace.id)
        self.assertTrue(self.engine.waste.is_empty())

        # Try placing 3 on Ace (illegal)
        three = Card(Suit.HEARTS, 3, is_face_up=True)
        self.engine.waste.push(three)
        self.engine._sync_registry()
        self.assertFalse(self.engine.move_waste_to_foundation(0))

        # Place 2 on Ace (legal)
        two = Card(Suit.HEARTS, 2, is_face_up=True)
        self.engine.waste.pop()
        self.engine.waste.push(two)
        self.engine._sync_registry()
        self.assertTrue(self.engine.move_waste_to_foundation(0))
        self.assertEqual(f0.size(), 2)

    def test_hints_available(self):
        hints = self.engine.get_hints()
        self.assertIsInstance(hints, list)
        self.assertGreater(len(hints), 0)
        best = self.engine.get_best_hint()
        self.assertIsNotNone(best)
        self.assertIn("Move", best.description)

    def test_win_condition(self):
        self.assertFalse(self.engine.check_win_condition())
        # Artificially fill foundations with 13 cards each
        for suit_idx, suit in enumerate(Suit.ALL):
            f = self.engine.foundations[suit_idx]
            f.clear()
            for r in range(1, 14):
                f.push(Card(suit, r, is_face_up=True))

        self.assertTrue(self.engine.check_win_condition())
        self.assertTrue(self.engine.is_game_won)


if __name__ == '__main__':
    unittest.main()
