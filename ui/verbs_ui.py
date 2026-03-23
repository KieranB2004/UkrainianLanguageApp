import tkinter as tk
from data.verbs import verbs
from ui.prefixes_ui import PrefixesPage

class VerbsPage(tk.Frame):
    def __init__(self, parent, go_home):
        super().__init__(parent, bg="black")

        self.parent = parent
        self.go_home = go_home

        tk.Button(self, text="Home", command=go_home).pack(pady=5)
        tk.Button(self, text="Prefixes", command=self.show_prefixes).pack(pady=5)

        for i, v in enumerate(verbs):
            lbl = tk.Label(self, text=f"{v['inf']} - {v['en']}",
                           fg="white", bg="black")
            lbl.pack()
            lbl.bind("<Button-1>", lambda e, idx=i: self.open_detail(idx))

    def show_prefixes(self):
        self.destroy()
        PrefixesPage(self.parent, self.go_home).pack(fill="both", expand=True)

    def open_detail(self, idx):
        v = verbs[idx]

        top = tk.Toplevel(self)
        top.title(v["inf"])
        top.configure(bg="black")

        tk.Label(top, text=f"{v['inf']} — {v['en']}",
                 fg="white", bg="black",
                 font=("Segoe UI", 16, "bold")).pack(pady=10)

        table = tk.Frame(top, bg="black")
        table.pack()

        headers = ["", "Present", "Past", "Future"]
        persons = ["я", "ти", "він/вона", "ми", "ви", "вони"]

        for c, h in enumerate(headers):
            tk.Label(table, text=h, fg="white", bg="black").grid(row=0, column=c)

        pres = v.get("present", [""]*6)
        past = v.get("past", [""]*6)
        fut = v.get("future", [""]*6)

        for i in range(6):
            tk.Label(table, text=persons[i], fg="white", bg="black").grid(row=i+1, column=0)
            tk.Label(table, text=pres[i], fg="#ccc", bg="black").grid(row=i+1, column=1)
            tk.Label(table, text=past[i], fg="#ccc", bg="black").grid(row=i+1, column=2)
            tk.Label(table, text=fut[i], fg="#ccc", bg="black").grid(row=i+1, column=3)