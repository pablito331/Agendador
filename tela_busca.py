"""
tela_busca.py - Busca Global
Busca em tempo real em todas as abas (Agenda, Receitas)
Ignora acentos, maiúsculas/minúsculas, busca parcial
"""
import customtkinter as ctk
from datetime import date
from typing import Optional
from config_manager import ExcelManager
from utils import search_match, normalize_text

COR_FUNDO = "#2b2b2b"
COR_TEXTO = "#ffffff"
COR_DESTAQUE = "#1f6aa5"
COR_SUCESSO = "#28a745"
COR_ERRO = "#dc3545"
COR_AVISO = "#ffc107"


class TelaBusca:
    """Tela de busca global"""
    
    def __init__(self, excel: ExcelManager, termo_inicial: str = "", usuario: str = "Sistema"):
        self.excel = excel
        self.usuario = usuario
        self.termo_atual = termo_inicial
        self.janela = None
        self._timer_busca = None
        self._abrir()
    
    def _abrir(self):
        """Abre a janela de busca"""
        if self.janela:
            try:
                if self.janela.winfo_exists():
                    self.janela.lift()
                    self._executar_busca()
                    return
            except:
                pass
        
        self.janela = ctk.CTkToplevel()
        self.janela.title("🔍 Busca Global")
        self.janela.geometry("700x550")
        self.janela.resizable(True, True)
        self.janela.minsize(600, 400)
        self.janela.protocol("WM_DELETE_WINDOW", self._fechar)
        
        # Frame principal
        self.frame = ctk.CTkFrame(self.janela, fg_color=COR_FUNDO)
        self.frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Título
        ctk.CTkLabel(
            self.frame,
            text="🔍 Busca Global",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COR_TEXTO
        ).pack(anchor="w", pady=(0, 10))
        
        # Campo de busca
        busca_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        busca_frame.pack(fill="x", pady=(0, 10))
        
        self.busca_entry = ctk.CTkEntry(
            busca_frame,
            placeholder_text="🔍 Digite para buscar... (nome, médico, medicamento)",
            height=40,
            font=ctk.CTkFont(size=13),
            fg_color="#333333",
            border_color="#555555",
            text_color=COR_TEXTO
        )
        self.busca_entry.pack(fill="x", side="left", expand=True)
        
        # Botão de filtrar período
        self.filtro_btn = ctk.CTkButton(
            busca_frame,
            text="📅 Filtrar período",
            command=self._toggle_filtro_periodo,
            fg_color="#444444",
            hover_color="#555555",
            text_color=COR_TEXTO,
            width=120,
            height=40,
            font=ctk.CTkFont(size=11)
        )
        self.filtro_btn.pack(side="right", padx=(10, 0))
        
        # Frame de filtro de período (inicialmente oculto)
        self.filtro_frame = ctk.CTkFrame(self.frame, fg_color="#333333", corner_radius=8)
        self.filtro_visivel = False
        
        # Área de resultados com abas
        self.resultados_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.resultados_frame.pack(fill="both", expand=True)
        
        # Abas de resultados
        self.abas_resultados = ctk.CTkTabview(
            self.resultados_frame, 
            fg_color=COR_FUNDO,
            text_color=COR_TEXTO,
            segmented_button_fg_color="#333333",
            segmented_button_selected_color=COR_DESTAQUE,
            segmented_button_unselected_color="#444444"
        )
        self.abas_resultados.pack(fill="both", expand=True)
        
        self.aba_agenda = self.abas_resultados.add("📅 Consultas")
        self.agenda_container = ctk.CTkScrollableFrame(
            self.aba_agenda, fg_color="transparent"
        )
        self.agenda_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.aba_receitas = self.abas_resultados.add("💊 Receitas")
        self.receitas_container = ctk.CTkScrollableFrame(
            self.aba_receitas, fg_color="transparent"
        )
        self.receitas_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Vincular eventos de busca
        self.busca_entry.bind('<KeyRelease>', self._on_busca_change)
        self.busca_entry.bind('<Return>', lambda e: self._executar_busca())
        
        # Centralizar
        self.janela.update_idletasks()
        largura = self.janela.winfo_width()
        altura = self.janela.winfo_height()
        x = (self.janela.winfo_screenwidth() // 2) - (largura // 2)
        y = (self.janela.winfo_screenheight() // 2) - (altura // 2)
        self.janela.geometry(f"+{x}+{y}")
        
        # Se tinha termo inicial, preencher e buscar
        if self.termo_atual:
            self.busca_entry.insert(0, self.termo_atual)
            self._executar_busca()
        else:
            self.busca_entry.focus()
    
    def _on_busca_change(self, event=None):
        """Dispara busca com debounce (300ms)"""
        if self._timer_busca:
            self.janela.after_cancel(self._timer_busca)
        self._timer_busca = self.janela.after(300, self._executar_busca)
    
    def _toggle_filtro_periodo(self):
        """Mostra/oculta filtro de período"""
        if self.filtro_visivel:
            self.filtro_frame.pack_forget()
            self.filtro_visivel = False
            return
        
        self.filtro_frame = ctk.CTkFrame(self.frame, fg_color="#333333", corner_radius=8)
        self.filtro_frame.pack(fill="x", pady=(0, 10), before=self.resultados_frame)
        self.filtro_visivel = True
        
        ctk.CTkLabel(
            self.filtro_frame,
            text="Filtrar por período:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COR_TEXTO
        ).pack(pady=(10, 5))
        
        periodo_frame = ctk.CTkFrame(self.filtro_frame, fg_color="transparent")
        periodo_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        ctk.CTkLabel(
            periodo_frame,
            text="De:",
            font=ctk.CTkFont(size=12),
            text_color=COR_TEXTO
        ).pack(side="left")
        
        from tkcalendar import DateEntry
        
        self.data_inicio = DateEntry(
            periodo_frame,
            width=12,
            background='darkblue',
            foreground='white',
            borderwidth=2,
            locale='pt_BR',
            date_pattern='dd/MM/yyyy'
        )
        self.data_inicio.pack(side="left", padx=5)
        
        ctk.CTkLabel(
            periodo_frame,
            text="Até:",
            font=ctk.CTkFont(size=12),
            text_color=COR_TEXTO
        ).pack(side="left", padx=(15, 0))
        
        self.data_fim = DateEntry(
            periodo_frame,
            width=12,
            background='darkblue',
            foreground='white',
            borderwidth=2,
            locale='pt_BR',
            date_pattern='dd/MM/yyyy'
        )
        self.data_fim.pack(side="left", padx=5)
        
        ctk.CTkButton(
            periodo_frame,
            text="APLICAR",
            command=self._executar_busca,
            fg_color=COR_DESTAQUE,
            hover_color="#1a5a8c",
            text_color=COR_TEXTO,
            width=80,
            height=25,
            font=ctk.CTkFont(size=10)
        ).pack(side="left", padx=(15, 0))
    
    def _executar_busca(self):
        """Executa a busca com o termo atual"""
        termo = self.busca_entry.get().strip()
        
        if not termo:
            # Mostrar estado vazio
            for container in [self.agenda_container, self.receitas_container]:
                for widget in container.winfo_children():
                    widget.destroy()
                ctk.CTkLabel(
                    container,
                    text="Digite um termo para buscar",
                    font=ctk.CTkFont(size=14),
                    text_color="#888888"
                ).pack(pady=30)
            return
        
        # Executar busca
        resultados = self.excel.buscar_global(termo)
        
        # Atualizar abas
        self._exibir_resultados_agenda(resultados.get('agenda', []))
        self._exibir_resultados_receitas(resultados.get('receitas', []))
    
    def _exibir_resultados_agenda(self, resultados):
        """Exibe resultados de consultas"""
        for widget in self.agenda_container.winfo_children():
            widget.destroy()
        
        if not resultados:
            ctk.CTkLabel(
                self.agenda_container,
                text="Nenhuma consulta encontrada",
                font=ctk.CTkFont(size=13),
                text_color="#888888"
            ).pack(pady=20)
            return
        
        # Cabeçalho
        cabecalho = ctk.CTkFrame(self.agenda_container, fg_color="transparent")
        cabecalho.pack(fill="x", pady=(0, 5))
        
        for texto, largura in [("Paciente", 180), ("Médico", 120), ("Tipo", 80), ("Data", 75), ("Hora", 55), ("Status", 65), ("Ações", 75)]:
            ctk.CTkLabel(
                cabecalho,
                text=texto,
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color="#888888",
                width=largura
            ).pack(side="left")
        
        for r in resultados:
            linha = ctk.CTkFrame(self.agenda_container, fg_color="#333333", corner_radius=3)
            linha.pack(fill="x", pady=2)

            topo = ctk.CTkFrame(linha, fg_color="transparent")
            topo.pack(fill="x")
            
            ctk.CTkLabel(
                topo,
                text=r.get('paciente', ''),
                font=ctk.CTkFont(size=12),
                text_color=COR_TEXTO,
                width=180,
                anchor="w"
            ).pack(side="left", padx=2)
            
            ctk.CTkLabel(
                topo,
                text=r.get('medico', ''),
                font=ctk.CTkFont(size=11),
                text_color="#aaaaaa",
                width=120
            ).pack(side="left")
            
            tipo = r.get('tipo', '')
            prefixo = "⚡ " if r.get('encaixe') == 'TRUE' else ""
            ctk.CTkLabel(
                topo,
                text=f"{prefixo}{tipo}",
                font=ctk.CTkFont(size=11),
                text_color=COR_AVISO if r.get('encaixe') == 'TRUE' else COR_TEXTO,
                width=80
            ).pack(side="left")
            
            data = r.get('data', '')
            if data and len(data) >= 10:
                data = data[8:10] + '/' + data[5:7] + '/' + data[:4]
            ctk.CTkLabel(
                topo,
                text=data,
                font=ctk.CTkFont(size=11),
                text_color=COR_TEXTO,
                width=75
            ).pack(side="left")
            
            ctk.CTkLabel(
                topo,
                text=r.get('hora', ''),
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=COR_TEXTO,
                width=55
            ).pack(side="left")
            
            status = r.get('status', '')
            cor = COR_SUCESSO if status == 'ATIVO' else COR_ERRO
            ctk.CTkLabel(
                topo,
                text=status,
                font=ctk.CTkFont(size=11),
                text_color=cor,
                width=65
            ).pack(side="left")

            if status == 'ATIVO':
                ctk.CTkButton(
                    topo,
                    text="✏️ EDITAR",
                    command=lambda consulta=r: self._abrir_edicao(consulta),
                    fg_color=COR_DESTAQUE,
                    hover_color="#1a5a8c",
                    text_color=COR_TEXTO,
                    width=75,
                    height=24,
                    font=ctk.CTkFont(size=10, weight="bold")
                ).pack(side="left", padx=2)
            else:
                ctk.CTkLabel(
                    topo,
                    text="—",
                    font=ctk.CTkFont(size=11),
                    text_color="#666666",
                    width=75
                ).pack(side="left", padx=2)

            observacao = str(r.get('observacao', '') or '').strip()
            if observacao:
                ctk.CTkLabel(
                    linha,
                    text=f"Obs: {observacao}",
                    font=ctk.CTkFont(size=10),
                    text_color="#d9d9d9",
                    justify="left",
                    anchor="w"
                ).pack(fill="x", padx=8, pady=(0, 6))

    def _abrir_edicao(self, r: dict):
        """Abre o modal de edição para uma consulta da busca"""
        from tela_edicao_consulta import TelaEdicaoConsulta
        consulta_dict = {
            'id':            r.get('id'),
            'paciente':      r.get('paciente', ''),
            'medico':        r.get('medico', ''),
            'tipo_consulta': r.get('tipo', 'Normal'),
            'data':          r.get('data', ''),
            'hora':          r.get('hora', ''),
            'encaixe':       r.get('encaixe', 'FALSE'),
            'observacao':    r.get('observacao', ''),
            'status':        r.get('status', ''),
        }
        TelaEdicaoConsulta(
            excel=self.excel,
            consulta=consulta_dict,
            usuario=self.usuario,
            callback_salvo=self._executar_busca,
            parent=self.janela
        )

    
    def _abrir_retirada_receita(self, receita):
        """Abre a tela de retirada a partir de um resultado da busca"""
        from tela_receitas import ModalRetiradaReceita
        ModalRetiradaReceita(
            excel=self.excel,
            receita=receita,
            usuario=self.usuario,
            callback_sucesso=self._executar_busca,
            parent=self.janela
        )

    def _exibir_resultados_receitas(self, resultados):
        """Exibe resultados de receitas"""
        for widget in self.receitas_container.winfo_children():
            widget.destroy()
        
        if not resultados:
            ctk.CTkLabel(
                self.receitas_container,
                text="Nenhuma receita encontrada",
                font=ctk.CTkFont(size=13),
                text_color="#888888"
            ).pack(pady=20)
            return
        
        # Cabeçalho
        cabecalho = ctk.CTkFrame(self.receitas_container, fg_color="transparent")
        cabecalho.pack(fill="x", pady=(0, 5))
        
        for texto, largura in [("Paciente", 200), ("Status", 100), ("Quem Retirou", 150), ("Data Pedido", 120), ("Ações", 90)]:
            ctk.CTkLabel(
                cabecalho,
                text=texto,
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color="#888888",
                width=largura
            ).pack(side="left")
        
        for r in resultados:
            linha = ctk.CTkFrame(self.receitas_container, fg_color="#333333", corner_radius=3)
            linha.pack(fill="x", pady=2)

            topo = ctk.CTkFrame(linha, fg_color="transparent")
            topo.pack(fill="x")
            
            ctk.CTkLabel(
                topo,
                text=r.get('paciente', ''),
                font=ctk.CTkFont(size=12),
                text_color=COR_TEXTO,
                width=200,
                anchor="w"
            ).pack(side="left", padx=2)
            
            status = str(r.get('status', '')).upper()
            cor = COR_SUCESSO if status == 'RETIRADA' else COR_AVISO
            ctk.CTkLabel(
                topo,
                text=status,
                font=ctk.CTkFont(size=11),
                text_color=cor,
                width=100
            ).pack(side="left")
            
            ctk.CTkLabel(
                topo,
                text=r.get('quem_retirou', ''),
                font=ctk.CTkFont(size=11),
                text_color="#aaaaaa",
                width=150
            ).pack(side="left")
            
            data = r.get('data_pedido', '')
            if data and len(data) >= 10:
                data = data[:10]
            ctk.CTkLabel(
                topo,
                text=data,
                font=ctk.CTkFont(size=11),
                text_color="#aaaaaa",
                width=120
            ).pack(side="left")

            if status != 'RETIRADA':
                ctk.CTkButton(
                    topo,
                    text="📤 RETIRAR",
                    command=lambda receita=r: self._abrir_retirada_receita(receita),
                    fg_color=COR_DESTAQUE,
                    hover_color="#1a5a8c",
                    text_color=COR_TEXTO,
                    width=90,
                    height=24,
                    font=ctk.CTkFont(size=10, weight="bold")
                ).pack(side="left", padx=2)
            else:
                ctk.CTkLabel(
                    topo,
                    text="—",
                    font=ctk.CTkFont(size=11),
                    text_color="#666666",
                    width=90
                ).pack(side="left", padx=2)

            observacao = str(r.get('observacao', '') or '').strip()
            if observacao:
                ctk.CTkLabel(
                    linha,
                    text=f"Obs: {observacao}",
                    font=ctk.CTkFont(size=10),
                    text_color="#d9d9d9",
                    justify="left",
                    anchor="w"
                ).pack(fill="x", padx=8, pady=(0, 6))
    
    def _fechar(self):
        try:
            if self._timer_busca:
                self.janela.after_cancel(self._timer_busca)
            self.janela.destroy()
        except:
            pass

