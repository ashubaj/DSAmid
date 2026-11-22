"""
CSC200 - Data Structures & Algorithms
Card Representation & Deck Implementation (Phase 1)

Implements:
- Suit and Rank definitions
- Card class with suit, rank, color, and face-up state
- Move legality helpers (alternating colors for tableau, same suit ascending for foundation)
- Deck class using Array/List with custom Fisher-Yates shuffle
"""

import random
from typing import List, Optional


class Suit:
    HEARTS = "Hearts"
    DIAMONDS = "Diamonds"
    CLUBS = "Clubs"
    SPADES = "Spades"

    ALL = [HEARTS, DIAMONDS, CLUBS, SPADES]
    SYMBOLS = {
        HEARTS: "♥",
        DIAMONDS: "♦",
        CLUBS: "♣",
        SPADES: "♠"
    }
    COLORS = {
        HEARTS: "RED",
        DIAMONDS: "RED",
        CLUBS: "BLACK",
        SPADES: "BLACK"
    }


class Rank:
    ACE = 1
    JACK = 11
    QUEEN = 12
    KING = 13

    NAMES = {
        1: "A",
        2: "2",
        3: "3",
        4: "4",
        5: "5",
        6: "6",
        7: "7",
        8: "8",
        9: "9",
        10: "10",
        11: "J",
        12: "Q",
        13: "K"
    }

    FULL_NAMES = {
        1: "Ace", 2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six", 7: "Seven",
        8: "Eight", 9: "Nine", 10: "Ten", 11: "Jack", 12: "Queen", 13: "King"
    }


class Card:
    """
    Represents a playing card in the Solitaire game.
    Attributes:
      - suit: Hearts, Diamonds, Clubs, Spades
      - rank: 1 (Ace) to 13 (King)
      - is_face_up: bool
      - id: unique identifier string e.g. 'H_1', 'S_13'
    """
    def __init__(self, suit: str, rank: int, is_face_up: bool = False):
        if suit not in Suit.ALL:
            raise ValueError(f"Invalid suit: {suit}")
        if not (1 <= rank <= 13):
            raise ValueError(f"Invalid rank: {rank}")

        self.suit = suit
        self.rank = rank
        self.is_face_up = is_face_up
        self.color = Suit.COLORS[suit]
        self.symbol = Suit.SYMBOLS[suit]
        self.rank_name = Rank.NAMES[rank]
        self.id = f"{suit[0]}_{rank}"  # e.g., 'H_1' for Ace of Hearts

    def flip(self, face_up: Optional[bool] = None) -> None:
        """Flips card face up/down or toggles."""
        if face_up is None:
            self.is_face_up = not self.is_face_up
        else:
            self.is_face_up = face_up

    def can_stack_on_tableau(self, target_card: Optional['Card']) -> bool:
        """
        Rule for Tableau placement:
        - If tableau is empty (target_card is None): Only a KING (rank 13) can be placed.
        - If tableau has cards: Moving card must be opposite color and rank exactly 1 lower.
        """
        if target_card is None:
            return self.rank == Rank.KING
        return (self.color != target_card.color) and (self.rank == target_card.rank - 1)

    def can_stack_on_foundation(self, top_foundation_card: Optional['Card']) -> bool:
        """
        Rule for Foundation placement:
        - If foundation is empty (top_card is None): Only an ACE (rank 1) can be placed.
        - If foundation has cards: Moving card must have the same suit and rank exactly 1 higher.
        """
        if top_foundation_card is None:
            return self.rank == Rank.ACE
        return (self.suit == top_foundation_card.suit) and (self.rank == top_foundation_card.rank + 1)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Card):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def __str__(self) -> str:
        if not self.is_face_up:
            return "[???]"
        return f"[{self.rank_name}{self.symbol}]"

    def __repr__(self) -> str:
        status = "UP" if self.is_face_up else "DOWN"
        return f"Card({self.rank_name}{self.symbol}, {status})"


class Deck:
    """
    Array/List implementation storing the 52 standard playing cards.
    Provides:
      - Array/List storage for all 52 cards before dealing
      - Custom Fisher-Yates shuffle algorithm for O(N) unbiased random permutation
      - Dealing cards
    """
    def __init__(self, seed: Optional[int] = None):
        self._rng = random.Random(seed)
        self.cards: List[Card] = []
        self.reset()

    def reset(self) -> None:
        """Populates the deck with standard 52 playing cards, all face-down."""
        self.cards = []
        for suit in Suit.ALL:
            for rank in range(1, 14):
                self.cards.append(Card(suit=suit, rank=rank, is_face_up=False))

    def shuffle(self) -> None:
        """
        In-place Fisher-Yates (Knuth) Shuffle algorithm.
        Time Complexity: O(N) where N = 52.
        Space Complexity: O(1).
        """
        n = len(self.cards)
        for i in range(n - 1, 0, -1):
            j = self._rng.randint(0, i)
            self.cards[i], self.cards[j] = self.cards[j], self.cards[i]

    def deal(self) -> Optional[Card]:
        """Deals one card from the deck array (O(1))."""
        if not self.cards:
            return None
        return self.cards.pop()

    def size(self) -> int:
        return len(self.cards)

    def is_empty(self) -> bool:
        return len(self.cards) == 0

    def __len__(self) -> int:
        return len(self.cards)
