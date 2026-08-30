; ===============================================
; AgendadorESF - Online Installer NSIS
; Baixa e instala o app do GitHub
; ===============================================

!include "MUI2.nsh"
!include "x64.nsh"
!include "WinMessages.nsh"

; ===============================================
; CONFIGURAÇÕES
; ===============================================

Name "AgendadorESF Installer"
OutFile "AgendadorESF-Setup.exe"
InstallDir "$PROGRAMFILES\AgendadorESF"
InstallDirRegKey HKCU "Software\AgendadorESF" "Install_Dir"

RequestExecutionLevel admin
CRCCheck on

; Versão (será substituída automaticamente)
!define VERSION "1.0.1"
!define GITHUB_REPO "pablito331/Agendador"
!define GITHUB_API "https://api.github.com/repos/${GITHUB_REPO}/releases/latest"

; ===============================================
; INTERFACE
; ===============================================

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_LANGUAGE "Portuguese"
!insertmacro MUI_LANGUAGE "PortugueseBR"

; ===============================================
; VARIÁVEIS
; ===============================================

Var DownloadURL
Var TempDir
Var ExeFile
Var InstalledVersion

; ===============================================
; FUNÇÕES
; ===============================================

Function .onInit
  ${If} ${RunningX64}
    SetRegView 64
  ${EndIf}
  
  ; Verificar se já está instalado
  ReadRegStr $InstalledVersion HKCU "Software\AgendadorESF" "Version"
  ${If} $InstalledVersion != ""
    MessageBox MB_YESNO|MB_ICONQUESTION "AgendadorESF v$InstalledVersion já está instalado.$\n$\nDeseja atualizar?" IDYES NoAbort IDNO ExitSetup
    NoAbort:
    ; Remover versão anterior
    ExecWait '"$INSTDIR\Uninstall.exe" _?=$INSTDIR'
    Goto Continue
    ExitSetup:
    Quit
    Continue:
  ${EndIf}
FunctionEnd

Function GetLatestReleaseURL
  ; Criar diretório temporário
  InitPluginsDir
  StrCpy $TempDir "$PLUGINSDIR\AgendadorESF-temp"
  CreateDirectory "$TempDir"
  
  ; Baixar JSON da API do GitHub
  DetailPrint "Buscando versão mais recente no GitHub..."
  
  ; Usar PowerShell para fazer o download (está disponível em todas as versões modernas do Windows)
  ExecDos::Exec 'powershell -Command "$ProgressPreference=''Silent''; (New-Object System.Net.ServicePointManager).SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12; $response = Invoke-RestMethod -Uri ''${GITHUB_API}'' -ErrorAction Stop; $asset = $response.assets | Where-Object {$_.name -notmatch ''Setup'' -and $_.name -like ''*.exe''} | Select-Object -First 1; if ($asset) { Set-Content -Path ''$TempDir\download_url.txt'' -Value $asset.browser_download_url } else { exit 1 }" ' $0
  
  ${If} $0 == 0
    ; Ler URL do arquivo
    FileOpen $0 "$TempDir\download_url.txt" r
    ${If} $0 != 0
      FileRead $0 $DownloadURL
      FileClose $0
      DetailPrint "URL encontrada: $DownloadURL"
    ${Else}
      DetailPrint "Erro ao ler URL do arquivo"
      Abort "Falha ao obter URL de download"
    ${EndIf}
  ${Else}
    DetailPrint "Erro ao conectar com GitHub API"
    Abort "Falha ao conectar ao GitHub. Verifique sua conexão com internet."
  ${EndIf}
FunctionEnd

Function DownloadExecutable
  DetailPrint "Baixando AgendadorESF..."
  
  ${If} $DownloadURL == ""
    Abort "URL de download não encontrada"
  ${EndIf}
  
  StrCpy $ExeFile "$TempDir\AgendadorESF.exe"
  
  ; Baixar usando PowerShell
  ExecDos::Exec 'powershell -Command "$ProgressPreference='Continue'; (New-Object System.Net.ServicePointManager).SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12; try { Invoke-WebRequest -Uri ''$DownloadURL'' -OutFile ''$ExeFile'' -ErrorAction Stop; exit 0 } catch { exit 1 }" ' $0
  
  ${If} $0 != 0
    DetailPrint "Erro ao baixar arquivo"
    Abort "Falha ao baixar AgendadorESF. Verifique sua conexão com internet."
  ${EndIf}
  
  ; Verificar se arquivo foi baixado
  ${If} ${FileExists} $ExeFile
    DetailPrint "Download concluído com sucesso"
  ${Else}
    Abort "Arquivo não foi baixado"
  ${EndIf}
FunctionEnd

Function InstallApplication
  DetailPrint "Instalando AgendadorESF..."
  
  ; Copiar executável para pasta de instalação
  CreateDirectory "$INSTDIR"
  CopyFiles "$ExeFile" "$INSTDIR\AgendadorESF.exe"
  
  ${If} ${FileExists} "$INSTDIR\AgendadorESF.exe"
    DetailPrint "Executável instalado com sucesso"
  ${Else}
    Abort "Falha ao copiar executável"
  ${EndIf}
FunctionEnd

