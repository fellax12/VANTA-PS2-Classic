#!/usr/bin/env python3
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET

ANDROID_NS = "http://schemas.android.com/apk/res/android"
APP_NS = "http://schemas.android.com/apk/res-auto"
A = "{" + ANDROID_NS + "}"
P = "{" + APP_NS + "}"
ET.register_namespace("android", ANDROID_NS)
ET.register_namespace("app", APP_NS)

BUILD = "0.4-performance-lab-3668"
VERSION_CODE = "366804"
VERSION_NAME = "VANTA 0.4 Performance Lab"
LABEL = "VANTA PS2"
MARKER_DEFAULTS = "VANTA_R04_DEFAULTS"
MARKER_SETTINGS = "VANTA_R04_SETTINGS_CENTER"

FRIENDLY = {
    "EmuCore/GS/Renderer": ("Renderizador (GPU)", "Vulkan costuma render melhor em Mali. Use OpenGL se um jogo apresentar glitch ou travamento específico."),
    "EmuCore/GS/upscale_multiplier": ("Resolução interna", "1× é a base de desempenho. Aumente só quando a GPU tiver folga."),
    "EmuCore/GS/HWDownloadMode": ("Readbacks da GPU", "Preciso prioriza compatibilidade. Rápido pode dar muito FPS em alguns jogos; volte ao Preciso se efeitos sumirem."),
    "EmuCore/GS/ThreadedPresentation": ("Apresentação em thread (Mali)", "Move a apresentação Vulkan para uma thread separada. Pode ajudar em dispositivos Mali quando o GS não é o gargalo principal."),
    "EmuCore/GS/texture_preloading": ("Pré-carregar texturas", "Full/Hash Cache usa mais memória, mas pode reduzir stutter e recompilações em alguns jogos."),
    "EmuCore/GS/accurate_blending_unit": ("Precisão de blending", "Basic é o ponto seguro. Minimum reduz trabalho gráfico, mas pode quebrar efeitos."),
    "EmuCore/GS/MaxAnisotropy": ("Filtro anisotrópico", "Melhora nitidez de superfícies em ângulo. Custa GPU e raramente ajuda desempenho."),
    "EmuCore/GS/filter": ("Filtro de textura", "Bilinear PS2 mantém aparência original. Forced pode suavizar mais, com pequeno custo."),
    "EmuCore/GS/mipmap_hw": ("Mipmapping", "Automático é o recomendado. Alterar pode corrigir ou quebrar texturas em jogos específicos."),
    "EmuCore/GS/UserHacks_TriFilter": ("Filtro trilinear", "Mantenha automático salvo quando um jogo específico pedir outra opção."),
    "EmuCore/Speedhacks/EECycleRate": ("EE Cycle Rate • underclock", "0 = PS2 normal. -1/-2 reduzem carga da CPU emulada, mas podem alterar timing e física."),
    "EmuCore/Speedhacks/EECycleSkip": ("EE Cycle Skip • pulo de ciclos", "0 = correto. Valores positivos pulam ciclos e podem ajudar hardware fraco, com risco de quebrar jogos."),
    "EmuCore/AffinityControlMode": ("Prioridade dos núcleos • Affinity", "Define a ordem EE/GS/VU nos núcleos fortes. No Helio G96 há apenas dois Cortex-A76."),
    "EmuCore/Speedhacks/vuThread": ("MTVU • VU1 em thread separada", "Pode acelerar jogos com VU pesado; no G96 também pode disputar os dois núcleos grandes. Teste por jogo."),
    "EmuCore/Speedhacks/vu1Instant": ("Instant VU1", "Otimização do VU1 útil principalmente quando MTVU está desligado."),
    "EmuCore/Speedhacks/fastCDVD": ("Leitura rápida do disco", "Reduz esperas do CD/DVD emulado. Pode causar incompatibilidade em jogos que dependem de timing."),
    "EmuCore/CPU/Recompiler/EnableFastmem": ("Fastmem ARM64", "Caminho rápido de memória do recompilador. Normalmente deve permanecer ligado."),
    "EmuCore/GS/SkipDuplicateFrames": ("Pular frames duplicados", "Pode reduzir trabalho quando o jogo repete frames. Útil para teste A/B; nem todo jogo ganha."),
    "EmuCore/GS/paltex": ("Paletas na GPU", "Move conversão de paleta da CPU para a GPU. Pode ajudar casos específicos, mas costuma ser mais lento globalmente."),
    "EmuCore/GS/OsdShowFPS": ("FPS / VPS", "Mostra frames internos e frequência de vídeo."),
    "EmuCore/GS/OsdShowSpeed": ("Velocidade %", "100% significa que a emulação acompanha o tempo real do PS2."),
    "EmuCore/GS/OsdShowCPU": ("CPU • EE / GS / VU", "Exibe o tempo das threads principais e ajuda a localizar gargalos."),
    "EmuCore/GS/OsdShowGPU": ("GPU", "Mostra tempo/carga da GPU. Se houver folga, reduzir resolução provavelmente não é a solução."),
    "EmuCore/GS/OsdShowFrameTimes": ("Frame times", "Mostra média e pior frame. Excelente para localizar microtravadas."),
    "EmuCore/GS/OsdShowResolution": ("Resolução", "Mostra a resolução interna atual no OSD."),
    "UI/Theme": ("Tema VANTA", "Obsidian = escuro/grafite. Ivory = claro/marfim. A paleta é aplicada ao aplicativo inteiro."),
}

