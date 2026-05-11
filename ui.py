import threading
import tkinter as tk
import queue
import time

_ui_queue = queue.Queue()


def _ui_thread_func():
    root = tk.Tk()
    root.title("Jerry")
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.configure(bg="#0d0d0d")

    # ── Window size & position (bottom-right) ──────────────────────────────────
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()
    WIN_W, WIN_H = 360, 220
    root.geometry(f"{WIN_W}x{WIN_H}+{screen_w - WIN_W - 20}+{screen_h - WIN_H - 60}")

    # ── Outer glow border ──────────────────────────────────────────────────────
    outer = tk.Frame(root, bg="#1a6aff", bd=1)
    outer.pack(expand=True, fill="both", padx=1, pady=1)

    inner = tk.Frame(outer, bg="#0d0d0d")
    inner.pack(expand=True, fill="both", padx=1, pady=1)

    # ── Title bar ──────────────────────────────────────────────────────────────
    title_bar = tk.Frame(inner, bg="#111111", height=28)
    title_bar.pack(fill="x")
    title_bar.pack_propagate(False)

    dot_canvas = tk.Canvas(title_bar, width=50, height=28, bg="#111111", highlightthickness=0)
    dot_canvas.pack(side="left", padx=8)
    dot_canvas.create_oval(4, 9, 16, 21, fill="#ff5f56", outline="")
    dot_canvas.create_oval(20, 9, 32, 21, fill="#ffbd2e", outline="")
    dot_canvas.create_oval(36, 9, 48, 21, fill="#27c93f", outline="")

    tk.Label(title_bar, text="  J E R R Y", font=("Segoe UI", 9, "bold"),
             fg="#1a6aff", bg="#111111").pack(side="left")

    # ── Pulsing indicator dot ──────────────────────────────────────────────────
    _pulse_state = {"on": False, "color": "#333333"}
    indicator = tk.Canvas(title_bar, width=12, height=12,
                          bg="#111111", highlightthickness=0)
    indicator.pack(side="right", padx=10, pady=8)
    dot_id = indicator.create_oval(1, 1, 11, 11, fill="#333333", outline="")

    def set_listening(active):
        color = "#1a6aff" if active else "#333333"
        indicator.itemconfig(dot_id, fill=color)

    def on_drag_start(e):
        root._drag_x = e.x
        root._drag_y = e.y

    def on_drag_motion(e):
        root.geometry(f"+{root.winfo_x() + e.x - root._drag_x}+{root.winfo_y() + e.y - root._drag_y}")

    title_bar.bind("<ButtonPress-1>", on_drag_start)
    title_bar.bind("<B1-Motion>", on_drag_motion)

    def hide_window(e=None):
        root.withdraw()
        from mouth import stop_speaking
        stop_speaking()

    close_lbl = tk.Label(title_bar, text="  x  ", font=("Segoe UI", 9),
                         fg="#666666", bg="#111111", cursor="hand2")
    close_lbl.pack(side="right")
    close_lbl.bind("<Button-1>", hide_window)
    close_lbl.bind("<Enter>", lambda e: close_lbl.config(fg="#ff5f56"))
    close_lbl.bind("<Leave>", lambda e: close_lbl.config(fg="#666666"))

    # ── You said label ─────────────────────────────────────────────────────────
    you_frame = tk.Frame(inner, bg="#0d0d0d")
    you_frame.pack(fill="x", padx=12, pady=(8, 2))

    you_label = tk.Label(you_frame, text="", font=("Segoe UI", 8),
                         fg="#555555", bg="#0d0d0d", anchor="w", justify="left",
                         wraplength=320)
    you_label.pack(fill="x")

    # ── Thin separator ─────────────────────────────────────────────────────────
    sep = tk.Frame(inner, bg="#1a1a1a", height=1)
    sep.pack(fill="x", padx=12)

    # ── Jerry response area ───────────────────────────────────────────────────
    resp_frame = tk.Frame(inner, bg="#0d0d0d")
    resp_frame.pack(expand=True, fill="both", padx=12, pady=(6, 10))

    response_text = tk.Text(
        resp_frame,
        font=("Segoe UI", 11),
        fg="#e8e8e8",
        bg="#0d0d0d",
        wrap=tk.WORD,
        bd=0,
        highlightthickness=0,
        insertbackground="#0d0d0d",
        state=tk.DISABLED,
        cursor="arrow"
    )
    response_text.pack(expand=True, fill="both")

    # ── Initially hidden ───────────────────────────────────────────────────────
    root.withdraw()
    _visible = {"v": False}

    def show():
        if not _visible["v"]:
            root.deiconify()
            _visible["v"] = True

    def hide():
        if _visible["v"]:
            root.withdraw()
            _visible["v"] = False

    # ── Queue processor ────────────────────────────────────────────────────────
    def process_queue():
        while not _ui_queue.empty():
            msg = _ui_queue.get()
            action = msg.get("action")

            if action == "set_user":
                you_label.config(text=f'You: "{msg.get("text", "")}"')
                show()

            elif action == "clear_response":
                response_text.config(state=tk.NORMAL)
                response_text.delete("1.0", tk.END)
                response_text.config(state=tk.DISABLED)

            elif action == "append_response":
                response_text.config(state=tk.NORMAL)
                response_text.insert(tk.END, msg.get("text", ""))
                response_text.see(tk.END)
                response_text.config(state=tk.DISABLED)
                show()

            elif action == "set_listening":
                set_listening(msg.get("active", False))

            elif action == "hide":
                hide()

        root.after(40, process_queue)

    root.after(40, process_queue)
    root.mainloop()


# ── Start UI thread ────────────────────────────────────────────────────────────
_thread = threading.Thread(target=_ui_thread_func, daemon=True)
_thread.start()


# ── Public API ─────────────────────────────────────────────────────────────────
def set_user_text(text):
    _ui_queue.put({"action": "set_user", "text": text})

def clear_response():
    _ui_queue.put({"action": "clear_response"})

def append_response(text):
    _ui_queue.put({"action": "append_response", "text": text})

def set_listening(active: bool):
    _ui_queue.put({"action": "set_listening", "active": active})

def hide_ui():
    _ui_queue.put({"action": "hide"})

# Keep old names working so nothing else breaks
def clear_ui():
    clear_response()

def append_to_ui(text):
    append_response(text)

def set_ui_text(text):
    clear_response()
    append_response(text)
