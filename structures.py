"""
CSC200 - Data Structures & Algorithms
Custom Data Structures for Solitaire (Klondike)

Implements:
1. Stack (LIFO) - For Foundations, Undo/Redo, and Tableau top card mechanics
2. Queue (FIFO) - For Stockpile draw mechanics
3. DoublyLinkedList - For Tableau column manipulation (slicing and splicing sub-stacks)
4. CardHashMap - Custom Hash Map / Dictionary for O(1) card state and location lookup
"""

from typing import Generic, TypeVar, Optional, List, Any, Iterator

T = TypeVar('T')


# ============================================================================
# 1. STACK (LIFO)
# ============================================================================

class StackNode(Generic[T]):
    """Node for a linked Stack implementation."""
    def __init__(self, data: T, next_node: Optional['StackNode[T]'] = None):
        self.data: T = data
        self.next: Optional['StackNode[T]'] = next_node


class Stack(Generic[T]):
    """
    LIFO (Last-In-First-Out) Stack data structure.
    Used for:
      - Foundation piles (Ace -> King)
      - Undo and Redo histories
      - Tableau top-card access
    """
    def __init__(self, name: str = "Stack"):
        self.name = name
        self._top: Optional[StackNode[T]] = None
        self._size: int = 0

    def push(self, item: T) -> None:
        """Pushes an element onto the top of the stack (O(1))."""
        new_node = StackNode(item, self._top)
        self._top = new_node
        self._size += 1

    def pop(self) -> T:
        """Removes and returns the top element of the stack (O(1))."""
        if self.is_empty():
            raise IndexError(f"pop from empty {self.name}")
        popped = self._top.data
        self._top = self._top.next
        self._size -= 1
        return popped

    def peek(self) -> Optional[T]:
        """Returns the top element without removing it (O(1))."""
        if self.is_empty():
            return None
        return self._top.data

    def is_empty(self) -> bool:
        """Checks if the stack is empty (O(1))."""
        return self._size == 0

    def size(self) -> int:
        """Returns current number of elements (O(1))."""
        return self._size

    def clear(self) -> None:
        """Clears all elements from the stack."""
        self._top = None
        self._size = 0

    def to_list(self) -> List[T]:
        """Returns elements from bottom to top as a list (for iteration/rendering)."""
        elements = []
        curr = self._top
        while curr is not None:
            elements.append(curr.data)
            curr = curr.next
        elements.reverse()  # Bottom to top
        return elements

    def __len__(self) -> int:
        return self._size

    def __iter__(self) -> Iterator[T]:
        # Iterate from bottom to top
        return iter(self.to_list())

    def __repr__(self) -> str:
        return f"{self.name}(size={self._size}, top={self.peek()})"


# ============================================================================
# 2. QUEUE (FIFO)
# ============================================================================

class QueueNode(Generic[T]):
    """Node for a linked Queue implementation."""
    def __init__(self, data: T):
        self.data: T = data
        self.next: Optional['QueueNode[T]'] = None


class Queue(Generic[T]):
    """
    FIFO (First-In-First-Out) Queue data structure.
    Used for:
      - Stockpile (Draw pile): cards are drawn from the front in strict FIFO order,
        ensuring deterministic drawing cycle for 1-card or 3-card draw.
    """
    def __init__(self, name: str = "Queue"):
        self.name = name
        self._front: Optional[QueueNode[T]] = None
        self._rear: Optional[QueueNode[T]] = None
        self._size: int = 0

    def enqueue(self, item: T) -> None:
        """Adds an item to the rear of the queue (O(1))."""
        new_node = QueueNode(item)
        if self.is_empty():
            self._front = new_node
            self._rear = new_node
        else:
            self._rear.next = new_node
            self._rear = new_node
        self._size += 1

    def dequeue(self) -> T:
        """Removes and returns the item from the front of the queue (O(1))."""
        if self.is_empty():
            raise IndexError(f"dequeue from empty {self.name}")
        removed_data = self._front.data
        self._front = self._front.next
        if self._front is None:
            self._rear = None
        self._size -= 1
        return removed_data

    def peek(self) -> Optional[T]:
        """Returns the item at the front without removing it (O(1))."""
        if self.is_empty():
            return None
        return self._front.data

    def is_empty(self) -> bool:
        """Checks if the queue is empty (O(1))."""
        return self._size == 0

    def size(self) -> int:
        """Returns the number of elements in the queue (O(1))."""
        return self._size

    def clear(self) -> None:
        """Empties the queue."""
        self._front = None
        self._rear = None
        self._size = 0

    def to_list(self) -> List[T]:
        """Returns elements from front to rear as a list."""
        elements = []
        curr = self._front
        while curr is not None:
            elements.append(curr.data)
            curr = curr.next
        return elements

    def __len__(self) -> int:
        return self._size

    def __iter__(self) -> Iterator[T]:
        return iter(self.to_list())

    def __repr__(self) -> str:
        return f"{self.name}(size={self._size}, front={self.peek()})"