CATEGORY_TITLES = {
    "system_preferences.xml": ["CPU, EE & VU", "VELOCIDADE & LIMITES"],
    "graphics_preferences.xml": ["GPU & RENDERIZAÇÃO", "TELA & PROPORÇÃO", "PÓS-PROCESSAMENTO", "TEXTURAS"],
    "general_preferences.xml": ["INTERFACE & JOGABILIDADE", "DIAGNÓSTICO NA TELA"],
    "advanced_preferences.xml": ["NÚCLEO • AVANÇADO", "GRÁFICOS • AVANÇADO", "DEBUG & LOGS"],
    "system_game_settings_preferences.xml": ["CPU, EE & VU • DESTE JOGO", "VELOCIDADE • DESTE JOGO"],
    "graphics_game_settings_preferences.xml": ["GPU & RENDERIZAÇÃO • DESTE JOGO", "TELA • DESTE JOGO", "PÓS-PROCESSAMENTO • DESTE JOGO", "TEXTURAS • DESTE JOGO"],
    "general_game_settings_preferences.xml": ["PERFIS • DESTE JOGO", "CONTROLE • DESTE JOGO", "INTERFACE • DESTE JOGO", "DIAGNÓSTICO • DESTE JOGO"],
}


def find_smali(root: Path, rel: str) -> Path:
    hits = list(root.glob(f"smali*/{rel}"))
    if len(hits) != 1:
        raise RuntimeError(f"Expected one {rel}, found {hits}")
    return hits[0]


def patch_manifest(root: Path):
    p = root / "AndroidManifest.xml"
    tree = ET.parse(p)
    doc = tree.getroot()
    app = doc.find("application")
    if app is None:
        raise RuntimeError("manifest application not found")

    app.set(A + "label", LABEL)
    doc.set(A + "versionCode", VERSION_CODE)
    doc.set(A + "versionName", VERSION_NAME)

    for node in list(app.findall("activity")) + list(app.findall("activity-alias")):
        name = node.attrib.get(A + "name", "")
        if name.endswith("MainActivity"):
            node.set(A + "label", LABEL)

    activity_name = "xyz.aethersx2.android.VantaCenterActivity"
    exists = any(n.attrib.get(A + "name") == activity_name for n in app.findall("activity"))
    if not exists:
        a = ET.SubElement(app, "activity")
        a.set(A + "name", activity_name)
        a.set(A + "exported", "false")
        a.set(A + "theme", "@style/AppTheme.NoActionBar")

    for meta in list(app.findall("meta-data")):
        if meta.attrib.get(A + "name") == "com.vanta.ps2.build":
            app.remove(meta)
    meta = ET.SubElement(app, "meta-data")
    meta.set(A + "name", "com.vanta.ps2.build")
    meta.set(A + "value", BUILD)

    tree.write(p, encoding="utf-8", xml_declaration=True)
    print("[ok] manifest / VantaCenterActivity")


