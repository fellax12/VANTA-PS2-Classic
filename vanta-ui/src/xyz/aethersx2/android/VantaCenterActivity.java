package xyz.aethersx2.android;

import android.app.Activity;
import android.content.Intent;
import android.content.SharedPreferences;
import android.graphics.Color;
import android.graphics.Typeface;
import android.graphics.drawable.GradientDrawable;
import android.os.Bundle;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.Window;
import android.widget.AdapterView;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.Spinner;
import android.widget.Switch;
import android.widget.TextView;
import android.widget.Toast;

import java.util.Locale;

public class VantaCenterActivity extends Activity {
    private SharedPreferences prefs;
    private boolean dark;
    private int bg;
    private int surface;
    private int surface2;
    private int text;
    private int muted;
    private int accent;
    private int accent2;
    private int outline;
    private int danger;
    private TextView statusText;

    private static final String PREF_RENDERER = "EmuCore/GS/Renderer";
    private static final String PREF_RESOLUTION = "EmuCore/GS/upscale_multiplier";
    private static final String PREF_READBACKS = "EmuCore/GS/HWDownloadMode";
    private static final String PREF_THREADED_PRESENT = "EmuCore/GS/ThreadedPresentation";
    private static final String PREF_MTVU = "EmuCore/Speedhacks/vuThread";
    private static final String PREF_INSTANT_VU = "EmuCore/Speedhacks/vu1Instant";
    private static final String PREF_EE_RATE = "EmuCore/Speedhacks/EECycleRate";
    private static final String PREF_EE_SKIP = "EmuCore/Speedhacks/EECycleSkip";
    private static final String PREF_AFFINITY = "EmuCore/AffinityControlMode";
    private static final String PREF_FASTMEM = "EmuCore/CPU/Recompiler/EnableFastmem";
    private static final String PREF_TEXTURE_PRELOAD = "EmuCore/GS/texture_preloading";
    private static final String PREF_BLEND = "EmuCore/GS/accurate_blending_unit";
    private static final String PREF_SKIP_DUP = "EmuCore/GS/SkipDuplicateFrames";
    private static final String PREF_PALETTE_GPU = "EmuCore/GS/paltex";

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        prefs = getSharedPreferences(getPackageName() + "_preferences", MODE_PRIVATE);
        dark = !"light".equals(prefs.getString("UI/Theme", "dark"));
        resolvePalette();
        styleSystemBars();
        setContentView(buildUi());
    }

    private void resolvePalette() {
        if (dark) {
            bg = Color.parseColor("#0A0C10");
            surface = Color.parseColor("#12151B");
            surface2 = Color.parseColor("#1A1E26");
            text = Color.parseColor("#F4F5F7");
            muted = Color.parseColor("#A9B0BB");
            accent = Color.parseColor("#FF7446");
            accent2 = Color.parseColor("#FF9B75");
            outline = Color.parseColor("#303744");
            danger = Color.parseColor("#FF646A");
        } else {
            bg = Color.parseColor("#F5F1E9");
            surface = Color.parseColor("#FFFDF8");
            surface2 = Color.parseColor("#ECE6DA");
            text = Color.parseColor("#171A1F");
            muted = Color.parseColor("#626973");
            accent = Color.parseColor("#C9502C");
            accent2 = Color.parseColor("#E06D43");
            outline = Color.parseColor("#D6CFC2");
            danger = Color.parseColor("#B72D35");
        }
    }

    private void styleSystemBars() {
        Window w = getWindow();
        w.setStatusBarColor(bg);
        w.setNavigationBarColor(bg);
        if (!dark) {
            w.getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR | View.SYSTEM_UI_FLAG_LIGHT_NAVIGATION_BAR);
        }
    }

    private View buildUi() {
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(bg);
        root.setPadding(dp(16), dp(12), dp(16), dp(20));

        root.addView(buildHeader());

        ScrollView scroll = new ScrollView(this);
        scroll.setFillViewport(true);
        LinearLayout content = new LinearLayout(this);
        content.setOrientation(LinearLayout.VERTICAL);
        content.setPadding(0, dp(6), 0, dp(24));
        scroll.addView(content, new ScrollView.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT));

        content.addView(scopeCard());
        content.addView(statusCard());
        content.addView(profileCard());
        content.addView(gpuCard());
        content.addView(cpuCard());
        content.addView(labCard());
        content.addView(diagnosticsCard());
        content.addView(themeCard());
        content.addView(advancedCard());

        root.addView(scroll, new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f));
        return root;
    }

    private View buildHeader() {
        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setGravity(Gravity.CENTER_VERTICAL);
        row.setPadding(0, dp(6), 0, dp(8));

        TextView back = text("‹", 38, text, Typeface.NORMAL);
        back.setGravity(Gravity.CENTER);
        back.setPadding(dp(6), 0, dp(14), 0);
        back.setOnClickListener(new View.OnClickListener() {
            @Override public void onClick(View v) { finish(); }
        });
        row.addView(back, new LinearLayout.LayoutParams(dp(50), dp(52)));

        LinearLayout titles = new LinearLayout(this);
        titles.setOrientation(LinearLayout.VERTICAL);
        TextView title = text("VANTA PS2", 22, text, Typeface.BOLD);
        title.setLetterSpacing(0.08f);
        TextView sub = text("Performance Center • R0.4", 11, accent, Typeface.BOLD);
        sub.setLetterSpacing(0.12f);
        titles.addView(title);
        titles.addView(sub);
        row.addView(titles, new LinearLayout.LayoutParams(0, ViewGroup.LayoutParams.WRAP_CONTENT, 1f));

        TextView chip = badge(dark ? "OBSIDIAN" : "IVORY");
        row.addView(chip);
        return row;
    }

    private View scopeCard() {
        LinearLayout c = card("ESCOPO", "Antes de mexer, saiba exatamente onde a mudança será aplicada.");
        TextView chip = badge("GLOBAL • TODOS OS JOGOS");
        LinearLayout.LayoutParams cp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        cp.topMargin = dp(12);
        c.addView(chip, cp);
        c.addView(paragraph("Tudo nesta Central VANTA altera o perfil global. Para mexer só em um jogo, segure o jogo na biblioteca e abra Propriedades. As telas por jogo agora também exibem um aviso de escopo no topo."));
        return c;
    }

    private View statusCard() {
        LinearLayout c = card("AGORA", "Resumo do perfil que está realmente salvo no emulador.");
        statusText = text("", 14, text, Typeface.BOLD);
        statusText.setPadding(0, dp(12), 0, 0);
        c.addView(statusText);
        updateStatus();
        return c;
    }

    private View profileCard() {
        LinearLayout c = card("PERFIS RÁPIDOS", "Comece por um perfil e refine só o que o jogo pedir.");
        c.addView(actionButton("Equilibrado G96", "Vulkan • 1× • Readbacks rápidos • MTVU OFF • Performance Cores", new View.OnClickListener() {
            @Override public void onClick(View v) { applyBalancedG96(); }
        }, true));
        c.addView(actionButton("VU pesado • LAB", "God of War e jogos onde VU domina. Usa -2/2 + MTVU + prioridade VU. Experimental.", new View.OnClickListener() {
            @Override public void onClick(View v) { applyVuHeavy(); }
        }, false));
        c.addView(actionButton("Qualidade estável", "1.5× • Readbacks precisos • sem underclock • Vulkan", new View.OnClickListener() {
            @Override public void onClick(View v) { applyQuality(); }
        }, false));
        return c;
    }

    private View gpuCard() {
        LinearLayout c = card("GPU & IMAGEM", "Ajustes que mexem no renderizador. Se a GPU não for o gargalo, baixar resolução pode não ajudar.");
        addSpinner(c, "Renderizador", "Vulkan costuma favorecer Mali. OpenGL é o plano B para glitches específicos.", PREF_RENDERER,
                new String[]{"Vulkan", "OpenGL", "Software (diagnóstico)"}, new String[]{"14", "12", "13"}, "14");
        addSpinner(c, "Resolução interna", "Use 1× como base no G96. Suba apenas quando o OSD mostrar folga na GPU.", PREF_RESOLUTION,
                new String[]{"0.75× • emergência", "1× • base", "1.25×", "1.5×", "1.75×", "2×"},
                new String[]{"0.750000", "1.000000", "1.250000", "1.500000", "1.750000", "2.000000"}, "1.000000");
        addSpinner(c, "Readbacks da GPU", "Preciso = compatibilidade. Rápido = grande ganho em alguns jogos. Não sincronizado/ignorar são modos de laboratório.", PREF_READBACKS,
                new String[]{"Preciso / recomendado", "Rápido • sem readbacks", "Não sincronizado • LAB", "Ignorar transferências • extremo"},
                new String[]{"0", "1", "2", "3"}, "1");
        addSwitch(c, "Apresentação em thread", "Ajuda Vulkan em alguns Mali quando a thread GS não é o gargalo principal.", PREF_THREADED_PRESENT, true);
        addSpinner(c, "Pré-carregar texturas", "Full usa cache/hash e pode suavizar stutter; consome mais memória.", PREF_TEXTURE_PRELOAD,
                new String[]{"Nenhum", "Parcial", "Full / Hash Cache"}, new String[]{"0", "1", "2"}, "2");
        addSpinner(c, "Precisão de blending", "Minimum reduz trabalho da GPU, mas pode quebrar efeitos. Basic é o ponto seguro.", PREF_BLEND,
                new String[]{"Minimum • rápido", "Basic • seguro", "Medium", "High", "Full", "Ultra"},
                new String[]{"0", "1", "2", "3", "4", "5"}, "1");
        return c;
    }

    private View cpuCard() {
        LinearLayout c = card("CPU, EE & VU", "Aqui ficam os ajustes que mais importam quando o jogo está lento mesmo com GPU folgada.");
        addSpinner(c, "Afinidade dos núcleos", "Diz ao emulador qual thread deve receber primeiro os núcleos fortes. No G96 há apenas 2 Cortex-A76.", PREF_AFFINITY,
                new String[]{"Desligado", "EE → VU → GS", "EE → GS → VU", "VU → EE → GS", "VU → GS → EE", "GS → EE → VU", "GS → VU → EE", "Performance Cores • automático"},
                new String[]{"0", "1", "2", "3", "4", "5", "6", "7"}, "7");
        addSwitch(c, "MTVU • VU1 em thread separada", "Pode ajudar jogos com VU pesado; no Helio G96 também pode disputar os dois núcleos grandes. Teste por jogo.", PREF_MTVU, false);
        addSwitch(c, "Instant VU1", "Otimização rápida para VU1 quando MTVU está desligado. Mantida ON no perfil G96.", PREF_INSTANT_VU, true);
        addSpinner(c, "EE Cycle Rate", "0 = PS2 normal. -1/-2 reduzem o trabalho emulado. Podem alterar timing e física.", PREF_EE_RATE,
                new String[]{"50% (-3) • extremo", "60% (-2)", "75% (-1)", "100% (0) • normal", "130% (+1)", "180% (+2)", "300% (+3)"},
                new String[]{"-3", "-2", "-1", "0", "1", "2", "3"}, "0");
        addSpinner(c, "EE Cycle Skip", "0 = correto. 1/2/3 pulam ciclos e podem salvar hardware fraco, mas são hacks de timing.", PREF_EE_SKIP,
                new String[]{"Normal (0)", "Leve (1)", "Moderado (2)", "Máximo (3)"}, new String[]{"0", "1", "2", "3"}, "0");
        addSwitch(c, "Fastmem", "Mantém o caminho rápido de memória do recompilador ARM64. Normalmente deve ficar ligado.", PREF_FASTMEM, true);
        return c;
    }

    private View labCard() {
        LinearLayout c = card("PERFORMANCE LAB", "Recursos reais do core expostos para teste A/B. Ligue um por vez e compare a mesma cena.");
        addSwitch(c, "Pular frames duplicados", "Evita apresentar frames repetidos quando o jogo internamente roda abaixo da taxa de vídeo. Pode reduzir trabalho em alguns drivers/jogos.", PREF_SKIP_DUP, false);
        addSwitch(c, "Paletas na GPU", "Move conversão de paleta da CPU para GPU. Pode ajudar casos específicos; em muitos jogos é mais lento.", PREF_PALETTE_GPU, false);
        TextView note = paragraph("Próxima camada nativa: Smart Affinity própria do VANTA, ADPF/Performance Hint e Thermal Headroom. Esses recursos exigem mexer no motor nativo; não são simulados nesta versão.");
        note.setTextColor(accent2);
        c.addView(note);
        return c;
    }

    private View diagnosticsCard() {
        LinearLayout c = card("DIAGNÓSTICO NA TELA", "Use durante benchmark. Depois desligue o que não precisar para evitar qualquer overhead desnecessário.");
        addSwitch(c, "FPS / VPS", "Mostra frames internos e velocidade de vídeo.", "EmuCore/GS/OsdShowFPS", false);
        addSwitch(c, "Velocidade %", "100% significa que o PS2 emulado está acompanhando o tempo real.", "EmuCore/GS/OsdShowSpeed", false);
        addSwitch(c, "CPU / EE / GS / VU", "Ajuda a descobrir se o gargalo está nas threads do emulador.", "EmuCore/GS/OsdShowCPU", false);
        addSwitch(c, "GPU", "Mostra tempo/carga da GPU. Se ela tem folga, reduzir resolução pode não ajudar.", "EmuCore/GS/OsdShowGPU", false);
        addSwitch(c, "Frame times", "Mostra média e pior frame; útil para caçar microtravadas.", "EmuCore/GS/OsdShowFrameTimes", false);
        return c;
    }

    private View themeCard() {
        LinearLayout c = card("TEMA VANTA", "Duas identidades completas. A escolha altera o aplicativo inteiro, incluindo menus, diálogos e configurações.");
        c.addView(actionButton("VANTA Obsidian", "Grafite profundo + laranja elétrico", new View.OnClickListener() {
            @Override public void onClick(View v) { setThemeMode("dark"); }
        }, dark));
        c.addView(actionButton("VANTA Ivory", "Marfim + grafite + terracota", new View.OnClickListener() {
            @Override public void onClick(View v) { setThemeMode("light"); }
        }, !dark));
        return c;
    }

    private View advancedCard() {
        LinearLayout c = card("AVANÇADO", "Nada foi removido. A interface técnica original continua disponível para ajustes raros.");
        Button b = actionButton("Abrir configurações técnicas", "Tabs originais do Aether/Nether, agora com escopo e nomes mais claros.", new View.OnClickListener() {
            @Override public void onClick(View v) {
                Intent i = new Intent();
                i.setClassName(VantaCenterActivity.this, "xyz.aethersx2.android.SettingsActivity");
                i.putExtra("vanta_bypass", true);
                startActivity(i);
            }
        }, false);
        c.addView(b);
        TextView warning = paragraph("Dica: se um jogo pedir algo específico, prefira Propriedades do jogo. Assim você não contamina todos os outros títulos com um hack necessário só naquele game.");
        warning.setTextColor(danger);
        c.addView(warning);
        return c;
    }

    private void applyBalancedG96() {
        SharedPreferences.Editor e = prefs.edit();
        e.putString(PREF_RENDERER, "14");
        e.putString(PREF_RESOLUTION, "1.000000");
        e.putString(PREF_READBACKS, "1");
        e.putBoolean(PREF_THREADED_PRESENT, true);
        e.putBoolean(PREF_MTVU, false);
        e.putBoolean(PREF_INSTANT_VU, true);
        e.putString(PREF_EE_RATE, "0");
        e.putString(PREF_EE_SKIP, "0");
        e.putString(PREF_AFFINITY, "7");
        e.putBoolean(PREF_FASTMEM, true);
        e.putString(PREF_TEXTURE_PRELOAD, "2");
        e.putString(PREF_BLEND, "1");
        e.putBoolean(PREF_SKIP_DUP, false);
        e.putBoolean("EmuCore/WarnAboutUnsafeSettings", true);
        e.apply();
        toast("Perfil Equilibrado G96 aplicado");
        updateStatus();
    }

    private void applyVuHeavy() {
        SharedPreferences.Editor e = prefs.edit();
        e.putString(PREF_RENDERER, "14");
        e.putString(PREF_RESOLUTION, "1.000000");
        e.putString(PREF_READBACKS, "1");
        e.putBoolean(PREF_THREADED_PRESENT, true);
        e.putBoolean(PREF_MTVU, true);
        e.putBoolean(PREF_INSTANT_VU, false);
        e.putString(PREF_EE_RATE, "-2");
        e.putString(PREF_EE_SKIP, "2");
        e.putString(PREF_AFFINITY, "3");
        e.putBoolean(PREF_FASTMEM, true);
        e.putBoolean("EmuCore/GS/OsdShowFPS", true);
        e.putBoolean("EmuCore/GS/OsdShowSpeed", true);
        e.putBoolean("EmuCore/GS/OsdShowCPU", true);
        e.putBoolean("EmuCore/GS/OsdShowGPU", true);
        e.putBoolean("EmuCore/GS/OsdShowFrameTimes", true);
        e.apply();
        toast("LAB VU pesado aplicado — use para teste A/B");
        updateStatus();
    }

    private void applyQuality() {
        SharedPreferences.Editor e = prefs.edit();
        e.putString(PREF_RENDERER, "14");
        e.putString(PREF_RESOLUTION, "1.500000");
        e.putString(PREF_READBACKS, "0");
        e.putBoolean(PREF_THREADED_PRESENT, true);
        e.putBoolean(PREF_MTVU, false);
        e.putBoolean(PREF_INSTANT_VU, true);
        e.putString(PREF_EE_RATE, "0");
        e.putString(PREF_EE_SKIP, "0");
        e.putString(PREF_AFFINITY, "7");
        e.putBoolean(PREF_FASTMEM, true);
        e.putString(PREF_TEXTURE_PRELOAD, "2");
        e.putString(PREF_BLEND, "1");
        e.apply();
        toast("Perfil Qualidade estável aplicado");
        updateStatus();
    }

    private void setThemeMode(String mode) {
        prefs.edit().putString("UI/Theme", mode).apply();
        toast("Tema alterado — recarregando a interface");
        recreate();
    }

    private void updateStatus() {
        if (statusText == null) return;
        String renderer = "14".equals(prefs.getString(PREF_RENDERER, "14")) ? "Vulkan" :
                ("12".equals(prefs.getString(PREF_RENDERER, "14")) ? "OpenGL" : "Software");
        String res = prefs.getString(PREF_RESOLUTION, "1.000000");
        String prettyRes = res.replace(".000000", "").replace(".500000", ".5").replace(".250000", ".25").replace(".750000", ".75");
        String mtvu = prefs.getBoolean(PREF_MTVU, false) ? "ON" : "OFF";
        String read = prefs.getString(PREF_READBACKS, "1");
        String readLabel = "0".equals(read) ? "Preciso" : ("1".equals(read) ? "Rápido" : ("2".equals(read) ? "Não sincronizado" : "Ignorar"));
        String aff = prefs.getString(PREF_AFFINITY, "7");
        String affLabel = "7".equals(aff) ? "Performance Cores" : "Modo " + aff;
        statusText.setText(renderer + "  •  " + prettyRes + "×  •  MTVU " + mtvu + "\nReadbacks: " + readLabel + "  •  Affinity: " + affLabel);
    }

    private void addSpinner(LinearLayout parent, String title, String summary, final String key,
                            final String[] labels, final String[] values, String def) {
        LinearLayout block = settingBlock(title, summary);
        final Spinner spinner = new Spinner(this, Spinner.MODE_DROPDOWN);
        ArrayAdapter<String> adapter = new ArrayAdapter<String>(this, android.R.layout.simple_spinner_dropdown_item, labels);
        spinner.setAdapter(adapter);
        String current = prefs.getString(key, def);
        int selected = 0;
        for (int i = 0; i < values.length; i++) if (values[i].equals(current)) selected = i;
        spinner.setSelection(selected, false);
        spinner.setPopupBackgroundDrawable(round(surface, dp(12), outline, 1));
        spinner.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {
            @Override public void onItemSelected(AdapterView<?> parent, View view, int position, long id) {
                prefs.edit().putString(key, values[position]).apply();
                updateStatus();
            }
            @Override public void onNothingSelected(AdapterView<?> parent) {}
        });
        LinearLayout.LayoutParams sp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, dp(52));
        sp.topMargin = dp(8);
        block.addView(spinner, sp);
        parent.addView(block);
    }

    private void addSwitch(LinearLayout parent, String title, String summary, final String key, boolean def) {
        LinearLayout block = settingBlock(title, summary);
        final Switch sw = new Switch(this);
        sw.setText(prefs.getBoolean(key, def) ? "ATIVO" : "DESLIGADO");
        sw.setTextColor(muted);
        sw.setChecked(prefs.getBoolean(key, def));
        sw.setOnCheckedChangeListener((buttonView, isChecked) -> {
            prefs.edit().putBoolean(key, isChecked).apply();
            sw.setText(isChecked ? "ATIVO" : "DESLIGADO");
            updateStatus();
        });
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        lp.gravity = Gravity.END;
        lp.topMargin = dp(6);
        block.addView(sw, lp);
        parent.addView(block);
    }

    private LinearLayout settingBlock(String title, String summary) {
        LinearLayout block = new LinearLayout(this);
        block.setOrientation(LinearLayout.VERTICAL);
        block.setPadding(dp(14), dp(12), dp(14), dp(12));
        GradientDrawable gd = round(surface2, dp(14), outline, 1);
        block.setBackground(gd);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        lp.topMargin = dp(10);
        block.setLayoutParams(lp);
        block.addView(text(title, 15, text, Typeface.BOLD));
        TextView s = text(summary, 12, muted, Typeface.NORMAL);
        s.setPadding(0, dp(4), 0, 0);
        block.addView(s);
        return block;
    }

    private LinearLayout card(String title, String subtitle) {
        LinearLayout c = new LinearLayout(this);
        c.setOrientation(LinearLayout.VERTICAL);
        c.setPadding(dp(16), dp(15), dp(16), dp(16));
        c.setBackground(round(surface, dp(18), outline, 1));
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        lp.topMargin = dp(12);
        c.setLayoutParams(lp);
        TextView t = text(title, 13, accent, Typeface.BOLD);
        t.setLetterSpacing(0.10f);
        c.addView(t);
        TextView st = text(subtitle, 13, muted, Typeface.NORMAL);
        st.setPadding(0, dp(5), 0, 0);
        c.addView(st);
        return c;
    }

    private Button actionButton(String title, String summary, View.OnClickListener click, boolean primary) {
        Button b = new Button(this);
        b.setAllCaps(false);
        b.setGravity(Gravity.START | Gravity.CENTER_VERTICAL);
        b.setText(title + "\n" + summary);
        b.setTextSize(13);
        b.setTextColor(primary ? (dark ? Color.BLACK : Color.WHITE) : text);
        b.setPadding(dp(14), dp(10), dp(14), dp(10));
        b.setBackground(round(primary ? accent : surface2, dp(14), primary ? accent : outline, 1));
        b.setOnClickListener(click);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        lp.topMargin = dp(10);
        b.setLayoutParams(lp);
        return b;
    }

    private TextView paragraph(String value) {
        TextView t = text(value, 13, muted, Typeface.NORMAL);
        t.setPadding(0, dp(10), 0, 0);
        return t;
    }

    private TextView badge(String value) {
        TextView t = text(value, 10, dark ? Color.BLACK : Color.WHITE, Typeface.BOLD);
        t.setLetterSpacing(0.08f);
        t.setPadding(dp(10), dp(6), dp(10), dp(6));
        t.setBackground(round(accent, dp(99), accent, 0));
        return t;
    }

    private TextView text(String value, float size, int color, int typeface) {
        TextView t = new TextView(this);
        t.setText(value);
        t.setTextSize(size);
        t.setTextColor(color);
        t.setTypeface(Typeface.create("sans-serif", typeface));
        t.setLineSpacing(0f, 1.06f);
        return t;
    }

    private GradientDrawable round(int fill, int radius, int strokeColor, int strokeDp) {
        GradientDrawable d = new GradientDrawable();
        d.setColor(fill);
        d.setCornerRadius(radius);
        if (strokeDp > 0) d.setStroke(dp(strokeDp), strokeColor);
        return d;
    }

    private int dp(int v) {
        return (int) (v * getResources().getDisplayMetrics().density + 0.5f);
    }

    private void toast(String s) {
        Toast.makeText(this, s, Toast.LENGTH_SHORT).show();
    }
}
