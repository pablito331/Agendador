import json
import os
import re
import sys
import urllib.request
import subprocess
import shutil


class GitHubUpdater:
    """Consulta a release mais recente do GitHub e compara com a versão local."""

    def __init__(self, repo: str = "pablito331/Agendador", current_version: str = "1.0.0"):
        self.repo = repo.strip().strip("/")
        self.current_version = current_version.strip()
        self.api_url = f"https://api.github.com/repos/{self.repo}/releases/latest"

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
        asset_url = ""
        
        # Priorizar instalador Setup se disponível, senão executável .exe
        for a in assets:
            nome = str(a.get("name", "")).lower()
            if "setup" in nome and nome.endswith(".exe"):
                asset_url = a.get("browser_download_url") or ""
                break
        
        if not asset_url:
            for a in assets:
                nome = str(a.get("name", "")).lower()
                if nome.endswith(".exe"):
                    asset_url = a.get("browser_download_url") or ""
                    break
        
        if not asset_url and assets:
            asset_url = assets[0].get("browser_download_url") or ""

        return {
            "version": tag.replace("v", "", 1),
            "tag": tag,
            "url": html_url,
            "asset_url": asset_url,
            "body": payload.get("body") or "",
        }

    def download_asset(self, destino: str = None):
        """Baixa o primeiro asset de release para o diretório informado."""
        info = self.check_for_update()
        if not info or not info.get("asset_url"):
            return None

        destino = destino or os.path.join(os.getcwd(), "agendador_update.exe")
        try:
            urllib.request.urlretrieve(info["asset_url"], destino)
            return destino
        except Exception:
            return None

    def download_and_install(self, progress_callback=None):
        """
        Baixa e instala a atualização automaticamente.
        
        Args:
            progress_callback: Função chamada com (mensagem, percentual) durante download
        
        Returns:
            bool: True se sucesso, False se erro
        """
        info = self.check_for_update()
        if not info or not info.get("asset_url"):
            return False

        try:
            # Definir diretório de downloads
            if hasattr(sys, 'frozen'):
                # App compilado com PyInstaller
                app_dir = os.path.dirname(sys.executable)
            else:
                app_dir = os.path.dirname(os.path.abspath(__file__))
            
            temp_dir = os.path.join(app_dir, ".updates")
            os.makedirs(temp_dir, exist_ok=True)
            
            destino = os.path.join(temp_dir, "AgendadorESF_new.exe")
            
            # Chamar progress callback
            if progress_callback:
                progress_callback("Conectando ao servidor...", 0)
            
            # Download com progresso
            def download_hook(bloco, tamanho_bloco, tamanho_total):
                if tamanho_total > 0 and progress_callback:
                    percentual = (bloco * tamanho_bloco) * 100 // tamanho_total
                    percentual = min(100, percentual)
                    progress_callback(f"Baixando ({percentual}%)...", percentual)
            
            urllib.request.urlretrieve(info["asset_url"], destino, reporthook=download_hook)
            
            if progress_callback:
                progress_callback("Instalando atualização...", 100)
            
            # Executar novo instalador
            if sys.platform == "win32":
                # Windows: executar e sair
                subprocess.Popen([destino])
                # Aguardar um pouco antes de sair
                import time
                time.sleep(1)
                sys.exit(0)
            else:
                # Outros SOs: apenas executar
                subprocess.Popen([destino])
            
            return True
            
        except Exception as e:
            print(f"Erro ao atualizar: {e}")
            return False
