"""
tela_principal.py - Janela principal (Hub de lançamentos)
Dimensões: 400x500 pixels
"""
import os
import customtkinter as ctk
from typing import Optional, Callable

APP_VERSION = "1.0.2"

# Cores do tema
COR_FUNDO = "#2b2b2b"
COR_TEXTO = "#ffffff"
COR_DESTAQUE = "#1f6aa5"
COR_SUCESSO = "#28a745"
COR_ERRO = "#dc3545"
COR_BOTAO_FUNDO = "#333333"
COR_BOTAO_HOVER = "#404040"


class TelaPrincipal:
    """Janela principal do ESF Gerenciador de Agenda"""
    
    def __init__(self, 
                 abrir_agendamento_callback: Callable,
                 abrir_receitas_callback: Callable,
                 abrir_agenda_dia_callback: Callable,
                 abrir_agenda_medico_callback: Callable,
                 abrir_config_callback: Callable,
                 abrir_busca_callback: Callable,
                 selecionar_planilha_callback: Callable,
                 abrir_feedback_callback: Optional[Callable] = None,
                 minimizar_callback: Optional[Callable] = None):
        
        self.abrir_agendamento = abrir_agendamento_callback
        self.abrir_receitas = abrir_receitas_callback
        self.abrir_agenda_dia = abrir_agenda_dia_callback
        self.abrir_agenda_medico = abrir_agenda_medico_callback
        self.abrir_config = abrir_config_callback
        self.abrir_busca = abrir_busca_callback
        self.selecionar_planilha = selecionar_planilha_callback
        self.abrir_feedback = abrir_feedback_callback
        self.minimizar = minimizar_callback
        
        self.janela = ctk.CTkToplevel()
        self.janela.title(f"🏥 ESF - Agenda v{APP_VERSION}")
        self.janela.geometry("400x600")
        self.janela.resizable(False, False)
        
        # Configurar para minimizar ao invés de fechar
        self.janela.protocol("WM_DELETE_WINDOW", self._fechar)
        
        # Vincular atalhos
        self.janela.bind('<Control-f>', lambda e: self._focar_busca())
        self.janela.bind('<Escape>', lambda e: self._minimizar())
        
        self._construir_interface()
        
        # Centralizar
        self.janela.update_idletasks()
        largura = self.janela.winfo_width()
        altura = self.janela.winfo_height()
        x = (self.janela.winfo_screenwidth() // 2) - (largura // 2)
        y = (self.janela.winfo_screenheight() // 2) - (altura // 2)
        self.janela.geometry(f"{largura}x{altura}+{x}+{y}")
    
    def _construir_interface(self):
        """Constrói todos os componentes da interface"""
        # Frame principal com padding
        self.frame = ctk.CTkFrame(self.janela, fg_color=COR_FUNDO)
        self.frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # === BARRA DE TÍTULO ===
        titulo_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        titulo_frame.pack(fill="x", pady=(0, 5))
        
        ctk.CTkLabel(
            titulo_frame,
            text="🏥 ESF - Agenda",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COR_TEXTO
        ).pack(side="left")
        
        from datetime import date
        from utils import get_weekday_name
        hoje = date.today()
        data_str = f"📅 {get_weekday_name(hoje)[:3]}, {hoje.strftime('%d/%m/%Y')}"
        ctk.CTkLabel(
            titulo_frame,
            text=data_str,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COR_DESTAQUE
        ).pack(side="right")
        
        # === INDICADOR DE TRAY ===
        tray_label = ctk.CTkLabel(
            self.frame,
            text="O app continuará rodando na bandeja do sistema",
            font=ctk.CTkFont(size=10),
            text_color="#888888"
        )
        tray_label.pack(pady=(0, 5))
        
        # === BARRA DE BUSCA ===
        busca_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        busca_frame.pack(fill="x", pady=(0, 15))
        
        self.busca_entry = ctk.CTkEntry(
            busca_frame,
            placeholder_text="🔍 Buscar paciente, médico, medicamento...",
            height=35,
            font=ctk.CTkFont(size=12),
            fg_color=COR_BOTAO_FUNDO,
            border_color="#555555",
            text_color=COR_TEXTO
        )
        self.busca_entry.pack(fill="x")
        self.busca_entry.bind('<Return>', lambda e: self._executar_busca())
        
        # Separador
        ctk.CTkFrame(self.frame, height=1, fg_color="#444444").pack(fill="x", pady=(0, 15))
        
        self.planilha_label = ctk.CTkLabel(
            self.frame,
            text="Planilha: nenhuma ainda",
            font=ctk.CTkFont(size=10),
            text_color="#bbbbbb",
            wraplength=320,
            justify="left"
        )
        self.planilha_label.pack(pady=(0, 10))

        # === BOTÕES DE AÇÃO ===
        self.botoes_frame = ctk.CTkScrollableFrame(self.frame, fg_color="transparent")
        self.botoes_frame.pack(fill="both", expand=True, pady=(0, 0))

        botoes = [
            ("📅", "AGENDAR CONSULTA", self.abrir_agendamento),
            ("📊", "AGENDA DO DIA", self.abrir_agenda_dia),
            ("📋", "AGENDA DO MÉDICO", self.abrir_agenda_medico),
            ("💊", "RECEITAS", self.abrir_receitas),
            ("⚙️", "CONFIGURAÇÕES", self.abrir_config),
            ("💬", "FEEDBACK / SUPORTE", self.abrir_feedback),
        ]
        
        for icone, texto, comando in botoes:
            self._criar_botao(icone, texto, comando, parent=self.botoes_frame)
        
        # === RODAPÉ ===
        ctk.CTkFrame(self.frame, height=1, fg_color="#444444").pack(fill="x", pady=(15, 10))
        
        ctk.CTkLabel(
            self.frame,
            text="Pressione Ctrl+Shift+A para abrir",
            font=ctk.CTkFont(size=10),
            text_color="#666666"
        ).pack()
        
        ctk.CTkLabel(
            self.frame,
            text="Ctrl+F para buscar | Esc para minimizar",
            font=ctk.CTkFont(size=9),
            text_color="#555555"
        ).pack()
    
    def _criar_botao(self, icone: str, texto: str, comando: Callable, parent=None):
        """Cria um botão de ação estilizado"""
        if parent is None:
            parent = self.frame

        botao = ctk.CTkButton(
            parent,
            text=f"{icone}  {texto}",
            command=comando,
            height=50,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=COR_BOTAO_FUNDO,
            hover_color=COR_BOTAO_HOVER,
            text_color=COR_TEXTO,
            corner_radius=8,
            anchor="w",
            border_width=0
        )
        botao.pack(fill="x", pady=4)
        return botao
    
    def _abrir_selecionar_planilha(self):
        if self.selecionar_planilha:
            self.selecionar_planilha()

    def atualizar_status_planilha(self, caminho: str):
        if caminho:
            nome = os.path.basename(caminho)
            self.planilha_label.configure(text=f"Planilha atual: {nome}\n{caminho}")
        else:
            self.planilha_label.configure(text="Planilha: nenhuma ainda")

    def _executar_busca(self):
        """Executa busca com o termo digitado"""
        termo = self.busca_entry.get().strip()
        if termo:
            self.abrir_busca(termo)
    
    def _focar_busca(self):
        """Foca no campo de busca"""
        self.busca_entry.focus()
        self.busca_entry.select_range(0, 'end')
    
    def _minimizar(self):
        """Minimiza a janela"""
        if self.minimizar:
            self.minimizar()
        else:
            self.janela.withdraw()
    
    def _fechar(self):
        """Fecha a janela (minimiza para tray)"""
        self._minimizar()
    
    def mostrar(self):
        """Mostra a janela e traz para a frente com foco garantido"""
        try:
            self.janela.deiconify()
            self.janela.state('normal')
            self.janela.lift()
            self.janela.attributes('-topmost', True)
            self.janela.after(100, lambda: self.janela.attributes('-topmost', False) if self.janela and self.janela.winfo_exists() else None)
            self.janela.focus_force()
        except Exception:
            pass
    
    def ocultar(self):
        """Oculta a janela"""
        self.janela.withdraw()
    
    def esta_visivel(self) -> bool:
        """Verifica se a janela está visível"""
        try:
            return self.janela.state() == 'normal' and self.janela.winfo_viewable()
        except:
            return False
    
    def destruir(self):
        """Destroi a janela"""
        try:
            self.janela.destroy()
        except:
            pass
    
    def mostrar_notificacao_atualizacao(self, info_atualizacao: dict, download_callback):
        """
        Mostra um banner notificando sobre atualização disponível
        
        Args:
            info_atualizacao: Dict com 'version', 'url', 'body', 'asset_url'
            download_callback: Função a chamar quando clicar em "Baixar"
        """
        # Criar frame para notificação
        notif_frame = ctk.CTkFrame(
            self.frame,
            fg_color="#1a3a52",
            border_color="#4a90e2",
            border_width=2,
            corner_radius=8
        )
        notif_frame.pack(fill="x", pady=(0, 15))
        
        # Conteúdo
        conteudo = ctk.CTkFrame(notif_frame, fg_color="transparent")
        conteudo.pack(fill="both", expand=True, padx=12, pady=10)
        
        # Título
        titulo = f"✨ Nova versão disponível: v{info_atualizacao['version']}"
        ctk.CTkLabel(
            conteudo,
            text=titulo,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#4a90e2"
        ).pack(anchor="w", pady=(0, 5))
        
        # Descrição
        desc = info_atualizacao.get('body', 'Novas melhorias e correções').strip()
        if len(desc) > 150:
            desc = desc[:150] + "..."
        
        if desc:
            ctk.CTkLabel(
                conteudo,
                text=desc,
                font=ctk.CTkFont(size=10),
                text_color="#cccccc",
                wraplength=300,
                justify="left"
            ).pack(anchor="w", pady=(0, 8))
        
        # Botões
        botoes_frame = ctk.CTkFrame(conteudo, fg_color="transparent")
        botoes_frame.pack(fill="x", pady=(5, 0))
        
        ctk.CTkButton(
            botoes_frame,
            text="📥 Baixar & Instalar",
            command=lambda: self._download_e_instalar(download_callback, notif_frame),
            fg_color="#4a90e2",
            hover_color="#357abd",
            text_color="white",
            height=32,
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(side="left", padx=(0, 5))
        
        ctk.CTkButton(
            botoes_frame,
            text="🔗 Ver Release",
            command=lambda: self._abrir_url(info_atualizacao['url']),
            fg_color="#555555",
            hover_color="#666666",
            text_color="white",
            height=32
        ).pack(side="left", padx=(0, 5))
        
        ctk.CTkButton(
            botoes_frame,
            text="✕",
            command=lambda: notif_frame.destroy(),
            fg_color="#333333",
            hover_color="#444444",
            text_color="#999999",
            width=32,
            height=32
        ).pack(side="left")
        
        # Mover para o topo (repackar)
        notif_frame.tkraise()
    
    def _download_e_instalar(self, callback, frame_notif):
        """Inicia download e instalação"""
        frame_notif.destroy()
        callback()
    
    def _abrir_url(self, url: str):
        """Abre URL no navegador"""
        import webbrowser
        try:
            webbrowser.open(url)
        except:
            pass

