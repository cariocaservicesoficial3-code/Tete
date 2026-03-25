#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════╗
║  Instagram Auto-Unfollow Script v2.0 (Playwright + Rich)        ║
║  Conta: @cariocamafiadostutorsoficial                           ║
║  Autor: Manus AI                                                ║
║  Data: 25/03/2026                                               ║
║                                                                 ║
║  Funcionalidades:                                               ║
║  - Login com suporte a 2FA (SMS / Google Authenticator)         ║
║  - Menu interativo com configuracao de velocidade               ║
║  - Debug log completo em tempo real (/sdcard/nh_files/)         ║
║  - Painel profissional com Rich                                 ║
║  - Avisos de erros e restricoes em tempo real                   ║
║  - Salva progresso para retomar depois                          ║
╚══════════════════════════════════════════════════════════════════╝
"""

import asyncio
import json
import os
import sys
import random
import time
import logging
import traceback
import getpass
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.layout import Layout
    from rich.live import Live
    from rich.text import Text
    from rich.prompt import Prompt, IntPrompt, Confirm
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn, MofNCompleteColumn
    from rich.align import Align
    from rich.rule import Rule
    from rich.columns import Columns
    from rich import box
    from rich.logging import RichHandler
    from rich.style import Style
    from rich.markup import escape
    from rich.traceback import install as install_rich_traceback
except ImportError:
    print("\n[ERRO] Biblioteca 'rich' nao esta instalada!")
    print("Execute: pip install rich")
    sys.exit(1)

try:
    from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("\n[ERRO] Playwright nao esta instalado!")
    print("Execute: pip install playwright && playwright install chromium")
    sys.exit(1)

# Instalar traceback bonito do Rich
install_rich_traceback(show_locals=True)

# Console principal
console = Console()

# ═══════════════════════════════════════════════════════════
# PATHS E CONFIGURACOES
# ═══════════════════════════════════════════════════════════

SCRIPT_DIR = Path(__file__).parent.resolve()
UNFOLLOW_LIST_FILE = SCRIPT_DIR / "unfollow_list.json"
PROGRESS_FILE = SCRIPT_DIR / "progress.json"
SESSION_DIR = SCRIPT_DIR / "session_data"
WHITELIST_FILE = SCRIPT_DIR / "whitelist.txt"
CONFIG_FILE = SCRIPT_DIR / "config.json"

# Debug log path - /sdcard/nh_files/ para NetHunter / Kali no Android
# Se nao existir (ex: rodando em PC), usa a pasta do script
DEBUG_LOG_DIR = Path("/sdcard/nh_files")
if not DEBUG_LOG_DIR.exists():
    DEBUG_LOG_DIR = SCRIPT_DIR / "logs"
DEBUG_LOG_DIR.mkdir(parents=True, exist_ok=True)
DEBUG_LOG_FILE = DEBUG_LOG_DIR / "debug_log.txt"


# ═══════════════════════════════════════════════════════════
# SISTEMA DE DEBUG LOG
# ═══════════════════════════════════════════════════════════

class DebugLogger:
    """Sistema de debug log completo em tempo real."""

    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.start_time = time.time()
        self.action_count = 0
        self.error_count = 0
        self.warning_count = 0

        # Configurar logger do Python
        self.logger = logging.getLogger("InstaUnfollow")
        self.logger.setLevel(logging.DEBUG)

        # Limpar handlers anteriores
        self.logger.handlers.clear()

        # Handler para arquivo com encoding UTF-8
        file_handler = logging.FileHandler(self.log_path, mode="a", encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(funcName)-25s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)

        # Escrever cabecalho da sessao
        self._write_session_header()

    def _write_session_header(self):
        """Escreve o cabecalho da nova sessao no log."""
        separator = "=" * 90
        header = f"""
{separator}
  INSTAGRAM AUTO-UNFOLLOW - DEBUG LOG
  Session ID: {self.session_id}
  Iniciado em: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
  Script Version: 2.0
  Log Path: {self.log_path}
  Python: {sys.version.split()[0]}
  OS: {os.uname().sysname} {os.uname().release}
{separator}
"""
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(header)

    def debug(self, msg):
        """Log de debug (detalhes tecnicos)."""
        self.logger.debug(msg)

    def info(self, msg):
        """Log informativo."""
        self.logger.info(msg)

    def action(self, msg):
        """Log de acao executada."""
        self.action_count += 1
        self.logger.info(f"[ACTION #{self.action_count}] {msg}")

    def success(self, msg):
        """Log de sucesso."""
        self.logger.info(f"[SUCCESS] {msg}")

    def warning(self, msg):
        """Log de aviso."""
        self.warning_count += 1
        self.logger.warning(f"[WARNING #{self.warning_count}] {msg}")

    def error(self, msg):
        """Log de erro."""
        self.error_count += 1
        self.logger.error(f"[ERROR #{self.error_count}] {msg}")

    def critical(self, msg):
        """Log critico."""
        self.logger.critical(f"[CRITICAL] {msg}")

    def exception(self, msg, exc_info=True):
        """Log de excecao com traceback."""
        self.error_count += 1
        self.logger.exception(f"[EXCEPTION] {msg}", exc_info=exc_info)

    def network(self, method, url, status=None, response_time=None):
        """Log de requisicao de rede."""
        rt = f" ({response_time:.2f}s)" if response_time else ""
        st = f" -> {status}" if status else ""
        self.logger.debug(f"[NETWORK] {method} {url}{st}{rt}")

    def performance(self, operation, elapsed):
        """Log de performance."""
        self.logger.debug(f"[PERF] {operation}: {elapsed:.3f}s")

    def unfollow_result(self, username, result, elapsed):
        """Log especifico de resultado de unfollow."""
        status_map = {
            "success": "UNFOLLOW OK",
            "already_unfollowed": "JA NAO SEGUIA",
            "not_found": "PERFIL NAO ENCONTRADO",
            "blocked": "ACAO BLOQUEADA",
            "error": "ERRO",
            "private_no_button": "PERFIL PRIVADO SEM BOTAO",
        }
        status = status_map.get(result, result.upper())
        self.logger.info(
            f"[UNFOLLOW] @{username} | Resultado: {status} | Tempo: {elapsed:.2f}s"
        )

    def session_summary(self, stats: dict):
        """Escreve resumo da sessao no log."""
        elapsed = time.time() - self.start_time
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)

        summary = f"""
{'='*90}
  RESUMO DA SESSAO - {self.session_id}
  Duracao: {minutes}min {seconds}s
  Unfollows realizados: {stats.get('success', 0)}
  Perfis nao encontrados: {stats.get('not_found', 0)}
  Ja nao seguia: {stats.get('already_unfollowed', 0)}
  Erros: {stats.get('errors', 0)}
  Bloqueios: {stats.get('blocked', 0)}
  Total de acoes: {self.action_count}
  Total de warnings: {self.warning_count}
  Total de erros: {self.error_count}
  Finalizado em: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}
{'='*90}
"""
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(summary)


# Inicializar logger global
debug_log = DebugLogger(DEBUG_LOG_FILE)


# ═══════════════════════════════════════════════════════════
# PERFIS DE VELOCIDADE
# ═══════════════════════════════════════════════════════════

class SpeedProfile(Enum):
    ULTRA_SAFE = "ultra_safe"
    SAFE = "safe"
    NORMAL = "normal"
    FAST = "fast"
    TURBO = "turbo"
    CUSTOM = "custom"


SPEED_PROFILES = {
    SpeedProfile.ULTRA_SAFE: {
        "name": "Ultra Seguro",
        "description": "Mais lento, risco zero de bloqueio",
        "min_delay": 40,
        "max_delay": 90,
        "per_hour": 12,
        "per_day": 80,
        "batch_size": 8,
        "batch_pause": 600,
        "icon": "[green]ULTRA SAFE[/]",
    },
    SpeedProfile.SAFE: {
        "name": "Seguro",
        "description": "Velocidade moderada, risco muito baixo",
        "min_delay": 25,
        "max_delay": 55,
        "per_hour": 20,
        "per_day": 120,
        "batch_size": 15,
        "batch_pause": 420,
        "icon": "[green]SAFE[/]",
    },
    SpeedProfile.NORMAL: {
        "name": "Normal",
        "description": "Equilibrio entre velocidade e seguranca",
        "min_delay": 15,
        "max_delay": 45,
        "per_hour": 25,
        "per_day": 150,
        "batch_size": 20,
        "batch_pause": 300,
        "icon": "[yellow]NORMAL[/]",
    },
    SpeedProfile.FAST: {
        "name": "Rapido",
        "description": "Mais rapido, risco moderado de bloqueio",
        "min_delay": 8,
        "max_delay": 25,
        "per_hour": 40,
        "per_day": 200,
        "batch_size": 25,
        "batch_pause": 180,
        "icon": "[bold yellow]FAST[/]",
    },
    SpeedProfile.TURBO: {
        "name": "Turbo",
        "description": "Velocidade maxima, ALTO risco de bloqueio",
        "min_delay": 4,
        "max_delay": 12,
        "per_hour": 60,
        "per_day": 300,
        "batch_size": 30,
        "batch_pause": 120,
        "icon": "[bold red]TURBO[/]",
    },
}

DEFAULT_CONFIG = {
    "speed_profile": "normal",
    "custom_min_delay": 15,
    "custom_max_delay": 45,
    "custom_per_hour": 25,
    "custom_per_day": 150,
    "custom_batch_size": 20,
    "custom_batch_pause": 300,
    "headless": True,
    "debug_log_path": str(DEBUG_LOG_FILE),
}


# ═══════════════════════════════════════════════════════════
# FUNCOES AUXILIARES
# ═══════════════════════════════════════════════════════════

def load_config():
    """Carrega configuracoes salvas."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            saved = json.load(f)
            config = DEFAULT_CONFIG.copy()
            config.update(saved)
            return config
    return DEFAULT_CONFIG.copy()


