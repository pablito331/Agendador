r"""
github_updater.py - Atualização automática via GitHub Releases

Fluxo:
 1. check_for_update() consulta a última release no GitHub e compara com a versão local
 2. baixar_atualizacao() baixa o instalador para %LOCALAPPDATA%\AgendadorESF\updates
 3. agendar_instalacao() inicia um helper (PowerShell) que:
      - espera o aplicativo fechar (libera o AgendadorESF.exe travado)
      - roda o instalador em modo silencioso (/S)
      - reabre o aplicativo já atualizado
 4. Uma flag registra a atualização pendente: se algo falhar (ex.: usuário
    cancelou o UAC do Windows), o app oferece tentar novamente na próxima abertura.

O usuário só precisa confirmar uma vez dentro do app; não precisa baixar nada do GitHub.
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.request

APP_DIR_NAME = "AgendadorESF"
EXE_NAME = "AgendadorESF.exe"

CREATE_NO_WINDOW = 0x08000000  # Windows: não abre janela de console para o helper


class GitHubUpdater:
    """Consulta a release mais recente do GitHub e aplica a atualização automaticamente."""

    def __init__(self, repo: str = "pablito331/Agendador", current_version: str = "1.0.0"):
        self.repo = repo.strip().strip("/")
        self.current_version = current_version.strip()
        self.api_url = f"https://api.github.com/repos/{self.repo}/releases/latest"

    # ==================== VERSÕES ====================

    @staticmethod
    def _normalizar_version(version: str):
        texto = str(version or "").strip().lower()
        texto = texto.replace("v", "", 1)
        match = re.search(r"\d+(?:\.\d+)+", texto)
        if not match:
            return (0,)
        partes = []
        for parte in match.group(0).split("."):
            try:
                partes.append(int(parte))
            except ValueError:
                partes.append(0)
        return tuple(partes)

    def _versao_maior(self, nova: str, atual: str) -> bool:
        return self._normalizar_version(nova) > self._normalizar_version(atual)

    # ==================== DIRETÓRIOS ====================

    @staticmethod
    def pasta_dados() -> str:
        """Pasta de dados do app no perfil do usuário (gravável sem admin)."""
        local_appdata = os.environ.get("LOCALAPPDATA") or os.path.join(
            os.path.expanduser("~"), "AppData", "Local"
        )
        return os.path.join(local_appdata, APP_DIR_NAME)

    @classmethod
    def pasta_updates(cls) -> str:
        """Pasta onde o instalador baixado fica temporariamente."""
        pasta = os.path.join(cls.pasta_dados(), "updates")
        try:
            os.makedirs(pasta, exist_ok=True)
        except OSError:
            pasta = cls.pasta_dados()
        return pasta

    @staticmethod
    def _diretorio_instalado() -> str:
        """Diretório onde o app está instalado/executando."""
        if getattr(sys, "frozen", False):
            return os.path.dirname(os.path.abspath(sys.executable))
        return os.path.dirname(os.path.abspath(__file__))

    # ==================== VERIFICAÇÃO ====================

    def check_for_update(self):
        """Retorna dict com info da release mais nova ou None se não houver atualização."""
        try:
            request = urllib.request.Request(
                self.api_url,
                headers={
                    "Accept": "application/vnd.github+json",
                    "User-Agent": "Agendador-App",
                },
            )
            with urllib.request.urlopen(request, timeout=10) as resposta:
                payload = json.loads(resposta.read().decode("utf-8"))
        except Exception:
            return None

        tag = (payload.get("tag_name") or "").strip()
        if not tag:
            return None

        if not self._versao_maior(tag, self.current_version):
            return None

        html_url = payload.get("html_url") or f"https://github.com/{self.repo}/releases/tag/{tag}"
        assets = payload.get("assets") or []

        # Prioridade: instalador Setup (.exe) > executável solto (.exe) > zip portátil
        asset_url = ""
        asset_nome = ""
        for pred in (
            lambda n: "setup" in n and n.endswith(".exe"),
            lambda n: n.endswith(".exe"),
            lambda n: n.endswith(".zip"),
        ):
            for a in assets:
                nome = str(a.get("name", "")).lower()
                if pred(nome):
                    asset_url = a.get("browser_download_url") or ""
                    asset_nome = str(a.get("name", ""))
                    break
            if asset_url:
                break

        return {
            "version": tag.replace("v", "", 1),
            "tag": tag,
            "url": html_url,
            "asset_url": asset_url,
            "asset_nome": asset_nome,
            "body": payload.get("body") or "",
        }

    # ==================== DOWNLOAD ====================

    def baixar_atualizacao(self, info: dict = None, progress_callback=None) -> str:
        """
        Baixa o instalador da atualização para a pasta de updates do usuário.

        Args:
            info: dict retornado por check_for_update (se None, consulta novamente)
            progress_callback: função (mensagem, percentual) chamada durante o download

        Retorna:
            Caminho do arquivo baixado, ou levanta exceção em caso de falha.
        """
        info = info or self.check_for_update()
        if not info or not info.get("asset_url"):
            raise RuntimeError("Nenhum arquivo de atualização disponível no GitHub.")

        if progress_callback:
            progress_callback("Conectando ao servidor...", 0)

        nome = info.get("asset_nome") or "AgendadorESF-Setup.exe"
        destino = os.path.join(self.pasta_updates(), nome)

        def hook(bloco, tamanho_bloco, tamanho_total):
            if tamanho_total > 0 and progress_callback:
                percentual = min(100, (bloco * tamanho_bloco) * 100 // tamanho_total)
                progress_callback(f"Baixando atualização... ({percentual}%)", percentual)

        # Remove arquivo incompleto de tentativa anterior
        try:
            if os.path.exists(destino):
                os.remove(destino)
        except OSError:
            pass

        urllib.request.urlretrieve(info["asset_url"], destino, reporthook=hook)

        if progress_callback:
            progress_callback("Download concluído.", 100)

        return destino

    # ==================== FLAG DE PENDÊNCIA ====================

    @classmethod
    def caminho_flag_pendente(cls) -> str:
        return os.path.join(cls.pasta_updates(), "atualizacao_pendente.json")

    @classmethod
    def marcar_atualizacao_pendente(cls, caminho_setup: str, reiniciar: bool = True):
        """Registra que há um instalador aguardando ser aplicado."""
        try:
            dados = {
                "setup": os.path.abspath(caminho_setup),
                "reiniciar": bool(reiniciar),
                "quando": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            with open(cls.caminho_flag_pendente(), "w", encoding="utf-8") as f:
                json.dump(dados, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Aviso: não foi possível registrar atualização pendente: {e}")

    @classmethod
    def limpar_atualizacao_pendente(cls):
        try:
            caminho = cls.caminho_flag_pendente()
            if os.path.exists(caminho):
                os.remove(caminho)
        except OSError:
            pass

    @classmethod
    def ler_atualizacao_pendente(cls) -> dict:
        try:
            caminho = cls.caminho_flag_pendente()
            if os.path.exists(caminho):
                with open(caminho, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                if isinstance(dados, dict) and dados.get("setup"):
                    return dados
        except Exception:
            pass
        return {}

    def verificar_atualizacao_pendente(self) -> dict:
        """Retorna a pendência somente se o instalador ainda existe em disco."""
        dados = self.ler_atualizacao_pendente()
        if dados and os.path.exists(dados.get("setup", "")):
            return dados
        self.limpar_atualizacao_pendente()
        return {}

    # ==================== INSTALAÇÃO ====================

    @staticmethod
    def _ps_quote(texto: str) -> str:
        """Escapa uma string para uso dentro de aspas simples no PowerShell."""
        return "'" + str(texto).replace("'", "''") + "'"

    def agendar_instalacao(self, caminho_setup: str, reiniciar: bool = True) -> bool:
        """
        Agenda a instalação silenciosa para acontecer assim que o app fechar.

        O helper (PowerShell) espera o processo atual terminar, executa o
        instalador em modo silencioso e reabre o aplicativo. Não bloqueia.
        """
        if not caminho_setup or not os.path.exists(caminho_setup):
            return False

        self.marcar_atualizacao_pendente(caminho_setup, reiniciar)

        pid = os.getpid()
        destino = self._diretorio_instalado()
        exe_novo = os.path.join(destino, EXE_NAME)

        # Sequência executada depois que este app encerrar:
        #  1) espera o app fechar (até 60s) para liberar o exe travado
        #  2) roda o instalador silenciosamente (/S)
        #  3) apaga o instalador temporário
        #  4) reabre o app já atualizado (opcional)
        comandos = [
            f"Wait-Process -Id {pid} -Timeout 60 -ErrorAction SilentlyContinue",
            f"Start-Process -FilePath {self._ps_quote(caminho_setup)} -ArgumentList '/S' -Wait",
            f"Remove-Item -LiteralPath {self._ps_quote(caminho_setup)} -Force -ErrorAction SilentlyContinue",
        ]
        if reiniciar:
            comandos.append(f"Start-Process -FilePath {self._ps_quote(exe_novo)}")

        script = (
            "$ErrorActionPreference = 'SilentlyContinue'; "
            + "; ".join(comandos)
        )

        try:
            kwargs = {}
            if sys.platform == "win32":
                kwargs["creationflags"] = CREATE_NO_WINDOW
            subprocess.Popen(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
                 "-WindowStyle", "Hidden", "-Command", script],
                **kwargs,
            )
            return True
        except Exception as e:
            print(f"Erro ao agendar instalação da atualização: {e}")
            # Fallback: abre o instalador em modo gráfico (usuário clica em Avançar)
            try:
                if sys.platform == "win32":
                    os.startfile(caminho_setup)
                else:
                    subprocess.Popen([caminho_setup])
                return True
            except Exception:
                return False
