import json
import os
import re
import sys
import urllib.request


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
        if assets:
            first_asset = assets[0]
            asset_url = first_asset.get("browser_download_url") or ""

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
