import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import json
from tkinter import filedialog
import webbrowser
from PIL import Image, ImageTk, ImageDraw
import sys
from datetime import datetime

if getattr(sys, "frozen", False):
    ICON_DIR = Path(sys._MEIPASS) / "class_icon"
else:
    ICON_DIR = Path(__file__).resolve().parent / "class_icon"
    
DB_PATH = (
    Path(sys.executable).resolve().parent / "builds_db.json"
    if getattr(sys, "frozen", False)
    else Path(__file__).resolve().parent / "builds_db.json"
)

# Elite-Spezialisierungen je Klasse
SPECIALIZATIONS = {
    "Elementalist": ["Core", "Tempest", "Weaver", "Catalyst", "Evoker"],
    "Mesmer": ["Core", "Chronomancer", "Mirage", "Virtuoso", "Troubadour"],
    "Necromancer": ["Core", "Reaper", "Scourge", "Harbinger", "Ritualist"],
    "Engineer": ["Core", "Scrapper", "Holosmith", "Mechanist", "Amalgam"],
    "Ranger": ["Core", "Druid", "Soulbeast", "Untamed", "Galeshot"],
    "Thief": ["Core", "Daredevil", "Deadeye", "Specter", "Antiquary"],
    "Guardian": ["Core", "Dragonhunter", "Firebrand", "Willbender", "Luminary"],
    "Warrior": ["Core", "Berserker", "Spellbreaker", "Bladesworn", "Paragon"],
    "Revenant": ["Core", "Herald", "Renegade", "Vindicator", "Conduit"],    
    "Allgemein": ["Core", "Quick","Alacrity", "Heal", "Tank",
                  "Toolkit", "Block", "pDPS", "cDPS", "Invul", "Stab", "Portal"],
}


BUILDS = []
GROUP_COUNT = 1
GROUP_SLOTS = {0: 5}
SQUAD = [
    {"build": None, "group": 0, "slot": i}
    for i in range(5)
]
MAX_GROUPS = 15
MAX_SLOTS = 10


def normalize(text):
    return "".join(c.lower() for c in text if c.isalnum())


def find_icon(elite, profession=None):
    if not ICON_DIR.exists():
        return None

    # Bei Core den Klassennamen verwenden
    if elite == "Core":
        if profession is None:
            return None
        elite = profession

    target = normalize(elite)

    for path in ICON_DIR.glob("*.png"):
        stem = path.stem.replace("_tango_icon_48px", "")

        if normalize(stem) == target:
            return path

    return None

