# Instagram Auto-Unfollow v2.0

Script profissional em Python utilizando **Playwright** e **Rich** para automatizar o processo de unfollow no Instagram, focado em perfis que nao seguem voce de volta. Desenvolvido para rodar no terminal do **Kali Linux** e **NetHunter**.

## Funcionalidades

- **Menu interativo no terminal** com visual profissional (Rich)
- **Login com 2FA** (SMS ou Google Authenticator)
- **Configuracao de velocidade** com 5 perfis pre-definidos + modo personalizado
- **Debug log completo em tempo real** salvo em `/sdcard/nh_files/debug_log.txt`
- **Barra de progresso** com tempo estimado e porcentagem
- **Avisos de bloqueio** em tempo real no painel
- **Whitelist** para proteger perfis especificos
- **Salva progresso** para retomar de onde parou

## Perfis de Velocidade

| Perfil | Delay | /Hora | /Dia | Risco |
|---|---|---|---|---|
| Ultra Seguro | 40-90s | 12 | 80 | Nenhum |
| Seguro | 25-55s | 20 | 120 | Muito Baixo |
| Normal | 15-45s | 25 | 150 | Baixo |
| Rapido | 8-25s | 40 | 200 | Moderado |
| Turbo | 4-12s | 60 | 300 | ALTO |
| Personalizado | Manual | Manual | Manual | Voce define |

## Instalacao no Kali Linux

```bash
git clone https://github.com/cariocaservicesoficial3-code/Tete.git
cd Tete
chmod +x install.sh
./install.sh
```

## Como Usar

```bash
python3 insta_unfollow.py
```

O menu interativo vai abrir com todas as opcoes disponiveis.

## Debug Log

O script gera um arquivo de debug log completo em tempo real com:

- Todas as acoes executadas com timestamp
- Requisicoes de rede (URLs, status, tempo de resposta)
- Resultado de cada unfollow individual
- Erros e excecoes com traceback completo
- Performance e metricas de cada operacao
- Resumo da sessao ao finalizar

**Caminho do log:**
- NetHunter/Android: `/sdcard/nh_files/debug_log.txt`
- PC/Linux: `./logs/debug_log.txt`

## Estrutura do Projeto

```
Tete/
├── insta_unfollow.py      # Script principal
├── install.sh             # Instalador automatico
├── unfollow_list.json     # Lista de 8.082 perfis para unfollow
├── whitelist.txt          # Perfis protegidos (edite manualmente)
├── config.json            # Configuracoes (gerado automaticamente)
├── progress.json          # Progresso (gerado automaticamente)
├── session_data/          # Sessao do navegador (gerado automaticamente)
├── logs/                  # Debug logs (se nao for NetHunter)
└── README.md              # Este arquivo
```

## Avisos de Seguranca

- Se o script detectar bloqueio do Instagram, ele para automaticamente e avisa no painel.
- Aguarde 24 horas apos um bloqueio antes de tentar novamente.
- Use perfis de velocidade mais lentos para contas novas ou que ja foram bloqueadas.