DEFAULTS_METHOD = r'''
# VANTA_R04_DEFAULTS
.method private vantaApplyR04Defaults()V
    .registers 5

    invoke-static {p0}, Landroidx/preference/PreferenceManager;->getDefaultSharedPreferences(Landroid/content/Context;)Landroid/content/SharedPreferences;
    move-result-object v0

    const-string v2, "VANTA/R04DefaultsApplied"
    const/4 v3, 0x0
    invoke-interface {v0, v2, v3}, Landroid/content/SharedPreferences;->getBoolean(Ljava/lang/String;Z)Z
    move-result v3
    if-nez v3, :vanta_r04_defaults_done

    invoke-interface {v0}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;
    move-result-object v1

    const-string v2, "EmuCore/GS/Renderer"
    const-string v3, "14"
    invoke-interface {v1, v2, v3}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;

    const-string v2, "EmuCore/GS/upscale_multiplier"
    const-string v3, "1.000000"
    invoke-interface {v1, v2, v3}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;

    const-string v2, "EmuCore/GS/HWDownloadMode"
    const-string v3, "1"
    invoke-interface {v1, v2, v3}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;

    const-string v2, "EmuCore/GS/ThreadedPresentation"
    const/4 v3, 0x1
    invoke-interface {v1, v2, v3}, Landroid/content/SharedPreferences$Editor;->putBoolean(Ljava/lang/String;Z)Landroid/content/SharedPreferences$Editor;

    const-string v2, "EmuCore/Speedhacks/vuThread"
    const/4 v3, 0x0
    invoke-interface {v1, v2, v3}, Landroid/content/SharedPreferences$Editor;->putBoolean(Ljava/lang/String;Z)Landroid/content/SharedPreferences$Editor;

    const-string v2, "EmuCore/Speedhacks/vu1Instant"
    const/4 v3, 0x1
    invoke-interface {v1, v2, v3}, Landroid/content/SharedPreferences$Editor;->putBoolean(Ljava/lang/String;Z)Landroid/content/SharedPreferences$Editor;

    const-string v2, "EmuCore/AffinityControlMode"
    const-string v3, "7"
    invoke-interface {v1, v2, v3}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;

    const-string v2, "EmuCore/Speedhacks/EECycleRate"
    const-string v3, "0"
    invoke-interface {v1, v2, v3}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;

    const-string v2, "EmuCore/Speedhacks/EECycleSkip"
    const-string v3, "0"
    invoke-interface {v1, v2, v3}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;

    const-string v2, "EmuCore/CPU/Recompiler/EnableFastmem"
    const/4 v3, 0x1
    invoke-interface {v1, v2, v3}, Landroid/content/SharedPreferences$Editor;->putBoolean(Ljava/lang/String;Z)Landroid/content/SharedPreferences$Editor;

    const-string v2, "EmuCore/GS/texture_preloading"
    const-string v3, "2"
    invoke-interface {v1, v2, v3}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;

    const-string v2, "EmuCore/GS/accurate_blending_unit"
    const-string v3, "1"
    invoke-interface {v1, v2, v3}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;

    const-string v2, "EmuCore/WarnAboutUnsafeSettings"
    const/4 v3, 0x1
    invoke-interface {v1, v2, v3}, Landroid/content/SharedPreferences$Editor;->putBoolean(Ljava/lang/String;Z)Landroid/content/SharedPreferences$Editor;

    const-string v2, "UI/Theme"
    const-string v3, "dark"
    invoke-interface {v1, v2, v3}, Landroid/content/SharedPreferences$Editor;->putString(Ljava/lang/String;Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;

    const-string v2, "VANTA/R04DefaultsApplied"
    const/4 v3, 0x1
    invoke-interface {v1, v2, v3}, Landroid/content/SharedPreferences$Editor;->putBoolean(Ljava/lang/String;Z)Landroid/content/SharedPreferences$Editor;

    invoke-interface {v1}, Landroid/content/SharedPreferences$Editor;->apply()V

:vanta_r04_defaults_done
    return-void
.end method
'''


