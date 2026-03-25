# Instagram Auto-Unfollow Script (Kali Linux)

Este pacote contém um script Python utilizando Playwright para automatizar o processo de unfollow no Instagram, focado em perfis que não seguem você de volta. O script foi configurado especificamente para rodar no terminal do Kali Linux.

## Funcionalidades

- **Login com 2FA:** Suporta login com verificação de duas etapas (SMS ou Google Authenticator).
- **Lista Inteligente:** Já inclui a lista de 8.082 perfis que não te seguem de volta, ordenada dos mais antigos para os mais recentes.
- **Delays Humanizados:** Pausas aleatórias entre ações para evitar bloqueios do Instagram.
- **Limites Seguros:** Configurado para no máximo 25 unfollows por hora e 150 por dia.
- **Salva Progresso:** Você pode parar o script a qualquer momento e ele continuará de onde parou na próxima vez.
- **Whitelist:** Permite proteger perfis específicos para não receberem unfollow.

## Como Instalar no Kali Linux

1. Extraia o arquivo ZIP em uma pasta de sua preferência.
2. Abra o terminal e navegue até a pasta extraída:
   ```bash
   cd caminho/para/pasta/instagram_unfollow
   ```
3. Dê permissão de execução e rode o script de instalação:
   ```bash
   chmod +x install.sh
   ./install.sh
   ```
   *O script de instalação vai baixar o Python, Playwright e o navegador Chromium necessário.*

## Como Usar

### 1. Configurar a Whitelist (Opcional)
Se houver perfis que não te seguem de volta, mas que você **NÃO** quer dar unfollow (ex: celebridades, marcas), adicione o username deles no arquivo `whitelist.txt` (um por linha, sem o @).

### 2. Iniciar o Script
Para iniciar o processo de unfollow, execute:
```bash
python3 insta_unfollow.py
```

O script vai:
1. Pedir seu usuário e senha (a senha não aparece enquanto você digita).
2. Se pedir 2FA, ele vai solicitar o código no terminal.
3. Após o login, ele salva a sessão (você não precisará logar de novo nas próximas vezes).
4. Começa a dar unfollow respeitando os limites de segurança.

### 3. Comandos Úteis

Ver o status do progresso (quantos faltam, quantos já foram):
```bash
python3 insta_unfollow.py --status
```

Listar os próximos perfis que receberão unfollow:
```bash
python3 insta_unfollow.py --list
```

Limitar a quantidade de unfollows em uma sessão (ex: fazer apenas 30 agora):
```bash
python3 insta_unfollow.py --limit 30
```

Rodar em modo "fantasma" (sem abrir a janela do navegador):
```bash
python3 insta_unfollow.py --headless
```

## Avisos de Segurança ⚠️

- **NÃO altere os limites de tempo no código.** O Instagram é muito rigoroso com automações. Se você tentar fazer muitos unfollows rápidos, sua conta será bloqueada temporariamente.
- Se o script avisar que a ação foi bloqueada, **pare imediatamente** e espere 24 horas antes de tentar de novo.
- O script leva cerca de 54 dias para limpar todos os 8.000 perfis de forma segura. Tenha paciência, é a única forma de não perder sua conta.
