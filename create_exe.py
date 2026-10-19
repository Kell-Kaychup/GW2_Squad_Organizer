from pathlib import Path
import sys
import subprocess
import re
from PIL import Image


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
    "Allgemein": ["Core", "Quick","Alacrity", "Heal", "Tank", "Toolkit", "Block", "pDPS", "cDPS", "Invul", "Stab", "Portal"],
}

CORE_CLASSES = list(SPECIALIZATIONS.keys())

# Ordner, in dem squadtool.py liegt
script = Path.cwd() / "squadtool.py"
icon_folder = script.parent / "class_icon"
ICON_DIR = icon_folder

exe_icon_png = icon_folder / "allgemein_tango_icon_48px.png"
exe_icon_ico = script.parent / "squadtool.ico"

if not exe_icon_png.is_file():
    print(f"FEHLER: Icon nicht gefunden: {exe_icon_png}")
    sys.exit(1)

img = Image.open(exe_icon_png).convert("RGBA")
img.save(
    exe_icon_ico,
    format="ICO",
    sizes=[(16, 16), (32, 32), (48, 48), (256, 256)]
)

    
def normalize(text):
    """Vereinheitlicht Namen für den Icon-Vergleich."""
    text = text.casefold()
    text = re.sub(r"_tango_icon_48px", "", text)
    return re.sub(r"[^a-z0-9]", "", text)


def find_icon(elite, profession=None):
    """
    Sucht ein PNG-Icon anhand des Spezialisierungsnamens.
    Bei 'Core' wird stattdessen der Klassenname verwendet.
    """
    if not ICON_DIR.is_dir():
        return None

    if elite == "Core":
        if not profession:
            return None
        elite = profession

    target = normalize(elite)

    for path in ICON_DIR.glob("*.png"):
        stem = path.stem.replace("_tango_icon_48px", "")

        if normalize(stem) == target:
            return path

    return None


# --------------------------------------------------
# Vorprüfung
# --------------------------------------------------

print("Script:", script)
print("Script vorhanden:", script.is_file())
print("Icon-Ordner:", icon_folder)
print("Icon-Ordner vorhanden:", icon_folder.is_dir())

if not script.is_file():
    print("\nFEHLER: squadtool.py wurde nicht gefunden.")
    sys.exit(1)

if not icon_folder.is_dir():
    print("\nFEHLER: Der Ordner class_icon wurde nicht gefunden.")
    sys.exit(1)


# --------------------------------------------------
# Alle Core- und Elite-Icons prüfen
# --------------------------------------------------

missing_icons = []
found_icons = 0

# Core wird pro Klasse einmal geprüft.
# Die restlichen Einträge sind Elite-Spezialisierungen.
total_icons = sum(len(specs) for specs in SPECIALIZATIONS.values())

print("\n========== CORE-ICON-PRÜFUNG ==========")

for profession in CORE_CLASSES:
    icon = find_icon("Core", profession)

    if icon is not None:
        print(f"  [OK]     {profession} -> {icon.name}")
        found_icons += 1
    else:
        print(f"  [FEHLT]  {profession}")
        missing_icons.append(("Core", profession))


print("\n========== ELITE-ICON-PRÜFUNG ==========")

for profession, specializations in SPECIALIZATIONS.items():
    print(f"\n{profession}:")

    for specialization in specializations:
        # Core wurde bereits oben geprüft.
        if specialization == "Core":
            continue

        icon = find_icon(specialization, profession)

        if icon is not None:
            print(f"  [OK]     {specialization} -> {icon.name}")
            found_icons += 1
        else:
            print(f"  [FEHLT]  {specialization}")
            missing_icons.append((profession, specialization))


# --------------------------------------------------
# Prüfungsergebnis
# --------------------------------------------------

print("\n========== ERGEBNIS ==========")
print(f"Benötigte Icons: {total_icons}")
print(f"Gefundene Icons: {found_icons}")
print(f"Fehlende Icons:  {len(missing_icons)}")

if missing_icons:
    print("\nFolgende Icons fehlen:")

    for profession, name in missing_icons:
        print(f"  - {profession}: {name}")

    print("\nBuild wird abgebrochen.")
    sys.exit(1)

print("\nAlle Core- und Elite-Icons sind vorhanden.")


# --------------------------------------------------
# PyInstaller-Build
# --------------------------------------------------

command = [
    sys.executable,
    "-m",
    "PyInstaller",
    "--noconfirm",
    "--clean",
    "--onefile",
    "--windowed",
    "--name",
    "GW2SquadOrganizer",
    "--icon",
    str(exe_icon_ico),
    "--collect-all",
    "PIL",
    "--add-data",
    f"{icon_folder};class_icon",
    str(script),
]
print("\n========== PYINSTALLER-BUILD ==========")
print("Starte Build ...\n")

result = subprocess.run(
    command,
    cwd=str(script.parent),
    text=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
)

print(result.stdout)
print("Build-Exit-Code:", result.returncode)

if result.returncode != 0:
    print("\nFEHLER: Der Build ist fehlgeschlagen.")
    sys.exit(result.returncode)

print("\nBuild erfolgreich abgeschlossen!")
print("EXE:", script.parent / "dist" / "GW2SquadOrganizer.exe")