def save_config(config):
    """Salva configuracoes."""
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
    debug_log.info(f"Configuracao salva: {json.dumps(config)}")


def get_speed_settings(config):
    """Retorna as configuracoes de velocidade ativas."""
    profile_name = config.get("speed_profile", "normal")
    if profile_name == "custom":
        return {
            "name": "Personalizado",
            "description": "Configuracao manual do usuario",
            "min_delay": config.get("custom_min_delay", 15),
            "max_delay": config.get("custom_max_delay", 45),
            "per_hour": config.get("custom_per_hour", 25),
            "per_day": config.get("custom_per_day", 150),
            "batch_size": config.get("custom_batch_size", 20),
            "batch_pause": config.get("custom_batch_pause", 300),
            "icon": "[cyan]CUSTOM[/]",
        }
    try:
        profile = SpeedProfile(profile_name)
    except ValueError:
        profile = SpeedProfile.NORMAL
    return SPEED_PROFILES.get(profile, SPEED_PROFILES[SpeedProfile.NORMAL])


def load_progress():
    """Carrega o progresso salvo."""
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
        "blocked_count": 0,
        "sessions_count": 0,
    }


def save_progress(progress):
    """Salva o progresso."""
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)


def load_unfollow_list():
    """Carrega a lista de perfis para unfollow."""
    if not UNFOLLOW_LIST_FILE.exists():
        console.print(Panel(
            "[bold red]Arquivo unfollow_list.json nao encontrado![/]\n"
            "Certifique-se de que o arquivo esta na mesma pasta do script.",
            title="ERRO", border_style="red"
        ))
        debug_log.critical(f"Arquivo nao encontrado: {UNFOLLOW_LIST_FILE}")
        sys.exit(1)
    with open(UNFOLLOW_LIST_FILE, "r") as f:
        data = json.load(f)
    debug_log.info(f"Lista de unfollow carregada: {len(data)} perfis")
    return data


