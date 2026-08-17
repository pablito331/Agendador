# 🏥 AgendadorESF - Sistema de Agendamento para ESF

<div align="center">

[![GitHub release (latest by date)](https://img.shields.io/github/v/release/pablito331/Agendador)](https://github.com/pablito331/Agendador/releases)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Um sistema completo de agendamento de consultas para Equipes de Saúde da Família (ESF) com suporte a:
- 📅 Agendamento inteligente com encaixe manual
- 📊 Agenda por dia e por médico
- 💊 Gerenciamento de receitas
- ⚙️ Configuração flexível de horários
- 🔄 Atualização automática

[Download](#instalação) • [Documentação](#documentação) • [Contribuir](#contribuição)

</div>

---

## ✨ Características

### 📅 Agendamento Inteligente
- Agendar consultas com seleção de médico e data
- **Encaixe manual**: Digitar hora customizada quando necessário
- Horários especiais por modalidade (Domiciliar, GERCON, Criança, Gestante)
- Validação automática de conflitos

### 📊 Visualizações
- **Agenda do Dia**: Ver todas as consultas de um dia específico
- **Agenda do Médico**: Filtrar por profissional
- **Busca Avançada**: Procurar pacientes por nome, medicamento, etc.

### 💊 Gestão de Receitas
- Registrar receitas para pacientes
- Status de receitas (Pendente, Retirada, etc.)
- Integração com agendamentos

### ⚙️ Configurações
- Definir horários de cada médico
- Configurar horários especiais por modalidade
- Gerenciar médicos e especialidades
- Logs de todas as ações

### 🔄 Atualização Automática
- Verifica automaticamente novas versões
- Notificação visual na tela principal
- Download e instalação com um clique
- Sem interrupção do usuário

---

## 🚀 Instalação

### Opção 1: Download do Executável (Recomendado)

1. Vá para [Releases](https://github.com/pablito331/Agendador/releases)
2. Baixe o arquivo `AgendadorESF.exe` mais recente
3. Execute o arquivo
4. O aplicativo se atualizará automaticamente

### Opção 2: Rodando do Código Fonte

```bash
# 1. Clonar repositório
git clone https://github.com/pablito331/Agendador.git
cd Agendador

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Executar
python app.py
```

### Requisitos do Sistema
- Windows 10 ou superior (executável)
- Python 3.11+ (para rodar do código fonte)
- 200MB de espaço em disco

---

## 📖 Guia de Uso

### Primeira Execução

1. **Selecionar Planilha**: Clique em "Selecionar Planilha" na tela principal
2. **Formato**: Arquivo Excel (.xlsx) com estrutura esperada
3. **Backup**: O sistema faz backup automático

### Fluxo de Agendamento

1. Clique em "AGENDAR CONSULTA"
2. Selecione o paciente (novo ou existente)
3. Escolha o médico e data
4. Selecione o horário (ou digite na modalidade encaixe)
5. Confirme o agendamento

### Encaixe Manual

Na tela de agendamento, quando selecionado encaixe:
- Dígite a hora no formato `HH:MM`
- Use botões de sugestão (Manhã/Tarde)
- Sistema não verifica conflitos (encaixe é independente)

---

## 🔧 Desenvolvimento

### Setup do Ambiente

```bash
# Criar ambiente virtual
python -m venv venv
venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt
```

### Estrutura do Projeto

```
agendador/
├── app.py                          # Aplicação principal
├── config_manager.py               # Gerenciamento de configurações
├── github_updater.py               # Sistema de atualização
├── caminho_planilha.py             # Gerenciamento de caminhos
│
├── telas/
│   ├── tela_principal.py           # Hub de lançamentos
│   ├── tela_agendamento.py         # Agendamento
│   ├── tela_agenda_dia.py          # Agenda por dia
│   ├── tela_agenda_medico.py       # Agenda por médico
│   ├── tela_receitas.py            # Gestão de receitas
│   ├── tela_config.py              # Configurações
│   ├── tela_busca.py               # Busca avançada
│   └── tela_edicao_consulta.py     # Edição de consultas
│
├── utils.py                        # Utilitários
├── impressao.py                    # Impressão de documentos
├── requirements.txt                # Dependências Python
├── AgendadorESF.spec               # Configuração PyInstaller
└── README.md                       # Este arquivo
```

### Arquitetura

**MVC Pattern**:
- **Model**: `config_manager.py` (ExcelManager)
- **View**: Arquivos em `tela_*.py`
- **Controller**: `app.py` (ESFApp)

**Componentes Principais**:

| Componente | Responsabilidade |
|-----------|-----------------|
| `ExcelManager` | Ler/escrever planilha Excel |
| `GitHubUpdater` | Verificar e baixar atualizações |
| `ESFApp` | Orquestração principal |

---

## 📦 Releases e Atualizações

Ver [RELEASE.md](RELEASE.md) para documentação completa.

### Checklist de Release Rápido

1. Atualizar versão em `app.py`
2. `git add -A && git commit -m "Bump version"`
3. `git push origin main`
4. ✅ GitHub Actions cria release automaticamente

---

## 🐛 Issues e Troubleshooting

- 🐛 [Reportar Bug](https://github.com/pablito331/Agendador/issues)
- 💡 [Solicitar Feature](https://github.com/pablito331/Agendador/issues)

---

## 📄 Licença

MIT License - Veja [LICENSE](LICENSE) para detalhes

---

<div align="center">

Feito com ❤️ para ESF | v1.0.0

</div>
