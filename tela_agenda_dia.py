"""
tela_agenda_dia.py - Janela da Agenda do Dia
Dimensões: 800x600 pixels
Mostra consultas do dia por médico, presença e receitas pendentes
"""
import customtkinter as ctk
from datetime import datetime, date
from typing import Optional, Callable
from config_manager import ExcelManager
from utils import date_str, date_br, get_weekday_name

COR_FUNDO = "#2b2b2b"
COR_TEXTO = "#ffffff"
COR_DESTAQUE = "#1f6aa5"
COR_SUCESSO = "#28a745"
COR_ERRO = "#dc3545"
COR_AVISO = "#ffc107"


class TelaAgendaDia:
    """Janela independente da agenda do dia"""
    
    def __init__(self, excel: ExcelManager, usuario: str = "Sistema"):
        self.excel = excel
        self.usuario = usuario
        self.janela = None
        self.widgets_medicos = {}
        self.receitas_frame = None
        
        self._criar_janela()
        self._atualizar_dados()
    
    def _criar_janela(self):
        """Cria a janela da agenda do dia"""
        hoje = date.today()
        data_exibicao = hoje.strftime("%d/%m/%Y")
        dia_semana = get_weekday_name(hoje)
        
        self.janela = ctk.CTkToplevel()
        self.janela.title(f"📊 AGENDA DO DIA - {data_exibicao} ({dia_semana})")
        self.janela.geometry("800x600")
        self.janela.resizable(True, True)
        self.janela.minsize(700, 500)
        
        # Comportamento de fechar (minimiza para tray)
        self.janela.protocol("WM_DELETE_WINDOW", self._minimizar)
        
        # Frame principal
        self.frame = ctk.CTkScrollableFrame(self.janela, fg_color=COR_FUNDO)
        self.frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Título
        titulo_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        titulo_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            titulo_frame,
            text=f"📊 AGENDA DO DIA - {data_exibicao}",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COR_TEXTO
        ).pack(side="left")
        
        # Botões direita
        btn_frame_dir = ctk.CTkFrame(titulo_frame, fg_color="transparent")
        btn_frame_dir.pack(side="right")

        ctk.CTkButton(
            btn_frame_dir,
            text="🖨️ IMPRIMIR",
            command=self._imprimir_agenda,
            fg_color="#555555",
            hover_color="#666666",
            text_color=COR_TEXTO,
            width=100,
            height=28,
            font=ctk.CTkFont(size=11)
        ).pack(side="right", padx=(5, 0))

        ctk.CTkButton(
            btn_frame_dir,
            text="🖨️ IMPRIMIR VISÃO",
            command=self._imprimir_visao,
            fg_color=COR_DESTAQUE,
            hover_color="#1a5a8c",
            text_color=COR_TEXTO,
            width=120,
            height=28,
            font=ctk.CTkFont(size=11)
        ).pack(side="right", padx=(5, 0))

        ctk.CTkButton(
            btn_frame_dir,
            text="🔄 ATUALIZAR",
            command=self._atualizar_dados,
            fg_color=COR_DESTAQUE,
            hover_color="#1a5a8c",
            text_color=COR_TEXTO,
            width=100,
            height=28,
            font=ctk.CTkFont(size=11)
        ).pack(side="right")
        
        # Container para seções de médicos
        self.medicos_container = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.medicos_container.pack(fill="both", expand=True)
        
        # Separador
        ctk.CTkFrame(self.frame, height=2, fg_color="#444444").pack(fill="x", pady=(15, 10))
        
        # Seção de receitas pendentes
        ctk.CTkLabel(
            self.frame,
            text="── RECEITAS PENDENTES ──",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=COR_TEXTO
        ).pack(pady=(5, 10))
        
        self.receitas_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.receitas_frame.pack(fill="x")
        
        # Centralizar
        self.janela.update_idletasks()
        largura = self.janela.winfo_width()
        altura = self.janela.winfo_height()
        x = (self.janela.winfo_screenwidth() // 2) - (largura // 2)
        y = (self.janela.winfo_screenheight() // 2) - (altura // 2)
        self.janela.geometry(f"{largura}x{altura}+{x}+{y}")
    
    def _atualizar_dados(self):
        """Atualiza todos os dados da agenda"""
        # Limpar widgets antigos
        for widget in self.medicos_container.winfo_children():
            widget.destroy()
        
        hoje = date_str()
        agenda = self.excel.get_agenda_do_dia()
        medicos = self.excel.get_medicos()
        
        if agenda.empty:
            ctk.CTkLabel(
                self.medicos_container,
                text="📭 Nenhuma consulta agendada para hoje",
                font=ctk.CTkFont(size=14),
                text_color="#888888"
            ).pack(pady=30)
        else:
            # Agrupar por médico
            for medico in medicos:
                consultas_medico = agenda[agenda['medico'] == medico]
                if consultas_medico.empty:
                    continue
                
                self._criar_secao_medico(medico, consultas_medico)
        
        # Atualizar receitas pendentes
        self._atualizar_receitas()
        
        # Agendar próxima atualização (a cada 30 segundos)
        if hasattr(self, '_timer_id'):
            self.janela.after_cancel(self._timer_id)
        self._timer_id = self.janela.after(30000, self._atualizar_dados)
    
    def _criar_secao_medico(self, medico: str, consultas):
        """Cria seção para um médico"""
        # Frame da seção
        secao = ctk.CTkFrame(self.medicos_container, fg_color="#333333", corner_radius=8)
        secao.pack(fill="x", pady=(0, 10))
        
        # Cabeçalho com nome e contagem
        total = len(consultas)
        presentes = len(consultas[consultas['compareceu'] == 'TRUE'])
        
        cabecalho = ctk.CTkFrame(secao, fg_color="transparent")
        cabecalho.pack(fill="x", padx=15, pady=(10, 5))
        
        ctk.CTkLabel(
            cabecalho,
            text=f"── {medico} ──",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=COR_DESTAQUE
        ).pack(side="left")
        
        ctk.CTkLabel(
            cabecalho,
            text=f"✅ {presentes}/{total} presentes",
            font=ctk.CTkFont(size=11),
            text_color="#aaaaaa"
        ).pack(side="right")
        
        # Colunas
        colunas_frame = ctk.CTkFrame(secao, fg_color="transparent")
        colunas_frame.pack(fill="x", padx=15, pady=(5, 0))
        
        for texto, largura in [("Horário", 80), ("Paciente", 200), ("Tipo", 100), ("Status", 100), ("Presença", 100)]:
            ctk.CTkLabel(
                colunas_frame,
                text=texto,
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color="#888888",
                width=largura
            ).pack(side="left")
        
        # Lista de consultas
        for _, consulta in consultas.iterrows():
            linha = ctk.CTkFrame(secao, fg_color="transparent")
            linha.pack(fill="x", padx=15, pady=2)
            
            # Horário
            ctk.CTkLabel(
                linha,
                text=consulta.get('hora', ''),
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=COR_TEXTO,
                width=80
            ).pack(side="left")
            
            # Paciente
            ctk.CTkLabel(
                linha,
                text=consulta.get('paciente', ''),
                font=ctk.CTkFont(size=12),
                text_color=COR_TEXTO,
                width=200,
                anchor="w"
            ).pack(side="left")

            obs = str(consulta.get('observacao', '') or '').strip()
            if obs:
                ctk.CTkLabel(
                    linha,
                    text=f"📝 {obs}",
                    font=ctk.CTkFont(size=10),
                    text_color=COR_AVISO,
                    wraplength=280,
                    justify="left",
                    anchor="w"
                ).pack(side="left", padx=(8, 0))
            
            # Tipo
            tipo = consulta.get('tipo_consulta', '')
            ctk.CTkLabel(
                linha,
                text=tipo,
                font=ctk.CTkFont(size=11),
                text_color=COR_TEXTO,
                width=100
            ).pack(side="left")
            
            # Status
            status = consulta.get('status', '')
            cor_status = COR_SUCESSO if status == 'ATIVO' else COR_ERRO
            ctk.CTkLabel(
                linha,
                text=status,
                font=ctk.CTkFont(size=11),
                text_color=cor_status,
                width=100
            ).pack(side="left")
            
            # Checkbox de presença
            id_agenda = int(consulta['id'])
            presente = consulta.get('compareceu') == 'TRUE'
            
            var_presenca = ctk.BooleanVar(value=presente)
            checkbox = ctk.CTkCheckBox(
                linha,
                text="✅ Presente" if presente else "☐ Presente",
                variable=var_presenca,
                command=lambda idx=id_agenda, var=var_presenca: self._toggle_presenca(idx, var),
                fg_color=COR_SUCESSO,
                hover_color="#218838",
                text_color=COR_TEXTO,
                font=ctk.CTkFont(size=11)
            )
            checkbox.pack(side="left", padx=(10, 0))
            
            if presente:
                checkbox.select()
    
    def _imprimir_agenda(self):
        """Gera PDF da agenda do dia e abre para impressão"""
        try:
            from impressao import imprimir_agenda_dia
            hoje = date.today()
            data_str = hoje.strftime("%Y-%m-%d")
            agenda = self.excel.get_agenda_do_dia()
            medicos = self.excel.get_medicos()

            agenda_por_medico = {}
            if not agenda.empty:
                for medico in medicos:
                    consultas_medico = agenda[agenda['medico'] == medico]
                    if not consultas_medico.empty:
                        agenda_por_medico[medico] = consultas_medico

            imprimir_agenda_dia(agenda_por_medico, data_str, abrir=True)
        except Exception as e:
            import tkinter.messagebox as mb
            mb.showerror("Erro ao imprimir", f"Não foi possível gerar o PDF:\n{e}",
                         parent=self.janela)

    def _imprimir_visao(self):
        """Imprime uma visão geral da janela atual em formato PDF."""
        try:
            from impressao import imprimir_lista
            itens = []
            for medico in self.excel.get_medicos():
                consultas = self.excel.get_agenda_do_dia()
                consultas_medico = consultas[consultas['medico'] == medico] if not consultas.empty else []
                for _, consulta in consultas_medico.iterrows():
                    itens.append({
                        'Médico': consulta.get('medico', ''),
                        'Horário': consulta.get('hora', ''),
                        'Paciente': consulta.get('paciente', ''),
                        'Tipo': consulta.get('tipo_consulta', ''),
                        'Observação': consulta.get('observacao', ''),
                    })
            imprimir_lista(itens, titulo="Visão da Agenda do Dia", abrir=True)
        except Exception as e:
            import tkinter.messagebox as mb
            mb.showerror("Erro ao imprimir", f"Não foi possível gerar o PDF:\n{e}", parent=self.janela)

    def _toggle_presenca(self, id_agenda: int, var: ctk.BooleanVar):
        """Alterna presença do paciente"""
        try:
            presente = var.get()
            self.excel.marcar_presenca(id_agenda, presente, self.usuario)
            # Atualizar imediatamente após marcar
            self._atualizar_dados()
        except Exception as e:
            print(f"Erro ao marcar presença: {e}")
    
    def _atualizar_receitas(self):
        """Atualiza a lista de receitas pendentes"""
        for widget in self.receitas_frame.winfo_children():
            widget.destroy()
        
        pendentes = self.excel.get_receitas_pendentes()
        
        if pendentes.empty:
            ctk.CTkLabel(
                self.receitas_frame,
                text="Nenhuma receita pendente",
                font=ctk.CTkFont(size=12),
                text_color="#888888"
            ).pack(pady=5)
            return
        
        receitas_ordenadas = []
        for _, receita in pendentes.iterrows():
            data_pedido = str(receita.get('data_pedido', '')).strip()
            data_prevista = ''
            if len(data_pedido) >= 10:
                data_prevista = self.excel.calcular_data_retirada_receita(data_pedido[:10])
            receitas_ordenadas.append((data_prevista, str(receita.get('paciente', '')).strip().lower(), receita))

        receitas_ordenadas.sort(key=lambda item: (item[0], item[1]))

        for _, _, receita in receitas_ordenadas[:10]:
            linha = ctk.CTkFrame(self.receitas_frame, fg_color="transparent")
            linha.pack(fill="x", pady=2)
            
            ctk.CTkLabel(
                linha,
                text=f"👤 {receita.get('paciente', '')}",
                font=ctk.CTkFont(size=12),
                text_color=COR_TEXTO,
                width=200,
                anchor="w"
            ).pack(side="left", padx=10)
            
            data_pedido = receita.get('data_pedido', '')
            data_prevista = ''
            if data_pedido and len(data_pedido) >= 10:
                data_pedido = data_pedido[:10]
                data_prevista = self.excel.get_data_retirada_formatada(data_pedido)
            observacao = str(receita.get('observacao', '') or '').strip()
            texto = f"📅 {data_pedido} | Retirada: {data_prevista or '-'}"
            if observacao:
                texto += f" | Obs: {observacao}"
            ctk.CTkLabel(
                linha,
                text=texto,
                font=ctk.CTkFont(size=11),
                text_color="#aaaaaa",
                width=320,
                anchor="w",
                wraplength=320
            ).pack(side="left")
            
            ctk.CTkButton(
                linha,
                text="RETIRAR",
                command=lambda r=receita: self._abrir_retirada(r),
                fg_color=COR_DESTAQUE,
                hover_color="#1a5a8c",
                text_color=COR_TEXTO,
                width=80,
                height=25,
                font=ctk.CTkFont(size=10, weight="bold")
            ).pack(side="right", padx=10)
    
    def _abrir_retirada(self, receita):
        """Abre formulário de retirada de receita"""
        from tela_receitas import ModalRetiradaReceita
        ModalRetiradaReceita(
            excel=self.excel,
            receita=receita if isinstance(receita, dict) else (receita.to_dict() if hasattr(receita, 'to_dict') else dict(receita)),
            usuario=self.usuario,
            callback_sucesso=self._atualizar_dados,
            parent=self.janela
        )
    
    def _minimizar(self):
        """Minimiza para a bandeja (oculta janela)"""
        try:
            self.janela.withdraw()
        except:
            pass
    
    def mostrar(self):
        """Mostra a janela"""
        if self.janela:
            self.janela.deiconify()
            self.janela.lift()
            self.janela.focus_force()
            self._atualizar_dados()
    
    def esta_visivel(self) -> bool:
        try:
            return self.janela and self.janela.winfo_viewable()
        except:
            return False
    
    def destruir(self):
        try:
            if hasattr(self, '_timer_id'):
                self.janela.after_cancel(self._timer_id)
            self.janela.destroy()
        except:
            pass

