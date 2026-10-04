# VANTA PS2 Classic 3668 — teste rápido R0.3 G96 Balanced

Objetivo: medir ganho real no Redmi Note 12S (Helio G96 / Mali-G57 MC2) sem comprar FPS com perda forte de qualidade.

## O que mudou na R0.3

- Base continua NetherSX2 Classic 2.1 / AetherSX2 3668.
- Vulkan continua como renderer padrão.
- Resolução volta para **1x Native real**. O experimento 0,75x da R0.2 foi removido.
- Threaded Presentation: ON.
- Hardware Download Mode: Disable Readbacks.
- MTVU / Multi-Threaded VU1: **OFF por padrão** para não disputar os dois Cortex-A76 fortes do G96.
- Instant VU1: ON.
- EE Cycle Rate: 100% / 0.
- EE Cycle Skip: 0.
- FXAA, CAS e VSync continuam OFF no baseline.
- Core e bibliotecas nativas continuam intactos nesta fase.

## Como testar

Use primeiro um jogo que você já conhece bem no aparelho e jogue a mesma cena por alguns minutos.

Observe:
- velocidade do jogo / FPS;
- frame pacing e microtravadas;
- áudio;
- glitches de efeitos;
- temperatura;
- diferença entre áreas leves e pesadas.

Depois faça um segundo teste apenas mudando **Hardware Download Mode** para um modo mais preciso. Se aparecer efeito gráfico faltando com Disable Readbacks, use o modo preciso apenas naquele jogo.

## O que NÃO é R0.3

R0.3 ainda não altera o scheduler nativo, afinidade EE/GS, ADPF, Thermal Headroom, JIT ARM64 ou Vulkan internamente. Essas mudanças exigem uma build da camada nativa; não são simuladas por preferências.

## Segurança de atualização

O preset R0.3 é aplicado uma vez. Depois disso, alterações manuais feitas no app são preservadas.
Não reutilize save states incompatíveis de outras linhas; prefira memory card/save interno.
