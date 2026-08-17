"""
caminho_planilha.py - Gerenciamento do caminho da planilha Excel
Salva e carrega o caminho em um arquivo JSON para persistência
"""
import json
import os
import sys

ARQUIVO_CONFIG = "caminho_planilha.json"


def _appdata_config_dir() -> str:
    """Diretório padrão para dados do app no Windows."""
    local_appdata = os.environ.get("LOCALAPPDATA") or os.path.join(os.path.expanduser("~"), "AppData", "Local")
    return os.path.abspath(os.path.join(local_appdata, "AgendadorESF"))


def _raiz_execucao() -> list[str]:
    """Lista as raízes relevantes para procurar o config atual."""
    roots = []
    cwd = os.path.abspath(os.getcwd()) if os.getcwd() else ""
    if cwd:
        roots.append(cwd)

    if getattr(sys, 'executable', None):
        roots.append(os.path.dirname(os.path.abspath(sys.executable)))

    if sys.argv and sys.argv[0]:
        try:
            roots.append(os.path.dirname(os.path.abspath(sys.argv[0])))
        except Exception:
            pass

    roots.append(os.path.dirname(os.path.abspath(__file__)))
    roots.append(_appdata_config_dir())

    vistos = set()
    ordered = []
    for root in roots:
        if not root:
            continue
        root = os.path.abspath(root)
        if root in vistos:
            continue
        ordered.append(root)
        vistos.add(root)

        parent = os.path.dirname(root)
        if parent and parent not in vistos:
            ordered.append(parent)
            vistos.add(parent)

        for _ in range(4):
            if parent == root:
                break
            root = parent
            parent = os.path.dirname(root)
            if root not in vistos:
                ordered.append(root)
                vistos.add(root)

    return ordered


def _caminho_config() -> str:
    """Retorna o arquivo de configuração mais provável no contexto de execução atual.

    Prioriza o diretório atual, seus ancestrais e o AppData do usuário. Apenas depois
    busca em diretórios mais distantes para manter a resolução estável e evitar o uso de
    uma planilha de outra versão ou outra instalação.
    """
    configuracoes = []
    for pasta in _raiz_execucao():
        config = os.path.join(pasta, ARQUIVO_CONFIG)
        if os.path.exists(config):
            configuracoes.append(config)

        try:
            for item in sorted(os.listdir(pasta)):
                if item == ARQUIVO_CONFIG:
                    config = os.path.join(pasta, item)
                    configuracoes.append(config)
        except OSError:
            pass

    if configuracoes:
        return configuracoes[0]

    app_data_dir = _appdata_config_dir()
    os.makedirs(app_data_dir, exist_ok=True)
    return os.path.join(app_data_dir, ARQUIVO_CONFIG)


def _diretorios_busca() -> list[str]:
    """Lista diretórios do contexto real de execução para encontrar a base Excel correta."""
    dirs = []
    vistos = set()

    for root in _raiz_execucao():
        if not root:
            continue
        atual = os.path.abspath(root)
        for _ in range(6):
            if atual not in vistos:
                dirs.append(atual)
                vistos.add(atual)
            pai = os.path.dirname(atual)
            if pai == atual:
                break
            atual = pai

        try:
            for item in sorted(os.listdir(root)):
                item_path = os.path.join(root, item)
                if os.path.isdir(item_path) and item_path not in vistos:
                    dirs.append(item_path)
                    vistos.add(item_path)
        except OSError:
            pass

    return dirs


def _procurar_planilha_viva() -> str:
    """Procura a planilha mais provável da base real pelo nome ou por qualquer Excel no diretório."""
    nomes_prioritarios = [
        "agenda_esf.xlsx",
        "agenda.xlsx",
        "planilha.xlsx",
        "base_agenda.xlsx",
    ]

    for pasta in _diretorios_busca():
        for nome in nomes_prioritarios:
            caminho = os.path.abspath(os.path.join(pasta, nome))
            if os.path.isfile(caminho):
                return caminho

        try:
            itens = os.listdir(pasta)
        except OSError:
            continue

        arquivos_xlsx = [
            os.path.abspath(os.path.join(pasta, item))
            for item in itens
            if item.lower().endswith('.xlsx')
        ]
        if arquivos_xlsx:
            arquivos_xlsx.sort()
            return arquivos_xlsx[0]

    return ""


def _candidatos_planilha(caminho: str, base_config: str) -> list[str]:
    """Gera candidatos de resolução para um caminho de planilha antigo ou relativo."""
    candidatos = []
    if not caminho:
        return candidatos

    candidatos.extend([
        os.path.abspath(caminho),
        os.path.abspath(os.path.join(base_config, caminho)),
        os.path.abspath(os.path.join(os.getcwd(), caminho)),
    ])

    candidatos.extend([os.path.abspath(os.path.join(pasta, caminho)) for pasta in _diretorios_busca()])
    candidatos.extend([os.path.abspath(os.path.join(pasta, os.path.basename(caminho))) for pasta in _diretorios_busca()])

    if os.path.basename(caminho).lower().endswith('.xlsx'):
        for pasta in _diretorios_busca():
            nome = os.path.basename(caminho)
            candidatos.append(os.path.abspath(os.path.join(pasta, nome)))

    return list(dict.fromkeys(candidatos))


def salvar_caminho(caminho: str):
    """Salva o caminho da planilha em um arquivo JSON utilizando caminho absoluto."""
    try:
        caminho_absoluto = os.path.abspath(caminho)
        config_path = _caminho_config()
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump({"caminho": caminho_absoluto}, f, indent=2)
        return True
    except Exception as e:
        print(f"Erro ao salvar caminho: {e}")
        return False


def carregar_caminho() -> str:
    """Carrega o caminho da planilha do arquivo JSON, aceitando caminhos relativos antigos ou fora do diretório atual."""
    try:
        config_path = _caminho_config()
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                caminho = dados.get("caminho", "")

                base_config = os.path.dirname(config_path)
                if caminho:
                    for candidato in _candidatos_planilha(caminho, base_config):
                        if os.path.exists(candidato):
                            return os.path.abspath(candidato)

                planilha_existente = _procurar_planilha_viva()
                if planilha_existente:
                    return planilha_existente

                if caminho:
                    return os.path.abspath(caminho)

        planilha_existente = _procurar_planilha_viva()
        if planilha_existente:
            return planilha_existente

        return ""
    except Exception as e:
        print(f"Erro ao carregar caminho: {e}")
        return ""


def limpar_caminho():
    """Remove o arquivo de configuração (volta ao padrão)"""
    try:
        if os.path.exists(_caminho_config()):
            os.remove(_caminho_config())
        return True
    except Exception as e:
        print(f"Erro ao limpar caminho: {e}")
        return False
