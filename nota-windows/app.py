import json
import sys
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


APP_NAME = "Nota"
CONFIG_PATH = Path.home() / ".nota-preferences.json"

THEMES = {
    "light": {
        "window": "#f5f1e8",
        "surface": "#fffdf8",
        "panel": "#ebe5d9",
        "text": "#24231f",
        "muted": "#746f64",
        "accent": "#d4663f",
        "accent_dark": "#b74f2e",
        "border": "#d9d1c2",
        "selection": "#f3c8b7",
    },
    "dark": {
        "window": "#1e211f",
        "surface": "#282c29",
        "panel": "#343a35",
        "text": "#f2eee6",
        "muted": "#aaa99f",
        "accent": "#e98459",
        "accent_dark": "#f39b77",
        "border": "#454b46",
        "selection": "#704b3e",
    },
}


class NoteDocument:
    def __init__(self, path=None, content=""):
        self.path = Path(path) if path else None
        self.content = content
        self.dirty = False

    @property
    def title(self):
        if self.path:
            return self.path.name
        return "Sin titulo"


def compatible_runtime():
    if sys.version_info < (3, 9):
        print("Nota necesita Python 3.9 o posterior.", file=sys.stderr)
        return False
    if tk.TclVersion < 8.5:
        print("Nota necesita Tkinter 8.5 o posterior.", file=sys.stderr)
        return False
    return True


class NotaApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1100x720")
        self.minsize(760, 500)
        self.documents = []
        self.active_index = None
        self.search_window = None
        self.preferences = self.load_preferences()
        self.theme_name = self.preferences.get("theme", "light")
        if self.theme_name not in THEMES:
            self.theme_name = "light"
        self.theme_var = tk.StringVar(value=self.theme_name)
        self.colors = THEMES[self.theme_name]
        self.configure(bg=self.colors["window"])
        self.setup_style()
        self.build_menu()
        self.build_ui()
        self.bind_shortcuts()
        self.new_document()

    def load_preferences(self):
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}

    def save_preferences(self):
        try:
            CONFIG_PATH.write_text(json.dumps({"theme": self.theme_name}), encoding="utf-8")
        except OSError:
            pass

    def setup_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("App.TFrame", background=self.colors["window"])
        style.configure("Panel.TFrame", background=self.colors["panel"])
        style.configure("Title.TLabel", background=self.colors["window"], foreground=self.colors["text"], font=("TkDefaultFont", 18, "bold"))
        style.configure("Muted.TLabel", background=self.colors["window"], foreground=self.colors["muted"], font=("TkDefaultFont", 9))
        style.configure("Toolbar.TButton", background=self.colors["panel"], foreground=self.colors["text"], borderwidth=0, padding=(12, 7), font=("TkDefaultFont", 9, "bold"))
        style.map("Toolbar.TButton", background=[("active", self.colors["border"])])
        style.configure("Accent.TButton", background=self.colors["accent"], foreground="#ffffff", borderwidth=0, padding=(14, 7), font=("TkDefaultFont", 9, "bold"))
        style.map("Accent.TButton", background=[("active", self.colors["accent_dark"])])
        style.configure("Status.TLabel", background=self.colors["panel"], foreground=self.colors["muted"], padding=(12, 6), font=("TkDefaultFont", 9))
        style.configure("Tab.TNotebook", background=self.colors["window"], borderwidth=0)
        style.configure("Tab.TNotebook.Tab", background=self.colors["panel"], foreground=self.colors["muted"], padding=(14, 8), borderwidth=0)
        style.map("Tab.TNotebook.Tab", background=[("selected", self.colors["surface"])], foreground=[("selected", self.colors["text"])])

    def build_menu(self):
        menu = tk.Menu(self, tearoff=False, bg=self.colors["surface"], fg=self.colors["text"], activebackground=self.colors["accent"], activeforeground="#ffffff")
        file_menu = tk.Menu(menu, tearoff=False)
        file_menu.add_command(label="Nuevo", accelerator="Ctrl+N", command=self.new_document)
        file_menu.add_command(label="Abrir...", accelerator="Ctrl+O", command=self.open_document)
        file_menu.add_command(label="Guardar", accelerator="Ctrl+S", command=self.save_document)
        file_menu.add_command(label="Guardar como...", accelerator="Ctrl+Shift+S", command=lambda: self.save_document(save_as=True))
        file_menu.add_separator()
        file_menu.add_command(label="Cerrar pestaña", accelerator="Ctrl+W", command=self.close_document)
        file_menu.add_command(label="Salir", command=self.destroy)
        menu.add_cascade(label="Archivo", menu=file_menu)
        edit_menu = tk.Menu(menu, tearoff=False)
        edit_menu.add_command(label="Buscar", accelerator="Ctrl+F", command=self.show_search)
        edit_menu.add_separator()
        edit_menu.add_command(label="Deshacer", accelerator="Ctrl+Z", command=lambda: self.editor.event_generate("<<Undo>>"))
        edit_menu.add_command(label="Rehacer", accelerator="Ctrl+Y", command=lambda: self.editor.event_generate("<<Redo>>"))
        menu.add_cascade(label="Editar", menu=edit_menu)
        view_menu = tk.Menu(menu, tearoff=False)
        view_menu.add_radiobutton(label="Claro", variable=self.theme_var, value="light", command=lambda: self.set_theme("light"))
        view_menu.add_radiobutton(label="Oscuro", variable=self.theme_var, value="dark", command=lambda: self.set_theme("dark"))
        view_menu.add_separator()
        view_menu.add_command(label="Alternar tema", accelerator="Ctrl+T", command=self.toggle_theme)
        menu.add_cascade(label="Vista", menu=view_menu)
        self.config(menu=menu)

    def build_ui(self):
        self.main = ttk.Frame(self, style="App.TFrame")
        self.main.pack(fill="both", expand=True)
        header = ttk.Frame(self.main, style="App.TFrame", padding=(24, 18, 24, 12))
        header.pack(fill="x")
        brand = ttk.Frame(header, style="App.TFrame")
        brand.pack(side="left")
        ttk.Label(brand, text="nota", style="Title.TLabel").pack(anchor="w")
        ttk.Label(brand, text="simple, local y tuyo", style="Muted.TLabel").pack(anchor="w", pady=(2, 0))
        actions = ttk.Frame(header, style="App.TFrame")
        actions.pack(side="right", pady=4)
        ttk.Button(actions, text="Buscar", style="Toolbar.TButton", command=self.show_search).pack(side="left", padx=(0, 8))
        self.theme_button = ttk.Button(actions, text=self.theme_label(), style="Toolbar.TButton", command=self.toggle_theme)
        self.theme_button.pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Guardar", style="Toolbar.TButton", command=self.save_document).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Nueva nota", style="Accent.TButton", command=self.new_document).pack(side="left")

        self.tabs = ttk.Notebook(self.main, style="Tab.TNotebook")
        self.tabs.pack(fill="both", expand=True, padx=24)
        self.tabs.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        footer = ttk.Frame(self.main, style="Panel.TFrame")
        footer.pack(fill="x", padx=24, pady=(10, 0))
        self.status = ttk.Label(footer, text="Listo", style="Status.TLabel")
        self.status.pack(side="left")
        self.counter = ttk.Label(footer, text="0 palabras  |  0 caracteres", style="Status.TLabel")
        self.counter.pack(side="right")
        self.main.pack_configure(pady=(0, 18))

    def bind_shortcuts(self):
        self.bind("<Control-n>", lambda event: self.new_document())
        self.bind("<Control-o>", lambda event: self.open_document())
        self.bind("<Control-s>", lambda event: self.save_document())
        self.bind("<Control-Shift-S>", lambda event: self.save_document(save_as=True))
        self.bind("<Control-w>", lambda event: self.close_document())
        self.bind("<Control-f>", lambda event: self.show_search())
        self.bind("<Control-t>", lambda event: self.toggle_theme())
        self.protocol("WM_DELETE_WINDOW", self.on_exit)

    def new_document(self):
        document = NoteDocument()
        frame = ttk.Frame(self.tabs, style="App.TFrame")
        editor = tk.Text(frame, wrap="word", undo=True, relief="flat", borderwidth=0, padx=34, pady=28, font=("TkDefaultFont", 14), insertwidth=2)
        editor.pack(fill="both", expand=True)
        editor.bind("<<Modified>>", self.on_editor_modified)
        editor.bind("<KeyRelease>", lambda event: self.update_status())
        document.editor = editor
        document.frame = frame
        self.documents.append(document)
        self.tabs.add(frame, text=document.title)
        self.tabs.select(frame)
        self.apply_editor_colors(editor)
        editor.focus_set()
        self.update_status()

    def open_document(self):
        path = filedialog.askopenfilename(title="Abrir nota", filetypes=[("Texto", "*.txt"), ("Markdown", "*.md"), ("Todos los archivos", "*")])
        if not path:
            return
        try:
            content = Path(path).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            messagebox.showerror("No se pudo abrir", str(error))
            return
        document = NoteDocument(path, content)
        frame = ttk.Frame(self.tabs, style="App.TFrame")
        editor = tk.Text(frame, wrap="word", undo=True, relief="flat", borderwidth=0, padx=34, pady=28, font=("TkDefaultFont", 14), insertwidth=2)
        editor.insert("1.0", content)
        editor.edit_reset()
        editor.pack(fill="both", expand=True)
        editor.bind("<<Modified>>", self.on_editor_modified)
        editor.bind("<KeyRelease>", lambda event: self.update_status())
        document.editor, document.frame = editor, frame
        self.documents.append(document)
        self.tabs.add(frame, text=document.title)
        self.tabs.select(frame)
        self.apply_editor_colors(editor)
        self.update_status()

    def active_document(self):
        if self.active_index is None or not self.documents:
            return None
        return self.documents[self.active_index]

    @property
    def editor(self):
        document = self.active_document()
        return document.editor if document else None

    def on_tab_changed(self, _event=None):
        current = self.tabs.select()
        self.active_index = next((i for i, doc in enumerate(self.documents) if str(doc.frame) == current), None)
        self.update_status()

    def on_editor_modified(self, _event=None):
        document = self.active_document()
        if document and document.editor.edit_modified():
            document.dirty = True
            self.update_tab_title(document)
            document.editor.edit_modified(False)
            self.update_status()

    def update_tab_title(self, document):
        title = ("* " if document.dirty else "") + document.title
        self.tabs.tab(document.frame, text=title)

    def save_document(self, save_as=False):
        document = self.active_document()
        if not document:
            return
        path = document.path
        if save_as or not path:
            path = filedialog.asksaveasfilename(title="Guardar nota", defaultextension=".txt", filetypes=[("Texto", "*.txt"), ("Markdown", "*.md")])
            if not path:
                return
            document.path = Path(path)
        try:
            document.path.write_text(document.editor.get("1.0", "end-1c"), encoding="utf-8")
        except OSError as error:
            messagebox.showerror("No se pudo guardar", str(error))
            return
        document.dirty = False
        self.update_tab_title(document)
        self.status.configure(text=f"Guardado: {document.path.name}")

    def close_document(self):
        document = self.active_document()
        if not document:
            return
        if document.dirty:
            answer = messagebox.askyesnocancel("Cambios sin guardar", f"Guardar cambios en {document.title}?")
            if answer is None:
                return
            if answer:
                self.save_document()
        index = self.active_index
        self.tabs.forget(document.frame)
        self.documents.pop(index)
        if not self.documents:
            self.new_document()
        else:
            self.active_index = min(index, len(self.documents) - 1)
            self.tabs.select(self.documents[self.active_index].frame)

    def show_search(self):
        if self.search_window and self.search_window.winfo_exists():
            self.search_window.focus_force()
            return
        self.search_window = tk.Toplevel(self)
        self.search_window.title("Buscar")
        self.search_window.resizable(False, False)
        self.search_window.configure(bg=self.colors["surface"])
        self.search_window.transient(self)
        ttk.Label(self.search_window, text="Buscar en la nota", style="Muted.TLabel").pack(anchor="w", padx=18, pady=(16, 6))
        entry = tk.Entry(self.search_window, relief="flat", font=("TkDefaultFont", 12), bg=self.colors["window"], fg=self.colors["text"], insertbackground=self.colors["text"])
        entry.pack(fill="x", padx=18, pady=(0, 12), ipady=7)
        entry.bind("<KeyRelease>", lambda _event: self.highlight_search(entry.get()))
        entry.focus_set()

    def highlight_search(self, query):
        editor = self.editor
        if not editor:
            return
        editor.tag_remove("search", "1.0", "end")
        if not query:
            return
        start = "1.0"
        while True:
            start = editor.search(query, start, stopindex="end", nocase=True)
            if not start:
                break
            end = f"{start}+{len(query)}c"
            editor.tag_add("search", start, end)
            start = end
        editor.tag_configure("search", background=self.colors["selection"], foreground=self.colors["text"])

    def toggle_theme(self):
        next_theme = "dark" if self.theme_name == "light" else "light"
        self.set_theme(next_theme)

    def set_theme(self, theme_name):
        if theme_name not in THEMES:
            return
        self.theme_name = theme_name
        self.theme_var.set(theme_name)
        self.colors = THEMES[self.theme_name]
        self.save_preferences()
        self.rebuild_theme()

    def theme_label(self):
        return "Tema: Oscuro" if self.theme_name == "dark" else "Tema: Claro"

    def rebuild_theme(self):
        self.configure(bg=self.colors["window"])
        self.setup_style()
        for document in self.documents:
            self.apply_editor_colors(document.editor)
        self.theme_button.configure(text=self.theme_label())
        if self.search_window and self.search_window.winfo_exists():
            self.search_window.destroy()
        self.build_menu()

    def apply_editor_colors(self, editor):
        editor.configure(bg=self.colors["surface"], fg=self.colors["text"], insertbackground=self.colors["accent"], selectbackground=self.colors["selection"], highlightthickness=0)

    def update_status(self):
        document = self.active_document()
        if not document:
            return
        content = document.editor.get("1.0", "end-1c")
        words = len(content.split())
        self.counter.configure(text=f"{words} palabras  |  {len(content)} caracteres")
        if document.dirty:
            self.status.configure(text="Cambios sin guardar")
        elif document.path:
            self.status.configure(text=document.path.name)
        else:
            self.status.configure(text="Nota local")

    def on_exit(self):
        dirty_documents = [document for document in self.documents if document.dirty]
        if dirty_documents and not messagebox.askyesno("Salir de Nota", "Hay cambios sin guardar. Salir de todas formas?"):
            return
        self.save_preferences()
        self.destroy()


if __name__ == "__main__":
    if compatible_runtime():
        NotaApp().mainloop()
