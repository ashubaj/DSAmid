"""
CSC200 - Data Structures & Algorithms
Interactive Text-Based (CLI) Solitaire Interface (Phase 4)

Provides:
- ASCII art rendering of Stock, Waste, Foundations, and Tableau
- Interactive text commands (draw, move, undo, redo, hint, auto, quit)
- Colorized terminal output
"""

import sys
from engine import SolitaireEngine
from card import Rank, Suit


class SolitaireCLI:
    def __init__(self):
        self.engine = SolitaireEngine(draw_count=1)

    def print_board(self):
        print("\n" + "=" * 65)
        print("          CSC200 KLONDIKE SOLITAIRE - TEXT INTERFACE")
        print("=" * 65)
        print(f"Time: {self.engine.get_formatted_time()} | Score: {self.engine.score} | Moves: {self.engine.moves_count}")
        print("-" * 65)

        # Upper row: Stock, Waste, Foundations
        stock_display = f"[{self.engine.stock.size()} cards]" if not self.engine.stock.is_empty() else "[ ↺ Empty ]"
        waste_card = self.engine.waste.peek()
        waste_display = str(waste_card) if waste_card else "[  Empty  ]"

        print(f"Stock: {stock_display:<12} Waste: {waste_display:<10}  |  Foundations:")
        f_strs = []
        for i, f in enumerate(self.engine.foundations):
            top = f.peek()
            f_strs.append(f"F{i+1}: {str(top) if top else '[   ]'}")
        print("  " + "  ".join(f_strs))

        print("\nTableau Columns (1 to 7):")
        # Find maximum height
        max_height = max(col.size() for col in self.engine.tableau)
        max_height = max(max_height, 1)

        headers = [f"  T{i+1}   " for i in range(7)]
        print(" ".join(headers))
        print(" ".join(["--------" for _ in range(7)]))

        for row in range(max_height):
            row_cards = []
            for col in self.engine.tableau:
                cards = col.to_list()
                if row < len(cards):
                    row_cards.append(f" {str(cards[row]):<7}")
                else:
                    row_cards.append("        ")
            print(" ".join(row_cards))

        print("=" * 65)

    def print_help(self):
        print("""
Available Commands:
  d, draw              - Draw card(s) from stockpile (or recycle if empty)
  wt <t_num>           - Move Waste card to Tableau column (e.g. 'wt 3')
  wf [f_num]           - Move Waste card to Foundation (e.g. 'wf' or 'wf 1')
  tt <src> <dst> [id]  - Move card/stack from Tableau <src> to Tableau <dst> (e.g. 'tt 1 3')
  tf <src> [f_num]     - Move top card of Tableau <src> to Foundation (e.g. 'tf 2')
  ft <f_num> <dst>     - Move card from Foundation <f_num> to Tableau <dst>
  auto <card_id>       - Automatically play card (e.g. 'auto H_1')
  finish               - Auto-finish game if all tableau cards revealed
  h, hint              - Show suggested strategic move
  u, undo              - Undo last move
  r, redo              - Redo last undone move
  new                  - Start a new game
  q, quit              - Exit game
""")

    def run(self):
        self.print_board()
        self.print_help()

        while True:
            if self.engine.check_win_condition():
                print("\n" + "*" * 60)
                print("🎉 CONGRATULATIONS! YOU HAVE WON KLONDIKE SOLITAIRE! 🎉")
                print(f"Final Score: {self.engine.score} | Time: {self.engine.get_formatted_time()} | Moves: {self.engine.moves_count}")
                print("*" * 60)
                break

            try:
                raw = input("\nEnter command (or 'help'): ").strip().lower()
                if not raw:
                    continue

                parts = raw.split()
                cmd = parts[0]

                if cmd in ['q', 'quit', 'exit']:
                    print("Exiting Solitaire. Thanks for playing!")
                    break

                elif cmd in ['h', 'hint']:
                    hint = self.engine.get_best_hint()
                    if hint:
                        print(f"💡 HINT: {hint.description}")
                    else:
                        print("No legal moves found! Try drawing from stockpile.")

                elif cmd in ['d', 'draw']:
                    if self.engine.draw_from_stock():
                        print("Drew from stockpile.")
                    else:
                        print("Cannot draw.")
                    self.print_board()

                elif cmd in ['u', 'undo']:
                    if self.engine.undo():
                        print("Move undone.")
                    else:
                        print("Nothing to undo.")
                    self.print_board()

                elif cmd in ['r', 'redo']:
                    if self.engine.redo():
                        print("Move redone.")
                    else:
                        print("Nothing to redo.")
                    self.print_board()

                elif cmd == 'wt' and len(parts) >= 2:
                    t_idx = int(parts[1]) - 1
                    if self.engine.move_waste_to_tableau(t_idx):
                        print(f"Moved Waste card to Tableau {t_idx+1}.")
                    else:
                        print("Illegal move!")
                    self.print_board()

                elif cmd == 'wf':
                    f_idx = (int(parts[1]) - 1) if len(parts) >= 2 else None
                    if self.engine.move_waste_to_foundation(f_idx):
                        print("Moved Waste card to Foundation.")
                    else:
                        print("Illegal move!")
                    self.print_board()

                elif cmd == 'tt' and len(parts) >= 3:
                    src = int(parts[1]) - 1
                    dst = int(parts[2]) - 1
                    card_id = parts[3].upper() if len(parts) >= 4 else None
                    if self.engine.move_tableau_to_tableau(src, dst, start_card_id=card_id):
                        print(f"Moved from Tableau {src+1} to Tableau {dst+1}.")
                    else:
                        print("Illegal move!")
                    self.print_board()

                elif cmd == 'tf' and len(parts) >= 2:
                    src = int(parts[1]) - 1
                    f_idx = (int(parts[2]) - 1) if len(parts) >= 3 else None
                    if self.engine.move_tableau_to_foundation(src, f_idx):
                        print(f"Moved from Tableau {src+1} to Foundation.")
                    else:
                        print("Illegal move!")
                    self.print_board()

                elif cmd == 'finish':
                    if self.engine.auto_finish_if_possible():
                        print("Auto-finish completed successfully!")
                    else:
                        print("Auto-finish is only available when all cards are revealed!")
                    self.print_board()

                elif cmd == 'new':
                    self.engine.start_new_game()
                    print("New game started.")
                    self.print_board()

                elif cmd == 'help':
                    self.print_help()

                else:
                    print(f"Unknown command: '{raw}'. Type 'help' for options.")

            except (ValueError, IndexError) as e:
                print(f"Error parsing command: {e}")
            except KeyboardInterrupt:
                print("\nExiting.")
                break


if __name__ == '__main__':
    cli = SolitaireCLI()
    cli.run()