def patch_main_activity(root: Path):
    p = find_smali(root, "xyz/aethersx2/android/MainActivity.smali")
    s = p.read_text(encoding="utf-8")
    if MARKER_DEFAULTS not in s:
        anchor = "# virtual methods"
        if anchor not in s:
            raise RuntimeError("MainActivity virtual methods anchor not found")
        s = s.replace(anchor, DEFAULTS_METHOD + "\n\n" + anchor, 1)
        pat = re.compile(r"(\.method[^\n]*\bonCreate\(Landroid/os/Bundle;\)V.*?\.end method)", re.S)
        m = pat.search(s)
        if not m:
            raise RuntimeError("MainActivity onCreate not found")
        block = m.group(1)
        lines = block.splitlines()
        super_idx = next((i for i, x in enumerate(lines) if "invoke-super" in x and "->onCreate(Landroid/os/Bundle;)V" in x), None)
        if super_idx is None:
            reg_idx = next((i for i, x in enumerate(lines) if x.strip().startswith((".registers", ".locals"))), None)
            if reg_idx is None:
                raise RuntimeError("MainActivity onCreate insertion point missing")
            super_idx = reg_idx
        lines.insert(super_idx + 1, "\n    invoke-direct {p0}, Lxyz/aethersx2/android/MainActivity;->vantaApplyR04Defaults()V")
        new_block = "\n".join(lines)
        s = s[:m.start()] + new_block + s[m.end():]
    p.write_text(s, encoding="utf-8")
    print("[ok] R0.4 balanced defaults")


SETTINGS_METHOD = r'''
# VANTA_R04_SETTINGS_CENTER
.method private vantaOpenCenterIfNeeded()V
    .registers 5

    invoke-virtual {p0}, Landroid/app/Activity;->getIntent()Landroid/content/Intent;
    move-result-object v0

    const-string v1, "vanta_bypass"
    const/4 v2, 0x0
    invoke-virtual {v0, v1, v2}, Landroid/content/Intent;->getBooleanExtra(Ljava/lang/String;Z)Z
    move-result v0
    if-nez v0, :vanta_settings_done

    new-instance v0, Landroid/content/Intent;
    invoke-direct {v0}, Landroid/content/Intent;-><init>()V
    invoke-virtual {p0}, Landroid/content/Context;->getPackageName()Ljava/lang/String;
    move-result-object v1
    const-string v2, "xyz.aethersx2.android.VantaCenterActivity"
    invoke-virtual {v0, v1, v2}, Landroid/content/Intent;->setClassName(Ljava/lang/String;Ljava/lang/String;)Landroid/content/Intent;
    invoke-virtual {p0, v0}, Landroid/app/Activity;->startActivity(Landroid/content/Intent;)V
    invoke-virtual {p0}, Landroid/app/Activity;->finish()V

:vanta_settings_done
    return-void
.end method
'''


def patch_settings_activity(root: Path):
    p = find_smali(root, "xyz/aethersx2/android/SettingsActivity.smali")
    s = p.read_text(encoding="utf-8")
    if MARKER_SETTINGS not in s:
        anchor = "# virtual methods"
        if anchor not in s:
            raise RuntimeError("SettingsActivity virtual methods anchor not found")
        s = s.replace(anchor, SETTINGS_METHOD + "\n\n" + anchor, 1)
        pat = re.compile(r"(\.method[^\n]*\bonCreate\(Landroid/os/Bundle;\)V.*?\.end method)", re.S)
        m = pat.search(s)
        if not m:
            raise RuntimeError("SettingsActivity onCreate not found")
        block = m.group(1)
        pos = block.rfind("    return-void")
        if pos < 0:
            raise RuntimeError("SettingsActivity onCreate return not found")
        block = block[:pos] + "    invoke-direct {p0}, Lxyz/aethersx2/android/SettingsActivity;->vantaOpenCenterIfNeeded()V\n\n" + block[pos:]
        s = s[:m.start()] + block + s[m.end():]
    p.write_text(s, encoding="utf-8")
    print("[ok] Settings -> VANTA Performance Center redirect")


