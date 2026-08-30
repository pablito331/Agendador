#!/usr/bin/env python3
"""
app.py - ESF Gerenciador de Agenda
Aplicativo principal com system tray e gerenciamento de janelas
"""
import sys
import os
import threading
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import customtkinter as ctk
from config_manager import ExcelManager
from github_updater import GitHubUpdater
from utils import now
from tela_principal import TelaPrincipal

APP_VERSION = "1.0.2"
GITHUB_REPO = "pablito331/Agendador"

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

COR_FUNDO = "#2b2b2b"
COR_TEXTO = "#ffffff"
COR_DESTAQUE = "#1f6aa5"

usuario_padrao = "Sistema"
_NOME_USUARIO = usuario_padrao


def get_usuario() -> str:
    global _NOME_USUARIO
    if _NOME_USUARIO != usuario_padrao:
        return _NOME_USUARIO
    import getpass
    try:
        _NOME_USUARIO = getpass.getuser()
    except:
        _NOME_USUARIO = usuario_padrao
    return _NOME_USUARIO


class ESFApp:
    """Classe principal do aplicativo ESF Agenda"""

    def __init__(self):
        from caminho_planilha import carregar_caminho
        caminho_salvo = carregar_caminho()
        self.caminho_planilha = caminho_salvo if caminho_salvo else None

        self.excel = ExcelManager(caminho=self.caminho_planilha)
        self.usuario = get_usuario()
        self.updater = GitHubUpdater(repo=GITHUB_REPO, current_version=APP_VERSION)

        self.tela_principal = None
        self.tela_agenda_dia = None

        self._rodando = True
        self._tray_icon = None
        self._hotkey_thread = None

        self._inicializar()

    def _inicializar(self):
        self._criar_janela_root()
        self._criar_janela_principal()
        self._verificar_atualizacao_thread()  # Verificar em background
        self._iniciar_tray()
        self._iniciar_hotkey()
        self._iniciar_loop()

    def _verificar_atualizacao_thread(self):
        """Verifica atualização em thread separada (background)"""
        def check():
            try:
                info = self.updater.check_for_update()
                if info and self.tela_principal:
                    # Mostrar notificação na thread principal
                    self._root.after(0, lambda: self._mostrar_notificacao_atualizacao(info))
            except Exception:
                pass
        
        thread = threading.Thread(target=check, daemon=True)
        thread.start()
    
    def _mostrar_notificacao_atualizacao(self, info: dict):
        """Mostra notificação de atualização na tela principal"""
        if self.tela_principal:
            self.tela_principal.mostrar_notificacao_atualizacao(
                info,
                download_callback=self._iniciar_download_atualizacao
            )
    
    def _iniciar_download_atualizacao(self):
        """Inicia download e instalação da atualização"""
        def download_thread():
            self.updater.download_and_install(
                progress_callback=self._atualizar_progresso_download
            )
        
        thread = threading.Thread(target=download_thread, daemon=True)
        thread.start()
    
    def _atualizar_progresso_download(self, mensagem: str, percentual: int):
        """Callback de progresso do download"""
        print(f"[Atualização] {mensagem} ({percentual}%)")

    def _criar_janela_root(self):
        """Cria janela root CTk oculta (obrigatória para que CTkToplevel funcione)"""
        self._root = ctk.CTk()
        self._root.title(f"ESF Agenda v{APP_VERSION}")
        self._root.withdraw()  # Mantém oculta — apenas TelaPrincipal fica visível
        self._root.protocol("WM_DELETE_WINDOW", self._sair)

    def _criar_janela_principal(self):
        if self.tela_principal:
            self.tela_principal.mostrar()
            return

        self.tela_principal = TelaPrincipal(
            abrir_agendamento_callback=self._abrir_agendamento,
            abrir_receitas_callback=self._abrir_receitas,
            abrir_agenda_dia_callback=self._abrir_agenda_dia,
            abrir_agenda_medico_callback=self._abrir_agenda_medico,
            abrir_config_callback=self._abrir_config,
            abrir_busca_callback=self._abrir_busca,
            selecionar_planilha_callback=self._selecionar_planilha,
            abrir_feedback_callback=self._abrir_feedback,
            minimizar_callback=self._minimizar_principal,
        )
        if self.caminho_planilha:
            self.tela_principal.atualizar_status_planilha(self.caminho_planilha)

    def _janela_ativa(self, instancia) -> bool:
        """Verifica se uma janela já está aberta e visível"""
        try:
            return bool(instancia and hasattr(instancia, 'janela') and instancia.janela and instancia.janela.winfo_exists())
        except Exception:
            return False

    def _focar_janela(self, instancia):
        """Traz janela existente para frente"""
        try:
            if hasattr(instancia, 'mostrar'):
                instancia.mostrar()
            elif hasattr(instancia, 'janela') and instancia.janela:
                instancia.janela.deiconify()
                instancia.janela.lift()
                instancia.janela.focus_force()
        except Exception:
            pass

    def _abrir_agendamento(self):
        if self._janela_ativa(getattr(self, '_tela_agendamento', None)):
            self._focar_janela(self._tela_agendamento)
            return
        from tela_agendamento import TelaAgendamento
        self._tela_agendamento = TelaAgendamento(self.excel, usuario=self.usuario)

    def _abrir_receitas(self):
        if self._janela_ativa(getattr(self, '_tela_receitas', None)):
            self._focar_janela(self._tela_receitas)
            return
        from tela_receitas import TelaReceitas
        self._tela_receitas = TelaReceitas(self.excel, usuario=self.usuario)

    def _abrir_agenda_dia(self):
        if self._janela_ativa(self.tela_agenda_dia):
            self._focar_janela(self.tela_agenda_dia)
        else:
            from tela_agenda_dia import TelaAgendaDia
            if self.tela_agenda_dia:
                self.tela_agenda_dia.destruir()
            self.tela_agenda_dia = TelaAgendaDia(self.excel, usuario=self.usuario)

    def _abrir_agenda_medico(self):
        if self._janela_ativa(getattr(self, '_tela_agenda_medico', None)):
            self._focar_janela(self._tela_agenda_medico)
            return
        from tela_agenda_medico import TelaAgendaMedico
        self._tela_agenda_medico = TelaAgendaMedico(self.excel, usuario=self.usuario)

    def _abrir_config(self):
        if self._janela_ativa(getattr(self, '_tela_config', None)):
            self._focar_janela(self._tela_config)
            return
        from tela_config import TelaConfig
        self._tela_config = TelaConfig(self.excel, usuario=self.usuario, app_ref=self)

    def _abrir_busca(self, termo: str = ""):
        if self._janela_ativa(getattr(self, '_tela_busca', None)):
            self._focar_janela(self._tela_busca)
            if termo and hasattr(self._tela_busca, 'busca_entry'):
                try:
                    self._tela_busca.busca_entry.delete(0, 'end')
                    self._tela_busca.busca_entry.insert(0, termo)
                    self._tela_busca._executar_busca()
                except Exception:
                    pass
            return
        from tela_busca import TelaBusca
        self._tela_busca = TelaBusca(self.excel, termo_inicial=termo, usuario=self.usuario)

    def _abrir_feedback(self):
        if self._janela_ativa(getattr(self, '_tela_feedback', None)):
            self._focar_janela(self._tela_feedback)
            return
        from tela_feedback import TelaFeedback
        self._tela_feedback = TelaFeedback(usuario=self.usuario, versao_app=APP_VERSION)

    def _selecionar_planilha(self):
        from tkinter import filedialog, messagebox
        from caminho_planilha import salvar_caminho

        parent = self.tela_principal.janela if self.tela_principal else self._root
        caminho_inicial = self.caminho_planilha or os.path.join(os.getcwd(), "agenda_esf.xlsx")
        caminho_inicial_dir = os.path.dirname(caminho_inicial) if os.path.dirname(caminho_inicial) else os.getcwd()

        caminho = filedialog.askopenfilename(
            parent=parent,
            title="Selecionar planilha Excel existente",
            initialdir=caminho_inicial_dir,
            filetypes=[("Arquivo Excel", "*.xlsx"), ("Todos os arquivos", "*.*")],
        )

        if not caminho:
            caminho = filedialog.asksaveasfilename(
                parent=parent,
                title="Criar nova planilha Excel",
                initialdir=caminho_inicial_dir,
                initialfile="agenda_esf.xlsx",
                defaultextension=".xlsx",
                filetypes=[("Arquivo Excel", "*.xlsx")],
            )

        if not caminho:
            return

        if not caminho.lower().endswith('.xlsx'):
            caminho = f"{caminho}.xlsx"

        if not os.path.exists(caminho):
            resposta = messagebox.askyesno(
                "Criar nova planilha",
                f"O arquivo não existe. Deseja criar uma nova planilha em:\n{caminho}?"
            )
            if not resposta:
                return

        self.caminho_planilha = os.path.abspath(caminho)
        self.excel = ExcelManager(caminho=self.caminho_planilha)
        salvar_caminho(self.caminho_planilha)

        if self.tela_principal:
            self.tela_principal.atualizar_status_planilha(self.caminho_planilha)

        messagebox.showinfo("Planilha alterada", f"Planilha pronta para uso:\n{self.caminho_planilha}")

    def _minimizar_principal(self):
        if self.tela_principal:
            self.tela_principal.ocultar()

    def _mostrar_principal(self):
        if self.tela_principal:
            self.tela_principal.mostrar()
        else:
            self._criar_janela_principal()

    # ==================== SYSTEM TRAY ====================

    def _iniciar_tray(self):
        try:
            import pystray
            from PIL import Image, ImageDraw

            def criar_icone():
                img = Image.new('RGB', (64, 64), color=COR_DESTAQUE)
                draw = ImageDraw.Draw(img)
                draw.text((10, 15), "ESF", fill="white")
                return img

            def ao_clicar(icon, item):
                if str(item) == "Abrir Agenda do Dia":
                    self._abrir_agenda_dia()
                elif str(item) == "Abrir Tela Principal":
                    self._mostrar_principal()
                elif str(item) == "Sair":
                    self._sair()

            def ao_duplo_clicar(icon):
                self._mostrar_principal()

            menu = pystray.Menu(
                pystray.MenuItem("Abrir Agenda do Dia", ao_clicar),
                pystray.MenuItem("Abrir Tela Principal", ao_clicar),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Sair", ao_clicar)
            )

            self._tray_icon = pystray.Icon(
                "esf_agenda", criar_icone(), "ESF - Agenda", menu
            )

            tray_thread = threading.Thread(target=self._tray_icon.run, daemon=True)
            tray_thread.start()

        except ImportError:
            print("pystray nao instalado. System tray desabilitado.")
        except Exception as e:
            print(f"Erro ao iniciar system tray: {e}")

    # ==================== GLOBAL HOTKEY ====================

    def _iniciar_hotkey(self):
        try:
            from pynput import keyboard

            def combinacao_ativada():
                if hasattr(self, '_root') and self._root:
                    try:
                        self._root.after(0, self._mostrar_principal)
                    except Exception:
                        pass
                else:
                    self._mostrar_principal()

            hotkey = keyboard.GlobalHotKeys({
                '<ctrl>+<shift>+a': combinacao_ativada,
                '<ctrl>+<shift>+A': combinacao_ativada
            })

            self._hotkey_thread = hotkey
            hotkey.daemon = True
            hotkey.start()

            print("Atalho Ctrl+Shift+A configurado!")

        except ImportError:
            print("pynput nao instalado. Hotkey global desabilitado.")
        except Exception as e:
            print(f"Erro ao configurar hotkey: {e}")

    # ==================== LOOP PRINCIPAL ====================

    def _iniciar_loop(self):
        self._rodando = True

        if self.tela_principal:
            self.tela_principal.mostrar()

        try:
            self._root.mainloop()
        except:
            pass

    def _sair(self):
        self._rodando = False

        if self.tela_principal:
            self.tela_principal.destruir()

        if self.tela_agenda_dia:
            self.tela_agenda_dia.destruir()

        if self._hotkey_thread:
            try:
                self._hotkey_thread.stop()
            except:
                pass

        if self._tray_icon:
            try:
                self._tray_icon.stop()
            except:
                pass

        try:
            self._root.destroy()
        except:
            pass

        try:
            sys.exit(0)
        except:
            os._exit(0)


if __name__ == "__main__":
    from tela_principal import TelaPrincipal
    app = ESFApp()