Function CreateShortcuts
  DetailPrint "Criando atalhos..."
  
  ; Atalho no Menu Iniciar
  CreateDirectory "$SMPROGRAMS\AgendadorESF"
  CreateShortCut "$SMPROGRAMS\AgendadorESF\AgendadorESF.lnk" "$INSTDIR\AgendadorESF.exe" "" "$INSTDIR\AgendadorESF.exe" 0
  CreateShortCut "$SMPROGRAMS\AgendadorESF\Desinstalar.lnk" "$INSTDIR\Uninstall.exe" "" "$INSTDIR\Uninstall.exe" 0
  
  ; Atalho no Desktop
  CreateShortCut "$DESKTOP\AgendadorESF.lnk" "$INSTDIR\AgendadorESF.exe" "" "$INSTDIR\AgendadorESF.exe" 0
  
  DetailPrint "Atalhos criados"
FunctionEnd

Function CreateUninstaller
  DetailPrint "Criando desinstalador..."
  
  ; Criar script de desinstalação
  FileOpen $0 "$INSTDIR\Uninstall.nsi" w
  FileWrite $0 "!include 'MUI2.nsh'$\n"
  FileWrite $0 "OutFile 'Uninstall.exe'$\n"
  FileWrite $0 "SetCompress off$\n"
  FileWrite $0 "Section 'Uninstall'$\n"
  FileWrite $0 "  Delete '$SMPROGRAMS\AgendadorESF\AgendadorESF.lnk'$\n"
  FileWrite $0 "  Delete '$SMPROGRAMS\AgendadorESF\Desinstalar.lnk'$\n"
  FileWrite $0 "  RMDir '$SMPROGRAMS\AgendadorESF'$\n"
  FileWrite $0 "  Delete '$DESKTOP\AgendadorESF.lnk'$\n"
  FileWrite $0 "  Delete '$INSTDIR\AgendadorESF.exe'$\n"
  FileWrite $0 "  Delete '$INSTDIR\Uninstall.exe'$\n"
  FileWrite $0 "  Delete '$INSTDIR\Uninstall.nsi'$\n"
  FileWrite $0 "  RMDir '$INSTDIR'$\n"
  FileWrite $0 "  DeleteRegKey HKCU 'Software\AgendadorESF'$\n"
  FileWrite $0 "SectionEnd$\n"
  FileClose $0
  
  ; Compilar script de desinstalação
  ExecDos::Exec 'makensis "$INSTDIR\Uninstall.nsi"' $0
  
  DetailPrint "Desinstalador criado"
FunctionEnd

Function RegistryEntries
  DetailPrint "Registrando no sistema..."
  
  ; Criar entrada no Registro
  WriteRegStr HKCU "Software\AgendadorESF" "Install_Dir" "$INSTDIR"
  WriteRegStr HKCU "Software\AgendadorESF" "Version" "${VERSION}"
  
  ; Entrada para Adicionar/Remover Programas
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\AgendadorESF" "DisplayName" "AgendadorESF v${VERSION}"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\AgendadorESF" "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\AgendadorESF" "InstallLocation" "$INSTDIR"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\AgendadorESF" "DisplayVersion" "${VERSION}"
  
  DetailPrint "Registro concluído"
FunctionEnd

; ===============================================
; SEÇÕES DE INSTALAÇÃO
; ===============================================

Section "Instalar AgendadorESF"
  SectionIn RO
  
  DetailPrint "Iniciando instalação do AgendadorESF v${VERSION}..."
  
  ; Obter URL de download
  Call GetLatestReleaseURL
  
  ; Baixar executável
  Call DownloadExecutable
  
  ; Instalar aplicação
  Call InstallApplication
  
  ; Criar atalhos
  Call CreateShortcuts
  
  ; Registrar no Registro do Windows
  Call RegistryEntries
  
  ; Criar desinstalador (comentado - pode ser adicionado depois)
  ; Call CreateUninstaller
  
  DetailPrint "Instalação concluída com sucesso!"
SectionEnd

Function .onInstSuccess
  MessageBox MB_YESNO|MB_ICONQUESTION "Instalação concluída! Deseja iniciar o AgendadorESF agora?" IDYES LaunchApp IDNO NoLaunch
  LaunchApp:
    Exec "$INSTDIR\AgendadorESF.exe"
  NoLaunch:
FunctionEnd

Function .onInstFailed
  DetailPrint "Instalação falhou!"
FunctionEnd

; ===============================================
; UNINSTALL SECTION
; ===============================================

Section "Uninstall"
  DetailPrint "Desinstalando AgendadorESF..."
  
  ; Remover atalhos
  Delete "$SMPROGRAMS\AgendadorESF\AgendadorESF.lnk"
  Delete "$SMPROGRAMS\AgendadorESF\Desinstalar.lnk"
  RMDir "$SMPROGRAMS\AgendadorESF"
  Delete "$DESKTOP\AgendadorESF.lnk"
  
  ; Remover arquivos de instalação
  Delete "$INSTDIR\AgendadorESF.exe"
  Delete "$INSTDIR\Uninstall.exe"
  Delete "$INSTDIR\Uninstall.nsi"
  
  ; Remover diretório
  RMDir "$INSTDIR"
  
  ; Remover entradas do Registro
  DeleteRegKey HKCU "Software\AgendadorESF"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\AgendadorESF"
  
  DetailPrint "Desinstalação concluída"
SectionEnd
