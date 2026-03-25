#!/bin/bash
# ═══════════════════════════════════════════════════════════
# Script de Instalação - Instagram Auto-Unfollow
# Para Kali Linux / Debian / Ubuntu
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
echo "  ╔══════════════════════════════════════════════╗"
echo "  ║  Instalador - Instagram Auto-Unfollow        ║"
echo "  ║  Para Kali Linux / Debian / Ubuntu            ║"
echo "  ╚══════════════════════════════════════════════╝"
echo -e "${RESET}"
echo ""

# Verificar se está rodando como root
if [ "$EUID" -eq 0 ]; then
    PIP_CMD="pip3 install"
    APT_CMD="apt"
else
    PIP_CMD="sudo pip3 install"
    APT_CMD="sudo apt"
fi

# 1. Atualizar pacotes
echo -e "${YELLOW}[1/5]${RESET} Atualizando lista de pacotes..."
$APT_CMD update -y -qq 2>/dev/null

# 2. Instalar dependências do sistema
echo -e "${YELLOW}[2/5]${RESET} Instalando dependências do sistema..."
$APT_CMD install -y -qq python3 python3-pip python3-venv \
    libatk1.0-0 libatk-bridge2.0-0 libcups2 libxkbcommon0 \
    libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
    libgbm1 libpango-1.0-0 libcairo2 libasound2 \
    libnspr4 libnss3 libxshmfence1 2>/dev/null

# 3. Instalar Playwright
echo -e "${YELLOW}[3/5]${RESET} Instalando Playwright para Python..."
$PIP_CMD playwright 2>/dev/null

# 4. Instalar navegador Chromium
echo -e "${YELLOW}[4/5]${RESET} Instalando navegador Chromium (pode demorar)..."
python3 -m playwright install chromium 2>/dev/null
python3 -m playwright install-deps chromium 2>/dev/null || true

# 5. Verificar instalação
echo -e "${YELLOW}[5/5]${RESET} Verificando instalação..."
python3 -c "from playwright.sync_api import sync_playwright; print('  Playwright OK')" 2>/dev/null

echo ""
echo -e "${GREEN}${BOLD}  ✓ Instalação concluída com sucesso!${RESET}"
echo ""
echo -e "  ${CYAN}Para usar o script:${RESET}"
echo -e "  ${BOLD}  python3 insta_unfollow.py${RESET}           # Iniciar unfollow"
echo -e "  ${BOLD}  python3 insta_unfollow.py --help${RESET}    # Ver todas as opções"
echo -e "  ${BOLD}  python3 insta_unfollow.py --status${RESET}  # Ver progresso"
echo ""
