# 📦 Guia de Releases e Atualizações

## Sistema de Atualização Automática

O **AgendadorESF** possui um sistema completo de atualização automática que:

1. ✅ Verifica automaticamente se há novas versões no GitHub
2. ✅ Notifica o usuário com uma interface visual amigável
3. ✅ Permite baixar e instalar atualizações com um clique
4. ✅ Mantém histórico de versões no GitHub

## Como Funciona

### Para Usuários

1. **Verificação Automática**: O aplicativo verifica a cada 30 segundos se há atualização disponível
2. **Notificação Visual**: Se houver atualização, aparece um banner na tela principal
3. **Download e Instalação**: Clique em "Baixar & Instalar" para:
   - Baixar o novo executável
   - Fechar a aplicação atual
   - Instalar a nova versão
   - Reiniciar automaticamente

### Para Desenvolvedores

#### Como Fazer uma Release

1. **Editar a versão em `app.py`**:
   ```python
   APP_VERSION = "1.0.1"  # Incrementar versão
   ```

2. **Commit e Push**:
   ```bash
   git add -A
   git commit -m "Bump version to 1.0.1"
   git push origin main
   ```

3. **O GitHub Actions vai automaticamente**:
   - ✅ Compilar o executável com PyInstaller
   - ✅ Criar uma release no GitHub
   - ✅ Fazer upload do `.exe`
   - ✅ Usuarios verão notificação de atualização

#### Manual (Se precisar)

Se o GitHub Actions não funcionar, faça manualmente:

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Compilar com PyInstaller
pyinstaller AgendadorESF.spec

# 3. O arquivo estará em: dist/AgendadorESF_vX.X.X.exe

# 4. Criar release no GitHub com o arquivo
```

## Estrutura de Versões

Usamos **Semantic Versioning**: MAJOR.MINOR.PATCH

- **MAJOR** (1.0.0): Mudanças incompatíveis, novas features grandes
- **MINOR** (1.1.0): Novas features compatíveis
- **PATCH** (1.0.1): Bug fixes

Exemplo:
- v1.0.0 → v1.0.1 (patch)
- v1.0.1 → v1.1.0 (minor)
- v1.1.0 → v2.0.0 (major)

## Arquivos Importantes

| Arquivo | Propósito |
|---------|-----------|
| `app.py` | Contém `APP_VERSION` |
| `AgendadorESF.spec` | Configuração PyInstaller |
| `.github/workflows/build.yml` | Automação GitHub Actions |
| `github_updater.py` | Lógica de verificação/download |
| `tela_principal.py` | UI de notificação |

## Checklist para Release

- [ ] Atualizar versão em `app.py`
- [ ] Testar aplicativo localmente
- [ ] Atualizar `TODO.md` com mudanças concluídas
- [ ] Commit com mensagem descritiva
- [ ] Push para `main`
- [ ] Aguardar GitHub Actions completar
- [ ] Verificar release em GitHub

## Troubleshooting

### "GitHub Actions não acionado"
- Verifique se mudou `app.py` (paths do workflow)
- Verifique as permissões do token do GitHub

### "Download falha para usuários"
- Certifique-se que o asset foi enviado corretamente
- Teste o link de download manualmente

### "Verificação de atualização lenta"
- A verificação roda em background (thread)
- Timeout é de 10 segundos

## Exemplo de Release Notes

Quando criar release, use este template:

```markdown
## v1.0.1 - 2024-01-XX

### ✨ Novas Features
- Adicionado suporte para horários especiais de modalidades

### 🐛 Bug Fixes
- Corrigido conflito de agendamento em encaixe manual
- Melhorado desempenho de carregamento de agenda

### 📚 Outros
- Atualizado documentação
- Melhorado interface de notificação

### 📥 Download
Execute o arquivo `AgendadorESF.exe` para atualizar automaticamente.
```

## Notas Importantes

⚠️ **Requisitos para GitHub Actions**:
- Python 3.11+
- PyInstaller
- Todas as dependências do `requirements.txt`

⚠️ **O executável é grande (~60MB)**:
- Inclui Python, todas as libs e dados
- Isso é normal para aplicações PyInstaller

💡 **Melhorias Futuras**:
- Implementar diff de atualizações (baixar apenas mudanças)
- Adicionar rollback automático se erro
- Notificação de atualizações de segurança críticas
