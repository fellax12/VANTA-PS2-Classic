# VANTA PS2 Classic 3668 — teste rápido R0.1

Objetivo desta primeira build: validar o núcleo 3668 no Redmi sem mexer no motor de emulação.

## Instalação
O package original do núcleo é preservado para reduzir risco de quebrar JNI/configurações.
Se houver AetherSX2/NetherSX2 instalado com assinatura incompatível, faça backup dos dados/saves
e desinstale a instalação anterior antes de instalar o APK VANTA.

## Primeiro teste
Comece com UM jogo que você já sabe que abriu no AetherSX2.

Perfil inicial sugerido:
- Resolução: 1x Native
- Renderer: OpenGL primeiro
- EE Cycle Rate: 100% inicialmente
- EE Cycle Skip: 0
- Multi-Threaded VU1: ON
- Instant VU1: ON/default
- Widescreen patches: OFF no primeiro benchmark
- Texture preloading/upscaling: OFF no primeiro benchmark

Depois, segundo teste:
- Renderer: Vulkan
- Threaded Presentation: ON
- Hardware Download Mode: Disable Readbacks
- Resolução: 1x Native

Compare:
- FPS/velocidade
- áudio picotando ou não
- travamentos
- glitches gráficos
- temperatura após alguns minutos

Não use save state da linha 4248 na 3668; prefira memory card/save interno.
