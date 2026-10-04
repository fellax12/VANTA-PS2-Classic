#!/usr/bin/env python3
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

ANDROID_NS = "http://schemas.android.com/apk/res/android"
A = "{" + ANDROID_NS + "}"
ET.register_namespace("android", ANDROID_NS)

VANTA_LABEL = "VANTA PS2 Classic"
VANTA_BUILD = "0.3-g96-balanced-3668"
VANTA_VERSION_CODE = "366803"
VANTA_VERSION_NAME = "VANTA 0.3 G96 Balanced"
UPSTREAM = "NetherSX2 Classic 2.1 / AetherSX2 3668 core"
MARKER = "VANTA_R03_G96_BALANCED"

PRESET_METHOD = r"""
# VANTA_R03_G96_BALANCED
.method private vantaApplyR03Preset()V
    .registers 5

    invoke-static {p0}, Landroidx/preference/PreferenceManager;->getDefaultSharedPreferences(Landroid/content/Context;)Landroid/content/SharedPreferences;
    move-result-object v0

    const-string v2, "VANTA/R03G96BalancedApplied"
    const/4 v3, 0x0
    invoke-interface {v0, v2, v3}, Landroid/content/SharedPreferences;->getBoolean(Ljava/lang/String;Z)Z
    move-result v3
    if-nez v3, :vanta_r03_done

    invoke-interface {v0}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;
    move-result-object v1

    # Vulkan. Renderer ID 14 is the Vulkan renderer used by the 3668 Android frontend.
    const-string v2, "EmuCore/GS/Renderer"
    const-string v3, "14"
    invoke-interface {v1, v2, v3}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;

    # Native resolution. Aether 3668 uses an integer upscale multiplier; do not use fractional 0.75 here.
    const-string v2, "EmuCore/GS/upscale_multiplier"
    const-string v3, "1"
    invoke-interface {v1, v2, v3}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;

    # Performance-oriented download/readback mode. Per-game fallback may be required for effects which need accurate readbacks.
    const-string v2, "EmuCore/GS/HWDownloadMode"
    const-string v3, "1"
    invoke-interface {v1, v2, v3}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;

    # False means threaded presentation remains enabled in this frontend.
    const-string v2, "EmuCore/GS/DisableThreadedPresentation"
    const/4 v3, 0x0
    invoke-interface {v1, v2, v3}, Landroid/content/SharedPreferences$Editor;->putBoolean(Ljava/lang/String;Z)Landroid/content/SharedPreferences$Editor;

    # Helio G96 has only two Cortex-A76 big cores. Keep MTVU off by default so EE/GS do not compete with a third heavy VU thread.
    const-string v2, "EmuCore/Speedhacks/vuThread"
    const/4 v3, 0x0
    invoke-interface {v1, v2, v3}, Landroid/content/SharedPreferences$Editor;->putBoolean(Ljava/lang/String;Z)Landroid/content/SharedPreferences$Editor;

    # Instant VU1 remains useful specifically when MTVU is off.
    const-string v2, "EmuCore/Speedhacks/vu1Instant"
    const/4 v3, 0x1
    invoke-interface {v1, v2, v3}, Landroid/content/SharedPreferences$Editor;->putBoolean(Ljava/lang/String;Z)Landroid/content/SharedPreferences$Editor;

    # Keep timing-safe baseline. Per-game EE underclock/cycle skip comes later via GameDB/profile work.
    const-string v2, "EmuCore/Speedhacks/EECycleRate"
    const-string v3, "0"
    invoke-interface {v1, v2, v3}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;

    const-string v2, "EmuCore/Speedhacks/EECycleSkip"
    const-string v3, "0"
    invoke-interface {v1, v2, v3}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;

    # Remove post-processing overhead from the baseline. Users can re-enable manually afterwards.
    const-string v2, "EmuCore/GS/fxaa"
    const/4 v3, 0x0
    invoke-interface {v1, v2, v3}, Landroid/content/SharedPreferences$Editor;->putBoolean(Ljava/lang/String;Z)Landroid/content/SharedPreferences$Editor;

    const-string v2, "EmuCore/GS/CASMode"
    const-string v3, "0"
    invoke-interface {v1, v2, v3}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;

    const-string v2, "EmuCore/GS/VsyncEnable"
    const/4 v3, 0x0
    invoke-interface {v1, v2, v3}, Landroid/content/SharedPreferences$Editor;->putBoolean(Ljava/lang/String;Z)Landroid/content/SharedPreferences$Editor;

    const-string v2, "VANTA/R03G96BalancedApplied"
    const/4 v3, 0x1
    invoke-interface {v1, v2, v3}, Landroid/content/SharedPreferences$Editor;->putBoolean(Ljava/lang/String;Z)Landroid/content/SharedPreferences$Editor;

    invoke-interface {v1}, Landroid/content/SharedPreferences$Editor;->apply()V

:vanta_r03_done
    return-void
.end method
"""


