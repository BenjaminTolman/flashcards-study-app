
import json
import random
import os
import tkinter as tk
from tkinter import messagebox

# Deck prep

def find_decks(directory="decks"):
    
    # Searches the given directory for JSON files and returns
    # a sorted list of full file paths.
    
    # If the directory does not exist, return an empty list
    # instead of throwing an exception and crashing the app.
    if not os.path.isdir(directory):
        return []

    # Build a list of full paths to .json files.
    # os.listdir() returns filenames only.
    # os.path.join() builds a correct path.
    return sorted(
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if f.lower().endswith(".json")
    )


def load_deck(path):
    #Loads a single deck from a JSON file and returns:
    #- deck title
    #- list of card dictionaries

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

    # Catch *any* exception and re-raise it with a clearer message
    except Exception as e:
        raise RuntimeError(f"Failed to load deck '{path}': {e}")

    # Get deck title, falling back to a default if missing
    title = data.get("title", "Untitled Deck")

    # Get card list, defaulting to empty list if missing
    cards = data.get("cards", [])

    # A deck with no cards is considered invalid
    if not cards:
        raise RuntimeError("Deck contains no cards.")

    # Shuffle cards once at load time to randomize quiz order
    random.shuffle(cards)

    return title, cards


# Game state

class Flashcards:
    # Handles the game data.

    def __init__(self, cards):
        # Create a shallow copy so the original list is not modified
        self.cards = cards[:]

        # Index of the current card
        self.index = 0

        # Number of correct answers
        self.score = 0

        # Total number of cards in the session
        self.total = len(cards)

        # Stores cards answered incorrectly for review later
        self.missed_cards = []

    def current(self):
        # Returns the current card dictionary.
        return self.cards[self.index]

    def has_next(self):
        return self.index < len(self.cards)

    def check(self, selected):
        
        # If the answer is correct, update score.
        if selected == self.current()["answer"]:
            self.score += 1
            return True

        # Track incorrect cards.
        if self.current() not in self.missed_cards:
            self.missed_cards.append(self.current())

        return False

    def next(self):
        # next card.
        self.index += 1

    def reset_for_review(self):
        # Resets the game to replay only the missed cards.
        
        self.cards = self.missed_cards[:]
        random.shuffle(self.cards)
        self.missed_cards.clear()
        self.index = 0
        self.score = 0
        self.total = len(self.cards)


# Tkinter UI