# ============================================================================
# 3. DOUBLY LINKED LIST (For Tableau Piles)
# ============================================================================

class DListNode(Generic[T]):
    """Node for Doubly Linked List."""
    def __init__(self, data: T):
        self.data: T = data
        self.prev: Optional['DListNode[T]'] = None
        self.next: Optional['DListNode[T]'] = None

    def __repr__(self) -> str:
        return f"Node({self.data})"


class DoublyLinkedList(Generic[T]):
    """
    Doubly Linked List representing Tableau columns.
    Enables:
      - Quick insertion at the end (O(1))
      - Quick removal of the top card (O(1))
      - Slicing a sub-stack from any node to the tail in O(1) pointer updates!
      - Splicing an entire sub-stack onto another column in O(1) pointer updates!
    """
    def __init__(self, name: str = "DoublyLinkedList"):
        self.name = name
        self.head: Optional[DListNode[T]] = None
        self.tail: Optional[DListNode[T]] = None
        self._size: int = 0

    def append(self, item: T) -> DListNode[T]:
        """Appends an item to the end of the list (tail) in O(1)."""
        new_node = DListNode(item)
        if self.head is None:
            self.head = new_node
            self.tail = new_node
        else:
            new_node.prev = self.tail
            self.tail.next = new_node
            self.tail = new_node
        self._size += 1
        return new_node

    def pop_tail(self) -> T:
        """Removes and returns the tail item in O(1)."""
        if self.tail is None:
            raise IndexError(f"pop from empty {self.name}")
        val = self.tail.data
        if self.head == self.tail:
            self.head = None
            self.tail = None
        else:
            self.tail = self.tail.prev
            self.tail.next = None
        self._size -= 1
        return val

    def peek_tail(self) -> Optional[T]:
        """Returns the tail item without removing it."""
        if self.tail is None:
            return None
        return self.tail.data

    def peek_tail_node(self) -> Optional[DListNode[T]]:
        """Returns the tail node."""
        return self.tail

    def is_empty(self) -> bool:
        return self._size == 0

    def size(self) -> int:
        return self._size

    def find_node(self, item: T) -> Optional[DListNode[T]]:
        """Finds the node containing the item (O(N))."""
        curr = self.head
        while curr is not None:
            if curr.data == item:
                return curr
            curr = curr.next
        return None

    def get_node_at_index(self, index: int) -> Optional[DListNode[T]]:
        """Returns node at specific 0-based index."""
        if index < 0 or index >= self._size:
            return None
        curr = self.head
        for _ in range(index):
            if curr is None:
                return None
            curr = curr.next
        return curr

    def detach_sublist_from_node(self, start_node: DListNode[T]) -> 'DoublyLinkedList[T]':
        """
        Detaches from start_node to tail and returns it as a new DoublyLinkedList.
        Runs in O(k) where k is the sublist length (only to update sizes),
        with O(1) pointer updates for list severance.
        """
        if start_node is None:
            raise ValueError("start_node cannot be None")

        # Count nodes being detached
        count = 0
        curr = start_node
        while curr is not None:
            count += 1
            curr = curr.next

        # Create new sublist
        sublist = DoublyLinkedList[T](name=f"{self.name}_sublist")
        sublist.head = start_node
        sublist.tail = self.tail
        sublist._size = count

        # Sever link in this list
        if start_node.prev is not None:
            start_node.prev.next = None
            self.tail = start_node.prev
            start_node.prev = None
        else:
            # start_node was head
            self.head = None
            self.tail = None

        self._size -= count
        return sublist

    def append_sublist(self, sublist: 'DoublyLinkedList[T]') -> None:
        """
        Appends an entire sublist to the tail in O(1) pointer operations.
        """
        if sublist is None or sublist.is_empty():
            return

        if self.head is None:
            self.head = sublist.head
            self.tail = sublist.tail
        else:
            self.tail.next = sublist.head
            sublist.head.prev = self.tail
            self.tail = sublist.tail

        self._size += sublist._size
        # Nullify sublist so it cannot be double-used
        sublist.head = None
        sublist.tail = None
        sublist._size = 0

    def to_list(self) -> List[T]:
        """Returns elements from head to tail as a standard list."""
        elements = []
        curr = self.head
        while curr is not None:
            elements.append(curr.data)
            curr = curr.next
        return elements

    def clear(self) -> None:
        self.head = None
        self.tail = None
        self._size = 0

    def __len__(self) -> int:
        return self._size

    def __iter__(self) -> Iterator[T]:
        return iter(self.to_list())

    def __repr__(self) -> str:
        return f"{self.name}(size={self._size}, items={self.to_list()})"