def load_whitelist():
    """Carrega a whitelist."""
    if not WHITELIST_FILE.exists():
        with open(WHITELIST_FILE, "w") as f:
            f.write("# Coloque aqui os usernames que voce NAO quer dar unfollow\n")
            f.write("# Um username por linha (sem @)\n")
        return set()
    whitelist = set()
    with open(WHITELIST_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                whitelist.add(line.lower())
    debug_log.info(f"Whitelist carregada: {len(whitelist)} perfis protegidos")
    return whitelist


def humanized_delay(min_sec, max_sec):
    """Gera delay humanizado."""
    delay = random.uniform(min_sec, max_sec)
    delay += random.gauss(0, 1.2)
    return max(min_sec * 0.8, delay)


# ═══════════════════════════════════════════════════════════
# VISUAL / UI COM RICH
# ═══════════════════════════════════════════════════════════

def show_banner():
    """Exibe o banner principal."""
    banner_text = """[bold cyan]
 ██╗███╗   ██╗███████╗████████╗ █████╗ 
 ██║████╗  ██║██╔════╝╚══██╔══╝██╔══██╗
 ██║██╔██╗ ██║███████╗   ██║   ███████║
 ██║██║╚██╗██║╚════██║   ██║   ██╔══██║
 ██║██║ ╚████║███████║   ██║   ██║  ██║
 ╚═╝╚═╝  ╚═══╝╚══════╝   ╚═╝   ╚═╝  ╚═╝[/]
[bold yellow]     AUTO-UNFOLLOW SCRIPT v2.0[/]
[dim]     Playwright + Rich | Kali Linux[/]"""
    console.print(Panel(
        Align.center(banner_text),
        border_style="cyan",
        padding=(0, 2),
    ))


def show_main_menu():
    """Exibe o menu principal e retorna a opcao escolhida."""
    config = load_config()
    speed = get_speed_settings(config)
    progress = load_progress()

    today = datetime.now().strftime("%Y-%m-%d")
    today_count = progress["unfollowed_today"] if progress["last_date"] == today else 0

    # Painel de status rapido
    status_text = (
        f"[bold]Unfollows hoje:[/] [cyan]{today_count}[/]/[cyan]{speed['per_day']}[/]  |  "
        f"[bold]Total:[/] [green]{progress['total_unfollowed']}[/]  |  "
        f"[bold]Velocidade:[/] {speed['icon']}  |  "
        f"[bold]Log:[/] [dim]{DEBUG_LOG_FILE}[/]"
    )
    console.print(Panel(status_text, border_style="dim", padding=(0, 1)))

    console.print()

    menu_table = Table(
        show_header=False,
        box=box.ROUNDED,
        border_style="cyan",
        padding=(0, 2),
        title="[bold white]MENU PRINCIPAL[/]",
        title_style="bold cyan",
    )
    menu_table.add_column("Opcao", style="bold yellow", width=6, justify="center")
    menu_table.add_column("Descricao", style="white")

    menu_table.add_row("1", "[bold]Iniciar Unfollow[/]")
    menu_table.add_row("2", "[bold]Configurar Velocidade[/]")
    menu_table.add_row("3", "[bold]Ver Status / Progresso[/]")
    menu_table.add_row("4", "[bold]Listar Proximos Perfis[/]")
    menu_table.add_row("5", "[bold]Gerenciar Whitelist[/]")
    menu_table.add_row("6", "[bold]Ver Debug Log[/]")
    menu_table.add_row("7", "[bold]Resetar Progresso[/]")
    menu_table.add_row("8", "[bold]Configuracoes Gerais[/]")
    menu_table.add_row("0", "[bold]Sair[/]")

    console.print(Align.center(menu_table))
    console.print()

    choice = Prompt.ask(
        "[bold cyan]  Escolha uma opcao[/]",
        choices=["0", "1", "2", "3", "4", "5", "6", "7", "8"],
        default="1"
    )
    return choice


def show_speed_menu(config):
    """Menu de configuracao de velocidade."""
    console.clear()
    show_banner()

    current = get_speed_settings(config)

    console.print(Panel(
        f"[bold]Perfil atual:[/] {current['icon']}  {current['name']}\n"
        f"[dim]{current['description']}[/]",
        title="[bold yellow]CONFIGURACAO DE VELOCIDADE[/]",
        border_style="yellow",
    ))

    speed_table = Table(
        box=box.DOUBLE_EDGE,
        border_style="yellow",
        title="[bold]Perfis Disponiveis[/]",
        padding=(0, 1),
    )
    speed_table.add_column("#", style="bold yellow", justify="center", width=4)
    speed_table.add_column("Perfil", style="bold white", width=16)
    speed_table.add_column("Delay (s)", justify="center", width=12)
    speed_table.add_column("/Hora", justify="center", width=8)
    speed_table.add_column("/Dia", justify="center", width=8)
    speed_table.add_column("Lote", justify="center", width=8)
    speed_table.add_column("Pausa (min)", justify="center", width=12)
    speed_table.add_column("Risco", justify="center", width=14)

    risk_styles = {
        SpeedProfile.ULTRA_SAFE: "[bold green]Nenhum[/]",
        SpeedProfile.SAFE: "[green]Muito Baixo[/]",
        SpeedProfile.NORMAL: "[yellow]Baixo[/]",
        SpeedProfile.FAST: "[bold yellow]Moderado[/]",
        SpeedProfile.TURBO: "[bold red]ALTO[/]",
    }

    for i, (profile, settings) in enumerate(SPEED_PROFILES.items(), 1):
        speed_table.add_row(
            str(i),
            f"{settings['name']}",
            f"{settings['min_delay']}-{settings['max_delay']}",
            str(settings['per_hour']),
            str(settings['per_day']),
            str(settings['batch_size']),
            f"{settings['batch_pause'] // 60}",
            risk_styles.get(profile, "[white]?[/]"),
        )
    speed_table.add_row(
        "6", "Personalizado", "Manual", "Manual", "Manual", "Manual", "Manual", "[cyan]Voce define[/]"
    )

    console.print(speed_table)
    console.print()

    choice = Prompt.ask(
        "[bold cyan]Escolha o perfil de velocidade[/]",
        choices=["1", "2", "3", "4", "5", "6", "0"],
        default="3"
    )

    if choice == "0":
        return config

    profile_map = {
        "1": "ultra_safe",
        "2": "safe",
        "3": "normal",
        "4": "fast",
        "5": "turbo",
    }

    if choice in profile_map:
        config["speed_profile"] = profile_map[choice]
        save_config(config)
        selected = get_speed_settings(config)
        console.print(Panel(
            f"[bold green]Perfil alterado para:[/] {selected['icon']}  {selected['name']}\n"
            f"[dim]{selected['description']}[/]",
            border_style="green",
        ))
        debug_log.info(f"Perfil de velocidade alterado para: {selected['name']}")

    elif choice == "6":
        console.print(Rule("[bold yellow]Configuracao Personalizada[/]"))
        config["speed_profile"] = "custom"
        config["custom_min_delay"] = IntPrompt.ask("[cyan]Delay minimo entre unfollows (segundos)[/]", default=15)
        config["custom_max_delay"] = IntPrompt.ask("[cyan]Delay maximo entre unfollows (segundos)[/]", default=45)
        config["custom_per_hour"] = IntPrompt.ask("[cyan]Maximo de unfollows por hora[/]", default=25)
        config["custom_per_day"] = IntPrompt.ask("[cyan]Maximo de unfollows por dia[/]", default=150)
        config["custom_batch_size"] = IntPrompt.ask("[cyan]Tamanho do lote (unfollows antes de pausar)[/]", default=20)
        config["custom_batch_pause"] = IntPrompt.ask("[cyan]Pausa entre lotes (segundos)[/]", default=300)
        save_config(config)
        console.print(Panel("[bold green]Configuracao personalizada salva![/]", border_style="green"))
        debug_log.info(f"Configuracao personalizada salva: delay={config['custom_min_delay']}-{config['custom_max_delay']}s, "
                       f"hora={config['custom_per_hour']}, dia={config['custom_per_day']}")

    Prompt.ask("\n[dim]Pressione Enter para voltar ao menu[/]", default="")
    return config


def show_status(config):
    """Exibe o status completo do progresso."""
    console.clear()
    show_banner()

    unfollow_list = load_unfollow_list()
    whitelist = load_whitelist()
    progress = load_progress()
    speed = get_speed_settings(config)

    today = datetime.now().strftime("%Y-%m-%d")
    today_count = progress["unfollowed_today"] if progress["last_date"] == today else 0

    filtered = [
        item for item in unfollow_list
        if item["username"].lower() not in whitelist
        and item["username"] not in progress["unfollowed_usernames"]
        and item["username"] not in progress["skipped_usernames"]
    ]

    remaining = len(filtered)
    days_needed = remaining / speed["per_day"] if speed["per_day"] > 0 else 999

    # Porcentagem concluida
    total_to_process = len(unfollow_list) - len(whitelist)
    done = progress['total_unfollowed'] + len(progress['skipped_usernames'])
    pct = (done / total_to_process * 100) if total_to_process > 0 else 0

    # Tabela de progresso
    progress_table = Table(
        box=box.DOUBLE_EDGE,
        border_style="cyan",
        title="[bold white]STATUS DO PROGRESSO[/]",
        padding=(0, 2),
    )
    progress_table.add_column("Metrica", style="bold white", width=35)
    progress_table.add_column("Valor", style="bold cyan", justify="right", width=20)

    progress_table.add_row("Total na lista de unfollow", f"[white]{len(unfollow_list)}[/]")
    progress_table.add_row("Na whitelist (protegidos)", f"[green]{len(whitelist)}[/]")
    progress_table.add_row("Unfollows realizados (total)", f"[bold green]{progress['total_unfollowed']}[/]")
    progress_table.add_row("Perfis ignorados/nao encontrados", f"[yellow]{len(progress['skipped_usernames'])}[/]")
    progress_table.add_row("Falhas", f"[red]{len(progress['failed_usernames'])}[/]")
    progress_table.add_row("Bloqueios detectados", f"[bold red]{progress.get('blocked_count', 0)}[/]")
    progress_table.add_row("Sessoes executadas", f"[white]{progress.get('sessions_count', 0)}[/]")
    progress_table.add_row("[dim]" + "-" * 30 + "[/]", "[dim]" + "-" * 15 + "[/]")
    progress_table.add_row("[bold]Restantes para processar[/]", f"[bold magenta]{remaining}[/]")
    progress_table.add_row("Unfollows hoje", f"[cyan]{today_count}/{speed['per_day']}[/]")
    progress_table.add_row("Dias estimados restantes", f"[yellow]{days_needed:.0f} dias[/]")
    progress_table.add_row("Progresso geral", f"[bold green]{pct:.1f}%[/]")

    console.print(progress_table)

    # Tabela de velocidade ativa
    speed_table = Table(
        box=box.ROUNDED,
        border_style="yellow",
        title=f"[bold]VELOCIDADE ATIVA: {speed['icon']}  {speed['name']}[/]",
        padding=(0, 2),
    )
    speed_table.add_column("Parametro", style="white", width=30)
    speed_table.add_column("Valor", style="yellow", justify="right", width=20)

    speed_table.add_row("Delay entre unfollows", f"{speed['min_delay']}-{speed['max_delay']}s")
    speed_table.add_row("Maximo por hora", f"{speed['per_hour']}")
    speed_table.add_row("Maximo por dia", f"{speed['per_day']}")
    speed_table.add_row("Tamanho do lote", f"{speed['batch_size']}")
    speed_table.add_row("Pausa entre lotes", f"{speed['batch_pause'] // 60} min")

    console.print(speed_table)

    # Info do debug log
    log_size = DEBUG_LOG_FILE.stat().st_size if DEBUG_LOG_FILE.exists() else 0
    log_size_str = f"{log_size / 1024:.1f} KB" if log_size < 1024 * 1024 else f"{log_size / (1024*1024):.1f} MB"

    console.print(Panel(
        f"[dim]Debug Log:[/] {DEBUG_LOG_FILE}\n"
        f"[dim]Tamanho:[/] {log_size_str}",
        title="[bold]DEBUG LOG[/]",
        border_style="dim",
    ))

    Prompt.ask("\n[dim]Pressione Enter para voltar ao menu[/]", default="")


def show_list_profiles():
    """Lista os proximos perfis para unfollow."""
    console.clear()
    show_banner()

    unfollow_list = load_unfollow_list()
    whitelist = load_whitelist()
    progress = load_progress()

    filtered = [
        item for item in unfollow_list
        if item["username"].lower() not in whitelist
        and item["username"] not in progress["unfollowed_usernames"]
        and item["username"] not in progress["skipped_usernames"]
    ]

    count = IntPrompt.ask("[cyan]Quantos perfis deseja listar?[/]", default=30)
    count = min(count, len(filtered))

    table = Table(
        box=box.SIMPLE_HEAVY,
        border_style="cyan",
        title=f"[bold]PROXIMOS {count} PERFIS PARA UNFOLLOW[/]",
        padding=(0, 1),
    )
    table.add_column("#", style="bold yellow", justify="right", width=5)
    table.add_column("Username", style="bold cyan", width=30)
    table.add_column("Seguido desde", style="white", justify="center", width=15)

    for i, item in enumerate(filtered[:count], 1):
        table.add_row(str(i), f"@{item['username']}", item.get("date", "N/A"))

    console.print(table)
    console.print(f"\n  [dim]Total restante: {len(filtered)} perfis[/]\n")

    Prompt.ask("[dim]Pressione Enter para voltar ao menu[/]", default="")


def show_whitelist_menu():
    """Menu de gerenciamento da whitelist."""
    console.clear()
    show_banner()

    whitelist = load_whitelist()

    console.print(Panel(
        f"[bold]Perfis protegidos:[/] {len(whitelist)}\n"
        f"[dim]Arquivo:[/] {WHITELIST_FILE}",
        title="[bold yellow]WHITELIST[/]",
        border_style="yellow",
    ))

    if whitelist:
        table = Table(box=box.SIMPLE, border_style="dim")
        table.add_column("#", style="dim", width=5)
        table.add_column("Username", style="green")
        for i, user in enumerate(sorted(whitelist), 1):
            table.add_row(str(i), f"@{user}")
        console.print(table)

    console.print()
    console.print("[bold]1[/] - Adicionar username a whitelist")
    console.print("[bold]2[/] - Remover username da whitelist")
    console.print("[bold]0[/] - Voltar")
    console.print()

    choice = Prompt.ask("[cyan]Opcao[/]", choices=["0", "1", "2"], default="0")

    if choice == "1":
        user = Prompt.ask("[cyan]Username para adicionar (sem @)[/]").strip().lower()
        if user:
            with open(WHITELIST_FILE, "a") as f:
                f.write(f"{user}\n")
            console.print(f"[green]@{user} adicionado a whitelist![/]")
            debug_log.info(f"Whitelist: adicionado @{user}")

    elif choice == "2":
        user = Prompt.ask("[cyan]Username para remover (sem @)[/]").strip().lower()
        if user in whitelist:
            lines = []
            with open(WHITELIST_FILE, "r") as f:
                lines = f.readlines()
            with open(WHITELIST_FILE, "w") as f:
                for line in lines:
                    if line.strip().lower() != user:
                        f.write(line)
            console.print(f"[green]@{user} removido da whitelist![/]")
            debug_log.info(f"Whitelist: removido @{user}")
        else:
            console.print(f"[red]@{user} nao esta na whitelist.[/]")

    Prompt.ask("\n[dim]Pressione Enter para voltar ao menu[/]", default="")


def show_debug_log():
    """Exibe as ultimas linhas do debug log."""
    console.clear()
    show_banner()

    if not DEBUG_LOG_FILE.exists():
        console.print(Panel("[yellow]Debug log ainda esta vazio.[/]", border_style="yellow"))
        Prompt.ask("\n[dim]Pressione Enter para voltar[/]", default="")
        return

    lines_count = IntPrompt.ask("[cyan]Quantas linhas deseja ver?[/]", default=50)

    with open(DEBUG_LOG_FILE, "r", encoding="utf-8") as f:
        all_lines = f.readlines()

    last_lines = all_lines[-lines_count:]

    log_size = DEBUG_LOG_FILE.stat().st_size
    log_size_str = f"{log_size / 1024:.1f} KB" if log_size < 1024 * 1024 else f"{log_size / (1024*1024):.1f} MB"

    console.print(Panel(
        f"[dim]Arquivo:[/] {DEBUG_LOG_FILE}\n"
        f"[dim]Tamanho:[/] {log_size_str} | [dim]Total de linhas:[/] {len(all_lines)}\n"
        f"[dim]Exibindo ultimas {len(last_lines)} linhas:[/]",
        title="[bold]DEBUG LOG[/]",
        border_style="cyan",
    ))

    for line in last_lines:
        line = line.rstrip()
        if "ERROR" in line or "CRITICAL" in line or "EXCEPTION" in line:
            console.print(f"  [red]{escape(line)}[/]")
        elif "WARNING" in line:
            console.print(f"  [yellow]{escape(line)}[/]")
        elif "SUCCESS" in line or "UNFOLLOW OK" in line:
            console.print(f"  [green]{escape(line)}[/]")
        elif "ACTION" in line:
            console.print(f"  [magenta]{escape(line)}[/]")
        elif "====" in line:
            console.print(f"  [bold cyan]{escape(line)}[/]")
        else:
            console.print(f"  [dim]{escape(line)}[/]")

    Prompt.ask("\n[dim]Pressione Enter para voltar ao menu[/]", default="")


def show_general_settings(config):
    """Menu de configuracoes gerais."""
    console.clear()
    show_banner()

    headless_str = "Sim (sem janela)" if config.get("headless", True) else "Nao (com janela)"
    session_exists = "Sim" if (SESSION_DIR / "state.json").exists() else "Nao"

    console.print(Panel(
        f"[bold]Modo headless:[/] {headless_str}\n"
        f"[bold]Debug log path:[/] {config.get('debug_log_path', str(DEBUG_LOG_FILE))}\n"
        f"[bold]Sessao salva:[/] {session_exists}",
        title="[bold yellow]CONFIGURACOES GERAIS[/]",
        border_style="yellow",
    ))

    console.print("[bold]1[/] - Alternar modo headless (com/sem janela)")
    console.print("[bold]2[/] - Limpar sessao salva (forcar novo login)")
    console.print("[bold]3[/] - Limpar debug log")
    console.print("[bold]0[/] - Voltar")
    console.print()

    choice = Prompt.ask("[cyan]Opcao[/]", choices=["0", "1", "2", "3"], default="0")

    if choice == "1":
        config["headless"] = not config.get("headless", True)
        save_config(config)
        mode = "HEADLESS (sem janela)" if config["headless"] else "COM JANELA"
        console.print(f"[green]Modo alterado para: {mode}[/]")
        debug_log.info(f"Modo headless alterado para: {config['headless']}")

    elif choice == "2":
        state_file = SESSION_DIR / "state.json"
        if state_file.exists():
            os.remove(state_file)
            console.print("[green]Sessao limpa! Sera necessario fazer login novamente.[/]")
            debug_log.info("Sessao de login limpa pelo usuario")
        else:
            console.print("[yellow]Nenhuma sessao salva encontrada.[/]")

    elif choice == "3":
        if DEBUG_LOG_FILE.exists():
            os.remove(DEBUG_LOG_FILE)
            console.print(f"[green]Debug log limpo: {DEBUG_LOG_FILE}[/]")
        else:
            console.print("[yellow]Debug log ja esta vazio.[/]")

    Prompt.ask("\n[dim]Pressione Enter para voltar ao menu[/]", default="")
    return config


def reset_progress_menu():
    """Menu de reset de progresso."""
    console.clear()
    show_banner()

    progress = load_progress()

    console.print(Panel(
        f"[bold]Unfollows realizados:[/] {progress['total_unfollowed']}\n"
        f"[bold]Sessoes executadas:[/] {progress.get('sessions_count', 0)}\n"
        f"[bold red]ATENCAO: Isso vai zerar todo o progresso![/]",
        title="[bold red]RESETAR PROGRESSO[/]",
        border_style="red",
    ))

    if Confirm.ask("[bold red]Tem certeza que deseja resetar?[/]", default=False):
        if PROGRESS_FILE.exists():
            os.remove(PROGRESS_FILE)
        console.print("[green]Progresso resetado com sucesso![/]")
        debug_log.warning("Progresso resetado pelo usuario")
    else:
        console.print("[yellow]Operacao cancelada.[/]")

    Prompt.ask("\n[dim]Pressione Enter para voltar ao menu[/]", default="")


# ═══════════════════════════════════════════════════════════
# LOGIN NO INSTAGRAM
# ═══════════════════════════════════════════════════════════

async def login_instagram(page):
    """Realiza o login no Instagram com suporte a 2FA."""
    debug_log.action("Iniciando processo de login no Instagram")

    console.print(Panel(
        "[bold]Acessando Instagram...[/]",
        border_style="cyan",
    ))

    t_start = time.time()
    await page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
    debug_log.network("GET", "https://www.instagram.com/", response_time=time.time() - t_start)
    await asyncio.sleep(3)

    # Verificar se ja esta logado
    for label in ["Pagina inicial", "Home", "Página inicial"]:
        try:
            await page.wait_for_selector(f'svg[aria-label="{label}"]', timeout=4000)
            console.print("[bold green]  Sessao anterior detectada! Ja esta logado.[/]")
            debug_log.success("Login via sessao salva - ja autenticado")
            return True
        except PlaywrightTimeout:
            continue

    debug_log.info("Sessao nao encontrada, iniciando login manual")

    # Aceitar cookies
    try:
        cookie_btn = await page.wait_for_selector(
            'button:has-text("Permitir todos os cookies"), button:has-text("Allow all cookies"), button:has-text("Aceitar")',
            timeout=5000
        )
        if cookie_btn:
            await cookie_btn.click()
            debug_log.debug("Cookies aceitos")
            await asyncio.sleep(1)
    except PlaywrightTimeout:
        debug_log.debug("Popup de cookies nao apareceu")

    # Pedir credenciais
    console.print(Panel(
        "[bold]Digite suas credenciais do Instagram[/]\n"
        "[dim]A senha nao aparece enquanto voce digita (e normal)[/]",
        title="[bold yellow]LOGIN[/]",
        border_style="yellow",
    ))

    username = Prompt.ask("  [bold cyan]Username ou Email[/]")
    password = getpass.getpass("  Senha: ")

    debug_log.action(f"Tentando login com username: {username[:3]}***")

    console.print("\n  [bold]Preenchendo credenciais...[/]")

    # Preencher username
    username_input = await page.wait_for_selector('input[name="username"]', timeout=10000)
    await username_input.click()
    await asyncio.sleep(0.5)
    await username_input.fill("")
    await username_input.type(username, delay=random.randint(50, 150))
    debug_log.debug("Username preenchido")
    await asyncio.sleep(0.5)

    # Preencher senha
    password_input = await page.wait_for_selector('input[name="password"]')
    await password_input.click()
    await asyncio.sleep(0.5)
    await password_input.fill("")
    await password_input.type(password, delay=random.randint(50, 150))
    debug_log.debug("Senha preenchida")
    await asyncio.sleep(1)

    # Clicar em Entrar
    login_btn = await page.wait_for_selector('button[type="submit"]')
    await login_btn.click()
    debug_log.action("Botao de login clicado, aguardando resposta...")

    with console.status("[bold cyan]Aguardando resposta do Instagram...[/]", spinner="dots"):
        await asyncio.sleep(5)

    # Verificar erro de login
    try:
        error_msg = await page.query_selector('#slfErrorAlert, [data-testid="login-error-message"]')
        if error_msg:
            error_text = await error_msg.inner_text()
            console.print(Panel(f"[bold red]Erro no login:[/] {error_text}", border_style="red"))
            debug_log.error(f"Erro no login: {error_text}")
            return False
    except Exception:
        pass

    # Verificar 2FA
    needs_2fa = False
    try:
        code_input = await page.wait_for_selector(
            'input[name="verificationCode"], input[name="security_code"], input[aria-label*="codigo"], input[aria-label*="code"], input[aria-label*="código"]',
            timeout=8000
        )
        if code_input:
            needs_2fa = True
    except PlaywrightTimeout:
        debug_log.debug("2FA nao detectado")

    if needs_2fa:
        debug_log.warning("Autenticacao 2FA detectada")

        console.print(Panel(
            "[bold yellow]O Instagram pediu verificacao de dois fatores![/]\n"
            "[white]Verifique seu SMS ou Google Authenticator e digite o codigo abaixo.[/]",
            title="[bold yellow]2FA NECESSARIO[/]",
            border_style="yellow",
        ))

        code = Prompt.ask("  [bold cyan]Codigo 2FA[/]")
        debug_log.action("Codigo 2FA recebido, inserindo...")

        code_input = await page.query_selector(
            'input[name="verificationCode"], input[name="security_code"], input[aria-label*="codigo"], input[aria-label*="code"], input[aria-label*="código"]'
        )

        if code_input:
            await code_input.click()
            await asyncio.sleep(0.3)
            await code_input.fill("")
            await code_input.type(code, delay=random.randint(80, 200))
            await asyncio.sleep(1)

            confirm_btn = await page.query_selector(
                'button[type="submit"], button:has-text("Confirmar"), button:has-text("Confirm")'
            )
            if confirm_btn:
                await confirm_btn.click()

            with console.status("[bold cyan]Verificando codigo 2FA...[/]", spinner="dots"):
                await asyncio.sleep(5)

            debug_log.action("Codigo 2FA enviado")
        else:
            debug_log.error("Campo de codigo 2FA nao encontrado")
            console.print("[bold red]  Nao foi possivel encontrar o campo de codigo 2FA.[/]")
            return False

    # Salvar informacoes de login
    try:
        save_btn = await page.wait_for_selector(
            'button:has-text("Salvar informações"), button:has-text("Salvar informacoes"), button:has-text("Save Info"), button:has-text("Save info")',
            timeout=5000
        )
        if save_btn:
            await save_btn.click()
            debug_log.debug("Informacoes de login salvas")
            await asyncio.sleep(2)
    except PlaywrightTimeout:
        pass

    # Descartar popup de notificacoes
    try:
        notif_btn = await page.wait_for_selector(
            'button:has-text("Agora não"), button:has-text("Agora nao"), button:has-text("Not Now")',
            timeout=5000
        )
        if notif_btn:
            await notif_btn.click()
            debug_log.debug("Popup de notificacoes descartado")
            await asyncio.sleep(2)
    except PlaywrightTimeout:
        pass

    # Verificar login bem sucedido
    try:
        await page.wait_for_selector(
            'svg[aria-label="Página inicial"], svg[aria-label="Pagina inicial"], svg[aria-label="Home"], a[href="/direct/inbox/"]',
            timeout=10000
        )
        console.print("[bold green]  Login realizado com sucesso![/]")
        debug_log.success("Login realizado com sucesso!")
        return True
    except PlaywrightTimeout:
        if "instagram.com" in page.url and "/accounts/login" not in page.url:
            console.print("[bold green]  Login aparentemente bem sucedido.[/]")
            debug_log.success("Login verificado pela URL")
            return True
        console.print("[bold red]  Nao foi possivel confirmar o login.[/]")
        debug_log.error("Falha na verificacao do login")
        return False


# ═══════════════════════════════════════════════════════════
# UNFOLLOW
# ═══════════════════════════════════════════════════════════

async def unfollow_user(page, username, attempt=1):
    """Da unfollow em um perfil especifico."""
    max_attempts = 2
    t_start = time.time()

    try:
        profile_url = f"https://www.instagram.com/{username}/"
        debug_log.action(f"Acessando perfil @{username} (tentativa {attempt})")

        response = await page.goto(profile_url, wait_until="domcontentloaded", timeout=15000)
        elapsed_nav = time.time() - t_start
        debug_log.network("GET", profile_url, status=response.status if response else None, response_time=elapsed_nav)
        await asyncio.sleep(random.uniform(2, 4))

        # Perfil nao existe
        if response and response.status == 404:
            debug_log.unfollow_result(username, "not_found", time.time() - t_start)
            return "not_found"

        page_text = await page.inner_text("body")
        if "Esta página não está disponível" in page_text or "Esta pagina nao esta disponivel" in page_text or "Sorry, this page" in page_text:
            debug_log.unfollow_result(username, "not_found", time.time() - t_start)
            return "not_found"

        # Procurar botao "Seguindo"
        following_btn = None
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
                    debug_log.debug(f"Botao encontrado com seletor: {selector}")
                    break
            except PlaywrightTimeout:
                continue

        if not following_btn:
            try:
                follow_btn = await page.query_selector('button:has-text("Seguir"), button:has-text("Follow")')
                if follow_btn:
                    btn_text = await follow_btn.inner_text()
                    if btn_text.strip() in ["Seguir", "Follow"]:
                        debug_log.unfollow_result(username, "already_unfollowed", time.time() - t_start)
                        return "already_unfollowed"
            except Exception:
                pass

            if attempt < max_attempts:
                debug_log.warning(f"Botao nao encontrado para @{username}, tentando novamente...")
                await asyncio.sleep(3)
                return await unfollow_user(page, username, attempt + 1)

            debug_log.unfollow_result(username, "error", time.time() - t_start)
            return "error"

        # Clicar em "Seguindo"
        await following_btn.click()
        debug_log.debug(f"Botao 'Seguindo' clicado para @{username}")
        await asyncio.sleep(random.uniform(1, 2))

        # Clicar em "Deixar de seguir"
        unfollow_btn = None
        unfollow_selectors = [
            'button:has-text("Deixar de seguir")',
            'button:has-text("Unfollow")',
            '[role="dialog"] button:has-text("Deixar de seguir")',
            '[role="dialog"] button:has-text("Unfollow")',
            'button._a9--._ap36._a9_1',
        ]

        for selector in unfollow_selectors:
            try:
                btn = await page.wait_for_selector(selector, timeout=4000)
                if btn:
                    unfollow_btn = btn
                    debug_log.debug(f"Botao 'Deixar de seguir' encontrado: {selector}")
                    break
            except PlaywrightTimeout:
                continue

        if unfollow_btn:
            await unfollow_btn.click()
            debug_log.debug(f"Botao 'Deixar de seguir' clicado para @{username}")
            await asyncio.sleep(random.uniform(1.5, 3))

            # Verificar sucesso
            try:
                await page.wait_for_selector(
                    'button:has-text("Seguir"), button:has-text("Follow")',
                    timeout=5000
                )
                debug_log.unfollow_result(username, "success", time.time() - t_start)
                return "success"
            except PlaywrightTimeout:
                # Verificar bloqueio
                try:
                    block_check = await page.query_selector(
                        'text="Tente novamente mais tarde", text="Try Again Later", text="Action Blocked"'
                    )
                    if block_check:
                        debug_log.unfollow_result(username, "blocked", time.time() - t_start)
                        return "blocked"
                except Exception:
                    pass

                debug_log.unfollow_result(username, "success", time.time() - t_start)
                return "success"
        else:
            debug_log.error(f"Modal de confirmacao nao apareceu para @{username}")
            debug_log.unfollow_result(username, "error", time.time() - t_start)
            return "error"

    except PlaywrightTimeout:
        debug_log.error(f"Timeout ao acessar @{username}")
        debug_log.unfollow_result(username, "error", time.time() - t_start)
        return "error"
    except Exception as e:
        debug_log.exception(f"Erro inesperado ao processar @{username}: {str(e)}")
        debug_log.unfollow_result(username, "error", time.time() - t_start)
        return "error"


# ═══════════════════════════════════════════════════════════
# PROCESSO PRINCIPAL DE UNFOLLOW
# ═══════════════════════════════════════════════════════════

async def run_unfollow(config):
    """Executa o processo de unfollow com painel em tempo real."""
    debug_log.info("=" * 60)
    debug_log.info("INICIANDO NOVA SESSAO DE UNFOLLOW")
    debug_log.info("=" * 60)

    # Carregar dados
    unfollow_list = load_unfollow_list()
    whitelist = load_whitelist()
    progress = load_progress()
    speed = get_speed_settings(config)

    # Resetar contagem diaria
    today = datetime.now().strftime("%Y-%m-%d")
    if progress["last_date"] != today:
        progress["unfollowed_today"] = 0
        progress["last_date"] = today
        debug_log.info("Novo dia detectado, contagem diaria resetada")

    # Filtrar lista
    filtered_list = [
        item for item in unfollow_list
        if item["username"].lower() not in whitelist
        and item["username"] not in progress["unfollowed_usernames"]
        and item["username"] not in progress["skipped_usernames"]
    ]

    debug_log.info(f"Lista filtrada: {len(filtered_list)} perfis restantes")
    debug_log.info(f"Velocidade: {speed['name']} | Delay: {speed['min_delay']}-{speed['max_delay']}s | "
                   f"Hora: {speed['per_hour']} | Dia: {speed['per_day']}")

    if progress["unfollowed_today"] >= speed["per_day"]:
        console.print(Panel(
            f"[bold yellow]Limite diario de {speed['per_day']} unfollows atingido![/]\n"
            "[white]Tente novamente amanha.[/]",
            title="[bold yellow]LIMITE DIARIO[/]",
            border_style="yellow",
        ))
        debug_log.warning(f"Limite diario atingido: {progress['unfollowed_today']}/{speed['per_day']}")
        Prompt.ask("\n[dim]Pressione Enter para voltar[/]", default="")
        return

    if not filtered_list:
        console.print(Panel("[bold green]Nenhum perfil restante para dar unfollow![/]", border_style="green"))
        Prompt.ask("\n[dim]Pressione Enter para voltar[/]", default="")
        return

    # Perguntar limite da sessao
    remaining_today = speed["per_day"] - progress["unfollowed_today"]
    max_possible = min(remaining_today, len(filtered_list))

    console.print(Panel(
        f"[bold]Perfis restantes:[/] {len(filtered_list)}\n"
        f"[bold]Disponivel hoje:[/] {remaining_today}\n"
        f"[bold]Velocidade:[/] {speed['icon']}  {speed['name']}",
        title="[bold cyan]INICIAR UNFOLLOW[/]",
        border_style="cyan",
    ))

    session_limit = IntPrompt.ask(
        f"[cyan]Quantos unfollows nesta sessao? (max: {max_possible})[/]",
        default=min(30, max_possible)
    )
    session_limit = min(session_limit, max_possible)

    if not Confirm.ask(f"[yellow]Iniciar unfollow de {session_limit} perfis?[/]", default=True):
        console.print("[yellow]Operacao cancelada.[/]")
        return

    debug_log.action(f"Sessao iniciada: {session_limit} unfollows planejados")

    # Iniciar Playwright
    console.print()
    with console.status("[bold cyan]Iniciando navegador...[/]", spinner="dots"):
        pw = await async_playwright().start()

        browser_args = [
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-dev-shm-usage",
        ]

        headless = config.get("headless", True)
        debug_log.info(f"Modo headless: {headless}")

        browser = await pw.chromium.launch(
            headless=headless,
            args=browser_args,
        )

        SESSION_DIR.mkdir(parents=True, exist_ok=True)
        state_path = SESSION_DIR / "state.json"

        context = await browser.new_context(
            storage_state=str(state_path) if state_path.exists() else None,
            viewport={"width": 1366, "height": 768},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="pt-BR",
        )

        page = await context.new_page()

        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'languages', { get: () => ['pt-BR', 'pt', 'en-US', 'en'] });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
        """)

        debug_log.info("Navegador iniciado com sucesso")

    # Login
    logged_in = await login_instagram(page)
    if not logged_in:
        console.print(Panel("[bold red]Falha no login. Encerrando.[/]", border_style="red"))
        debug_log.error("Falha no login, sessao encerrada")
        await browser.close()
        await pw.stop()
        Prompt.ask("\n[dim]Pressione Enter para voltar[/]", default="")
        return

    # Salvar sessao
    await context.storage_state(path=str(state_path))
    debug_log.info("Sessao de login salva")
    await asyncio.sleep(3)

    # Contadores da sessao
    session_stats = {
        "success": 0,
        "not_found": 0,
        "already_unfollowed": 0,
        "errors": 0,
        "blocked": 0,
    }
    hour_count = 0
    hour_start = time.time()
    batch_count = 0
    session_start = time.time()

    progress["sessions_count"] = progress.get("sessions_count", 0) + 1

    # Painel de progresso com Rich
    console.print()
    console.print(Rule("[bold cyan]PROCESSO DE UNFOLLOW INICIADO[/]"))
    console.print()

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold cyan]{task.description}[/]"),
        BarColumn(bar_width=30, complete_style="green", finished_style="bold green"),
        MofNCompleteColumn(),
        TextColumn("[bold]{task.percentage:>3.0f}%[/]"),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
        expand=False,
    ) as progress_bar:

        task = progress_bar.add_task("Unfollow", total=session_limit)

        for i, item in enumerate(filtered_list[:session_limit]):
            username = item["username"]
            follow_date = item.get("date", "N/A")

            # Verificar limite diario
            if progress["unfollowed_today"] >= speed["per_day"]:
                console.print(Panel(
                    f"[bold yellow]Limite diario de {speed['per_day']} atingido![/]",
                    border_style="yellow",
                ))
                debug_log.warning("Limite diario atingido durante a sessao")
                break

            # Verificar limite por hora
            elapsed_hour = time.time() - hour_start
            if elapsed_hour >= 3600:
                hour_count = 0
                hour_start = time.time()
                debug_log.info("Contador horario resetado")

            if hour_count >= speed["per_hour"]:
                wait_time = 3600 - elapsed_hour + random.uniform(30, 120)
                wait_min = int(wait_time / 60)
                console.print(Panel(
                    f"[bold yellow]Limite por hora atingido ({speed['per_hour']}/h)[/]\n"
                    f"[white]Aguardando {wait_min} minutos...[/]",
                    title="[bold yellow]PAUSA HORARIA[/]",
                    border_style="yellow",
                ))
                debug_log.warning(f"Limite horario atingido, pausando {wait_min} minutos")
                await asyncio.sleep(wait_time)
                hour_count = 0
                hour_start = time.time()

            # Pausa entre lotes
            if batch_count >= speed["batch_size"]:
                pause = speed["batch_pause"] + random.uniform(-30, 60)
                pause_min = int(pause / 60)
                console.print(Panel(
                    f"[yellow]Pausa de seguranca: {pause_min} minutos...[/]",
                    border_style="yellow",
                ))
                debug_log.info(f"Pausa entre lotes: {pause_min} minutos")
                await asyncio.sleep(pause)
                batch_count = 0

            # Atualizar descricao do progresso
            progress_bar.update(task, description=f"@{username[:20]}")

            # Executar unfollow
            result = await unfollow_user(page, username)

            # Processar resultado
            if result == "success":
                session_stats["success"] += 1
                hour_count += 1
                batch_count += 1
                progress["unfollowed_today"] += 1
                progress["total_unfollowed"] += 1
                progress["unfollowed_usernames"].append(username)
                console.print(f"  [bold green]>[/] @{username} [green]UNFOLLOW OK[/] [dim]({follow_date})[/]")

            elif result == "already_unfollowed":
                session_stats["already_unfollowed"] += 1
                progress["skipped_usernames"].append(username)
                console.print(f"  [yellow]~[/] @{username} [yellow]ja nao seguia[/]")

            elif result == "not_found":
                session_stats["not_found"] += 1
                progress["skipped_usernames"].append(username)
                console.print(f"  [dim]x[/] @{username} [dim]perfil nao encontrado[/]")

            elif result == "blocked":
                session_stats["blocked"] += 1
                progress["blocked_count"] = progress.get("blocked_count", 0) + 1

                console.print()
                console.print(Panel(
                    "[bold red]ACAO BLOQUEADA PELO INSTAGRAM![/]\n\n"
                    "[white]O Instagram detectou atividade automatizada e bloqueou as acoes.[/]\n"
                    "[white]O script sera encerrado para proteger sua conta.[/]\n\n"
                    "[bold yellow]RECOMENDACOES:[/]\n"
                    "  [white]1. Aguarde pelo menos 24 horas antes de tentar novamente[/]\n"
                    "  [white]2. Considere usar um perfil de velocidade mais lento[/]\n"
                    "  [white]3. Nao use o Instagram manualmente por algumas horas[/]",
                    title="[bold red]BLOQUEIO DETECTADO[/]",
                    border_style="bold red",
                    padding=(1, 2),
                ))

                debug_log.critical("ACAO BLOQUEADA PELO INSTAGRAM - Sessao encerrada")
                save_progress(progress)
                await context.storage_state(path=str(state_path))
                debug_log.session_summary(session_stats)
                await browser.close()
                await pw.stop()
                Prompt.ask("\n[dim]Pressione Enter para voltar[/]", default="")
                return

            elif result == "error":
                session_stats["errors"] += 1
                progress["failed_usernames"].append(username)
                console.print(f"  [red]![/] @{username} [red]ERRO[/]")

            # Avancar barra de progresso
            progress_bar.advance(task)

            # Salvar progresso periodicamente
            if (session_stats["success"] % 5) == 0 and session_stats["success"] > 0:
                save_progress(progress)
                await context.storage_state(path=str(state_path))
                debug_log.debug("Progresso salvo (checkpoint)")

            # Delay humanizado
            if i < session_limit - 1:
                delay = humanized_delay(speed["min_delay"], speed["max_delay"])
                debug_log.performance("Delay antes do proximo unfollow", delay)
                await asyncio.sleep(delay)

    # Salvar progresso final
    save_progress(progress)
    await context.storage_state(path=str(state_path))

    # Relatorio final da sessao
    elapsed_total = time.time() - session_start
    elapsed_min = int(elapsed_total // 60)
    elapsed_sec = int(elapsed_total % 60)

    remaining_after = len(filtered_list) - (
        session_stats["success"] + session_stats["not_found"] +
        session_stats["already_unfollowed"] + session_stats["errors"]
    )

    report_table = Table(
        box=box.DOUBLE_EDGE,
        border_style="cyan",
        title="[bold white]RELATORIO DA SESSAO[/]",
        padding=(0, 2),
    )
    report_table.add_column("Metrica", style="bold white", width=35)
    report_table.add_column("Valor", justify="right", width=15)

    report_table.add_row("Unfollows realizados", f"[bold green]{session_stats['success']}[/]")
    report_table.add_row("Perfis nao encontrados", f"[dim]{session_stats['not_found']}[/]")
    report_table.add_row("Ja nao seguia", f"[dim]{session_stats['already_unfollowed']}[/]")
    report_table.add_row("Erros", f"[red]{session_stats['errors']}[/]")
    report_table.add_row("Bloqueios", f"[bold red]{session_stats['blocked']}[/]")
    report_table.add_row("[dim]" + "-" * 30 + "[/]", "[dim]" + "-" * 10 + "[/]")
    report_table.add_row("Duracao da sessao", f"[cyan]{elapsed_min}min {elapsed_sec}s[/]")
    report_table.add_row("Total acumulado", f"[bold cyan]{progress['total_unfollowed']}[/]")
    report_table.add_row("Restantes", f"[yellow]{remaining_after}[/]")

    console.print()
    console.print(report_table)

    console.print(Panel(
        f"[dim]Debug log salvo em:[/] {DEBUG_LOG_FILE}\n"
        f"[dim]Progresso salvo em:[/] {PROGRESS_FILE}",
        border_style="dim",
    ))

    debug_log.session_summary(session_stats)
    debug_log.info("Sessao finalizada com sucesso")

    await browser.close()
    await pw.stop()

    Prompt.ask("\n[dim]Pressione Enter para voltar ao menu[/]", default="")


# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

async def main():
    """Loop principal do menu."""
    config = load_config()

    while True:
        console.clear()
        show_banner()
        choice = show_main_menu()

        if choice == "0":
            console.print(Panel(
                "[bold cyan]Ate a proxima! Bom unfollow![/]",
                border_style="cyan",
            ))
            debug_log.info("Script encerrado pelo usuario")
            break

        elif choice == "1":
            console.clear()
            show_banner()
            await run_unfollow(config)

        elif choice == "2":
            config = show_speed_menu(config)

        elif choice == "3":
            show_status(config)

        elif choice == "4":
            show_list_profiles()

        elif choice == "5":
            show_whitelist_menu()

        elif choice == "6":
            show_debug_log()

        elif choice == "7":
            reset_progress_menu()

        elif choice == "8":
            config = show_general_settings(config)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Script interrompido pelo usuario (Ctrl+C)[/]")
        debug_log.warning("Script interrompido por Ctrl+C")
    except Exception as e:
        console.print(f"\n[bold red]Erro fatal: {e}[/]")
        debug_log.exception(f"Erro fatal: {e}")
        console.print_exception()
