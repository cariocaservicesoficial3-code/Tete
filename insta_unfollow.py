#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════╗
║  Instagram Auto-Unfollow Script (Playwright)                ║
║  Conta: @cariocamafiadostutorsoficial                       ║
║  Autor: Manus AI                                            ║
║  Data: 25/03/2026                                           ║
║                                                             ║
║  Funcionalidades:                                           ║
║  - Login com suporte a 2FA (SMS ou Google Authenticator)    ║
║  - Unfollow de perfis que não seguem de volta               ║
║  - Prioriza perfis mais antigos                             ║
║  - Delays humanizados para evitar bloqueios                 ║
║  - Salva progresso para retomar depois                      ║
║  - Log detalhado de todas as ações                          ║
╚══════════════════════════════════════════════════════════════╝
"""

import asyncio
import json
import os
import sys
import random
import time
import argparse
from datetime import datetime, timedelta
from pathlib import Path

try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("\n[ERRO] Playwright não está instalado!")
    print("Execute: pip install playwright && playwright install chromium")
    sys.exit(1)


# ═══════════════════════════════════════════════════════════
# CONFIGURAÇÕES
# ═══════════════════════════════════════════════════════════

SCRIPT_DIR = Path(__file__).parent.resolve()
UNFOLLOW_LIST_FILE = SCRIPT_DIR / "unfollow_list.json"
PROGRESS_FILE = SCRIPT_DIR / "progress.json"
LOG_FILE = SCRIPT_DIR / "unfollow_log.txt"
SESSION_DIR = SCRIPT_DIR / "session_data"
WHITELIST_FILE = SCRIPT_DIR / "whitelist.txt"

# Limites de segurança
MAX_UNFOLLOWS_PER_HOUR = 25
MAX_UNFOLLOWS_PER_DAY = 150
MIN_DELAY_BETWEEN_UNFOLLOWS = 15   # segundos
MAX_DELAY_BETWEEN_UNFOLLOWS = 45   # segundos
PAUSE_AFTER_BATCH = 300            # 5 minutos de pausa a cada lote
BATCH_SIZE = 20                    # unfollows por lote antes de pausar

# Cores para o terminal
class Colors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def log(msg, level="INFO"):
    """Log com timestamp no terminal e no arquivo."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    color_map = {
        "INFO": Colors.CYAN,
        "OK": Colors.GREEN,
        "WARN": Colors.YELLOW,
        "ERROR": Colors.RED,
        "ACTION": Colors.MAGENTA,
        "HEADER": Colors.BOLD + Colors.WHITE,
    }
    color = color_map.get(level, Colors.WHITE)
    
    # Terminal (com cor)
    print(f"{Colors.BOLD}[{timestamp}]{Colors.RESET} {color}[{level}]{Colors.RESET} {msg}")
    
    # Arquivo (sem cor)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] [{level}] {msg}\n")


def print_banner():
    """Exibe o banner do script."""
    banner = f"""
{Colors.CYAN}{Colors.BOLD}
 ██╗███╗   ██╗███████╗████████╗ █████╗ 
 ██║████╗  ██║██╔════╝╚══██╔══╝██╔══██╗
 ██║██╔██╗ ██║███████╗   ██║   ███████║
 ██║██║╚██╗██║╚════██║   ██║   ██╔══██║
 ██║██║ ╚████║███████║   ██║   ██║  ██║
 ╚═╝╚═╝  ╚═══╝╚══════╝   ╚═╝   ╚═╝  ╚═╝
    {Colors.YELLOW}AUTO-UNFOLLOW SCRIPT v1.0{Colors.RESET}
    {Colors.WHITE}Para Kali Linux + Playwright{Colors.RESET}
"""
    print(banner)


def load_progress():
    """Carrega o progresso salvo anteriormente."""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, "r") as f:
            return json.load(f)
    return {
        "last_index": 0,
        "total_unfollowed": 0,
        "unfollowed_today": 0,
        "last_date": None,
        "unfollowed_usernames": [],
        "failed_usernames": [],
        "skipped_usernames": [],
    }


