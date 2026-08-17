#!/usr/bin/env python3
"""
compile_nsis_installer.py
Compila o instalador NSIS e substitui versão automaticamente
"""

import os
import re
import subprocess
import sys


def get_app_version():
    """Extrai versão do app.py"""
    with open("app.py", "r", encoding="utf-8") as f:
        content = f.read()
        match = re.search(r'APP_VERSION = "([^"]+)"', content)
        if match:
            return match.group(1)
    return "1.0.0"


def update_nsi_version(version):
    """Atualiza versão no arquivo NSI"""
    nsi_file = "AgendadorESF-Installer.nsi"
    
    with open(nsi_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Substituir versão
    content = re.sub(
        r'!define VERSION "[^"]*"',
        f'!define VERSION "{version}"',
        content
    )
    
    with open(nsi_file, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"[+] Versão atualizada em {nsi_file}: {version}")


def find_makensis():
    """Encontra o caminho do makensis.exe"""
    possible_paths = [
        r"C:\Program Files\NSIS\makensis.exe",
        r"C:\Program Files (x86)\NSIS\makensis.exe",
        r"C:\Program Files\Nsis\makensis.exe",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # Tentar encontrar no PATH
    result = subprocess.run(["where", "makensis.exe"], capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout.strip().split("\n")[0]
    
    return None


def compile_nsis():
    """Compila o instalador NSIS"""
    makensis = find_makensis()
    
    if not makensis:
        print("[-] ERRO: makensis.exe não encontrado!")
        print("Instale NSIS: https://nsis.sourceforge.io/Download")
        return False
    
    print(f"Usando makensis: {makensis}")
    print("Compilando instalador...")
    
    result = subprocess.run(
        [makensis, "AgendadorESF-Installer.nsi"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        print("[+] Instalador compilado com sucesso!")
        print("Arquivo: AgendadorESF-Setup.exe")
        return True
    else:
        print("[-] Erro ao compilar:")
        print(result.stdout)
        print(result.stderr)
        return False


def main():
    print("=" * 50)
    print("AgendadorESF - Compilador NSIS")
    print("=" * 50)
    
    # Obter versão
    version = get_app_version()
    print(f"\n[*] Versão: {version}")
    
    # Atualizar NSI com versão
    update_nsi_version(version)
    
    # Compilar
    print("\n[*] Compilando...")
    if compile_nsis():
        print("\n[+] Sucesso! Use AgendadorESF-Setup.exe para instalar")
        sys.exit(0)
    else:
        print("\n[-] Falha na compilação")
        sys.exit(1)


if __name__ == "__main__":
    main()