def patch_manifest(root: Path):
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

    app.set(A + "label", VANTA_LABEL)
    doc.set(A + "versionCode", VANTA_VERSION_CODE)
    doc.set(A + "versionName", VANTA_VERSION_NAME)

    changed = 0
    for tag in ("activity", "activity-alias"):
        for node in app.findall(tag):
            label = node.attrib.get(A + "label", "")
            has_main = False
            for intent in node.findall("intent-filter"):
                actions = {x.attrib.get(A + "name", "") for x in intent.findall("action")}
                cats = {x.attrib.get(A + "name", "") for x in intent.findall("category")}
                if "android.intent.action.MAIN" in actions and "android.intent.category.LAUNCHER" in cats:
                    has_main = True
                    break
            if has_main or label in ("AetherSX2", "NetherSX2", "NetherSX2 Classic"):
                node.set(A + "label", VANTA_LABEL)
                changed += 1

    for meta in list(app.findall("meta-data")):
        if meta.attrib.get(A + "name") == "com.vanta.ps2.build":
            app.remove(meta)

    meta = ET.SubElement(app, "meta-data")
    meta.set(A + "name", "com.vanta.ps2.build")
    meta.set(A + "value", VANTA_BUILD)

    tree.write(manifest, encoding="utf-8", xml_declaration=True)
    print(f"[ok] package preserved: {package_name}")
    print(f"[ok] version: {VANTA_VERSION_NAME} ({VANTA_VERSION_CODE})")
    print(f"[ok] launcher activities updated: {changed}")


def find_main_activity(root: Path) -> Path:
    candidates = list(root.glob("smali*/xyz/aethersx2/android/MainActivity.smali"))
    if len(candidates) != 1:
        raise RuntimeError(f"Expected one MainActivity.smali, found: {candidates}")
    return candidates[0]


def patch_main_activity(root: Path) -> Path:
    path = find_main_activity(root)
    text = path.read_text(encoding="utf-8")

    if MARKER in text:
        print("[ok] R0.3 G96 Balanced preset already present")
        return path

    anchor = "# virtual methods"
    if anchor in text:
        text = text.replace(anchor, PRESET_METHOD + "\n\n" + anchor, 1)
    else:
        idx = text.find(".method public")
        if idx < 0:
            raise RuntimeError("Could not find method insertion point")
        text = text[:idx] + PRESET_METHOD + "\n\n" + text[idx:]

    pat = re.compile(
        r"(\.method[^\n]*\bonCreate\(Landroid/os/Bundle;\)V\s*\n"
        r"\s+\.(?:registers|locals)\s+\d+\s*\n)",
        re.MULTILINE,
    )
    replacement = (
        r"\1\n"
        r"    invoke-direct {p0}, Lxyz/aethersx2/android/MainActivity;->vantaApplyR03Preset()V\n"
    )
    text2, count = pat.subn(replacement, text, count=1)
    if count != 1:
        raise RuntimeError("Could not inject preset call into MainActivity.onCreate")

    path.write_text(text2, encoding="utf-8")
    print(f"[ok] injected G96 Balanced preset into {path.relative_to(root)}")
    return path


def write_metadata(root: Path):
    assets = root / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    (assets / "vanta_build.txt").write_text(
        "VANTA PS2 Classic\n"
        f"Build: {VANTA_BUILD}\n"
        f"Upstream: {UPSTREAM}\n"
        "R0.3 G96 Balanced: Vulkan, 1x Native, Disable Readbacks, Threaded Presentation, MTVU OFF, Instant VU1 ON.\n"
        "Target: Redmi Note 12S / Helio G96 / Mali-G57 MC2 without sacrificing native image quality.\n"
        "EE Cycle Rate/Skip remain safe defaults; FXAA/CAS/VSync stay off for the baseline.\n"
        "Preset is applied once per R0.3 install; later manual changes are preserved.\n"
        "Native core/libs remain untouched in this phase; Smart Affinity/ADPF require a later native-layer build.\n",
        encoding="utf-8",
    )


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_vanta_ps2_classic.py <apktool-decoded-dir>")

    root = Path(sys.argv[1]).resolve()
    patch_manifest(root)
    smali_path = patch_main_activity(root)
    write_metadata(root)

    smali = smali_path.read_text(encoding="utf-8")
    required = [
        MARKER,
        "EmuCore/GS/Renderer",
        "EmuCore/GS/upscale_multiplier",
        "EmuCore/GS/HWDownloadMode",
        "EmuCore/GS/DisableThreadedPresentation",
        "EmuCore/Speedhacks/vuThread",
        "EmuCore/Speedhacks/vu1Instant",
        "VANTA/R03G96BalancedApplied",
    ]
    missing = [x for x in required if x not in smali]
    if missing:
        raise RuntimeError(f"R0.3 preflight missing: {missing}")

    # Guard against the two R0.2 mistakes we explicitly want to remove.
    if 'const-string v3, "0.750000"' in smali:
        raise RuntimeError("R0.2 fractional 0.75x value leaked into R0.3")

    mtvu_block = (
        'const-string v2, "EmuCore/Speedhacks/vuThread"\n'
        '    const/4 v3, 0x0'
    )
    if mtvu_block not in smali:
        raise RuntimeError("R0.3 MTVU-off invariant missing")

    print("[ok] VANTA PS2 Classic R0.3 G96 Balanced patch complete")


if __name__ == "__main__":
    main()
