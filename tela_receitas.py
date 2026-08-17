"""
tela_receitas.py - Gerenciamento de Receitas
Lista de pendentes, novo pedido, registro de retirada
"""
import customtkinter as ctk
from datetime import datetime
from typing import Optional
from config_manager import ExcelManager
from utils import validate_required, date_br

COR_FUNDO = "#2b2b2b"
COR_TEXTO = "#ffffff"
COR_DESTAQUE = "#1f6aa5"
COR_SUCESSO = "#28a745"
COR_ERRO = "#dc3545"
COR_AVISO = "#ffc107"


class TelaReceitas:
    """Tela de gerenciamento de receitas"""
    
    def __init__(self, excel: ExcelManager, usuario: str = "Sistema"):
        self.excel = excel
        self.usuario = usuario
        self.janela = None
        self._abrir()
    
    def _abrir(self):
        """Abre a janela de receitas"""
        if self.janela and self._esta_ativa():
            self.janela.lift()
            return
        
        self.janela = ctk.CTkToplevel()
        self.janela.title("💊 RECEITAS")
        self.janela.geometry("600x500")
        self.janela.resizable(True, True)
        self.janela.minsize(500, 400)
        self.janela.protocol("WM_DELETE_WINDOW", self._fechar)
        
        # Frame principal
        self.frame = ctk.CTkFrame(self.janela, fg_color=COR_FUNDO)
        self.frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Título
        titulo_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        titulo_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            titulo_frame,
            text="💊 RECEITAS",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COR_TEXTO
        ).pack(side="left")
        
        # Botão novo pedido
        ctk.CTkButton(
            titulo_frame,
            text="➕ NOVO PEDIDO",
            command=self._abrir_novo_pedido,
            fg_color=COR_SUCESSO,
            hover_color="#218838",
            text_color=COR_TEXTO,
            height=30,
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="right", padx=(10, 0))
        
        # Abas
        self.abas = ctk.CTkTabview(self.frame, fg_color=COR_FUNDO)
        self.abas.pack(fill="both", expand=True)
        
        # Aba Pendentes
        self.aba_pendentes = self.abas.add("📋 Pendentes")
        self.pendentes_container = ctk.CTkScrollableFrame(
            self.aba_pendentes, fg_color="transparent"
        )
        self.pendentes_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Aba Todas
        self.aba_todas = self.abas.add("📚 Todas")
        self.todas_container = ctk.CTkScrollableFrame(
            self.aba_todas, fg_color="transparent"
        )
        self.todas_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Centralizar
        self.janela.update_idletasks()
        largura = self.janela.winfo_width()
        altura = self.janela.winfo_height()
        x = (self.janela.winfo_screenwidth() // 2) - (largura // 2)
        y = (self.janela.winfo_screenheight() // 2) - (altura // 2)
        self.janela.geometry(f"+{x}+{y}")
        
        # Carregar dados
        self._carregar_pendentes()
        self._carregar_todas()
    
    def _carregar_pendentes(self):
        """Carrega lista de receitas pendentes"""
        for widget in self.pendentes_container.winfo_children():
            widget.destroy()
        
        pendentes = self.excel.get_receitas_pendentes()
        
        if pendentes.empty:
            ctk.CTkLabel(
                self.pendentes_container,
                text="📭 Nenhuma receita pendente",
                font=ctk.CTkFont(size=14),
                text_color="#888888"
            ).pack(pady=30)
            return
        
        # Cabeçalho
        cabecalho = ctk.CTkFrame(self.pendentes_container, fg_color="transparent")
        cabecalho.pack(fill="x", pady=(0, 10))
        
        for texto, largura in [("Paciente", 200), ("Data Pedido", 120), ("Ações", 150)]:
            ctk.CTkLabel(
                cabecalho,
                text=texto,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="#888888",
                width=largura
            ).pack(side="left")
        
        for _, receita in pendentes.iterrows():
            self._criar_linha_pendente(receita)
    
    def _criar_linha_pendente(self, receita):
        """Cria uma linha de receita pendente"""
        linha = ctk.CTkFrame(self.pendentes_container, fg_color="#333333", corner_radius=5)
        linha.pack(fill="x", pady=3, padx=2)
        
        # Paciente
        ctk.CTkLabel(
            linha,
            text=f"👤 {receita.get('paciente', '')}",
            font=ctk.CTkFont(size=13),
            text_color=COR_TEXTO,
            width=200,
            anchor="w"
        ).pack(side="left", padx=10)
        
        # Data do pedido
        data = receita.get('data_pedido', '')
        if data and len(data) >= 10:
            data = data[:10]
        ctk.CTkLabel(
            linha,
            text=data,
            font=ctk.CTkFont(size=12),
            text_color="#aaaaaa",
            width=120
        ).pack(side="left")
        
        # Botão retirar
        ctk.CTkButton(
            linha,
            text="📤 RETIRAR",
            command=lambda r=receita: self._abrir_retirada(r),
            fg_color=COR_DESTAQUE,
            hover_color="#1a5a8c",
            text_color=COR_TEXTO,
            width=100,
            height=28,
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(side="right", padx=10)
    
    def _formatar_data_hora(self, valor) -> str:
        """Formata valores de data/hora para exibição em formato brasileiro."""
        if not valor:
            return ""
        try:
            return datetime.strptime(str(valor), "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M")
        except ValueError:
            try:
                return datetime.strptime(str(valor), "%Y-%m-%d").strftime("%d/%m/%Y")
            except ValueError:
                return str(valor)

    def _carregar_todas(self):
        """Carrega lista de todas as receitas"""
        for widget in self.todas_container.winfo_children():
            widget.destroy()
        
        todas = self.excel.get_todas_receitas()
        
        if todas.empty:
            ctk.CTkLabel(
                self.todas_container,
                text="Nenhuma receita registrada",
                font=ctk.CTkFont(size=14),
                text_color="#888888"
            ).pack(pady=30)
            return
        
        # Cabeçalho
        cabecalho = ctk.CTkFrame(self.todas_container, fg_color="transparent")
        cabecalho.pack(fill="x", pady=(0, 10))
        
        for texto, largura in [("Paciente", 160), ("Status", 90), ("Quem Retirou", 110), ("Data Pedido", 95), ("Retirada em", 135)]:
            ctk.CTkLabel(
                cabecalho,
                text=texto,
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color="#888888",
                width=largura
            ).pack(side="left")
        
        for _, receita in todas.iterrows():
            linha = ctk.CTkFrame(self.todas_container, fg_color="#333333", corner_radius=3)
            linha.pack(fill="x", pady=2)
            
            ctk.CTkLabel(
                linha,
                text=receita.get('paciente', ''),
                font=ctk.CTkFont(size=12),
                text_color=COR_TEXTO,
                width=160,
                anchor="w"
            ).pack(side="left", padx=5)
            
            status = receita.get('status', '')
            cor = COR_SUCESSO if status == 'RETIRADA' else COR_AVISO
            ctk.CTkLabel(
                linha,
                text=status,
                font=ctk.CTkFont(size=11),
                text_color=cor,
                width=90
            ).pack(side="left")
            
            ctk.CTkLabel(
                linha,
                text=receita.get('quem_retirou', ''),
                font=ctk.CTkFont(size=11),
                text_color="#aaaaaa",
                width=110
            ).pack(side="left")
            
            data = receita.get('data_pedido', '')
            if data and len(data) >= 10:
                data = data[:10]
            ctk.CTkLabel(
                linha,
                text=data,
                font=ctk.CTkFont(size=11),
                text_color="#aaaaaa",
                width=95
            ).pack(side="left")

            retirada_em = self._formatar_data_hora(receita.get('data_retirada', ''))
            ctk.CTkLabel(
                linha,
                text=retirada_em if retirada_em else "-",
                font=ctk.CTkFont(size=11),
                text_color="#aaaaaa",
                width=135
            ).pack(side="left")
    
    def _abrir_novo_pedido(self):
        """Abre formulário para novo pedido de receita"""
        janela = ctk.CTkToplevel(self.janela)
        janela.title("📝 Novo Pedido de Receita")
        janela.geometry("420x320")
        janela.resizable(False, False)
        janela.transient(self.janela)
        janela.grab_set()
        
        frame = ctk.CTkFrame(janela, fg_color=COR_FUNDO)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            frame,
            text="Novo Pedido de Receita",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COR_TEXTO
        ).pack(pady=(0, 15))
        
        ctk.CTkLabel(
            frame,
            text="Nome do paciente:",
            font=ctk.CTkFont(size=13),
            text_color=COR_TEXTO
        ).pack(anchor="w")
        
        paciente_entry = ctk.CTkEntry(
            frame,
            placeholder_text="Digite o nome completo",
            height=35,
            font=ctk.CTkFont(size=13),
            fg_color="#333333",
            border_color="#555555",
            text_color=COR_TEXTO
        )
        paciente_entry.pack(fill="x", pady=(5, 10))
        paciente_entry.focus()

        ctk.CTkLabel(
            frame,
            text="Observação (opcional):",
            font=ctk.CTkFont(size=12),
            text_color="#aaaaaa"
        ).pack(anchor="w")

        obs_entry = ctk.CTkEntry(
            frame,
            placeholder_text="Ex: duas receitas para renovar, entregar amanhã...",
            height=35,
            font=ctk.CTkFont(size=12),
            fg_color="#333333",
            border_color="#555555",
            text_color=COR_TEXTO
        )
        obs_entry.pack(fill="x", pady=(5, 10))
        
        msg_label = ctk.CTkLabel(
            frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=COR_ERRO
        )
        msg_label.pack()
        
        botoes_frame = ctk.CTkFrame(frame, fg_color="transparent")
        botoes_frame.pack(fill="x", pady=(10, 0))
        
        ctk.CTkButton(
            botoes_frame,
            text="CANCELAR",
            command=janela.destroy,
            fg_color="#555555",
            hover_color="#666666",
            text_color=COR_TEXTO,
            width=100
        ).pack(side="left")
        
        def salvar():
            paciente = paciente_entry.get().strip()
            erro = validate_required(paciente, "Nome do paciente")
            if erro:
                msg_label.configure(text=erro)
                return
            
            try:
                self.excel.pedir_receita(paciente, observacao=obs_entry.get().strip(), usuario=self.usuario)
                msg_label.configure(text="✅ Receita solicitada com sucesso!", text_color=COR_SUCESSO)
                janela.after(1000, janela.destroy)
                self._carregar_pendentes()
                self._carregar_todas()
            except Exception as e:
                msg_label.configure(text=f"Erro: {str(e)}")
        
        ctk.CTkButton(
            botoes_frame,
            text="💾 SALVAR",
            command=salvar,
            fg_color=COR_SUCESSO,
            hover_color="#218838",
            text_color=COR_TEXTO,
            width=100
        ).pack(side="right")
    
    def _abrir_retirada(self, receita):
        """Abre formulário para registrar retirada"""
        janela = ctk.CTkToplevel(self.janela if self.janela else None)
        janela.title("📤 Registrar Retirada")
        janela.geometry("400x300")
        janela.resizable(False, False)
        if self.janela:
            janela.transient(self.janela)
        janela.grab_set()
        
        frame = ctk.CTkFrame(janela, fg_color=COR_FUNDO)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            frame,
            text=f"Retirada de Receita - {receita.get('paciente', '')}",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=COR_TEXTO
        ).pack(pady=(0, 15))
        
        ctk.CTkLabel(
            frame,
            text="Quem retirou:",
            font=ctk.CTkFont(size=13),
            text_color=COR_TEXTO
        ).pack(anchor="w")
        
        retirou_entry = ctk.CTkEntry(
            frame,
            placeholder_text="Nome de quem está retirando",
            height=35,
            font=ctk.CTkFont(size=13),
            fg_color="#333333",
            border_color="#555555",
            text_color=COR_TEXTO
        )
        retirou_entry.pack(fill="x", pady=(5, 10))
        retirou_entry.focus()
        
        ctk.CTkLabel(
            frame,
            text="Observação (opcional):",
            font=ctk.CTkFont(size=12),
            text_color="#aaaaaa"
        ).pack(anchor="w")
        
        obs_entry = ctk.CTkEntry(
            frame,
            placeholder_text="Observações...",
            height=30,
            font=ctk.CTkFont(size=12),
            fg_color="#333333",
            border_color="#555555",
            text_color=COR_TEXTO
        )
        obs_entry.pack(fill="x", pady=(5, 10))
        
        msg_label = ctk.CTkLabel(
            frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=COR_ERRO
        )
        msg_label.pack()
        
        botoes_frame = ctk.CTkFrame(frame, fg_color="transparent")
        botoes_frame.pack(fill="x", pady=(10, 0))
        
        ctk.CTkButton(
            botoes_frame,
            text="CANCELAR",
            command=janela.destroy,
            fg_color="#555555",
            hover_color="#666666",
            text_color=COR_TEXTO,
            width=100
        ).pack(side="left")
        
        def confirmar():
            quem = retirou_entry.get().strip()
            if not quem:
                quem = str(receita.get('paciente', '') or '').strip() or "Solicitante"
            
            try:
                id_receita = int(receita['id'])
                self.excel.retirar_receita(
                    id_receita, quem,
                    observacao=obs_entry.get().strip(),
                    usuario=self.usuario
                )
                msg_label.configure(text="✅ Retirada registrada com sucesso!", text_color=COR_SUCESSO)
                janela.after(1000, janela.destroy)
                self._carregar_pendentes()
                self._carregar_todas()
                if hasattr(self, '_parent_window') and self._parent_window:
                    self._parent_window.after(0, self._parent_window.update_idletasks)
            except Exception as e:
                msg_label.configure(text=f"Erro: {str(e)}")
        
        ctk.CTkButton(
            botoes_frame,
            text="✅ CONFIRMAR RETIRADA",
            command=confirmar,
            fg_color=COR_DESTAQUE,
            hover_color="#1a5a8c",
            text_color=COR_TEXTO,
            width=150
        ).pack(side="right")
    
    def _esta_ativa(self) -> bool:
        try:
            return self.janela and self.janela.winfo_exists()
        except:
            return False
    
    def _fechar(self):
        try:
            self.janela.destroy()
        except:
            pass
        self.janela = None