class Organizer:
    def __init__(self, root):
        self.root = root
        root.title("GW2 Squad Organizer")
        root.geometry("1150x720")
        root.configure(bg="#202630")

        self.images = {}
        self.drag_data = None
        self.drag_icon = None
        self.squad_slots = []
        
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "TCombobox",
            fieldbackground="#303b49",
            background="#39485a",
            foreground="white"
        )

        main = tk.Frame(root, bg="#202630")
        main.pack(fill="both", expand=True, padx=10, pady=10)

        # LINKS: Squad
        self.left = tk.Frame(main, bg="#2b3441", width=420)
        self.left.pack(
            side="left",
            fill="both",
            expand=False,
            padx=(0, 5)
        )
        self.left.pack_propagate(False)

        tk.Label(
            self.left, text="SQUAD",
            bg="#2b3441", fg="white",
            font=("Arial", 16, "bold")
        ).pack(anchor="w", padx=10, pady=10)

        # Scrollbarer Squad-Bereich
        self.squad_container = tk.Frame(self.left, bg="#2b3441")
        self.squad_container.pack(fill="both", expand=True, padx=8)
        
        self.squad_canvas = tk.Canvas(
            self.squad_container,
            bg="#2b3441",
            highlightthickness=0
        )
        
        self.squad_scrollbar = ttk.Scrollbar(
            self.squad_container,
            orient="vertical",
            command=self.squad_canvas.yview
        )
        
        self.squad_canvas.configure(
            yscrollcommand=self.squad_scrollbar.set
        )
        
        self.squad_scrollbar.pack(side="right", fill="y")
        self.squad_canvas.pack(side="left", fill="both", expand=True)
        
        self.squad_area = tk.Frame(self.squad_canvas, bg="#2b3441")
        
        self.squad_window = self.squad_canvas.create_window(
            (0, 0),
            window=self.squad_area,
            anchor="nw"
        )
        
        self.squad_area.bind(
            "<Configure>",
            lambda e: self.squad_canvas.configure(
                scrollregion=self.squad_canvas.bbox("all")
            )
        )
        
        self.squad_canvas.bind(
            "<Configure>",
            lambda e: self.squad_canvas.itemconfigure(
                self.squad_window, width=e.width
            )
        )
        
        # Mausrad zum Scrollen
        self.squad_canvas.bind(
            "<MouseWheel>",
            lambda e: self.squad_canvas.yview_scroll(
                int(-e.delta / 120), "units"
            )
        )

        tk.Label(
            self.left,
            text="Build-Icons hierher ziehen",
            bg="#2b3441", fg="#aebdce"
        ).pack(pady=5)

        # RECHTS: Build-Bibliothek
        self.right = tk.Frame(main, bg="#2b3441")
        self.right.pack(
            side="right",
            fill="both",
            expand=True,
            padx=(5, 0)
        )

        tk.Label(
            self.right, text="BUILDS",
            bg="#2b3441", fg="white",
            font=("Arial", 16, "bold")
        ).pack(anchor="w", padx=10, pady=10)

        self.build_area = tk.Frame(self.right, bg="#2b3441")
        self.build_area.pack(fill="both", expand=True, padx=8)

        self.build_canvas = tk.Canvas(
            self.build_area, bg="#2b3441",
            highlightthickness=0
        )
        scrollbar = ttk.Scrollbar(
            self.build_area, orient="vertical",
            command=self.build_canvas.yview
        )
        self.build_canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.build_canvas.pack(side="left", fill="both", expand=True)

        self.build_grid = tk.Frame(self.build_canvas, bg="#2b3441")
        self.canvas_window = self.build_canvas.create_window(
            (0, 0), window=self.build_grid, anchor="nw"
        )

        self.build_grid.bind(
            "<Configure>",
            lambda e: self.build_canvas.configure(
                scrollregion=self.build_canvas.bbox("all")
            )
        )
        self.build_canvas.bind(
            "<Configure>",
            lambda e: self.build_canvas.itemconfigure(
                self.canvas_window, width=e.width
            )
        )

        build_buttons = tk.Frame(self.right, bg="#2b3441")
        build_buttons.pack(fill="x", padx=10, pady=10)
        
        tk.Button(
            build_buttons,
            text="+ Build erstellen",
            command=self.create_build
        ).pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        tk.Button(
            build_buttons,
            text="Build löschen",
            command=self.delete_build
        ).pack(side="left", fill="x", expand=True, padx=(5, 0))
        tk.Button(
            build_buttons,
            text="Save in DB",
            command=self.save_to_db
        ).pack(side="left", fill="x", expand=True, padx=(5, 0))
        
        tk.Button(
            build_buttons,
            text="Load from DB",
            command=self.load_from_db
        ).pack(side="left", fill="x", expand=True, padx=(5, 0))
        # Eigenschaften des angeklickten Builds
        self.details = tk.Frame(root, bg="#18202a")
        self.details.pack(fill="x", side="bottom")
        
        self.detail_text = tk.Label(
            self.details,
            text="Build auswählen, um Details anzuzeigen",
            bg="#18202a",
            fg="white",
            anchor="w",
            justify="left",
            padx=12,
            pady=8
        )
        self.detail_text.pack(side="left", fill="x", expand=True)
        
        self.link_label = tk.Label(
            self.details,
            text="Build öffnen ↗",
            bg="#18202a",
            fg="#69b7ff",
            cursor="hand2",
            padx=12
        )
        self.link_label.pack(side="right")
        self.link_label.bind("<Button-1>", self.open_build_link)
        toolbar = tk.Frame(root, bg="#202630")
        toolbar.pack(fill="x", padx=10, pady=(8, 0))
        
        tk.Button(
            toolbar,
            text="Exportieren",
            command=self.export_data
        ).pack(side="left", padx=(0, 5))
        
        tk.Button(
            toolbar,
            text="Importieren",
            command=self.import_data
        ).pack(side="left", padx=(0, 5))
        tk.Button(
            toolbar,
            text="Clear Squad",
            command=self.clear_squad
        ).pack(side="left", padx=(0, 5))
        tk.Button(
            toolbar,
            text="Create Post",
            command=self.create_post
        ).pack(side="left")
        
        
        
        self.details.pack(fill="x", side="bottom")
        
        self.add_default_builds()
        self.refresh_squad()
        self.refresh_builds()
    
    
    def icon_to_relative(self, icon_path):
        if not icon_path:
            return ""
    
        path = Path(icon_path)
    
        # Bereits relativen Pfad beibehalten
        if not path.is_absolute():
            return path.as_posix()
    
        # Pfad relativ zum Programmordner speichern
        try:
            return path.resolve().relative_to(
                Path(__file__).resolve().parent
            ).as_posix()
        except ValueError:
            return path.name
    
    
    def icon_to_absolute(self, icon_path):
        if not icon_path:
            return None
    
        path = Path(icon_path)
    
        # Relative Pfade auflösen
        if not path.is_absolute():
            path = Path(__file__).resolve().parent / path
    
        if path.is_file():
            return path
    
        # Fallback: Icon anhand von Klasse und Elite suchen
        return None

    def clear_squad(self):
        if not messagebox.askyesno(
            "Clear Squad",
            "Möchtest du den Squad auf eine Gruppe mit 5 leeren Slots zurücksetzen?"
        ):
            return
    
        # Squad leeren
        SQUAD.clear()
    
        # Eine Gruppe mit 5 Slots wiederherstellen
        GROUP_SLOTS.clear()
        GROUP_SLOTS[0] = 5
    
        # Fünf leere Slots erstellen
        for slot in range(5):
            SQUAD.append({
                "build": None,
                "group": 0,
                "slot": slot
            })
    
        # Anzeige aktualisieren
        self.refresh_squad()
            
    def delete_build(self):
        build = getattr(self, "selected_build", None)
    
        if not build:
            messagebox.showwarning(
                "Build löschen",
                "Bitte zuerst ein Build auswählen."
            )
            return
    
        if not messagebox.askyesno(
            "Build löschen",
            f'Möchtest du das Build "{build["name"]}" wirklich löschen?\n\n'
            "Es wird auch aus dem Squad entfernt."
        ):
            return
    
        # Aus allen Squad-Slots entfernen
        SQUAD[:] = [
            entry for entry in SQUAD
            if entry["build"] is not build
        ]
    
        # Aus der Build-Bibliothek entfernen
        BUILDS[:] = [
            item for item in BUILDS
            if item is not build
        ]
    
        self.selected_build = None
    
        self.detail_text.config(
            text="Build auswählen, um Details anzuzeigen"
        )
        self.link_label.config(
            text="Kein Link",
            fg="#888888",
            cursor="arrow"
        )
    
        self.refresh_builds()
        self.refresh_squad()
    
    def create_post(self):
        from tkinter import filedialog, messagebox
    
        # Verwendete Builds sammeln, jeden Build nur einmal
        lines = []
        #used_build_ids = set()
        build_counts = {}
        
        for entry in SQUAD:
            build = entry.get("build")

            if not build:
                continue

            build_id = build["id"]

            if build_id not in build_counts:
                build_counts[build_id] = {
                    "build": build,
                    "count": 0
                }

            build_counts[build_id]["count"] += 1

        lines = []

        for item in build_counts.values():
            build = item["build"]
            count = item["count"]

            name = build.get("name", "")
            role = build.get("rolle", "")
            link = build.get("link", "")

            line = f"[{name} : {role} (Anzahl: {count})]"

            if link:
                line += f"({link})"

            lines.append(line)
    
        # Standardtext zusammenbauen
        intro = "Verwendete Builds für das Event:"
        subtitle = "Reagiert mit dem Klassenemote um am Event teilzunemehn."
    
        initial_text = (
            intro + "\n\n"
            + "\n".join(lines)
            + "\n\n"
            + subtitle
        )
    
        # Bearbeitungsfenster
        dialog = tk.Toplevel(self.root)
        dialog.title("Create Post")
        dialog.geometry("750x600")
        dialog.configure(bg="#202630")
    
        tk.Label(
            dialog,
            text="Dateiname:",
            bg="#202630",
            fg="white"
        ).pack(anchor="w", padx=12, pady=(12, 2))
    
        filename = tk.Entry(dialog)
        filename.insert(0, "event_builds")
        filename.pack(fill="x", padx=12, pady=(0, 10))
    
        # Ein einziges bearbeitbares Textfeld
        text_frame = tk.Frame(dialog, bg="#202630")
        text_frame.pack(fill="both", expand=True, padx=12, pady=5)
    
        text_box = tk.Text(
            text_frame,
            bg="#2b3441",
            fg="white",
            insertbackground="white",
            wrap="word",
            undo=True,
            font=("Arial", 11)
        )
        scrollbar = ttk.Scrollbar(
            text_frame,
            orient="vertical",
            command=text_box.yview
        )
        text_box.configure(yscrollcommand=scrollbar.set)
    
        scrollbar.pack(side="right", fill="y")
        text_box.pack(side="left", fill="both", expand=True)
        text_box.insert("1.0", initial_text)
    
        def save_post():
            name = filename.get().strip()
            if not name:
                messagebox.showwarning(
                    "Dateiname fehlt",
                    "Bitte einen Dateinamen eingeben.",
                    parent=dialog
                )
                return
    
            name = "".join(
                c for c in name
                if c.isalnum() or c in ("-", "_", " ")
            ).strip()
    
            if not name:
                return
    
            output_dir = filedialog.askdirectory(
                parent=dialog,
                title="Speicherordner auswählen"
            )
            if not output_dir:
                return
    
            output_dir = Path(output_dir)
            final_text = text_box.get("1.0", "end-1c")
    
            try:
                # Text speichern
                text_path = output_dir / f"{name}.txt"
                text_path.write_text(final_text, encoding="utf-8")
    
                # Squad-Bild erstellen
                groups = sorted(GROUP_SLOTS.keys())
                slot_size = 58
                padding = 20
                header_height = 30
                group_gap = 14
    
                max_slots = max(
                    (GROUP_SLOTS[g] for g in groups),
                    default=5
                )
    
                width = padding * 2 + max_slots * slot_size
                height = padding * 2 + sum(
                    header_height + slot_size + group_gap
                    for _ in groups
                )
    
                image = Image.new(
                    "RGB", (width, height), "#202630"
                )
                draw = ImageDraw.Draw(image)
                y = padding
    
                for group in groups:
                    draw.text(
                        (padding, y),
                        f"Gruppe {group + 1}",
                        fill="white"
                    )
                    y += header_height
    
                    for slot in range(GROUP_SLOTS[group]):
                        x = padding + slot * slot_size
    
                        draw.rounded_rectangle(
                            (
                                x, y,
                                x + slot_size - 6,
                                y + slot_size - 6
                            ),
                            radius=5,
                            fill="#354252"
                        )
    
                        entry = next(
                            (
                                item for item in SQUAD
                                if item["group"] == group
                                and item["slot"] == slot
                            ),
                            None
                        )
    
                        if entry and entry.get("build"):
                            icon_path = entry["build"].get("icon")
    
                            if icon_path and Path(icon_path).is_file():
                                icon = Image.open(
                                    icon_path
                                ).convert("RGBA")
                                icon.thumbnail((48, 48))
    
                                image.paste(
                                    icon,
                                    (
                                        x + (slot_size - 6 - icon.width) // 2,
                                        y + (slot_size - 6 - icon.height) // 2
                                    ),
                                    icon
                                )
    
                    y += slot_size + group_gap
    
                image_path = output_dir / f"{name}.png"
                image.save(image_path)
    
                messagebox.showinfo(
                    "Gespeichert",
                    f"Text und Squad-Bild gespeichert:\n\n"
                    f"{text_path}\n{image_path}",
                    parent=dialog
                )
    
            except OSError as error:
                messagebox.showerror(
                    "Fehler beim Speichern",
                    str(error),
                    parent=dialog
                )
    
        tk.Button(
            dialog,
            text="Speichern",
            command=save_post
        ).pack(pady=12)

    def get_image(self, path, size=48):
        if not path or not Path(path).exists():
            return None

        key = (str(path), size)

        if key not in self.images:
            image = Image.open(path).convert("RGBA")
            image = image.resize((size, size), Image.Resampling.LANCZOS)
            self.images[key] = ImageTk.PhotoImage(image)

        return self.images[key]

    def show_details(self, build):
        self.selected_build = build
    
        self.detail_text.config(
            text=(
                f'ID: {build["id"]} | '
                f'Name: {build["name"]} | '
                f'Klasse: {build["klasse"]} | '
                f'Elite: {build["elite"]} | '
                f'Rolle: {build["rolle"]} | '
                f'Link: {build.get("link", "")}\n'
                f'Erstellt am: {build.get("zeit", "Unbekannt")}'
            )
        )
    
        if build.get("link"):
            self.link_label.config(
                text="Link öffnen ↗",
                fg="#69b7ff",
                cursor="hand2"
            )
        else:
            self.link_label.config(
                text="Kein Link",
                fg="#888888",
                cursor="arrow"
            )

    def open_build_link(self, event=None):
        if self.selected_build and self.selected_build.get("link"):
            webbrowser.open(self.selected_build["link"])
    
    def export_data(self):
        path = filedialog.asksaveasfilename(
            title="Squad und Builds exportieren",
            defaultextension=".json",
            filetypes=[("JSON-Dateien", "*.json")]
        )
        if not path:
            return
    
        data = {
            "builds": [
                {
                    **build,
                    "icon": self.icon_to_relative(build.get("icon"))
                }
                for build in BUILDS
            ],
            "squad": [
                {
                    "build_id": (
                        entry["build"]["id"]
                        if entry["build"] else None
                    ),
                    "group": entry["group"],
                    "slot": entry["slot"]
                }
                for entry in SQUAD
            ],
            "group_slots": {
                str(group): slots
                for group, slots in GROUP_SLOTS.items()
            }
        }
    
        try:
            with open(path, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=2, ensure_ascii=False)
    
            messagebox.showinfo("Export", "Export erfolgreich.")
        except OSError as error:
            messagebox.showerror("Export fehlgeschlagen", str(error))
    
    
    def import_data(self):
        path = filedialog.askopenfilename(
            title="Squad und Builds importieren",
            filetypes=[("JSON-Dateien", "*.json")]
        )
        if not path:
            return
    
        try:
            with open(path, "r", encoding="utf-8") as file:
                data = json.load(file)
    
            builds_data = data["builds"]
            squad_data = data["squad"]
            slots_data = data["group_slots"]
    
            # Erst validieren, bevor vorhandene Daten ersetzt werden.
            if not isinstance(builds_data, list):
                raise ValueError("Ungültige Build-Liste.")
            if not isinstance(squad_data, list):
                raise ValueError("Ungültige Squad-Liste.")
            if not isinstance(slots_data, dict):
                raise ValueError("Ungültige Gruppendaten.")
    
            new_builds = []
            ids = set()
    
            for build in builds_data:
                build_id = int(build["id"])
    
                if build_id in ids:
                    raise ValueError(f"Doppelte Build-ID: {build_id}")
    
                ids.add(build_id)
    
                new_builds.append({
                                "id": build_id,
                                "name": str(build["name"]),
                                "klasse": str(build["klasse"]),
                                "elite": str(build["elite"]),
                                "rolle": str(build.get("rolle", "")),
                                "link": str(build.get("link", "")),
                                "icon": (
                                        self.icon_to_absolute(build.get("icon"))
                                        or find_icon(
                                            build.get("elite", ""),
                                            build.get("klasse", "")
                                        )
                                    ),
                                "zeit": str(build.get("zeit", "")),
                            })
    
            new_group_slots = {
                int(group): int(slots)
                for group, slots in slots_data.items()
            }
    
            if not 1 <= len(new_group_slots) <= MAX_GROUPS:
                raise ValueError("Es sind maximal 15 Gruppen erlaubt.")
    
            for group, slots in new_group_slots.items():
                if not 0 <= group < MAX_GROUPS:
                    raise ValueError("Ungültige Gruppennummer.")
                if not 1 <= slots <= MAX_SLOTS:
                    raise ValueError("Eine Gruppe darf 1–10 Slots haben.")
    
            new_squad = []
    
            for entry in squad_data:
                group = int(entry["group"])
                slot = int(entry["slot"])
                build_id = entry.get("build_id")
    
                if group not in new_group_slots:
                    raise ValueError("Squad-Eintrag verweist auf Gruppe.")
                if not 0 <= slot < new_group_slots[group]:
                    raise ValueError("Ungültiger Squad-Slot.")
    
                build = next(
                    (b for b in new_builds if b["id"] == build_id),
                    None
                ) if build_id is not None else None
    
                if build_id is not None and build is None:
                    raise ValueError(f"Build-ID {build_id} fehlt.")
    
                new_squad.append({
                    "build": build,
                    "group": group,
                    "slot": slot
                })
    
            occupied = [
                (entry["group"], entry["slot"])
                for entry in new_squad
            ]
    
            if len(occupied) != len(set(occupied)):
                raise ValueError("Ein Squad-Slot ist mehrfach belegt.")
    
            # Daten erst nach erfolgreicher Validierung übernehmen.
            BUILDS.clear()
            BUILDS.extend(new_builds)
    
            SQUAD.clear()
            SQUAD.extend(new_squad)
    
            GROUP_SLOTS.clear()
            GROUP_SLOTS.update(new_group_slots)
    
            self.refresh_builds()
            self.refresh_squad()
    
            messagebox.showinfo("Import", "Import erfolgreich.")
    
        except (OSError, ValueError, KeyError, TypeError) as error:
            messagebox.showerror(
                "Import fehlgeschlagen",
                str(error)
            )


    # ---------- Build-Bibliothek ----------
    def add_default_builds(self):
       defaults = ["Heal", "pDPS", "Stab"]

       existing = {
           (build["klasse"], build["elite"])
           for build in BUILDS
       }

       for spec in defaults:
           if ("Allgemein", spec) in existing:
               continue

           icon_path = find_icon(spec, "Allgemein")

           BUILDS.append({
               "id": max((b["id"] for b in BUILDS), default=0) + 1,
               "name": f"Allgemein - {spec}",
               "klasse": "Allgemein",
               "elite": spec,
               "rolle": spec,
               "link": "",
               "icon": icon_path,
               "zeit": datetime.now().strftime("%Y-%m-%d %H:%M"),
           })
           
    def refresh_builds(self):
        for widget in self.build_grid.winfo_children():
            widget.destroy()

        for index, build in enumerate(BUILDS):
            image = self.get_image(build["icon"])

            card = tk.Frame(
                self.build_grid, bg="#354252",
                padx=5, pady=5
            )
            card.grid(
                row=index // 8,
                column=index % 8,
                padx=3,
                pady=3,
                sticky="nsew"
            )

            button = tk.Button(
                card,
                image=image,
                text="" if image else "?",
                width=55, height=55,
                bg="#354252", activebackground="#526b86",
                relief="flat",
                command=lambda b=build: self.show_details(b)
            )
            button.image = image
            button.pack()
            
            # Buildname – erste Zeile
            tk.Label(
                card,
                text=build["name"][:10],
                bg="#354252",
                fg="white",
                wraplength=65
            ).pack()
            
            # Rolle – zweite Zeile
            date_text = build.get("zeit", "")

            tk.Label(
                card,
                text=f'{build.get("rolle", "")[:10]}\n{date_text}',
                bg="#354252",
                fg="#aebdce",
                font=("Arial", 7),
                wraplength=90,
                justify="center"
            ).pack()
            
            # Drag-and-drop starten
            button.bind(
                "<ButtonPress-1>",
                lambda e, b=build: self.start_drag(e, b, "library")
            )
            button.bind("<B1-Motion>", self.move_drag)
            button.bind("<ButtonRelease-1>", self.end_drag)

            # Klick zeigt Eigenschaften
            button.bind(
                "<Double-Button-1>",
                lambda e, b=build: self.show_details(b)
            )


    # ---------- Squad ----------

    def add_group(self):
        if len(GROUP_SLOTS) >= MAX_GROUPS:
            messagebox.showinfo("Squad", "Maximal 15 Gruppen möglich.")
            return
    
        group = max(GROUP_SLOTS.keys(), default=-1) + 1
        GROUP_SLOTS[group] = 5
        self.refresh_squad()
    
    def delete_last_group(self):
        if not GROUP_SLOTS:
            return
    
        group = max(GROUP_SLOTS.keys())
    
        if len(GROUP_SLOTS) <= 1:
            messagebox.showinfo(
                "Gruppe löschen",
                "Mindestens eine Gruppe muss bestehen bleiben."
            )
            return
    
        if not messagebox.askyesno(
            "Gruppe löschen",
            f"Möchtest du Gruppe {group + 1} wirklich löschen?\n\n"
            "Alle Builds in dieser Gruppe werden aus dem Squad entfernt."
        ):
            return
    
        # Alle Slots der letzten Gruppe entfernen
        SQUAD[:] = [
            entry for entry in SQUAD
            if entry["group"] != group
        ]
    
        # Gruppe entfernen
        del GROUP_SLOTS[group]
    
        self.refresh_squad()
    
    
    
    def add_slot(self, group):
        if GROUP_SLOTS[group] >= MAX_SLOTS:
            messagebox.showinfo(
                "Gruppe", "Maximal 10 Slots pro Gruppe möglich."
            )
            return
    
        slot = GROUP_SLOTS[group]
        GROUP_SLOTS[group] += 1
    
        SQUAD.append({
            "build": None,
            "group": group,
            "slot": slot
        })
    
        self.refresh_squad()
    
    def remove_slot(self, group):
        if GROUP_SLOTS[group] <= 1:
            messagebox.showinfo(
                "Slot entfernen",
                "Jede Gruppe muss mindestens einen Slot behalten."
            )
            return
    
        slot = GROUP_SLOTS[group] - 1
    
        if not messagebox.askyesno(
            "Slot entfernen",
            f"Möchtest du Slot {slot + 1} aus Gruppe {group + 1} entfernen?\n\n"
            "Ein Build in diesem Slot wird aus dem Squad entfernt."
        ):
            return
    
        # Einträge im letzten Slot dieser Gruppe entfernen
        SQUAD[:] = [
            entry for entry in SQUAD
            if not (entry["group"] == group and entry["slot"] == slot)
        ]
    
        GROUP_SLOTS[group] -= 1
        self.refresh_squad()
        
    def refresh_squad(self):
        for widget in self.squad_area.winfo_children():
            widget.destroy()
    
        self.squad_slots = []
    
        SLOTS_PER_ROW = 5
    
        for group in sorted(GROUP_SLOTS):
            frame = tk.LabelFrame(
                self.squad_area,
                text=f"Gruppe {group + 1}",
                bg="#2b3441",
                fg="white",
                padx=4,
                pady=4
            )
            frame.pack(fill="x", pady=4, anchor="n")
    
            # Slots in Zeilen mit jeweils maximal 5 Slots anzeigen
            slots_frame = tk.Frame(frame, bg="#2b3441")
            slots_frame.pack(side="left", anchor="nw")
    
            for slot in range(GROUP_SLOTS[group]):
                entry = next(
                    (
                        item for item in SQUAD
                        if item["group"] == group
                        and item["slot"] == slot
                    ),
                    None
                )
    
                row = slot // SLOTS_PER_ROW
                column = slot % SLOTS_PER_ROW
    
                cell = tk.Frame(
                    slots_frame,
                    width=48,
                    height=48,
                    bg="#202630"
                )
                cell.grid(
                    row=row,
                    column=column,
                    padx=2,
                    pady=2
                )
                cell.pack_propagate(False)
    
                if entry and entry["build"]:
                    build = entry["build"]
                    image = self.get_image(build["icon"], 40)
    
                    button = tk.Button(
                        cell,
                        image=image,
                        text="" if image else "?",
                        bg="#202630",
                        relief="flat",
                        command=lambda b=build: self.show_details(b)
                    )
                    button.image = image
                    button.pack(fill="both", expand=True)
    
                    button.bind(
                        "<ButtonPress-1>",
                        lambda e, item=entry: self.start_drag(
                            e, item, "squad"
                        )
                    )
                    button.bind("<B1-Motion>", self.move_drag)
                    button.bind("<ButtonRelease-1>", self.end_drag)
    
                else:
                    empty = tk.Label(
                        cell,
                        text="·",
                        bg="#202630",
                        fg="#73869a"
                    )
                    empty.pack(fill="both", expand=True)
    
                cell.bind(
                    "<ButtonRelease-1>",
                    lambda e, g=group, s=slot: self.drop_to_slot(g, s)
                )
    
                self.squad_slots.append((cell, group, slot))
    
            # Slot-Buttons rechts neben den Slots
            controls = tk.Frame(frame, bg="#2b3441")
            controls.pack(side="left", padx=(6, 0), anchor="n")
    
            if GROUP_SLOTS[group] < MAX_SLOTS:
                tk.Button(
                    controls,
                    text="+",
                    width=2,
                    height=1,
                    font=("Arial", 7),
                    command=lambda g=group: self.add_slot(g)
                ).pack(pady=(2, 3))
    
            if GROUP_SLOTS[group] > 1:
                tk.Button(
                    controls,
                    text="-",
                    width=2,
                    height=1,
                    font=("Arial", 7),
                    command=lambda g=group: self.remove_slot(g)
                ).pack(pady=2)
            
        # Gruppen-Buttons
        buttons = tk.Frame(self.squad_area, bg="#2b3441")
        buttons.pack(anchor="w", pady=6)
    
        if len(GROUP_SLOTS) < MAX_GROUPS:
            tk.Button(
                buttons,
                text="+ Gruppe hinzufügen",
                command=self.add_group
            ).pack(side="left", padx=(0, 5))
    
        if len(GROUP_SLOTS) > 1:
            tk.Button(
                buttons,
                text="- Letzte Gruppe löschen",
                command=self.delete_last_group
            ).pack(side="left")
            

    # ---------- Drag-and-drop ----------

    def start_drag(self, event, item, source):
        self.drag_data = {
            "item": item,
            "source": source,
            "x": event.x_root,
            "y": event.y_root,
        }
    
        # Build ermitteln
        build = item if source == "library" else item["build"]
    
        if not build:
            return
    
        self.show_details(build)
    
        # Icon laden
        image = self.get_image(build.get("icon"), 48)
    
        if image:
            self.drag_icon = tk.Label(
                self.root,
                image=image,
                bg="#354252",
                bd=2,
                relief="solid"
            )
            self.drag_icon.image = image
    
            # Icon direkt am Mauszeiger anzeigen
            self.drag_icon.place(
                x=event.x_root - self.root.winfo_rootx() + 10,
                y=event.y_root - self.root.winfo_rooty() + 10
            )
    
            self.drag_icon.lift()

    def move_drag(self, event):
        if self.drag_data:
            self.root.configure(cursor="hand2")
    
            if self.drag_icon:
                x = event.x_root - self.root.winfo_rootx() + 10
                y = event.y_root - self.root.winfo_rooty() + 10
    
                self.drag_icon.place(x=x, y=y)
                self.drag_icon.lift()

    def end_drag(self, event):
        self.root.configure(cursor="")
    
        # Drag-Icon entfernen
        if self.drag_icon:
            self.drag_icon.destroy()
            self.drag_icon = None
    
        if not self.drag_data:
            return
    
        x, y = event.x_root, event.y_root
        target = None
    
        for cell, group, slot in self.squad_slots:
            left = cell.winfo_rootx()
            top = cell.winfo_rooty()
            right = left + cell.winfo_width()
            bottom = top + cell.winfo_height()
    
            if left <= x <= right and top <= y <= bottom:
                target = (group, slot)
                break
    
        if target:
            self.place_item(*target)
    
        else:
            # Build aus dem Squad entfernen, wenn er
            # außerhalb aller Squad-Slots losgelassen wird.
            if self.drag_data["source"] == "squad":
                item = self.drag_data["item"]
    
                if item in SQUAD:
                    SQUAD.remove(item)
                    self.refresh_squad()
    
        self.drag_data = None

    def drop_to_slot(self, group, slot):
        # Funktioniert auch durch Klick auf einen leeren Slot.
        if self.drag_data:
            self.place_item(group, slot)
            self.drag_data = None
            self.root.configure(cursor="")

    def place_item(self, group, slot):
        if not self.drag_data:
            return

        item = self.drag_data["item"]
        source = self.drag_data["source"]

        existing = next(
            (
                entry for entry in SQUAD
                if entry["group"] == group and entry["slot"] == slot
            ),
            None
        )

        if source == "library":
            if existing and existing["build"] is not None:
                messagebox.showinfo(
                    "Slot belegt",
                    "Bitte einen freien Slot auswählen."
                )
                return
        
            if existing:
                existing["build"] = item
            else:
                SQUAD.append({
                    "build": item,
                    "group": group,
                    "slot": slot
                })

        else:
            old_group = item["group"]
            old_slot = item["slot"]

            if existing is item:
                return

            if existing:
                # Beide Einträge tauschen die Plätze.
                existing["group"], existing["slot"] = old_group, old_slot

            item["group"], item["slot"] = group, slot

        self.refresh_squad()
        
    def save_to_db(self):
        build = getattr(self, "selected_build", None)
    
        if not build:
            messagebox.showwarning(
                "Save in DB",
                "Bitte zuerst einen Build in der Bibliothek auswählen."
            )
            return
    
        try:
            if DB_PATH.exists():
                with open(DB_PATH, "r", encoding="utf-8") as file:
                    data = json.load(file)
            else:
                data = {"builds": []}
    
            if not isinstance(data, dict):
                raise ValueError("Ungültiges Datenbankformat.")
    
            db_builds = data.setdefault("builds", [])
    
            if not isinstance(db_builds, list):
                raise ValueError("Ungültige Build-Liste.")
    
            icon_path = build.get("icon")

            if icon_path:
                try:
                    relative_icon = Path(icon_path).resolve().relative_to(
                        Path(__file__).resolve().parent
                    )
                    icon_value = relative_icon.as_posix()
                except ValueError:
                    # Icons außerhalb des Programmordners nicht als absoluten
                    # Pfad speichern.
                    icon_value = Path(icon_path).name
            else:
                icon_value = ""
            
            item = {
                **build,
                "icon": icon_value,
                "zeit": build.get("zeit") or datetime.now().strftime(
                    "%Y-%m-%d %H:%M"
                ),
            }
    
            # Build anhand seiner ID aktualisieren oder neu einfügen
            found = False
    
            for index, saved in enumerate(db_builds):
                if int(saved["id"]) == int(build["id"]):
                    db_builds[index] = item
                    found = True
                    break
    
            if not found:
                db_builds.append(item)
    
            with open(DB_PATH, "w", encoding="utf-8") as file:
                json.dump(data, file, indent=2, ensure_ascii=False)
    
            # Datum auch im ausgewählten Build aktualisieren
            build["zeit"] = item["zeit"]
            self.show_details(build)
    
            messagebox.showinfo(
                "Save in DB",
                f'Build "{build["name"]}" gespeichert.\n\n{DB_PATH}'
            )
    
        except (OSError, ValueError, KeyError, TypeError) as error:
            messagebox.showerror(
                "Datenbankfehler",
                str(error)
            )
    def load_from_db(self):
        if not DB_PATH.exists():
            messagebox.showinfo(
                "Load from DB",
                f"Die Datenbank existiert noch nicht:\n{DB_PATH}\n\n"
                "Speichere zuerst einen Build mit 'Save in DB'."
            )
            return
    
        try:
            with open(DB_PATH, "r", encoding="utf-8") as file:
                data = json.load(file)
    
            db_builds = data["builds"]
    
            if not isinstance(db_builds, list):
                raise ValueError("Ungültige Build-Liste.")
    
        except (OSError, ValueError, KeyError, TypeError) as error:
            messagebox.showerror(
                "Datenbankfehler",
                str(error)
            )
            return
    
        dialog = tk.Toplevel(self.root)
        dialog.title("Load from DB")
        dialog.geometry("600x500")
        dialog.configure(bg="#202630")
        dialog.transient(self.root)
    
        tk.Label(
            dialog,
            text="Builds aus der Datenbank auswählen",
            bg="#202630",
            fg="white",
            font=("Arial", 14, "bold")
        ).pack(anchor="w", padx=12, pady=12)
    
        container = tk.Frame(dialog, bg="#202630")
        container.pack(fill="both", expand=True, padx=12)
    
        canvas = tk.Canvas(
            container,
            bg="#2b3441",
            highlightthickness=0
        )
        scrollbar = ttk.Scrollbar(
            container,
            orient="vertical",
            command=canvas.yview
        )
    
        canvas.configure(yscrollcommand=scrollbar.set)
    
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
    
        list_frame = tk.Frame(canvas, bg="#2b3441")
        window_id = canvas.create_window(
            (0, 0),
            window=list_frame,
            anchor="nw"
        )
    
        list_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
    
        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfigure(
                window_id,
                width=e.width
            )
        )
    
        variables = []
    
        if not db_builds:
            tk.Label(
                list_frame,
                text="Die Datenbank enthält keine Builds.",
                bg="#2b3441",
                fg="white"
            ).pack(anchor="w", padx=8, pady=8)
    
        for build in db_builds:
            var = tk.BooleanVar(value=False)
            variables.append((var, build))
    
            label_text = (
                f'{build.get("name", "Unbenannt")} | '
                f'{build.get("klasse", "")} | '
                f'{build.get("elite", "")} | '
                f'{build.get("rolle", "")} | '
                f'{build.get("zeit", "Kein Datum")}'
            )
    
            tk.Checkbutton(
                list_frame,
                text=label_text,
                variable=var,
                bg="#2b3441",
                fg="white",
                selectcolor="#202630",
                activebackground="#2b3441",
                activeforeground="white",
                anchor="w",
                justify="left",
                wraplength=520
            ).pack(fill="x", anchor="w", padx=5, pady=3)
    
        buttons = tk.Frame(dialog, bg="#202630")
        buttons.pack(fill="x", padx=12, pady=12)
    
        def uncheck_all():
            for var, _ in variables:
                var.set(False)
    
        def load_selected():
            chosen = [
                build for var, build in variables
                if var.get()
            ]
    
            if not chosen:
                messagebox.showwarning(
                    "Load",
                    "Bitte mindestens einen Build auswählen.",
                    parent=dialog
                )
                return
    
            # Vorhandene IDs berücksichtigen
            existing_ids = {
                int(build["id"])
                for build in BUILDS
            }
    
            loaded = 0
    
            for item in chosen:
                build_id = int(item["id"])
    
                if build_id in existing_ids:
                    continue
    
                class_name = str(item.get("klasse", ""))
                elite = str(item.get("elite", ""))
    
                icon_path = find_icon(elite, class_name)
    
                # Falls ein Icon-Pfad gespeichert wurde und noch gültig ist
                saved_icon = item.get("icon", "")

                if saved_icon:
                    saved_path = Path(saved_icon)
                
                    if not saved_path.is_absolute():
                        saved_path = Path(__file__).resolve().parent / saved_path
                
                    if saved_path.is_file():
                        icon_path = saved_path
    
                build = {
                    "id": build_id,
                    "name": str(item.get("name", "")),
                    "klasse": class_name,
                    "elite": elite,
                    "rolle": str(item.get("rolle", "")),
                    "link": str(item.get("link", "")),
                    "icon": icon_path,
                    "zeit": str(item.get("zeit", "")),
                }
    
                BUILDS.append(build)
                existing_ids.add(build_id)
                loaded += 1
    
            self.refresh_builds()
    
            messagebox.showinfo(
                "Load from DB",
                f"{loaded} Build(s) geladen.\n"
                f"{len(chosen) - loaded} bereits vorhandene Builds übersprungen.",
                parent=dialog
            )
    
            dialog.destroy()
    
        tk.Button(
            buttons,
            text="Uncheck all",
            command=uncheck_all
        ).pack(side="left")
    
        tk.Button(
            buttons,
            text="Load",
            command=load_selected
        ).pack(side="right")
    
        
    # ---------- Build erstellen ----------
    
    def create_build(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Build erstellen")
        dialog.configure(bg="#2b3441")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        form = tk.Frame(dialog, bg="#2b3441", padx=15, pady=15)
        form.pack()

        def add_label(text, row):
            tk.Label(
                form, text=text, bg="#2b3441", fg="white"
            ).grid(row=row, column=0, sticky="w", pady=5)

        add_label("Klasse:", 0)
        klasse = ttk.Combobox(
            form, values=list(SPECIALIZATIONS),
            state="readonly", width=28
        )
        klasse.grid(row=0, column=1, pady=5)

        add_label("Elite-Spezialisierung:", 1)
        elite = ttk.Combobox(
            form, state="readonly", width=28
        )
        elite.grid(row=1, column=1, pady=5)

        add_label("Buildname:", 2)
        name = tk.Entry(form, width=31)
        name.grid(row=2, column=1, pady=5)

        add_label("Rolle:", 3)
        role = tk.Entry(form, width=31)
        role.grid(row=3, column=1, pady=5)

        add_label("Build-Link:", 4)
        link = tk.Entry(form, width=31)
        link.grid(row=4, column=1, pady=5)

        preview = tk.Label(form, bg="#2b3441")
        preview.grid(row=5, column=1, sticky="w", pady=8)
        preview.image = None

        def update_elites(event=None):
            specs = SPECIALIZATIONS.get(klasse.get(), [])
        
            elite.set("")
            elite["values"] = specs
        
            preview.config(image="", text="Elite auswählen")
            preview.image = None
        
        
        def update_icon(event=None):
            spec = elite.get().strip()
            class_name = klasse.get()
            if not spec:
                return
        
            path = find_icon(spec, class_name)
        
            if path is None:
                preview.config(image="", text=f"Icon nicht gefunden: {spec}")
                preview.image = None
                return
        
            image = self.get_image(path, 48)
            preview.config(image=image, text="")
            preview.image = image

        klasse.bind("<<ComboboxSelected>>", update_elites)
        elite.bind("<<ComboboxSelected>>", update_icon)

        def save():
            class_name = klasse.get()
            spec = elite.get()
            build_name = name.get().strip()
            build_role = role.get()
            build_link = link.get().strip()
            icon_path = find_icon(spec, class_name) if spec else None

            if not all([class_name, spec, build_name]):
                messagebox.showwarning(
                    "Fehlende Angaben",
                    "Bitte Klasse, Elite und Name ausfüllen.",
                    parent=dialog
                )
                return

            if not icon_path:
                messagebox.showwarning(
                    "Icon fehlt",
                    f"Kein Icon für {spec} gefunden.\n\n"
                    "Erwarteter Dateiname beispielsweise:\n"
                    f"{spec}_tango_icon_48px.png",
                    parent=dialog
                )
                return

            BUILDS.append({
                "id": max((b["id"] for b in BUILDS), default=0) + 1,
                "name": build_name,
                "klasse": class_name,
                "elite": spec,
                "rolle": build_role,
                "link": build_link,
                "icon": icon_path,
                "zeit": datetime.now().strftime("%Y-%m-%d %H:%M"),
            })

            self.refresh_builds()
            dialog.destroy()

        tk.Button(
            form, text="Speichern", command=save
        ).grid(row=6, column=1, sticky="e", pady=10)
        


if __name__ == "__main__":
    root = tk.Tk()
    Organizer(root)
    root.mainloop()
