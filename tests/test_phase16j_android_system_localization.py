from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]


def strings(path: str) -> dict[str, str]:
    root = ET.parse(ROOT / path).getroot()
    return {node.attrib["name"]: node.text or "" for node in root.findall("string")}


def test_android_launcher_shortcuts_have_english_default_and_greek_locale():
    default = {}
    greek = {}
    for name in ("phase14_strings.xml", "phase15_strings.xml"):
        default.update(strings(f"android/app/src/main/res/values/{name}"))
        greek.update(strings(f"android/app/src/main/res/values-el/{name}"))

    assert default["individual_plants_shortcut"] == "Individual Plants"
    assert default["individual_plants_shortcut_long"] == "Individual Plants / Trees"
    assert default["sensor_data_shortcut"] == "Sensors"
    assert default["sensor_data_shortcut_long"] == "Sensors / API"
    assert greek["individual_plants_shortcut"] == "Μεμονωμένα Δέντρα"
    assert greek["individual_plants_shortcut_long"] == "Μεμονωμένα Φυτά / Δέντρα"
    assert greek["sensor_data_shortcut"] == "Αισθητήρες"
    assert greek["sensor_data_shortcut_long"] == "Αισθητήρες / API"

    shortcuts = (ROOT / "android/app/src/main/res/xml/shortcuts.xml").read_text(encoding="utf-8")
    for key in default:
        assert f"@string/{key}" in shortcuts