class FlashcardApp:
    # Handles all UI behavior and user interaction.
    

    def __init__(self, root):
        # Store root Tk window
        self.root = root
        self.root.title("Flashcards")

        # Set initial window size and minimum size
        self.root.geometry("960x540")
        self.root.minsize(720, 405)

        # Game state and UI state
        self.game = None
        self.decks = []
        self.last_correct = False
        self.selected_answer = ""

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Main container
        self.frame = tk.Frame(root, padx=20, pady=20)
        self.frame.grid(sticky="nsew")
        self.frame.columnconfigure(0, weight=1)

        # Title
        self.title_label = tk.Label(self.frame, font=("Arial", 18))
        self.title_label.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        # Question text
        self.question_label = tk.Label(
            self.frame, font=("Arial", 14), justify="center"
        )
        self.question_label.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        # Feedback text (Correct / Incorrect)
        self.feedback_label = tk.Label(
            self.frame, font=("Arial", 14, "bold")
        )
        self.feedback_label.grid(row=2, column=0, sticky="ew")

        # Selected and correct answer
        self.answer_info_label = tk.Label(
            self.frame, font=("Arial", 12), justify="center"
        )
        self.answer_info_label.grid(row=3, column=0, sticky="ew")

        # Explanation text
        self.explanation_label = tk.Label(
            self.frame, font=("Arial", 13), justify="center"
        )
        self.explanation_label.grid(row=4, column=0, sticky="ew", pady=(0, 10))

        # All buttons
        self.buttons_frame = tk.Frame(self.frame)
        self.buttons_frame.grid(row=5, column=0, sticky="ew", pady=10)

        # Score display
        self.score_label = tk.Label(self.frame)
        self.score_label.grid(row=6, column=0, sticky="ew")

        # Resize event to dynamically adjust text wrapping
        self.frame.bind("<Configure>", self.on_resize)

        # Start app at deck selection screen
        self.show_deck_selector()


    def on_resize(self, event):
        # Adjust text wrapping dynamically when the window is resized.
        
        wrap = max(400, event.width - 40)
        self.question_label.config(wraplength=wrap)
        self.answer_info_label.config(wraplength=wrap)
        self.explanation_label.config(wraplength=wrap)


    def hide_explanation_area(self):
        #Hide feedback and explanation labels.
        self.feedback_label.grid_remove()
        self.answer_info_label.grid_remove()
        self.explanation_label.grid_remove()

    def show_explanation_area(self):
        #Show feedback and explanation labels.
        self.feedback_label.grid()
        self.answer_info_label.grid()
        self.explanation_label.grid()


    def show_deck_selector(self):
       # Displays the deck selection screen.
        
        self.clear_buttons()
        self.hide_explanation_area()
        self.question_label.config(text="")
        self.score_label.config(text="")

        self.decks = find_decks()
        if not self.decks:
            messagebox.showerror(
                "Error", "No JSON decks found in the 'decks' folder."
            )
            self.root.quit()
            return

        self.title_label.config(text="Select a Deck")

        list_frame = tk.Frame(self.buttons_frame)
        list_frame.pack(pady=10)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")

        self.deck_listbox = tk.Listbox(
            list_frame, width=50, height=10, yscrollcommand=scrollbar.set
        )
        self.deck_listbox.pack(side="left", fill="y")
        scrollbar.config(command=self.deck_listbox.yview)

        # Display filenames without .json extension
        for deck_path in self.decks:
            name = os.path.splitext(os.path.basename(deck_path))[0]
            self.deck_listbox.insert(tk.END, name)

        self.deck_listbox.selection_set(0)
        self.deck_listbox.bind("<Double-Button-1>", lambda e: self.start_game())

        tk.Button(
            self.buttons_frame,
            text="Start",
            width=20,
            command=self.start_game
        ).pack(pady=10)


    def start_game(self):
        # Loads the selected deck and starts the quiz.
        selection = self.deck_listbox.curselection()
        if not selection:
            messagebox.showwarning("Select Deck", "Please select a deck.")
            return

        deck_path = self.decks[selection[0]]
        title, cards = load_deck(deck_path)

        self.game = Flashcards(cards)
        self.title_label.config(text=title)
        self.next_question()


    def next_question(self):
        # Displays the next question or results if finished.
        self.clear_buttons()
        self.hide_explanation_area()

        if not self.game.has_next():
            self.show_results()
            return

        card = self.game.current()
        self.question_label.config(text=card["question"])
        self.score_label.config(
            text=f"Score: {self.game.score}/{self.game.total}"
        )

        # Copy list to avoid changing original order
        choices = card["choices"][:]
        random.shuffle(choices)

        for choice in choices:
            tk.Button(
                self.buttons_frame,
                text=choice,
                command=lambda c=choice: self.submit_answer(c)
            ).pack(fill="x", pady=3)


    def submit_answer(self, selected):
        # Handles answer selection.
        self.selected_answer = selected
        self.last_correct = self.game.check(selected)
        self.show_explanation()


    def show_explanation(self):
        # Displays feedback and explanation.
        self.clear_buttons()
        self.show_explanation_area()

        card = self.game.current()

        if self.last_correct:
            self.feedback_label.config(text="Correct!", fg="green")
            self.answer_info_label.config(
                text=f"Your answer: {self.selected_answer}"
            )
        else:
            self.feedback_label.config(text="Incorrect", fg="red")
            self.answer_info_label.config(
                text=f"Your answer: {self.selected_answer}\n"
                     f"Correct answer: {card['answer']}"
            )

        self.explanation_label.config(
            text=card.get("explanation", "No explanation provided.")
        )

        tk.Button(
            self.buttons_frame,
            text="Next",
            width=20,
            command=self.advance
        ).pack(pady=15)


    def advance(self):
        # next card.
        self.game.next()
        self.next_question()


    def show_results(self):
        # Final score and options.
        self.clear_buttons()
        self.hide_explanation_area()

        self.question_label.config(
            text=f"Quiz Complete!\n\nScore: {self.game.score}/{self.game.total}"
        )

        if self.game.missed_cards:
            tk.Button(
                self.buttons_frame,
                text=f"Redo Wrong Answers ({len(self.game.missed_cards)})",
                width=25,
                command=self.redo_wrong
            ).pack(pady=5)

        tk.Button(
            self.buttons_frame,
            text="Restart Deck",
            width=25,
            command=self.show_deck_selector
        ).pack(pady=5)

        tk.Button(
            self.buttons_frame,
            text="Quit",
            width=25,
            command=self.root.quit
        ).pack(pady=5)


    def redo_wrong(self):
        # Restart quiz using only missed cards.
        self.game.reset_for_review()
        self.next_question()


    def clear_buttons(self):
        # Remove all buttons from the button frame.
        for widget in self.buttons_frame.winfo_children():
            widget.destroy()


# Entry point

if __name__ == "__main__":
    # Create the Tk window
    root = tk.Tk()

    # Initialize
    FlashcardApp(root)

    # Start the Tkinter loop
    root.mainloop()
