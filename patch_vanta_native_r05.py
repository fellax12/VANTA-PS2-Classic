#!/usr/bin/env python3
from pathlib import Path
import re
import sys

PIN = "d383b3636947565d9201f81e32178d0288623d8d"
MARKER = "VANTA_NATIVE_R05_NIGHT_GAME"


def fail(msg: str):
    raise RuntimeError(msg)


def read(path: Path) -> str:
    if not path.is_file():
        fail(f"missing file: {path}")
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str):
    path.write_text(text, encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        fail(f"{label}: expected 1 occurrence, found {count}")
    return text.replace(old, new, 1)


def regex_once(text: str, pattern: str, repl: str, label: str, flags=0) -> str:
    out, count = re.subn(pattern, repl, text, count=1, flags=flags)
    if count != 1:
        fail(f"{label}: expected 1 regex match, found {count}")
    return out


def patch_performance_tab(root: Path):
    p = root / "platforms/android/app/src/main/java/com/armsx2/ui/settings/PerformanceTab.kt"
    s = read(p)
    if MARKER in s:
        print("[skip] PerformanceTab already patched")
        return

    anchor = '''    Column(
        modifier = Modifier
            .fillMaxWidth(),
    ) {
        // Prominent latency preset: zero queued GS frames keeps the emulated CPU
'''

    block = r'''    Column(
        modifier = Modifier
            .fillMaxWidth(),
    ) {
        // VANTA_NATIVE_R05_NIGHT_GAME
        CollapsibleSection("VANTA • OTIMIZAÇÃO RÁPIDA", initiallyExpanded = true) {
            HelpText(
                "Escolha pelo sintoma, não pelo nome técnico. Os perfis abaixo preservam 1× Native e ativam " +
                    "telemetria para você comparar a mesma cena. Use em escopo JOGO sempre que possível."
            )
            SegmentedGridRow(
                label = "Qual é o gargalo?",
                options = listOf(
                    "Equilibrado G96",
                    "CPU / VU pesado",
                    "GPU / sincronização",
                    "Mali FB Fetch • LAB",
                    "LIMITE • instável",
                    "Compatibilidade",
                ),
                selectedIndex = -1,
                columns = 2,
                description = "RE4/GoW com GPU folgada: CPU/VU. Quedas com RB/efeitos: GPU/sincronização. " +
                    "Mali FB Fetch e LIMITE são experimentais e podem causar glitches.",
                onChange = { profile ->
                    val adpfOn = profile != 5
                    com.armsx2.runtime.MainActivityRuntime.prefs.edit {
                        putBoolean("ui.adpf", adpfOn)
                        // Boost sustentado pode limitar pico; deixamos desligado nos perfis VANTA.
                        putBoolean("ui.sustainedPerf", false)
                    }
                    runCatching { kr.co.iefriends.pcsx2.NativeApp.setAdpfEnabled(adpfOn) }

                    val telemetry = s.osd.copy(
                        osdShowFps = true,
                        osdShowVps = true,
                        osdShowSpeed = true,
                        osdShowCpu = true,
                        osdShowGpu = true,
                        osdShowFrameTimes = true,
                        osdShowResolution = true,
                    )

                    // Base comum: qualidade nativa, Vulkan, shader cache e recursos ARM64 rápidos.
                    val common = s.copy(
                        output = s.output.copy(
                            renderer = "vulkan",
                            upscaleFloat = 1.0f,
                            affinityMode = 7,
                        ),
                        cpu = s.cpu.copy(
                            eeCycleRate = 0,
                            eeCycleSkip = 0,
                            mtvu = true,
                            vu1Instant = true,
                            vuFlagHack = true,
                            intcStat = true,
                            waitLoop = true,
                            fastCDVD = false,
                            vuNeonFusions = true,
                            vuDeferredWrites = false,
                            vuSkipStallSim = false,
                            recEE = true,
                            recIOP = true,
                            recVU0 = true,
                            recVU1 = true,
                            enableFastmem = true,
                            vu1InlineFmacStall = false,
                            vu1CrossBlockPState = false,
                            vu1InlineDrainTestPipes = false,
                            vu1FmacInstanceRouting = false,
                        ),
                        graphics = s.graphics.copy(
                            hardwareDownloadMode = 0,
                            accurateBlendingUnit = 1,
                            hwMipmap = true,
                            texturePreloading = 2,
                            fxaa = false,
                        ),
                        display = s.display.copy(
                            disableFramebufferFetch = false,
                            hwRov = false,
                            hwAa1 = false,
                            hwAccurateAlphaTest = false,
                            coalesceRenderPasses = true,
                            forceMaliFbFetch = false,
                            useAngleOpenGL = false,
                            gsBackThreadMode = 0,
                            disableShaderCache = false,
                            vsyncEnable = false,
                        ),
                        hwFixes = s.hwFixes.copy(
                            gpuProfile = 1, // Mali
                            vsyncQueueSize = 2,
                            spinGpuReadbacks = false,
                            spinCpuReadbacks = false,
                        ),
                        audio = s.audio.copy(
                            spu2NeonReverb = true,
                            spu2LightweightMix = false,
                        ),
                        emuCore = s.emuCore.copy(skipDuplicateFrames = true),
                        osd = telemetry,
                    )

                    val updated = when (profile) {
                        // Boa primeira tentativa: zero hacks de timing; deixa EAS trabalhar no tier forte.
                        0 -> common

                        // Para cenas como RE4/GoW onde VU/EE dominam e a GPU está sobrando.
                        1 -> common.copy(
                            output = common.output.copy(affinityMode = 3), // VU > EE > GS
                            cpu = common.cpu.copy(
                                eeCycleRate = -1,
                                mtvu = true,
                                vu1Instant = false,
                                vu1InlineFmacStall = true,
                                vu1CrossBlockPState = true,
                                vu1InlineDrainTestPipes = true,
                            ),
                        )

                        // Mantém correção visual, mas torna GPU->CPU readback não bloqueante e separa GS.
                        2 -> common.copy(
                            graphics = common.graphics.copy(hardwareDownloadMode = 5), // Asynchronous
                            display = common.display.copy(gsBackThreadMode = 1),
                        )

                        // Teste MediaTek/Mali: evita barreira por primitiva quando o driver suporta ROAA correto.
                        // Pode gerar textura preta/ausente em drivers Mali afetados: use apenas A/B.
                        3 -> common.copy(
                            graphics = common.graphics.copy(hardwareDownloadMode = 5),
                            display = common.display.copy(
                                gsBackThreadMode = 1,
                                forceMaliFbFetch = true,
                                coalesceRenderPasses = true,
                            ),
                        )

                        // Tudo que hoje é experimental no caminho VU/GS. É propositalmente agressivo.
                        4 -> common.copy(
                            output = common.output.copy(affinityMode = 3),
                            cpu = common.cpu.copy(
                                eeCycleRate = -1,
                                eeCycleSkip = 1,
                                mtvu = true,
                                vu1Instant = false,
                                vuNeonFusions = true,
                                vuDeferredWrites = true,
                                vuSkipStallSim = true,
                                vu1InlineFmacStall = true,
                                vu1CrossBlockPState = true,
                                vu1InlineDrainTestPipes = true,
                                vu1FmacInstanceRouting = true,
                            ),
                            graphics = common.graphics.copy(hardwareDownloadMode = 5),
                            display = common.display.copy(
                                gsBackThreadMode = 1,
                                coalesceRenderPasses = true,
                            ),
                            audio = common.audio.copy(
                                spu2NeonReverb = true,
                                spu2LightweightMix = true,
                            ),
                        )

                        // Volta para um caminho conservador sem abandonar Native/Vulkan.
                        else -> common.copy(
                            output = common.output.copy(renderer = "auto", affinityMode = 7),
                            cpu = common.cpu.copy(
                                eeCycleRate = 0,
                                eeCycleSkip = 0,
                                mtvu = true,
                                vu1Instant = true,
                                vuDeferredWrites = false,
                                vuSkipStallSim = false,
                                vu1InlineFmacStall = false,
                                vu1CrossBlockPState = false,
                                vu1InlineDrainTestPipes = false,
                                vu1FmacInstanceRouting = false,
                            ),
                            graphics = common.graphics.copy(hardwareDownloadMode = 0),
                            display = common.display.copy(
                                coalesceRenderPasses = false,
                                forceMaliFbFetch = false,
                                gsBackThreadMode = 0,
                            ),
                        )
                    }
                    apply(updated)
                },
            )
            HelpText(
                "Regra VANTA: GPU abaixo de ~80% + EE/VU altos = não reduza resolução. " +
                    "RB/spikes = teste Async. Perfil LIMITE pode quebrar timing/gráficos; reinicie o jogo após mudar opções marcadas como restart."
            )
        }
        SettingsDivider()

        // Prominent latency preset: zero queued GS frames keeps the emulated CPU
'''
    s = replace_once(s, anchor, block, "insert VANTA profiles")

    old_tail = '''            ToggleRow(str("perf.hack.deferVuWrites"), s.cpu.vuDeferredWrites, description = str("perf.hack.deferVuWrites.desc")) { apply(s.copy(cpu = s.cpu.copy(vuDeferredWrites = it))) }
            ToggleRow(str("perf.hack.skipDupeFrames"), s.emuCore.skipDuplicateFrames, description = str("perf.hack.skipDupeFrames.desc")) { apply(s.copy(emuCore = s.emuCore.copy(skipDuplicateFrames = it))) }
'''
    new_tail = '''            ToggleRow(str("perf.hack.deferVuWrites"), s.cpu.vuDeferredWrites, description = str("perf.hack.deferVuWrites.desc")) { apply(s.copy(cpu = s.cpu.copy(vuDeferredWrites = it))) }
            ToggleRow("VANTA • Inline FMAC Stall", s.cpu.vu1InlineFmacStall,
                description = "Substitui chamadas de stall FMAC por código inline quando a análise do JIT considera seguro. Teste por jogo.") {
                apply(s.copy(cpu = s.cpu.copy(vu1InlineFmacStall = it)))
            }
            ToggleRow("VANTA • Cross-block VU state", s.cpu.vu1CrossBlockPState,
                description = "Propaga estado do pipeline VU entre blocos JIT para reduzir gates/stalls desnecessários.") {
                apply(s.copy(cpu = s.cpu.copy(vu1CrossBlockPState = it)))
            }
            ToggleRow("VANTA • Inline VU drain", s.cpu.vu1InlineDrainTestPipes,
                description = "Evita call/return e invalidação de cache em drains FMAC que o pre-walk prova serem simples.") {
                apply(s.copy(cpu = s.cpu.copy(vu1InlineDrainTestPipes = it)))
            }
            ToggleRow("VANTA • FMAC instance routing • LAB", s.cpu.vu1FmacInstanceRouting,
                description = "Roteamento experimental de 4 slots de flags FMAC. Pode ser rápido e pode quebrar jogos: use A/B.") {
                apply(s.copy(cpu = s.cpu.copy(vu1FmacInstanceRouting = it)))
            }
            ToggleRow(str("perf.hack.skipDupeFrames"), s.emuCore.skipDuplicateFrames, description = str("perf.hack.skipDupeFrames.desc")) { apply(s.copy(emuCore = s.emuCore.copy(skipDuplicateFrames = it))) }
'''
    s = replace_once(s, old_tail, new_tail, "expose VU JIT lab")
    write(p, s)
    print("[ok] PerformanceTab VANTA profiles + VU JIT lab")


def patch_settings_scope(root: Path):
    p = root / "platforms/android/app/src/main/java/com/armsx2/ui/settingshub/SettingsScreen.kt"
    s = read(p)
    if "VANTA_SCOPE_BANNER_R05" in s:
        print("[skip] SettingsScreen already patched")
        return
    anchor = '''                if (scopeContext != null) {
                    // Global ↔ Per-Game switch. Re-load()s the ViewModel for the chosen scope, which
'''
    block = '''                // VANTA_SCOPE_BANNER_R05 — impossível confundir Global com configuração do jogo.
                Box(
                    Modifier
                        .fillMaxWidth()
                        .padding(horizontal = 8.dp, vertical = 4.dp)
                        .background(
                            if (scopeGame == null) MaterialTheme.colorScheme.surfaceVariant
                            else MaterialTheme.colorScheme.primaryContainer,
                            RoundedCornerShape(14.dp),
                        )
                        .padding(horizontal = 14.dp, vertical = 10.dp),
                ) {
                    Text(
                        if (scopeGame == null) "GLOBAL • TODOS OS JOGOS"
                        else "JOGO • SOMENTE ${scopeGame?.title?.uppercase() ?: "ESTE JOGO"}",
                        style = MaterialTheme.typography.titleMedium,
                        color = if (scopeGame == null) MaterialTheme.colorScheme.onSurfaceVariant
                        else MaterialTheme.colorScheme.onPrimaryContainer,
                    )
                }
                if (scopeContext != null) {
                    // Global ↔ Per-Game switch. Re-load()s the ViewModel for the chosen scope, which
'''
    s = replace_once(s, anchor, block, "scope banner")
    write(p, s)
    print("[ok] Settings scope banner")


def patch_theme(root: Path):
    p = root / "platforms/android/app/src/main/java/com/armsx2/ui/theme/Theme.kt"
    s = read(p)
    if "VANTA_THEME_R05" in s:
        print("[skip] Theme already patched")
        return

    s = replace_once(s, "val mode = mutableStateOf(ThemeMode.System)", "val mode = mutableStateOf(ThemeMode.Orange)", "default theme state")
    s = replace_once(s, "getString(PreferenceKey, ThemeMode.System.name)", "getString(PreferenceKey, ThemeMode.Orange.name)", "default theme pref")
    s = replace_once(s, "?: ThemeMode.Blue", "?: ThemeMode.Orange", "theme fallback")

    day_pat = r'''private val DayScheme = lightColorScheme\(.*?\n\)\n\n// Neutral dark schemes'''
    day_repl = '''// VANTA_THEME_R05 — VANTA Ivory
private val DayScheme = lightColorScheme(
    primary = Color(0xFFC9502C),
    onPrimary = Color.White,
    primaryContainer = Color(0xFFF4D4C6),
    onPrimaryContainer = Color(0xFF3B1408),
    secondary = Color(0xFF6E4B3A),
    onSecondary = Color.White,
    secondaryContainer = Color(0xFFEAD9CC),
    onSecondaryContainer = Color(0xFF2A1A12),
    tertiary = Color(0xFF7C5B42),
    background = Color(0xFFF5F1E9),
    onBackground = Color(0xFF171A1F),
    surface = Color(0xFFFFFDF8),
    onSurface = Color(0xFF171A1F),
    surfaceVariant = Color(0xFFECE6DA),
    onSurfaceVariant = Color(0xFF626973),
    outline = Color(0xFFD6CFC2),
    outlineVariant = Color(0xFFE4DDD1),
    error = Color(0xFFB72D35),
    scrim = Color.Black,
    surfaceTint = Color.Transparent,
)

// Neutral dark schemes'''
    s = regex_once(s, day_pat, day_repl, "Ivory scheme", flags=re.S)

    orange_pat = r'''private val OrangeScheme = tintedDark\(.*?\n\)\nprivate val GreenScheme'''
    orange_repl = '''// VANTA Obsidian — grafite profundo + laranja elétrico.
private val OrangeScheme = darkColorScheme(
    primary = Color(0xFFFF7446),
    onPrimary = Color(0xFF211008),
    primaryContainer = Color(0xFF4A2417),
    onPrimaryContainer = Color(0xFFFFD8C8),
    secondary = Color(0xFFFF9B75),
    onSecondary = Color(0xFF24100A),
    secondaryContainer = Color(0xFF3A2119),
    onSecondaryContainer = Color(0xFFFFD8C8),
    tertiary = Color(0xFFD9B29D),
    background = Color(0xFF0A0C10),
    onBackground = Color(0xFFF4F5F7),
    surface = Color(0xFF12151B),
    onSurface = Color(0xFFF4F5F7),
    surfaceVariant = Color(0xFF1A1E26),
    onSurfaceVariant = Color(0xFFA9B0BB),
    outline = Color(0xFF303744),
    outlineVariant = Color(0xFF252B35),
    error = Color(0xFFFF646A),
    scrim = Color.Black,
    surfaceTint = Color.Transparent,
)
private val GreenScheme'''
    s = regex_once(s, orange_pat, orange_repl, "Obsidian scheme", flags=re.S)
    write(p, s)

    p = root / "platforms/android/app/src/main/java/com/armsx2/ui/settings/AppTab.kt"
    s = read(p)
    old = '''                ThemeMode.entries.filter {
                    !it.requiresDynamicColor || Build.VERSION.SDK_INT >= Build.VERSION_CODES.S
                }.forEach { theme ->
                    val apply = { ThemePreferences.set(theme) }
                    FilterChip(
                        selected = ThemePreferences.mode.value == theme,
                        onClick = apply,
                        label = { Text(str("app.theme.${theme.name.lowercase()}")) },
                        shape = RoundedCornerShape(11.dp),
                        modifier = Modifier.controllerFocusable(
                            "app.theme.${theme.name}",
                            RoundedCornerShape(11.dp),
                            onConfirm = apply,
                        ),
                    )
                }
'''
    new = '''                // VANTA: só duas identidades oficiais, aplicadas pelo MaterialTheme inteiro.
                listOf(ThemeMode.Orange, ThemeMode.Light).forEach { theme ->
                    val apply = { ThemePreferences.set(theme) }
                    FilterChip(
                        selected = ThemePreferences.mode.value == theme,
                        onClick = apply,
                        label = { Text(if (theme == ThemeMode.Orange) "VANTA Obsidian" else "VANTA Ivory") },
                        shape = RoundedCornerShape(11.dp),
                        modifier = Modifier.controllerFocusable(
                            "app.theme.${theme.name}",
                            RoundedCornerShape(11.dp),
                            onConfirm = apply,
                        ),
                    )
                }
'''
    s = replace_once(s, old, new, "two VANTA theme picker")

    oled_old = r'''
            // OLED black is a MODIFIER on whichever theme is chosen above, not a theme of its own,
            // so "OLED + purple" / "OLED + yellow" are possible (the standalone OLED chip stays as
            // the neutral blue-accent preset). A chip rather than a ToggleRow so it lives with the
            // theme chips and keeps the controllerFocusable registration pad navigation needs.
            Spacer(Modifier.height(10.dp))
            run {
                val toggleOled = { ThemePreferences.setOledBase(!ThemePreferences.oledBase.value) }
                FilterChip(
                    selected = ThemePreferences.oledBase.value,
                    onClick = toggleOled,
                    label = { Text(str("app.theme.oledBase")) },
                    shape = RoundedCornerShape(11.dp),
                    modifier = Modifier.controllerFocusable(
                        "app.theme.oledBase",
                        RoundedCornerShape(11.dp),
                        onConfirm = toggleOled,
                    ),
                )
            }
'''
    s = replace_once(s, oled_old, '\n            // VANTA R0.5: OLED modifier hidden; somente Obsidian/Ivory.\n', "hide OLED modifier")
    write(p, s)
    print("[ok] VANTA Obsidian / Ivory global themes")


def patch_build_config(root: Path):
    p = root / "platforms/android/app/build.gradle.kts"
    s = read(p)
    # Do not let a VANTA test build self-update into an upstream ARMSX2 release.
    old = 'buildConfigField("boolean", "IN_APP_UPDATER", "true")'
    if old in s:
        s = s.replace(old, 'buildConfigField("boolean", "IN_APP_UPDATER", "false") // VANTA R0.5 pinned experimental', 1)
    write(p, s)
    print("[ok] upstream self-updater disabled for VANTA build")


def write_marker(root: Path):
    p = root / "VANTA_NATIVE_BUILD.txt"
    p.write_text(
        "VANTA PS2 Native R0.5 Night Game\n"
        f"Pinned ARMSX2 commit: {PIN}\n"
        "Target: Redmi Note 12S / Helio G96 / Cortex-A76+A55 / Mali-G57 MC2\n"
        "Features: ADPF, LTO, A76 tune, VANTA profiles, async readbacks, Mali fbfetch lab, "
        "GS render-pass coalescing, ARM64 VU JIT lab, global Obsidian/Ivory themes.\n",
        encoding="utf-8",
    )


def preflight(root: Path):
    perf = read(root / "platforms/android/app/src/main/java/com/armsx2/ui/settings/PerformanceTab.kt")
    settings = read(root / "platforms/android/app/src/main/java/com/armsx2/ui/settingshub/SettingsScreen.kt")
    theme = read(root / "platforms/android/app/src/main/java/com/armsx2/ui/theme/Theme.kt")
    app = read(root / "platforms/android/app/src/main/java/com/armsx2/ui/settings/AppTab.kt")
    build = read(root / "platforms/android/app/build.gradle.kts")
    must = {
        "profiles": "VANTA • OTIMIZAÇÃO RÁPIDA" in perf,
        "async readback": "hardwareDownloadMode = 5" in perf,
        "mali fbfetch": "forceMaliFbFetch = true" in perf,
        "VU inline": "vu1InlineFmacStall = true" in perf,
        "VU cross block": "vu1CrossBlockPState = true" in perf,
        "VU drain": "vu1InlineDrainTestPipes = true" in perf,
        "VU routing": "vu1FmacInstanceRouting = true" in perf,
        "ADPF": 'putBoolean("ui.adpf", adpfOn)' in perf,
        "scope": "VANTA_SCOPE_BANNER_R05" in settings,
        "obsidian": "VANTA Obsidian" in app and "VANTA Obsidian" in theme,
        "ivory": "VANTA Ivory" in app and "VANTA Ivory" in theme,
        "updater off": 'IN_APP_UPDATER", "false"' in build,
    }
    bad = [k for k, ok in must.items() if not ok]
    if bad:
        fail("preflight failed: " + ", ".join(bad))
    print("[ok] preflight: " + ", ".join(must))


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: patch_vanta_native_r05.py <ARMSX2-repo-root>")
    root = Path(sys.argv[1]).resolve()
    patch_performance_tab(root)
    patch_settings_scope(root)
    patch_theme(root)
    patch_build_config(root)
    write_marker(root)
    preflight(root)
    print("[ok] VANTA PS2 Native R0.5 Night Game patch complete")


if __name__ == "__main__":
    main()
