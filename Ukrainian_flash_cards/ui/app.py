import tkinter as tk

from ui.home import HomePage
from ui.flashcards import FlashcardUI
from ui.dashboard import DashboardUI
from ui.user_words_ui import UserWordsPage
from ui.verbs_ui import VerbsPage
from ui.adverbs_ui import AdverbsPage
from ui.prefixes_ui import PrefixesPage


class AppShell(tk.Frame):
    def __init__(self, master):
        super().__init__(master, bg="#0d0d0f")
        self.master = master
        self.current = None
        master.app_controller = self
        self.show_home()

    def _set_page(self, widget):
        if self.current is not None:
            self.current.destroy()
        self.current = widget
        self.current.pack(fill="both", expand=True)

    def show_home(self):
        self._set_page(HomePage(self.master, controller=self))

    def show_study(self, deck_name=None, focus_word=None):
        if self.current is not None:
            self.current.destroy()
        self.current = FlashcardUI(self.master, deck_name=deck_name, focus_word=focus_word)

    def show_dashboard(self):
        DashboardUI(self.master)

    def show_words(self):
        from ui.user_words_ui import UserWordsPage
        self._set_page(UserWordsPage(self.master, go_home=self.show_home))

    def show_verbs(self):
        self._set_page(VerbsPage(self.master, go_home=self.show_home))

    def show_adverbs(self):
        self._set_page(AdverbsPage(self.master, go_home=self.show_home))

    def show_prefixes(self):
        self._set_page(PrefixesPage(self.master, go_home=self.show_home))