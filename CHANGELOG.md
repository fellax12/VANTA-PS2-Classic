# VANTA PS2 Classic — changelog

## R0.3 G96 Balanced

Primeira revisão orientada especificamente ao Redmi Note 12S / Helio G96 / Mali-G57 MC2.

- Corrige o baseline de resolução para 1x Native.
- Desliga MTVU por padrão em hardware com apenas dois big cores no perfil alvo.
- Mantém Vulkan + Threaded Presentation.
- Mantém Disable Readbacks como baseline de performance, com fallback manual por jogo.
- Mantém Instant VU1 ligado.
- Mantém EE Cycle Rate/Skip em valores seguros.
- Não altera classes nativas nem bibliotecas do core nesta fase.
- Prepara a separação entre otimizações seguras de configuração e a futura Performance Engine nativa.