def make_scope_category(game: bool):
    cat = ET.Element("PreferenceCategory")
    cat.set(P + "iconSpaceReserved", "false")
    cat.set(P + "title", "JOGO • SOMENTE ESTE TÍTULO" if game else "GLOBAL • TODOS OS JOGOS")
    info = ET.SubElement(cat, "Preference")
    info.set(P + "iconSpaceReserved", "false")
    info.set(P + "selectable", "false")
    info.set(P + "title", "Escopo desta tela")
    info.set(P + "summary", "Estas opções afetam somente este jogo. Ajustes sem valor usam o global." if game else "Estas opções afetam todos os jogos. Para exceções, use Propriedades no jogo.")
    return cat


def patch_preference_file(path: Path, game: bool):
    tree = ET.parse(path)
    root = tree.getroot()
    root.insert(0, make_scope_category(game))

    category_titles = CATEGORY_TITLES.get(path.name, [])
    categories = [x for x in list(root) if x.tag.endswith("PreferenceCategory")][1:]
    for idx, cat in enumerate(categories):
        if idx < len(category_titles):
            cat.set(P + "title", category_titles[idx])

    for node in root.iter():
        key = node.attrib.get(P + "key")
        if key and key in FRIENDLY:
            title, summary = FRIENDLY[key]
            node.set(P + "title", title)
            node.set(P + "summary", summary)
    tree.write(path, encoding="utf-8", xml_declaration=True)


def patch_preferences(root: Path):
    global_files = [
        "system_preferences.xml", "graphics_preferences.xml", "general_preferences.xml", "advanced_preferences.xml",
        "audio_preferences.xml", "memory_card_preferences.xml", "controller_preferences.xml",
    ]
    game_files = [
        "system_game_settings_preferences.xml", "graphics_game_settings_preferences.xml", "general_game_settings_preferences.xml",
        "advanced_game_settings_preferences.xml", "audio_game_settings_preferences.xml", "achievements_game_settings_preferences.xml",
    ]
    xdir = root / "res/xml"
    for name in global_files:
        p = xdir / name
        if p.exists():
            patch_preference_file(p, False)
    for name in game_files:
        p = xdir / name
        if p.exists():
            patch_preference_file(p, True)
    print("[ok] preference scope banners + friendly labels")


def patch_arrays(root: Path):
    p = root / "res/values/arrays.xml"
    tree = ET.parse(p)
    r = tree.getroot()

    def replace_array(name, values):
        arr = next((x for x in r if x.tag == "string-array" and x.attrib.get("name") == name), None)
        if arr is None:
            return False
        arr.clear()
        arr.set("name", name)
        for v in values:
            item = ET.SubElement(arr, "item")
            item.text = v
        return True

    replace_array("theme_entries", ["VANTA Obsidian", "VANTA Ivory"])
    replace_array("theme_values", ["dark", "light"])
    replace_array("settings_tabs", ["Geral", "CPU / Sistema", "GPU / Gráficos", "Áudio", "Memory Cards", "Biblioteca", "BIOS", "Conquistas", "Avançado"])
    replace_array("affinity_control_entries", [
        "Desligado",
        "EE → VU → GS",
        "EE → GS → VU",
        "VU → EE → GS",
        "VU → GS → EE",
        "GS → EE → VU",
        "GS → VU → EE",
        "Performance Cores • automático",
    ])
    tree.write(p, encoding="utf-8", xml_declaration=True)
    print("[ok] arrays: two VANTA themes / clearer tabs / affinity labels")


def patch_palette_dir(values_dir: Path, palette: dict):
    values_dir.mkdir(parents=True, exist_ok=True)
    found = set()
    xmls = list(values_dir.glob("*.xml"))
    for path in xmls:
        try:
            tree = ET.parse(path)
        except ET.ParseError:
            continue
        root = tree.getroot()
        changed = False
        for node in root.findall("color"):
            name = node.attrib.get("name")
            if name in palette:
                node.text = palette[name]
                found.add(name)
                changed = True
        if changed:
            tree.write(path, encoding="utf-8", xml_declaration=True)

    missing = [k for k in palette if k not in found]
    if missing:
        target = values_dir / "vanta_palette.xml"
        resources = ET.Element("resources")
        for k in missing:
            n = ET.SubElement(resources, "color", {"name": k})
            n.text = palette[k]
        ET.ElementTree(resources).write(target, encoding="utf-8", xml_declaration=True)


