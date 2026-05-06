# BYTE-FORGE
README.md

# Snake Arena — Login & Game

Pequeno projeto de interface com tela de login e área de jogo (canvas). Inclui estilos para a tela de login e estilos originais do jogo, HTML de exemplo e scripts básicos para alternar telas, toggle de senha, checkbox customizado, toast e partículas.

## Como usar (local)
1. Clone ou baixe o repositório.
2. Abra `index.html` no navegador (ou use Live Server / http-server para testar).
3. Na tela de login, clique em "JOGAR" para ver a tela do jogo.

## Estrutura do repositório
- index.html — HTML principal (login + game)
- css/
  - login.css — estilos da tela de login
  - game.css — estilos do jogo
- js/
  - app.js — controle de telas e UI (eye toggle, checkbox, toast, partículas)
  - game.js — placeholder para lógica do jogo / canvas
- assets/ — imagens, vídeos, ícones (opcional)
- README.md — este arquivo
- .gitignore — recomendado (node_modules/, .DS_Store, /dist, etc.)
- LICENSE — opcional (ex: MIT)

## Recursos incluídos
- Tela de login estilizada (HTML/CSS)
- Toggle para mostrar/esconder senha
- Checkbox customizado acessível (aria-pressed)
- Toasts simples
- Geração leve de partículas (DOM)
- Estrutura separada para lógica do jogo (game.js)

## Boas práticas e próximos passos
- Separar CSS em variáveis/SCSS para manutenção.
- Mover partículas para canvas ou otimizar se muitos elementos.
- Implementar autenticação real antes de alternar para a tela de jogo.
- Adicionar testes e pipeline de build (npm, parcel, vite) se necessário.

## Licença
Escolha uma licença (ex.: MIT). Exemplo rápido: adicione arquivo `LICENSE` com texto MIT.

---

Se quiser, gero um arquivo LICENSE (MIT) e um .gitignore pronto, ou envio os conteúdos completos para copiar/colar.
