; ===============================================
; AgendadorESF - Instalador Oficial NSIS
; ===============================================

!include "MUI2.nsh"
!include "x64.nsh"

; ===============================================
; CONFIGURAÇÕES DO INSTALADOR
; ===============================================

Name "AgendadorESF"
OutFile "AgendadorESF-Setup.exe"
InstallDir "$PROGRAMFILES\AgendadorESF"
InstallDirRegKey HKCU "Software\AgendadorESF" "Install_Dir"
RequestExecutionLevel admin
SetCompressor /SOLID lzma

; Versão (atualizada automaticamente pelo build)
!define VERSION "1.0.2"
!define PUBLISHER "ESF Saúde"
!define EXE_NAME "AgendadorESF.exe"

; ===============================================
; PÁGINAS DA INTERFACE
; ===============================================

!define MUI_ABORTWARNING
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES

!define MUI_FINISHPAGE_RUN "$INSTDIR\${EXE_NAME}"
!define MUI_FINISHPAGE_RUN_TEXT "Iniciar o AgendadorESF agora"
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "PortugueseBR"

; ===============================================
; INSTALAÇÃO
; ===============================================

Section "AgendadorESF" SecApp
  SectionIn RO

  ; Se já estiver rodando, fecha antes de atualizar
  DetailPrint "Preparando diretório de instalação..."
  SetOutPath "$INSTDIR"

  ; Copia o executável principal embutido
  File "dist\AgendadorESF.exe"

  ; Grava informações no Registro do Windows
  WriteRegStr HKCU "Software\AgendadorESF" "Install_Dir" "$INSTDIR"
  WriteRegStr HKCU "Software\AgendadorESF" "Version" "${VERSION}"

  ; Entrada em Adicionar ou Remover Programas do Windows
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\AgendadorESF" "DisplayName" "AgendadorESF - Gerenciador de Agenda"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\AgendadorESF" "UninstallString" '"$INSTDIR\Uninstall.exe"'
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\AgendadorESF" "DisplayIcon" '"$INSTDIR\${EXE_NAME}"'
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\AgendadorESF" "DisplayVersion" "${VERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\AgendadorESF" "Publisher" "${PUBLISHER}"

  ; Cria atalhos no Menu Iniciar e Desktop
  CreateDirectory "$SMPROGRAMS\AgendadorESF"
  CreateShortCut "$SMPROGRAMS\AgendadorESF\AgendadorESF.lnk" "$INSTDIR\${EXE_NAME}" "" "$INSTDIR\${EXE_NAME}" 0
  CreateShortCut "$SMPROGRAMS\AgendadorESF\Desinstalar.lnk" "$INSTDIR\Uninstall.exe" "" "$INSTDIR\Uninstall.exe" 0
  CreateShortCut "$DESKTOP\AgendadorESF.lnk" "$INSTDIR\${EXE_NAME}" "" "$INSTDIR\${EXE_NAME}" 0

  ; Cria o desinstalador
  WriteUninstaller "$INSTDIR\Uninstall.exe"
SectionEnd

; ===============================================
; DESINSTALAÇÃO
; ===============================================

Section "Uninstall"
  ; Remove arquivos instalados
  Delete "$INSTDIR\${EXE_NAME}"
  Delete "$INSTDIR\Uninstall.exe"

  ; Remove atalhos
  Delete "$SMPROGRAMS\AgendadorESF\AgendadorESF.lnk"
  Delete "$SMPROGRAMS\AgendadorESF\Desinstalar.lnk"
  RMDir "$SMPROGRAMS\AgendadorESF"
  Delete "$DESKTOP\AgendadorESF.lnk"

  ; Remove chaves do Registro
  DeleteRegKey HKCU "Software\AgendadorESF"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\AgendadorESF"

  ; Remove diretório (se estiver vazio)
  RMDir "$INSTDIR"
SectionEnd
