#!/bin/bash
# ═══════════════════════════════════════════════════════════
# Script de Instalacao - Instagram Auto-Unfollow v2.0
# Para Kali Linux / NetHunter / Debian / Ubuntu
# ═══════════════════════════════════════════════════════════

set -e

RED='\033[0;91m'
GREEN='\033[0;92m'
YELLOW='\033[0;93m'
CYAN='\033[0;96m'
BOLD='\033[1m'
RESET='\033[0m'

echo ""
echo -e "${CYAN}${BOLD}"
echo "  ╔══════════════════════════════════════════════════╗"
echo "  ║  Instalador - Instagram Auto-Unfollow v2.0       ║"
echo "  ║  Para Kali Linux / NetHunter / Debian / Ubuntu    ║"
echo "  ╚══════════════════════════════════════════════════╝"
echo -e "${RESET}"
echo ""

# Verificar se esta rodando como root
if [ "$EUID" -eq 0 ]; then
    PIP_CMD="pip3 install"
    APT_CMD="apt"
else
    PIP_CMD="sudo pip3 install"
    APT_CMD="sudo apt"
fi

# 1. Atualizar pacotes
echo -e "${YELLOW}[1/6]${RESET} Atualizando lista de pacotes..."
$APT_CMD update -y -qq 2>/dev/null || true

# 2. Instalar dependencias do sistema
echo -e "${YELLOW}[2/6]${RESET} Instalando dependencias do sistema..."
$APT_CMD install -y -qq python3 python3-pip python3-venv \
    libatk1.0-0 libatk-bridge2.0-0 libcups2 libxkbcommon0 \
    libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libgbm1 libpango-1.0-0 libcairo2 libasound2 \
    libnspr4 libnss3 libxshmfence1 2>/dev/null || true

# 3. Instalar Rich (visual profissional no terminal)
echo -e "${YELLOW}[3/6]${RESET} Instalando Rich (interface visual)..."
$PIP_CMD rich 2>/dev/null || pip3 install rich 2>/dev/null

# 4. Instalar Playwright
echo -e "${YELLOW}[4/6]${RESET} Instalando Playwright para Python..."
$PIP_CMD playwright 2>/dev/null || pip3 install playwright 2>/dev/null

# 5. Instalar navegador Chromium
echo -e "${YELLOW}[5/6]${RESET} Instalando navegador Chromium (pode demorar)..."
python3 -m playwright install chromium 2>/dev/null
python3 -m playwright install-deps chromium 2>/dev/null || true

# 6. Criar pasta de debug log
echo -e "${YELLOW}[6/6]${RESET} Configurando pasta de debug log..."
if [ -d "/sdcard/nh_files" ]; then
    echo -e "  ${GREEN}Pasta /sdcard/nh_files/ detectada (NetHunter)${RESET}"
    echo -e "  ${GREEN}Debug logs serao salvos em: /sdcard/nh_files/debug_log.txt${RESET}"
else
    mkdir -p "$(dirname "$0")/logs"
    echo -e "  ${YELLOW}Pasta /sdcard/nh_files/ nao encontrada${RESET}"
    echo -e "  ${YELLOW}Debug logs serao salvos em: $(dirname "$0")/logs/debug_log.txt${RESET}"
fi

# Verificar instalacao
echo ""
echo -e "${BOLD}Verificando instalacao...${RESET}"
python3 -c "from rich.console import Console; Console().print('[green]  Rich OK[/]')" 2>/dev/null || echo -e "  ${RED}Rich FALHOU${RESET}"
python3 -c "from playwright.sync_api import sync_playwright; print('  Playwright OK')" 2>/dev/null || echo -e "  ${RED}Playwright FALHOU${RESET}"

# Dar permissao de execucao ao script principal
chmod +x "$(dirname "$0")/insta_unfollow.py" 2>/dev/null || true

echo ""
echo -e "${GREEN}${BOLD}  Instalacao concluida com sucesso!${RESET}"
echo ""
echo -e "  ${CYAN}Para usar o script:${RESET}"
echo -e "  ${BOLD}  python3 insta_unfollow.py${RESET}           # Abrir o menu principal"
echo ""
echo -e "  ${CYAN}Funcionalidades do menu:${RESET}"
echo -e "  ${BOLD}  [1]${RESET} Iniciar Unfollow"
echo -e "  ${BOLD}  [2]${RESET} Configurar Velocidade"
echo -e "  ${BOLD}  [3]${RESET} Ver Status / Progresso"
echo -e "  ${BOLD}  [4]${RESET} Listar Proximos Perfis"
echo -e "  ${BOLD}  [5]${RESET} Gerenciar Whitelist"
echo -e "  ${BOLD}  [6]${RESET} Ver Debug Log"
echo -e "  ${BOLD}  [7]${RESET} Resetar Progresso"
echo -e "  ${BOLD}  [8]${RESET} Configuracoes Gerais"
echo ""
