#!/usr/bin/env python3
"""
VANTA PS2 Classic R0.1
Minimal, low-risk presentation layer over NetherSX2 Classic 3668.

Design goal for R0.1:
- DO NOT touch classes.dex, native libraries, GameDB or emulation core.
- Keep upstream package id for maximum compatibility.
- Change only launcher/application branding and add build metadata.
"""
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ANDROID_NS = "http://schemas.android.com/apk/res/android"
A = "{" + ANDROID_NS + "}"
ET.register_namespace("android", ANDROID_NS)

VANTA_LABEL = "VANTA PS2 Classic"
VANTA_BUILD = "0.1-classic-3668"
UPSTREAM = "NetherSX2 Classic 2.1 / AetherSX2 3668 core"

def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_vanta_ps2_classic.py <apktool-decoded-dir>")

    root = Path(sys.argv[1]).resolve()
    manifest = root / "AndroidManifest.xml"
    if not manifest.is_file():
        raise RuntimeError(f"AndroidManifest.xml not found: {manifest}")

    tree = ET.parse(manifest)
    doc = tree.getroot()
    app = doc.find("application")
    if app is None:
        raise RuntimeError("application node not found")

    package_name = doc.attrib.get("package", "")
    if not package_name:
        raise RuntimeError("manifest package name not found")

    # Keep package and code namespace untouched. Only presentation changes.
    app.set(A + "label", VANTA_LABEL)

    changed_activities = 0
    for tag in ("activity", "activity-alias"):
        for node in app.findall(tag):
            label = node.attrib.get(A + "label", "")
            name = node.attrib.get(A + "name", "")
            has_main = False
            for intent in node.findall("intent-filter"):
                actions = {x.attrib.get(A + "name", "") for x in intent.findall("action")}
                cats = {x.attrib.get(A + "name", "") for x in intent.findall("category")}
                if ("android.intent.action.MAIN" in actions and
                    "android.intent.category.LAUNCHER" in cats):
                    has_main = True
                    break
            if has_main or label in ("AetherSX2", "NetherSX2", "NetherSX2 Classic"):
                node.set(A + "label", VANTA_LABEL)
                changed_activities += 1

    # Harmless provenance marker.
    meta = ET.SubElement(app, "meta-data")
    meta.set(A + "name", "com.vanta.ps2.build")
    meta.set(A + "value", VANTA_BUILD)

    tree.write(manifest, encoding="utf-8", xml_declaration=True)

    assets = root / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    (assets / "vanta_build.txt").write_text(
        "VANTA PS2 Classic\n"
        f"Build: {VANTA_BUILD}\n"
        f"Upstream: {UPSTREAM}\n"
        "Core/native libraries are unmodified in R0.1.\n"
        "NetherSX2/AetherSX2/PCSX2 credits and notices remain upstream.\n",
        encoding="utf-8",
    )

    print(f"[ok] package preserved: {package_name}")
    print(f"[ok] launcher/application label: {VANTA_LABEL}")
    print(f"[ok] launcher activities updated: {changed_activities}")
    print("[ok] emulation code/native libraries untouched")

if __name__ == "__main__":
    main()