# ============================================================================
# 4. HASH MAP / DICTIONARY (Card Registry for O(1) Lookup)
# ============================================================================

class CardMetadata:
    """Stores the tracked state of a card in the game."""
    def __init__(self, card_id: str, pile_type: str, pile_index: int, depth: int, is_face_up: bool):
        self.card_id = card_id
        self.pile_type = pile_type    # 'stock', 'waste', 'tableau', 'foundation'
        self.pile_index = pile_index  # 0-6 for tableau, 0-3 for foundation, 0 for stock/waste
        self.depth = depth            # Position within pile
        self.is_face_up = is_face_up

    def __repr__(self) -> str:
        return (f"CardMetadata(id={self.card_id}, pile={self.pile_type}[{self.pile_index}], "
                f"depth={self.depth}, face_up={self.is_face_up})")


class CardHashMap:
    """
    Custom HashMap tracking card positions, states (face-up/down), and pile locations.
    Fulfills requirement:
      'HashMap/Dictionary: Track card positions, states (face-up or face-down),
       and pile locations. Implementation: Use dictionaries to map tableau and
       foundation piles to cards for quick access.'
    """
    def __init__(self, capacity: int = 64):
        self._capacity = capacity
        self._buckets: List[List[tuple]] = [[] for _ in range(self._capacity)]
        self._size = 0

    def _hash(self, key: str) -> int:
        # Custom polynomial rolling hash
        h = 0
        for char in str(key):
            h = (h * 31 + ord(char)) % self._capacity
        return h

    def put(self, key: str, value: CardMetadata) -> None:
        """Associates card_id with CardMetadata in O(1) average time."""
        bucket_idx = self._hash(key)
        bucket = self._buckets[bucket_idx]
        for i, (k, v) in enumerate(bucket):
            if k == key:
                bucket[i] = (key, value)
                return
        bucket.append((key, value))
        self._size += 1

    def get(self, key: str) -> Optional[CardMetadata]:
        """Retrieves CardMetadata for a card_id in O(1) average time."""
        bucket_idx = self._hash(key)
        bucket = self._buckets[bucket_idx]
        for k, v in bucket:
            if k == key:
                return v
        return None

    def remove(self, key: str) -> bool:
        """Removes a key from the map."""
        bucket_idx = self._hash(key)
        bucket = self._buckets[bucket_idx]
        for i, (k, v) in enumerate(bucket):
            if k == key:
                del bucket[i]
                self._size -= 1
                return True
        return False

    def contains(self, key: str) -> bool:
        return self.get(key) is not None

    def size(self) -> int:
        return self._size

    def all_items(self) -> List[tuple]:
        items = []
        for bucket in self._buckets:
            items.extend(bucket)
        return items

    def clear(self) -> None:
        self._buckets = [[] for _ in range(self._capacity)]
        self._size = 0