def patch_theme_colors(root: Path):
    light = {
        "colorAccent": "#FFC9502C",
        "colorMainBackground": "#FFF5F1E9",
        "colorNavigation": "#FFF5F1E9",
        "colorPrimary": "#FF24282F",
        "colorPrimaryDark": "#FF14171C",
        "colorSurface": "#FFFFFDF8",
        "colorToolbarBackground": "#FFFFFDF8",
    }
    dark = {
        "colorAccent": "#FFFF7446",
        "colorMainBackground": "#FF0A0C10",
        "colorNavigation": "#FF0A0C10",
        "colorPrimary": "#FF12151B",
        "colorPrimaryDark": "#FF080A0D",
        "colorSurface": "#FF12151B",
        "colorToolbarBackground": "#FF12151B",
    }
    patch_palette_dir(root / "res/values", light)
    patch_palette_dir(root / "res/values-night", dark)
    print("[ok] global VANTA Obsidian / Ivory palettes")


def patch_navigation(root: Path):
    p = root / "res/menu/menu_main_navigation.xml"
    if not p.exists():
        return
    tree = ET.parse(p)
    r = tree.getroot()
    replacements = {
        "@id/action_settings": "Central VANTA",
        "@id/action_controller_settings": "Controle & mapeamento",
        "@id/action_reset_settings": "Restaurar configurações",
        "@id/action_transfer_data": "Backup & transferência",
        "@id/action_scan_for_new_games": "Procurar novos jogos",
        "@id/action_rescan_all_games": "Reescanear biblioteca",
        "@id/action_save_state_cleanup": "Gerenciar save states",
        "@id/action_download_covers": "Baixar capas",
        "@id/action_change_background": "Plano de fundo",
        "@id/action_show_faq": "Ajuda / FAQ",
        "@id/action_show_version": "Sobre o VANTA",
    }
    for item in r.iter("item"):
        rid = item.attrib.get(A + "id")
        if rid in replacements:
            item.set(A + "title", replacements[rid])
    tree.write(p, encoding="utf-8", xml_declaration=True)
    print("[ok] clearer main navigation")


def write_metadata(root: Path):
    assets = root / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    (assets / "vanta_build.txt").write_text(
        "VANTA PS2\n"
        f"Build: {BUILD}\n"
        "Base: NetherSX2 Classic 2.1 / AetherSX2 3668\n"
        "R0.4: VANTA Performance Center, global scope banners, per-game scope banners, Obsidian/Ivory themes, G96 profiles and Performance Lab.\n"
        "Default G96 baseline: Vulkan, 1x, Disable Readbacks, Threaded Presentation, MTVU OFF, Instant VU1 ON, Performance Cores, Fastmem.\n"
        "Native Smart Affinity / ADPF / Thermal Headroom are NOT claimed in R0.4 and remain future native-layer work.\n",
        encoding="utf-8",
    )


def preflight(root: Path):
    main = find_smali(root, "xyz/aethersx2/android/MainActivity.smali").read_text(encoding="utf-8")
    settings = find_smali(root, "xyz/aethersx2/android/SettingsActivity.smali").read_text(encoding="utf-8")
    required_main = [MARKER_DEFAULTS, "EmuCore/GS/ThreadedPresentation", "1.000000", "EmuCore/AffinityControlMode"]
    required_settings = [MARKER_SETTINGS, "VantaCenterActivity", "vanta_bypass"]
    missing = [x for x in required_main if x not in main] + [x for x in required_settings if x not in settings]
    if missing:
        raise RuntimeError(f"preflight missing: {missing}")
    arrays = (root / "res/values/arrays.xml").read_text(encoding="utf-8")
    for x in ["VANTA Obsidian", "VANTA Ivory", "Performance Cores"]:
        if x not in arrays:
            raise RuntimeError(f"arrays missing {x}")
    print("[ok] R0.4 preflight")


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_vanta_ps2_r04.py <apktool-decoded-dir>")
    root = Path(sys.argv[1]).resolve()
    patch_manifest(root)
    patch_main_activity(root)
    patch_settings_activity(root)
    patch_preferences(root)
    patch_arrays(root)
    patch_theme_colors(root)
    patch_navigation(root)
    write_metadata(root)
    preflight(root)
    print("[ok] VANTA PS2 R0.4 Performance Lab patch complete")


if __name__ == "__main__":
    main()