def save_progress(progress):
    """Salva o progresso atual."""
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)


def load_unfollow_list():
    """Carrega a lista de perfis para dar unfollow."""
    if not UNFOLLOW_LIST_FILE.exists():
        log(f"Arquivo {UNFOLLOW_LIST_FILE} não encontrado!", "ERROR")
        log("Certifique-se de que o arquivo unfollow_list.json está na mesma pasta do script.", "ERROR")
        sys.exit(1)
    
    with open(UNFOLLOW_LIST_FILE, "r") as f:
        data = json.load(f)
    
    return data


def load_whitelist():
    """Carrega a whitelist de perfis que não devem ser removidos."""
    if not WHITELIST_FILE.exists():
        # Criar arquivo de exemplo
        with open(WHITELIST_FILE, "w") as f:
            f.write("# Coloque aqui os usernames que você NÃO quer dar unfollow\n")
            f.write("# Um username por linha (sem @)\n")
            f.write("# Exemplo:\n")
            f.write("# instagram\n")
            f.write("# meuamigo123\n")
        return set()
    
    whitelist = set()
    with open(WHITELIST_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                whitelist.add(line.lower())
    return whitelist


def humanized_delay(min_sec=None, max_sec=None):
    """Gera um delay humanizado com variação aleatória."""
    min_s = min_sec or MIN_DELAY_BETWEEN_UNFOLLOWS
    max_s = max_sec or MAX_DELAY_BETWEEN_UNFOLLOWS
    delay = random.uniform(min_s, max_s)
    # Adiciona micro-variações para parecer mais humano
    delay += random.gauss(0, 1.5)
    return max(min_s, delay)


async def login_instagram(page):
    """Realiza o login no Instagram com suporte a 2FA."""
    log("Acessando Instagram...", "ACTION")
    await page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
    await asyncio.sleep(3)

    # Verificar se já está logado (sessão salva)
    try:
        await page.wait_for_selector('svg[aria-label="Página inicial"]', timeout=5000)
        log("Sessão anterior detectada! Já está logado.", "OK")
        return True
    except PlaywrightTimeout:
        pass

    # Também tentar seletor em inglês
    try:
        await page.wait_for_selector('svg[aria-label="Home"]', timeout=3000)
        log("Sessão anterior detectada! Já está logado.", "OK")
        return True
    except PlaywrightTimeout:
        pass

    log("Sessão não encontrada. Iniciando login...", "INFO")
    
    # Aceitar cookies se aparecer
    try:
        cookie_btn = await page.wait_for_selector(
            'button:has-text("Permitir todos os cookies"), button:has-text("Allow all cookies"), button:has-text("Aceitar")',
            timeout=5000
        )
        if cookie_btn:
            await cookie_btn.click()
            await asyncio.sleep(1)
    except PlaywrightTimeout:
        pass

    # Preencher credenciais
    print(f"\n{Colors.YELLOW}{'='*50}")
    print(f"  CREDENCIAIS DE LOGIN")
    print(f"{'='*50}{Colors.RESET}\n")
    
    username = input(f"  {Colors.CYAN}Username ou Email: {Colors.RESET}").strip()
    
    # Usar getpass para senha (oculta no terminal)
    import getpass
    password = getpass.getpass(f"  {Colors.CYAN}Senha: {Colors.RESET}").strip()
    
    print()
    
    log("Preenchendo credenciais...", "ACTION")
    
    # Preencher username
    username_input = await page.wait_for_selector(
        'input[name="username"]', timeout=10000
    )
    await username_input.click()
    await asyncio.sleep(0.5)
    await username_input.fill("")
    await username_input.type(username, delay=random.randint(50, 150))
    await asyncio.sleep(0.5)
    
    # Preencher senha
    password_input = await page.wait_for_selector('input[name="password"]')
    await password_input.click()
    await asyncio.sleep(0.5)
    await password_input.fill("")
    await password_input.type(password, delay=random.randint(50, 150))
    await asyncio.sleep(1)
    
    # Clicar em Entrar
    login_btn = await page.wait_for_selector(
        'button[type="submit"]'
    )
    await login_btn.click()
    log("Aguardando resposta do login...", "INFO")
    await asyncio.sleep(5)

    # Verificar se houve erro de login
    try:
        error_msg = await page.query_selector('#slfErrorAlert, [data-testid="login-error-message"]')
        if error_msg:
            error_text = await error_msg.inner_text()
            log(f"Erro no login: {error_text}", "ERROR")
            return False
    except Exception:
        pass

    # Verificar se precisa de 2FA
    needs_2fa = False
    try:
        # Verificar campo de código de verificação
        code_input = await page.wait_for_selector(
            'input[name="verificationCode"], input[name="security_code"], input[aria-label*="código"], input[aria-label*="code"]',
            timeout=8000
        )
        if code_input:
            needs_2fa = True
    except PlaywrightTimeout:
        pass

    if needs_2fa:
        log("Autenticação de dois fatores (2FA) detectada!", "WARN")
        print(f"\n{Colors.YELLOW}{'='*50}")
        print(f"  AUTENTICAÇÃO DE DOIS FATORES (2FA)")
        print(f"{'='*50}{Colors.RESET}")
        print(f"\n  {Colors.WHITE}O Instagram pediu o código de verificação.")
        print(f"  Verifique seu SMS ou Google Authenticator.{Colors.RESET}\n")
        
        code = input(f"  {Colors.CYAN}Código 2FA: {Colors.RESET}").strip()
        
        log("Inserindo código 2FA...", "ACTION")
        
        # Encontrar e preencher o campo do código
        code_input = await page.query_selector(
            'input[name="verificationCode"], input[name="security_code"], input[aria-label*="código"], input[aria-label*="code"]'
        )
        
        if code_input:
            await code_input.click()
            await asyncio.sleep(0.3)
            await code_input.fill("")
            await code_input.type(code, delay=random.randint(80, 200))
            await asyncio.sleep(1)
            
            # Clicar em confirmar
            confirm_btn = await page.query_selector(
                'button[type="submit"], button:has-text("Confirmar"), button:has-text("Confirm")'
            )
            if confirm_btn:
                await confirm_btn.click()
            
            log("Código 2FA enviado. Aguardando verificação...", "INFO")
            await asyncio.sleep(5)
        else:
            log("Não foi possível encontrar o campo de código 2FA.", "ERROR")
            return False

    # Lidar com "Salvar informações de login"
    try:
        save_btn = await page.wait_for_selector(
            'button:has-text("Salvar informações"), button:has-text("Save Info"), button:has-text("Save info")',
            timeout=5000
        )
        if save_btn:
            await save_btn.click()
            log("Informações de login salvas.", "OK")
            await asyncio.sleep(2)
    except PlaywrightTimeout:
        pass

    # Lidar com popup de notificações
    try:
        notif_btn = await page.wait_for_selector(
            'button:has-text("Agora não"), button:has-text("Not Now"), button:has-text("Agora Não")',
            timeout=5000
        )
        if notif_btn:
            await notif_btn.click()
            log("Popup de notificações descartado.", "OK")
            await asyncio.sleep(2)
    except PlaywrightTimeout:
        pass

    # Verificar se login foi bem sucedido
    try:
        await page.wait_for_selector(
            'svg[aria-label="Página inicial"], svg[aria-label="Home"], a[href="/direct/inbox/"]',
            timeout=10000
        )
        log("Login realizado com sucesso!", "OK")
        return True
    except PlaywrightTimeout:
        # Tentar verificar pela URL
        if "instagram.com" in page.url and "/accounts/login" not in page.url:
            log("Login aparentemente bem sucedido (verificado pela URL).", "OK")
            return True
        log("Não foi possível confirmar o login. Verifique manualmente.", "ERROR")
        return False


async def unfollow_user(page, username, attempt=1):
    """
    Dá unfollow em um perfil específico.
    Retorna: 'success', 'already_unfollowed', 'not_found', 'blocked', 'error'
    """
    max_attempts = 2
    
    try:
        profile_url = f"https://www.instagram.com/{username}/"
        log(f"Acessando perfil @{username}...", "ACTION")
        
        response = await page.goto(profile_url, wait_until="domcontentloaded", timeout=15000)
        await asyncio.sleep(random.uniform(2, 4))
        
        # Verificar se o perfil existe
        if response and response.status == 404:
            log(f"@{username} - Perfil não encontrado (404)", "WARN")
            return "not_found"
        
        # Verificar página de erro
        page_text = await page.inner_text("body")
        if "Esta página não está disponível" in page_text or "Sorry, this page" in page_text:
            log(f"@{username} - Perfil não existe mais", "WARN")
            return "not_found"

        # Procurar botão "Seguindo" / "Following"
        following_btn = None
        
        # Tentar vários seletores para o botão "Seguindo"
        selectors = [
            'button:has-text("Seguindo")',
            'button:has-text("Following")',
            'div[role="button"]:has-text("Seguindo")',
            'div[role="button"]:has-text("Following")',
        ]
        
        for selector in selectors:
            try:
                btn = await page.wait_for_selector(selector, timeout=3000)
                if btn:
                    following_btn = btn
                    break
            except PlaywrightTimeout:
                continue
        
        if not following_btn:
            # Verificar se já não segue
            try:
                follow_btn = await page.query_selector(
                    'button:has-text("Seguir"), button:has-text("Follow")'
                )
                if follow_btn:
                    btn_text = await follow_btn.inner_text()
                    if btn_text.strip() in ["Seguir", "Follow"]:
                        log(f"@{username} - Já não está seguindo", "WARN")
                        return "already_unfollowed"
            except Exception:
                pass
            
            if attempt < max_attempts:
                log(f"@{username} - Botão não encontrado, tentando novamente...", "WARN")
                await asyncio.sleep(3)
                return await unfollow_user(page, username, attempt + 1)
            
            log(f"@{username} - Não foi possível encontrar o botão de unfollow", "ERROR")
            return "error"
        
        # Clicar no botão "Seguindo"
        await following_btn.click()
        await asyncio.sleep(random.uniform(1, 2))
        
        # Clicar em "Deixar de seguir" no modal de confirmação
        unfollow_btn = None
        unfollow_selectors = [
            'button:has-text("Deixar de seguir")',
            'button:has-text("Unfollow")',
            'button._a9--._ap36._a9_1',  # seletor CSS do Instagram
        ]
        
        for selector in unfollow_selectors:
            try:
                btn = await page.wait_for_selector(selector, timeout=5000)
                if btn:
                    unfollow_btn = btn
                    break
            except PlaywrightTimeout:
                continue
        
        if not unfollow_btn:
            # Tentar encontrar pelo texto dentro de um dialog/modal
            try:
                unfollow_btn = await page.wait_for_selector(
                    '[role="dialog"] button:has-text("Deixar de seguir"), [role="dialog"] button:has-text("Unfollow")',
                    timeout=5000
                )
            except PlaywrightTimeout:
                pass
        
        if unfollow_btn:
            await unfollow_btn.click()
            await asyncio.sleep(random.uniform(1.5, 3))
            
            # Verificar se o unfollow foi realizado (botão mudou para "Seguir")
            try:
                await page.wait_for_selector(
                    'button:has-text("Seguir"), button:has-text("Follow")',
                    timeout=5000
                )
                log(f"@{username} - Unfollow realizado com sucesso!", "OK")
                return "success"
            except PlaywrightTimeout:
                # Verificar se apareceu mensagem de bloqueio
                try:
                    block_msg = await page.query_selector('text="Tente novamente mais tarde"')
                    if block_msg:
                        log(f"@{username} - AÇÃO BLOQUEADA pelo Instagram!", "ERROR")
                        return "blocked"
                except Exception:
                    pass
                
                log(f"@{username} - Unfollow pode ter sido realizado (não confirmado)", "WARN")
                return "success"
        else:
            log(f"@{username} - Modal de confirmação não apareceu", "ERROR")
            return "error"
            
    except PlaywrightTimeout:
        log(f"@{username} - Timeout ao acessar perfil", "ERROR")
        return "error"
    except Exception as e:
        log(f"@{username} - Erro inesperado: {str(e)}", "ERROR")
        return "error"


async def run_unfollow(args):
    """Função principal de unfollow."""
    print_banner()
    
    # Carregar dados
    log("Carregando lista de unfollow...", "INFO")
    unfollow_list = load_unfollow_list()
    whitelist = load_whitelist()
    progress = load_progress()
    
    # Resetar contagem diária se for um novo dia
    today = datetime.now().strftime("%Y-%m-%d")
    if progress["last_date"] != today:
        progress["unfollowed_today"] = 0
        progress["last_date"] = today
    
    # Filtrar whitelist
    filtered_list = [
        item for item in unfollow_list
        if item["username"].lower() not in whitelist
        and item["username"] not in progress["unfollowed_usernames"]
        and item["username"] not in progress["skipped_usernames"]
    ]
    
    # Estatísticas
    print(f"\n{Colors.BOLD}{'='*55}")
    print(f"  RESUMO DA OPERAÇÃO")
    print(f"{'='*55}{Colors.RESET}")
    print(f"  {Colors.WHITE}Total na lista de unfollow: {Colors.CYAN}{len(unfollow_list)}{Colors.RESET}")
    print(f"  {Colors.WHITE}Na whitelist (protegidos):  {Colors.GREEN}{len(whitelist)}{Colors.RESET}")
    print(f"  {Colors.WHITE}Já processados:            {Colors.YELLOW}{len(progress['unfollowed_usernames'])}{Colors.RESET}")
    print(f"  {Colors.WHITE}Restantes para processar:  {Colors.MAGENTA}{len(filtered_list)}{Colors.RESET}")
    print(f"  {Colors.WHITE}Unfollows hoje:            {Colors.CYAN}{progress['unfollowed_today']}/{MAX_UNFOLLOWS_PER_DAY}{Colors.RESET}")
    print(f"  {Colors.WHITE}Limite por hora:           {Colors.CYAN}{MAX_UNFOLLOWS_PER_HOUR}{Colors.RESET}")
    print(f"  {Colors.WHITE}Limite por dia:            {Colors.CYAN}{MAX_UNFOLLOWS_PER_DAY}{Colors.RESET}")
    
    if args.limit:
        print(f"  {Colors.WHITE}Limite desta sessão:       {Colors.YELLOW}{args.limit}{Colors.RESET}")
    
    print(f"{Colors.BOLD}{'='*55}{Colors.RESET}\n")
    
    # Verificar limite diário
    if progress["unfollowed_today"] >= MAX_UNFOLLOWS_PER_DAY:
        log(f"Limite diário de {MAX_UNFOLLOWS_PER_DAY} unfollows atingido!", "WARN")
        log("Tente novamente amanhã.", "INFO")
        return
    
    if not filtered_list:
        log("Nenhum perfil restante para dar unfollow!", "OK")
        return
    
    # Confirmar início
    if not args.yes:
        print(f"  {Colors.YELLOW}Deseja iniciar o processo de unfollow? (s/n): {Colors.RESET}", end="")
        confirm = input().strip().lower()
        if confirm not in ["s", "sim", "y", "yes"]:
            log("Operação cancelada pelo usuário.", "INFO")
            return
    
    print()
    
    # Definir limite da sessão
    session_limit = args.limit or (MAX_UNFOLLOWS_PER_DAY - progress["unfollowed_today"])
    session_limit = min(session_limit, len(filtered_list))
    
    # Iniciar Playwright
    log("Iniciando navegador...", "ACTION")
    
    async with async_playwright() as p:
        # Configurar browser
        browser_args = [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-dev-shm-usage",
        ]
        
        if args.headless:
            browser = await p.chromium.launch(
                headless=True,
                args=browser_args,
            )
        else:
            browser = await p.chromium.launch(
                headless=False,
                args=browser_args,
            )
        
        # Criar contexto com sessão persistente
        SESSION_DIR.mkdir(parents=True, exist_ok=True)
        
        context = await browser.new_context(
            storage_state=str(SESSION_DIR / "state.json") if (SESSION_DIR / "state.json").exists() else None,
            viewport={"width": 1366, "height": 768},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="pt-BR",
        )
        
        page = await context.new_page()
        
        # Adicionar script anti-detecção
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'languages', { get: () => ['pt-BR', 'pt', 'en-US', 'en'] });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
        """)
        
        # Login
        logged_in = await login_instagram(page)
        if not logged_in:
            log("Falha no login. Encerrando.", "ERROR")
            await browser.close()
            return
        
        # Salvar sessão após login
        await context.storage_state(path=str(SESSION_DIR / "state.json"))
        log("Sessão salva para uso futuro.", "OK")
        
        await asyncio.sleep(3)
        
        # Iniciar processo de unfollow
        log(f"\nIniciando unfollow de {session_limit} perfis...\n", "HEADER")
        
        session_count = 0
        hour_count = 0
        hour_start = time.time()
        batch_count = 0
        
        for i, item in enumerate(filtered_list[:session_limit]):
            username = item["username"]
            follow_date = item.get("date", "N/A")
            
            # Verificar limite diário
            if progress["unfollowed_today"] >= MAX_UNFOLLOWS_PER_DAY:
                log(f"\nLimite diário de {MAX_UNFOLLOWS_PER_DAY} atingido!", "WARN")
                break
            
            # Verificar limite por hora
            elapsed = time.time() - hour_start
            if elapsed >= 3600:
                hour_count = 0
                hour_start = time.time()
            
            if hour_count >= MAX_UNFOLLOWS_PER_HOUR:
                wait_time = 3600 - elapsed
                log(f"\nLimite por hora atingido! Aguardando {int(wait_time/60)} minutos...", "WARN")
                await asyncio.sleep(wait_time + random.uniform(30, 120))
                hour_count = 0
                hour_start = time.time()
            
            # Pausa entre lotes
            if batch_count >= BATCH_SIZE:
                pause = PAUSE_AFTER_BATCH + random.uniform(-60, 120)
                log(f"\nPausa de segurança: {int(pause/60)} minutos...\n", "WARN")
                await asyncio.sleep(pause)
                batch_count = 0
            
            # Exibir progresso
            remaining = session_limit - session_count
            log(f"[{session_count+1}/{session_limit}] @{username} (seguido desde {follow_date}) - Restam: {remaining}", "INFO")
            
            # Executar unfollow
            result = await unfollow_user(page, username)
            
            if result == "success":
                session_count += 1
                hour_count += 1
                batch_count += 1
                progress["unfollowed_today"] += 1
                progress["total_unfollowed"] += 1
                progress["unfollowed_usernames"].append(username)
                
            elif result == "already_unfollowed" or result == "not_found":
                progress["skipped_usernames"].append(username)
                
            elif result == "blocked":
                log("\n" + "!"*55, "ERROR")
                log("AÇÃO BLOQUEADA PELO INSTAGRAM!", "ERROR")
                log("O script será encerrado para proteger sua conta.", "ERROR")
                log("Aguarde pelo menos 24 horas antes de tentar novamente.", "ERROR")
                log("!"*55 + "\n", "ERROR")
                save_progress(progress)
                await context.storage_state(path=str(SESSION_DIR / "state.json"))
                await browser.close()
                return
                
            elif result == "error":
                progress["failed_usernames"].append(username)
            
            # Salvar progresso periodicamente
            if (session_count % 5) == 0:
                save_progress(progress)
                await context.storage_state(path=str(SESSION_DIR / "state.json"))
            
            # Delay humanizado
            if i < session_limit - 1:
                delay = humanized_delay()
                log(f"Aguardando {delay:.1f}s...", "INFO")
                await asyncio.sleep(delay)
        
        # Salvar progresso final
        save_progress(progress)
        await context.storage_state(path=str(SESSION_DIR / "state.json"))
        
        # Relatório final
        print(f"\n{Colors.BOLD}{'='*55}")
        print(f"  RELATÓRIO DA SESSÃO")
        print(f"{'='*55}{Colors.RESET}")
        print(f"  {Colors.GREEN}Unfollows realizados:  {session_count}{Colors.RESET}")
        print(f"  {Colors.YELLOW}Perfis ignorados:      {len(progress['skipped_usernames'])}{Colors.RESET}")
        print(f"  {Colors.RED}Falhas:                {len(progress['failed_usernames'])}{Colors.RESET}")
        print(f"  {Colors.CYAN}Total acumulado:       {progress['total_unfollowed']}{Colors.RESET}")
        print(f"  {Colors.WHITE}Restantes:             {len(filtered_list) - session_count}{Colors.RESET}")
        print(f"{Colors.BOLD}{'='*55}{Colors.RESET}\n")
        
        log("Sessão finalizada com sucesso!", "OK")
        log(f"Log salvo em: {LOG_FILE}", "INFO")
        log(f"Progresso salvo em: {PROGRESS_FILE}", "INFO")
        
        await browser.close()


async def list_mode(args):
    """Modo de listagem: mostra os próximos perfis a serem processados."""
    print_banner()
    
    unfollow_list = load_unfollow_list()
    whitelist = load_whitelist()
    progress = load_progress()
    
    filtered = [
        item for item in unfollow_list
        if item["username"].lower() not in whitelist
        and item["username"] not in progress["unfollowed_usernames"]
        and item["username"] not in progress["skipped_usernames"]
    ]
    
    count = args.list_count or 50
    
    print(f"\n{Colors.BOLD}  Próximos {min(count, len(filtered))} perfis para unfollow:{Colors.RESET}\n")
    print(f"  {'#':<5} {'Username':<30} {'Seguido desde':<15}")
    print(f"  {'-'*5} {'-'*30} {'-'*15}")
    
    for i, item in enumerate(filtered[:count]):
        print(f"  {i+1:<5} {Colors.CYAN}@{item['username']:<29}{Colors.RESET} {item.get('date', 'N/A')}")
    
    print(f"\n  {Colors.WHITE}Total restante: {len(filtered)} perfis{Colors.RESET}\n")


async def reset_mode():
    """Reseta o progresso."""
    print_banner()
    print(f"\n  {Colors.YELLOW}Tem certeza que deseja resetar todo o progresso? (s/n): {Colors.RESET}", end="")
    confirm = input().strip().lower()
    if confirm in ["s", "sim"]:
        if PROGRESS_FILE.exists():
            os.remove(PROGRESS_FILE)
        log("Progresso resetado com sucesso!", "OK")
    else:
        log("Operação cancelada.", "INFO")


async def status_mode():
    """Mostra o status atual."""
    print_banner()
    
    unfollow_list = load_unfollow_list()
    whitelist = load_whitelist()
    progress = load_progress()
    
    filtered = [
        item for item in unfollow_list
        if item["username"].lower() not in whitelist
        and item["username"] not in progress["unfollowed_usernames"]
        and item["username"] not in progress["skipped_usernames"]
    ]
    
    today = datetime.now().strftime("%Y-%m-%d")
    today_count = progress["unfollowed_today"] if progress["last_date"] == today else 0
    
    # Estimar tempo restante
    avg_time_per_unfollow = (MIN_DELAY_BETWEEN_UNFOLLOWS + MAX_DELAY_BETWEEN_UNFOLLOWS) / 2
    remaining = len(filtered)
    days_needed = remaining / MAX_UNFOLLOWS_PER_DAY
    
    print(f"\n{Colors.BOLD}{'='*55}")
    print(f"  STATUS DO PROCESSO DE UNFOLLOW")
    print(f"{'='*55}{Colors.RESET}")
    print(f"  {Colors.WHITE}Total na lista:            {Colors.CYAN}{len(unfollow_list)}{Colors.RESET}")
    print(f"  {Colors.WHITE}Na whitelist:              {Colors.GREEN}{len(whitelist)}{Colors.RESET}")
    print(f"  {Colors.WHITE}Já removidos (unfollow):   {Colors.GREEN}{progress['total_unfollowed']}{Colors.RESET}")
    print(f"  {Colors.WHITE}Ignorados/não encontrados: {Colors.YELLOW}{len(progress['skipped_usernames'])}{Colors.RESET}")
    print(f"  {Colors.WHITE}Falhas:                    {Colors.RED}{len(progress['failed_usernames'])}{Colors.RESET}")
    print(f"  {Colors.WHITE}Restantes:                 {Colors.MAGENTA}{remaining}{Colors.RESET}")
    print(f"  {Colors.WHITE}Unfollows hoje:            {Colors.CYAN}{today_count}/{MAX_UNFOLLOWS_PER_DAY}{Colors.RESET}")
    print(f"  {Colors.WHITE}Dias estimados restantes:  {Colors.YELLOW}{days_needed:.0f} dias{Colors.RESET}")
    print(f"{Colors.BOLD}{'='*55}{Colors.RESET}\n")


def main():
    parser = argparse.ArgumentParser(
        description="Instagram Auto-Unfollow Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
{Colors.CYAN}Exemplos de uso:{Colors.RESET}
  python3 insta_unfollow.py                    # Inicia o unfollow (modo padrão)
  python3 insta_unfollow.py --limit 50         # Limita a 50 unfollows nesta sessão
  python3 insta_unfollow.py --headless         # Roda sem abrir janela do navegador
  python3 insta_unfollow.py --list             # Lista os próximos perfis
  python3 insta_unfollow.py --list 100         # Lista os próximos 100 perfis
  python3 insta_unfollow.py --status           # Mostra o status do progresso
  python3 insta_unfollow.py --reset            # Reseta o progresso
  python3 insta_unfollow.py -y --limit 30      # Inicia sem pedir confirmação
        """
    )
    
    parser.add_argument(
        "--limit", "-l", type=int, default=None,
        help="Número máximo de unfollows nesta sessão"
    )
    parser.add_argument(
        "--headless", action="store_true",
        help="Executar sem interface gráfica (modo headless)"
    )
    parser.add_argument(
        "--list", dest="list_count", nargs="?", const=50, type=int,
        help="Listar próximos perfis para unfollow (padrão: 50)"
    )
    parser.add_argument(
        "--status", "-s", action="store_true",
        help="Mostrar status do progresso"
    )
    parser.add_argument(
        "--reset", action="store_true",
        help="Resetar todo o progresso"
    )
    parser.add_argument(
        "-y", "--yes", action="store_true",
        help="Pular confirmação inicial"
    )
    
    args = parser.parse_args()
    
    if args.status:
        asyncio.run(status_mode())
    elif args.reset:
        asyncio.run(reset_mode())
    elif args.list_count is not None:
        asyncio.run(list_mode(args))
    else:
        asyncio.run(run_unfollow(args))


if __name__ == "__main__":
    main()
