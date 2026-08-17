"""
tela_agendamento.py - Formulário de Agendamento
Fluxo: Tipo Consulta -> Médico (se Normal) -> Data -> Horário -> Paciente -> Confirmar
"""
import calendar
import customtkinter as ctk
from tkcalendar import DateEntry
from datetime import datetime, date
from typing import Optional, Callable
from config_manager import ExcelManager, MODALIDADES_DISPONIVEIS
from utils import (
    now, date_str, get_modalidade_rules, get_weekday_name,
    validate_required, normalize_text
)

DIAS_SEMANA = ['seg', 'ter', 'qua', 'qui', 'sex', 'sab', 'dom']
NOMES_DIAS = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
TURNOS = ['manha', 'tarde']
NOMES_TURNOS = {'manha': 'Manhã (08:00-12:00)', 'tarde': 'Tarde (13:00-17:00)'}


class TelaAgendamento:
    """Formulário de agendamento de consultas"""
    
    def __init__(self, excel: ExcelManager, usuario: str = "Sistema"):
        self.excel = excel
        self.usuario = usuario
        self.modo_encaixe = False
        
        # Estado do formulário
        self.passo = 1
        self.tipo_consulta = None
        self.medico = None
        self.medico_chave = None
        self.data = None
        self.data_selecionada = None  # Guarda data para navegação segura (evita erro ao destruir DateEntry)
        self.hora = None
        self.horarios_disponiveis = []
        self.dia_semana = None
        self.turno = None
        self.calendario = None  # Referência para o widget DateEntry
        self.mes_visualizacao = date.today().replace(day=1)
        self.medico_var = None
        self.paciente_nome = ""
        self.observacao = ""
        self._agenda_cache = None
        self._horarios_cache = {}
        self._medico_chaves_cache = None
        
        # Criar janela
        titulo = "📅 AGENDAR CONSULTA"
        largura = 640
        altura = 680
        
        self.janela = ctk.CTkToplevel()
        self.janela.title(titulo)
        self.janela.geometry(f"{largura}x{altura}")
        self.janela.resizable(False, False)
        self.janela.transient()  # Torna independente
        self.janela.protocol("WM_DELETE_WINDOW", self.fechar)
        self.janela.bind('<Escape>', lambda e: self.fechar())
        
        # Frame principal
        self.frame = ctk.CTkFrame(self.janela, fg_color="#2b2b2b")
        self.frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        self.titulo_label = ctk.CTkLabel(
            self.frame,
            text=titulo,
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#ffffff"
        )
        self.titulo_label.pack(pady=(0, 15))
        
        # Container para o conteúdo dinâmico
        self.conteudo_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.conteudo_frame.pack(fill="both", expand=True)
        
        # Container para mensagens
        self.msg_label = ctk.CTkLabel(
            self.frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="#28a745"
        )
        self.msg_label.pack(pady=(5, 0))
        
        # Navegação
        self.nav_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.nav_frame.pack(fill="x", pady=(15, 0))
        
        self.voltar_btn = ctk.CTkButton(
            self.nav_frame,
            text="← VOLTAR",
            command=self.passo_anterior,
            fg_color="#444444",
            hover_color="#555555",
            text_color="#ffffff",
            width=100,
            state="disabled"
        )
        self.voltar_btn.pack(side="left")
        
        self.indicador_label = ctk.CTkLabel(
            self.nav_frame,
            text="Passo 1/5",
            font=ctk.CTkFont(size=11),
            text_color="#888888"
        )
        self.indicador_label.pack(side="left", padx=20)
        
        self.avancar_btn = ctk.CTkButton(
            self.nav_frame,
            text="AVANÇAR →",
            command=self.proximo_passo,
            fg_color="#1f6aa5",
            hover_color="#1a5a8c",
            text_color="#ffffff",
            width=100
        )
        self.avancar_btn.pack(side="right")
        
        # Centralizar
        self.janela.update_idletasks()
        x = (self.janela.winfo_screenwidth() // 2) - (largura // 2)
        y = (self.janela.winfo_screenheight() // 2) - (altura // 2)
        self.janela.geometry(f"+{x}+{y}")
        
        # Iniciar no passo 1
        self._renderizar_passo_1()
        self._atualizar_indicador()
    
    def _atualizar_indicador(self):
        """Atualiza o indicador de progresso"""
        total = 6
        self.indicador_label.configure(text=f"Passo {self.passo}/{total}")
    
    # ============ PASSO 1: Tipo de Consulta ============
    
    def _renderizar_passo_1(self):
        self._limpar_conteudo()
        
        ctk.CTkLabel(
            self.conteudo_frame,
            text="Selecione o tipo de consulta:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#ffffff"
        ).pack(pady=(0, 15))
        
        tipos = self.excel.get_tipos_consulta_disponiveis()
        for tipo in tipos:
            btn = ctk.CTkButton(
                self.conteudo_frame,
                text=tipo,
                command=lambda t=tipo: self._selecionar_tipo(t),
                fg_color="#333333",
                hover_color="#444444",
                text_color="#ffffff",
                height=40,
                font=ctk.CTkFont(size=13)
            )
            btn.pack(fill="x", pady=4)
    
    def _selecionar_tipo(self, tipo: str):
        self.tipo_consulta = tipo
        self.proximo_passo()
    
    # ============ PASSO 2: Selecionar Médico (só para Normal) ============
    
    def _renderizar_passo_2(self):
        self._limpar_conteudo()
        
        if self.tipo_consulta == "Normal" or self.modo_encaixe:
            ctk.CTkLabel(
                self.conteudo_frame,
                text="Selecione o médico:",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#ffffff"
            ).pack(pady=(0, 15))
            
            medicos = self.excel.get_medicos()
            med_chaves = self.excel.get_medico_chaves()
            
            if not medicos:
                ctk.CTkLabel(
                    self.conteudo_frame,
                    text="Nenhum médico cadastrado!\nVá em Configurações para adicionar.",
                    font=ctk.CTkFont(size=12),
                    text_color="#dc3545"
                ).pack(pady=20)
                return
            
            for nome in medicos:
                btn = ctk.CTkButton(
                    self.conteudo_frame,
                    text=nome,
                    command=lambda n=nome: self._selecionar_medico_normal(n),
                    fg_color="#333333",
                    hover_color="#444444",
                    text_color="#ffffff",
                    height=40,
                    font=ctk.CTkFont(size=13)
                )
                btn.pack(fill="x", pady=4)
        else:
            regra = self.excel.get_regra_tipo_consulta(self.tipo_consulta)
            dia_idx = regra.get('weekday', 0)
            turno = regra.get('turno', 'manha')
            dia_nome = NOMES_DIAS[dia_idx]
            turno_nome = NOMES_TURNOS.get(turno, turno)
            
            medicos = self.excel.get_medicos()
            if not medicos:
                ctk.CTkLabel(
                    self.conteudo_frame,
                    text="Nenhum médico cadastrado!\nVá em Configurações para adicionar.",
                    font=ctk.CTkFont(size=12),
                    text_color="#dc3545"
                ).pack(pady=20)
                return
            
            self.medico_var = ctk.StringVar(value=self.excel.get_modalidade_medico(self.tipo_consulta) or medicos[0])
            self.medico = self.medico_var.get()
            self._definir_medico_chave()
            
            info_frame = ctk.CTkFrame(self.conteudo_frame, fg_color="#333333", corner_radius=8)
            info_frame.pack(fill="x", pady=10)
            
            ctk.CTkLabel(
                info_frame,
                text=f"📋 {self.tipo_consulta}",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#1f6aa5"
            ).pack(pady=(10, 5))
            
            ctk.CTkLabel(
                info_frame,
                text=f"📅 {dia_nome} - {turno_nome}",
                font=ctk.CTkFont(size=13),
                text_color="#ffffff"
            ).pack(pady=2)
            
            ctk.CTkLabel(
                info_frame,
                text="Selecione o médico responsável por esta modalidade:",
                font=ctk.CTkFont(size=12),
                text_color="#aaaaaa"
            ).pack(pady=(5, 5))

            menu = ctk.CTkOptionMenu(
                self.conteudo_frame,
                variable=self.medico_var,
                values=medicos,
                fg_color="#444444",
                button_color="#1f6aa5",
                button_hover_color="#1a5a8c",
                text_color="#ffffff"
            )
            menu.pack(fill="x", pady=(0, 10))
            
            ctk.CTkButton(
                self.conteudo_frame,
                text="✅ CONTINUAR",
                command=self._selecionar_medico_modalidade,
                fg_color="#28a745",
                hover_color="#218838",
                text_color="#ffffff",
                height=40,
                font=ctk.CTkFont(size=13, weight="bold")
            ).pack(pady=10)
    
    def _selecionar_medico_normal(self, nome: str):
        self.medico = nome
        self._definir_medico_chave()
        self.proximo_passo()

    def _selecionar_medico_modalidade(self):
        self.medico = self.medico_var.get() if self.medico_var else ""
        self._definir_medico_chave()
        self.proximo_passo()

    def _definir_medico_chave(self):
        if not self.medico:
            self.medico_chave = ""
            return
        medico_chaves = self.excel.get_medico_chaves()
        chaves_invertidas = {v: k for k, v in medico_chaves.items()}
        self.medico_chave = chaves_invertidas.get(self.medico, self.excel._chave_medico_fallback(self.medico)) if hasattr(self.excel, '_chave_medico_fallback') else ""
    
    # ============ PASSO 3: Selecionar Data (para Normal/Encaixe, ou confirmar automática) ============
    
    def _renderizar_passo_3(self):
        self._limpar_conteudo()
        
        ctk.CTkLabel(
            self.conteudo_frame,
            text="Selecione a data:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#ffffff"
        ).pack(pady=(0, 10))
        
        # Se modalidade com regra fixa
        if self.tipo_consulta != "Normal" and not self.modo_encaixe:
            regra = self.excel.get_regra_tipo_consulta(self.tipo_consulta)
            dia_idx = regra.get('weekday', 0)
            dia_nome = NOMES_DIAS[dia_idx]
            
            ctk.CTkLabel(
                self.conteudo_frame,
                text=f"⚠️ {self.tipo_consulta} só ocorre às {dia_nome}-feiras",
                font=ctk.CTkFont(size=12),
                text_color="#ffc107"
            ).pack(pady=(0, 10))

        self._renderizar_calendario_mes()
    
    # ============ PASSO 4: Selecionar Horário ============
    
    def _renderizar_calendario_mes(self):
        self._limpar_conteudo()

        ctk.CTkLabel(
            self.conteudo_frame,
            text=f"Agenda do mês para {self.tipo_consulta} com {self.medico or 'médico'}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#ffffff"
        ).pack(pady=(0, 10))

        nav_frame = ctk.CTkFrame(self.conteudo_frame, fg_color="transparent")
        nav_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkButton(
            nav_frame,
            text="◀",
            command=self._mes_anterior,
            width=40,
            fg_color="#444444",
            hover_color="#555555"
        ).pack(side="left")

        ctk.CTkLabel(
            nav_frame,
            text=self.mes_visualizacao.strftime("%B/%Y"),
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#ffffff"
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            nav_frame,
            text="▶",
            command=self._mes_posterior,
            width=40,
            fg_color="#444444",
            hover_color="#555555"
        ).pack(side="left")

        week_frame = ctk.CTkFrame(self.conteudo_frame, fg_color="transparent")
        week_frame.pack(fill="x")
        for col, nome in enumerate(['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']):
            label = ctk.CTkLabel(
                week_frame,
                text=nome,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="#aaaaaa"
            )
            label.grid(row=0, column=col, padx=2, pady=2, sticky="nsew")
            week_frame.grid_columnconfigure(col, weight=1)

        self._agenda_cache = self.excel.get_agenda(status='ATIVO')
        self._horarios_cache = {}

        cal = calendar.Calendar(firstweekday=0)
        mes = cal.monthdayscalendar(self.mes_visualizacao.year, self.mes_visualizacao.month)
        dias_frame = ctk.CTkFrame(self.conteudo_frame, fg_color="transparent")
        dias_frame.pack(fill="both", expand=True, pady=(8, 0))

        for row_idx, semana in enumerate(mes):
            for col_idx, dia in enumerate(semana):
                if dia == 0:
                    placeholder = ctk.CTkLabel(dias_frame, text="", fg_color="transparent", width=60, height=55)
                    placeholder.grid(row=row_idx, column=col_idx, padx=2, pady=2, sticky="nsew")
                    continue
                data_dt = date(self.mes_visualizacao.year, self.mes_visualizacao.month, dia)
                vagas = self._contar_horarios_disponiveis(data_dt.strftime("%Y-%m-%d"))
                btn = ctk.CTkButton(
                    dias_frame,
                    text=f"{dia}\n{vagas} vaga(s)",
                    command=lambda d=data_dt: self._selecionar_data_mes(d),
                    width=60,
                    height=55,
                    fg_color="#333333" if data_dt >= date.today() else "#555555",
                    hover_color="#1f6aa5" if data_dt >= date.today() else "#555555",
                    text_color="#ffffff",
                    state="disabled" if data_dt < date.today() else "normal"
                )
                btn.grid(row=row_idx, column=col_idx, padx=2, pady=2, sticky="nsew")
                dias_frame.grid_columnconfigure(col_idx, weight=1)

    def _mes_anterior(self):
        self.mes_visualizacao = self.mes_visualizacao.replace(day=1)
        if self.mes_visualizacao.month == 1:
            self.mes_visualizacao = self.mes_visualizacao.replace(year=self.mes_visualizacao.year - 1, month=12)
        else:
            self.mes_visualizacao = self.mes_visualizacao.replace(month=self.mes_visualizacao.month - 1)
        self._renderizar_calendario_mes()

    def _mes_posterior(self):
        self.mes_visualizacao = self.mes_visualizacao.replace(day=1)
        if self.mes_visualizacao.month == 12:
            self.mes_visualizacao = self.mes_visualizacao.replace(year=self.mes_visualizacao.year + 1, month=1)
        else:
            self.mes_visualizacao = self.mes_visualizacao.replace(month=self.mes_visualizacao.month + 1)
        self._renderizar_calendario_mes()

    def _selecionar_data_mes(self, data_obj: date):
        self.data_selecionada = data_obj
        self.data = data_obj.strftime("%Y-%m-%d")
        self.proximo_passo()

    def _contar_horarios_disponiveis(self, data_str: str) -> int:
        data_obj = datetime.strptime(data_str, "%Y-%m-%d").date()
        dia_semana = DIAS_SEMANA[data_obj.weekday()]

        medico = self.medico
        medico_chave = self.medico_chave
        if self.tipo_consulta != "Normal" and not self.modo_encaixe:
            if not medico:
                medico = self.excel.get_modalidade_medico(self.tipo_consulta) or ""
            if not medico_chave and medico:
                medico_chaves = self.excel.get_medico_chaves()
                invert = {v: k for k, v in medico_chaves.items()}
                medico_chave = invert.get(medico, "")

        if not medico_chave:
            return 0

        datas_indisponiveis = self.excel.get_datas_indisponiveis(medico)
        if data_str in datas_indisponiveis:
            return 0

        if self.tipo_consulta != "Normal" and not self.modo_encaixe:
            regra = self.excel.get_regra_tipo_consulta(self.tipo_consulta)
            dia_permitido = regra.get('weekday')
            if dia_permitido is not None and data_obj.weekday() != dia_permitido:
                return 0
            turnos = [regra.get('turno', 'manha')]
        else:
            turnos = ['manha', 'tarde']

        if self._agenda_cache is not None:
            agenda_df = self._agenda_cache
            if medico:
                agenda_df = agenda_df[agenda_df['medico'] == medico]
            agenda_df = agenda_df[agenda_df['data'] == data_str]
        else:
            agenda_df = self.excel.get_agenda(data=data_str, medico=medico, status='ATIVO')

        if self.tipo_consulta != "Normal" and not self.modo_encaixe:
            horarios_ocupados = agenda_df[
                (agenda_df['tipo_consulta'] == self.tipo_consulta) & (agenda_df['medico'] == medico)
            ]['hora'].tolist() if not agenda_df.empty else []
        else:
            horarios_ocupados = agenda_df[
                (agenda_df['tipo_consulta'] == 'Normal') & (agenda_df['medico'] == medico)
            ]['hora'].tolist() if not agenda_df.empty else []

        total = 0
        for turno in turnos:
            if self.tipo_consulta != "Normal" and not self.modo_encaixe:
                # Modalidades especiais usam horarios proprios
                chave_mod = normalize_text(self.tipo_consulta).replace(' ', '_')
                horarios = self.excel.get_horarios_modalidade(chave_mod, dia_semana, turno)
            else:
                horarios = self._get_horarios_cached(medico_chave, dia_semana, turno)
            total += len([h for h in horarios if h not in horarios_ocupados])

        return total

    def _renderizar_passo_4(self):
        self._limpar_conteudo()
        
        # Processar data selecionada - usa self.data_selecionada se disponivel (navegacao segura)
        if self.data_selecionada:
            data_obj = self.data_selecionada
        elif self.calendario:
            try:
                data_obj = self.calendario.get_date()
                self.data_selecionada = data_obj  # Guarda para navegacao
            except:
                data_obj = date.today()
        else:
            data_obj = date.today()
        
        self.data = data_obj.strftime("%Y-%m-%d")
        self.dia_semana = DIAS_SEMANA[data_obj.weekday()]
        data_exibicao = data_obj.strftime("%d/%m/%Y")
        
        # Determinar medico e chave
        if self.modo_encaixe or self.tipo_consulta == "Normal":
            if not self.medico:
                medicos = self.excel.get_medicos()
                self.medico = medicos[0] if medicos else ""
            self._definir_medico_chave()
        else:
            regra = self.excel.get_regra_tipo_consulta(self.tipo_consulta)
            self.turno = regra.get('turno', 'manha')
            if not self.medico:
                self.medico = self.excel.get_modalidade_medico(self.tipo_consulta) or (self.excel.get_medicos()[0] if self.excel.get_medicos() else "")
            self._definir_medico_chave()
        
        # MODO ENCAIXE: hora manual (nao usa grid de horarios do medico)
        if self.modo_encaixe:
            ctk.CTkLabel(
                self.conteudo_frame,
                text=f"⚡ ENCAIXE - {data_exibicao}",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#ffc107"
            ).pack(pady=(0, 15))
            
            ctk.CTkLabel(
                self.conteudo_frame,
                text="Digite o horario do encaixe manualmente:",
                font=ctk.CTkFont(size=13),
                text_color="#ffffff"
            ).pack(pady=(0, 10))
            
            self.hora_entry = ctk.CTkEntry(
                self.conteudo_frame,
                placeholder_text="HH:MM (ex: 10:30)",
                height=40,
                font=ctk.CTkFont(size=16, weight="bold"),
                fg_color="#333333",
                border_color="#555555",
                text_color="#ffffff",
                justify="center"
            )
            self.hora_entry.pack(fill="x", padx=80, pady=(0, 10))
            self.hora_entry.focus()
            self.hora_entry.bind('<Return>', lambda e: self._confirmar_hora_encaixe())
            
            ctk.CTkLabel(
                self.conteudo_frame,
                text="O encaixe nao utiliza vagas de consultas normais",
                font=ctk.CTkFont(size=11),
                text_color="#888888"
            ).pack(pady=(0, 15))
            
            self.avancar_btn.configure(text="✅ CONFIRMAR HORARIO", command=self._confirmar_hora_encaixe)
            return
        
        ctk.CTkLabel(
            self.conteudo_frame,
            text=f"Horarios disponiveis para {data_exibicao}:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#ffffff"
        ).pack(pady=(0, 10))
        
        self._carregar_horarios_disponiveis()
        
        if not self.horarios_disponiveis:
            ctk.CTkLabel(
                self.conteudo_frame,
                text="Nenhum horario disponivel nesta data.\nTente outro dia.",
                font=ctk.CTkFont(size=13),
                text_color="#dc3545"
            ).pack(pady=20)
            return
        
        # Criar grid de horarios
        grid_frame = ctk.CTkFrame(self.conteudo_frame, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True)
        
        linhas = (len(self.horarios_disponiveis) + 3) // 4
        for i, hora in enumerate(self.horarios_disponiveis):
            row = i // 4
            col = i % 4
            
            btn = ctk.CTkButton(
                grid_frame,
                text=hora,
                command=lambda h=hora: self._selecionar_horario(h),
                fg_color="#333333",
                hover_color="#1f6aa5",
                text_color="#ffffff",
                width=80,
                height=40,
                font=ctk.CTkFont(size=14, weight="bold")
            )
            btn.grid(row=row, column=col, padx=5, pady=5)
    
    def _confirmar_hora_encaixe(self):
        """Confirma a hora digitada manualmente para o encaixe"""
        from utils import validate_time
        hora_texto = self.hora_entry.get().strip()
        
        if not hora_texto:
            self._mostrar_erro("Digite um horario para o encaixe")
            return
        
        if not validate_time(hora_texto):
            self._mostrar_erro("Formato de horario invalido. Use HH:MM")
            return
        
        self.hora = hora_texto
        self.proximo_passo()
    
    def _carregar_horarios_disponiveis(self):
        """Carrega horarios disponiveis verificando a agenda"""
        if self.tipo_consulta != "Normal" and not self.modo_encaixe:
            if not self.medico:
                self.medico = self.excel.get_modalidade_medico(self.tipo_consulta) or ""
            if not self.medico_chave and self.medico:
                medico_chaves = self.excel.get_medico_chaves()
                invert = {v: k for k, v in medico_chaves.items()}
                self.medico_chave = invert.get(self.medico, "")

        if not self.medico_chave:
            self.horarios_disponiveis = []
            return

        turnos_para_tentar = ['manha', 'tarde']
        if self.tipo_consulta != "Normal" and not self.modo_encaixe:
            regras = get_modalidade_rules()
            turno_especifico = regras.get(self.tipo_consulta, {}).get('turno', 'manha')
            turnos_para_tentar = [turno_especifico]

        horarios = []
        if self.tipo_consulta != "Normal" and not self.modo_encaixe:
            # Modalidades especiais usam seus proprios horarios (separados das consultas normais)
            chave_mod = normalize_text(self.tipo_consulta).replace(' ', '_')
            for turno in turnos_para_tentar:
                horarios.extend(self.excel.get_horarios_modalidade(chave_mod, self.dia_semana, turno))
        else:
            for turno in turnos_para_tentar:
                horarios.extend(self.excel.get_horarios(self.medico_chave, self.dia_semana, turno))
        self.turno = turnos_para_tentar[0] if turnos_para_tentar else 'manha'

        if not horarios:
            self.horarios_disponiveis = []
            return

        agenda_df = self._get_agenda_filtered(data=self.data, medico=self.medico)
        if self.tipo_consulta != "Normal" and not self.modo_encaixe:
            horarios_ocupados = agenda_df[
                (agenda_df['tipo_consulta'] == self.tipo_consulta) & (agenda_df['medico'] == self.medico)
            ]['hora'].tolist() if not agenda_df.empty else []
        else:
            horarios_ocupados = agenda_df[
                (agenda_df['tipo_consulta'] == 'Normal') & (agenda_df['medico'] == self.medico)
            ]['hora'].tolist() if not agenda_df.empty else []

        self.horarios_disponiveis = [h for h in horarios if h not in horarios_ocupados]
    
    def _get_agenda_filtered(self, data: str = None, medico: str = None):
        if self._agenda_cache is None:
            return self.excel.get_agenda(data=data, medico=medico, status='ATIVO')

        agenda_df = self._agenda_cache
        if medico:
            agenda_df = agenda_df[agenda_df['medico'] == medico]
        if data:
            agenda_df = agenda_df[agenda_df['data'] == data]
        return agenda_df

    def _get_horarios_cached(self, medico_chave: str, dia_semana: str, turno: str):
        key = (medico_chave, dia_semana, turno)
        if key not in self._horarios_cache:
            self._horarios_cache[key] = self.excel.get_horarios(medico_chave, dia_semana, turno)
        return self._horarios_cache[key]

    def _get_medico_chaves_cached(self):
        if self._medico_chaves_cache is None:
            self._medico_chaves_cache = self.excel.get_medico_chaves()
        return self._medico_chaves_cache

    def _selecionar_horario(self, hora: str):
        self.hora = hora
        if self.modo_encaixe:
            self.proximo_passo()  # Vai direto para paciente
        else:
            self.proximo_passo()
    
    # ============ PASSO 5: Nome do Paciente (para Normal) ============
    
    def _renderizar_passo_5(self):
        self._limpar_conteudo()
        
        info_text = f"{self.tipo_consulta} - {self.medico} - {self.data} {self.hora}"
        ctk.CTkLabel(
            self.conteudo_frame,
            text=info_text,
            font=ctk.CTkFont(size=12),
            text_color="#1f6aa5"
        ).pack(pady=(0, 15))
        
        ctk.CTkLabel(
            self.conteudo_frame,
            text="Nome do paciente:",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#ffffff"
        ).pack(pady=(0, 10))
        
        self.paciente_entry = ctk.CTkEntry(
            self.conteudo_frame,
            placeholder_text="Digite o nome completo",
            height=40,
            font=ctk.CTkFont(size=13),
            fg_color="#333333",
            border_color="#555555",
            text_color="#ffffff"
        )
        if self.paciente_nome:
            self.paciente_entry.insert(0, self.paciente_nome)
        else:
            self.paciente_entry.delete(0, 'end')
        self.paciente_entry.pack(fill="x", pady=(0, 10))
        self.paciente_entry.focus()
        self.paciente_entry.bind('<Return>', lambda e: self._confirmar())
        
        # Observacao (opcional)
        ctk.CTkLabel(
            self.conteudo_frame,
            text="Observacao (opcional):",
            font=ctk.CTkFont(size=12),
            text_color="#aaaaaa"
        ).pack(pady=(10, 5))
        
        self.obs_entry = ctk.CTkEntry(
            self.conteudo_frame,
            placeholder_text="Observacoes...",
            height=30,
            font=ctk.CTkFont(size=12),
            fg_color="#333333",
            border_color="#555555",
            text_color="#ffffff"
        )
        if self.observacao:
            self.obs_entry.insert(0, self.observacao)
        else:
            self.obs_entry.delete(0, 'end')
        self.obs_entry.pack(fill="x")
    
    # ============ PASSO 6: Confirmar (para Normal) ou Confirmacao Final ============
    
    def _renderizar_passo_6(self):
        self._capturar_dados_paciente()
        self._limpar_conteudo()
        
        ctk.CTkLabel(
            self.conteudo_frame,
            text="📋 Confirme os dados:",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#ffffff"
        ).pack(pady=(0, 15))
        
        # Resumo
        resumo_frame = ctk.CTkFrame(self.conteudo_frame, fg_color="#333333", corner_radius=8)
        resumo_frame.pack(fill="x", pady=10)

        campos = [
            ("Tipo", self.tipo_consulta),
            ("Medico", self.medico),
            ("Data", self.data),
            ("Horario", self.hora),
            ("Paciente", self.paciente_nome),
        ]
        
        if self.modo_encaixe:
            campos.insert(0, ("Modalidade", "⚡ ENCAIXE"))
        
        for label, valor in campos:
            linha = ctk.CTkFrame(resumo_frame, fg_color="transparent")
            linha.pack(fill="x", padx=15, pady=3)
            
            ctk.CTkLabel(
                linha,
                text=f"{label}:",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#aaaaaa",
                width=80
            ).pack(side="left")
            
            ctk.CTkLabel(
                linha,
                text=str(valor) if valor else "",
                font=ctk.CTkFont(size=13),
                text_color="#ffffff"
            ).pack(side="left", padx=10)
        
        self.avancar_btn.configure(text="✅ CONFIRMAR")
        self.avancar_btn.configure(command=self._confirmar)
    
    def _capturar_dados_paciente(self):
        """Captura os dados do paciente e observacoes para preservar entre etapas."""
        paciente_valor = self.paciente_nome.strip() if getattr(self, 'paciente_nome', '') else ''
        observacao_valor = self.observacao.strip() if getattr(self, 'observacao', '') else ''

        if hasattr(self, 'paciente_entry'):
            try:
                valor = self.paciente_entry.get().strip()
                if valor:
                    paciente_valor = valor
            except Exception:
                pass

        if hasattr(self, 'obs_entry'):
            try:
                valor = self.obs_entry.get().strip()
                if valor:
                    observacao_valor = valor
            except Exception:
                pass

        self.paciente_nome = paciente_valor
        self.observacao = observacao_valor

    def _confirmar(self):
        """Confirma o agendamento/encaixe"""
        self._capturar_dados_paciente()
        paciente = self.paciente_nome
        
        erro = validate_required(paciente, "Nome do paciente")
        if erro:
            self._mostrar_erro(erro)
            return
        
        try:
            if self.modo_encaixe:
                # Verificar limite de encaixes
                if self.medico_chave:
                    encaixes_usados = self.excel.contar_encaixes_usados(self.medico, self.data)
                    limite = self.excel.get_limite_encaixes(self.medico_chave, self.dia_semana, self.turno)
                    
                    if encaixes_usados >= limite:
                        self._mostrar_erro(f"Limite de encaixes atingido ({limite}/{limite}) para {self.medico} neste turno!")
                        return
                
                obs = self.observacao
                novo_id = self.excel.agendar_consulta(
                    paciente=paciente,
                    medico=self.medico or "",
                    tipo_consulta="Normal",
                    data=self.data,
                    hora=self.hora or "",
                    encaixe=True,
                    observacao=obs,
                    usuario=self.usuario
                )
            else:
                obs = self.observacao
                novo_id = self.excel.agendar_consulta(
                    paciente=paciente,
                    medico=self.medico or "",
                    tipo_consulta=self.tipo_consulta,
                    data=self.data,
                    hora=self.hora or "",
                    encaixe=False,
                    observacao=obs,
                    usuario=self.usuario
                )
            
            self._mostrar_sucesso(f"Agendamento #{novo_id} realizado com sucesso!")
            
            # Desabilitar botoes apos confirmacao
            self.avancar_btn.configure(state="disabled", text="✅ CONFIRMADO")
            self.voltar_btn.configure(state="disabled")
            
            # Exibir botoes de comprovante
            self._exibir_botoes_comprovante(novo_id)
            
        except Exception as e:
            self._mostrar_erro(f"Erro ao agendar: {str(e)}")

    def _exibir_botoes_comprovante(self, novo_id: int):
        """Exibe botões de impressão de comprovante após confirmação bem-sucedida."""
        # Dados da consulta para impressão
        consulta_dados = {
            "id": novo_id,
            "paciente": self.paciente_nome,
            "medico": self.medico or "",
            "tipo_consulta": self.tipo_consulta or "Normal",
            "data": self.data or "",
            "hora": self.hora or "",
            "encaixe": "TRUE" if self.modo_encaixe else "FALSE",
            "observacao": self.observacao or "",
        }

        # Frame de comprovantes
        comp_frame = ctk.CTkFrame(self.frame, fg_color="#333333", corner_radius=8)
        comp_frame.pack(fill="x", pady=(8, 0))

        ctk.CTkLabel(
            comp_frame,
            text="🖨️  Imprimir comprovante:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#ffffff"
        ).pack(side="left", padx=(12, 10), pady=8)

        ctk.CTkButton(
            comp_frame,
            text="🖨️ Térmico (80mm)",
            command=lambda d=consulta_dados: self._imprimir_termico(d),
            fg_color="#555555",
            hover_color="#666666",
            text_color="#ffffff",
            width=140,
            height=30,
            font=ctk.CTkFont(size=11)
        ).pack(side="left", padx=(0, 6), pady=8)

        ctk.CTkButton(
            comp_frame,
            text="🖨️ A4 (3 por folha)",
            command=lambda d=consulta_dados: self._imprimir_a4(d),
            fg_color="#555555",
            hover_color="#666666",
            text_color="#ffffff",
            width=140,
            height=30,
            font=ctk.CTkFont(size=11)
        ).pack(side="left", padx=(0, 6), pady=8)

        ctk.CTkButton(
            comp_frame,
            text="🖨️ A4 Estilo Térmico",
            command=lambda d=consulta_dados: self._imprimir_a4_termico(d),
            fg_color="#555555",
            hover_color="#666666",
            text_color="#ffffff",
            width=155,
            height=30,
            font=ctk.CTkFont(size=11)
        ).pack(side="left", padx=(0, 6), pady=8)

        ctk.CTkButton(
            comp_frame,
            text="✖ Fechar",
            command=self.fechar,
            fg_color="#444444",
            hover_color="#dc3545",
            text_color="#aaaaaa",
            width=80,
            height=30,
            font=ctk.CTkFont(size=11)
        ).pack(side="right", padx=(0, 12), pady=8)

    def _imprimir_termico(self, consulta_dados: dict):
        """Imprime comprovante no formato térmico (80mm)."""
        try:
            from impressao import comprovante_termico
            comprovante_termico(consulta_dados, abrir=True)
        except Exception as e:
            self._mostrar_erro(f"Erro ao imprimir: {e}")

    def _imprimir_a4(self, consulta_dados: dict):
        """Imprime comprovante A4 (3 por folha)."""
        try:
            from impressao import comprovante_a4
            comprovante_a4(consulta_dados, abrir=True)
        except Exception as e:
            self._mostrar_erro(f"Erro ao imprimir: {e}")

    def _imprimir_a4_termico(self, consulta_dados: dict):
        """Imprime comprovante A4 estilo térmico (2 tiras de 80mm lado a lado, recortável)."""
        try:
            from impressao import comprovante_a4_termico
            comprovante_a4_termico(consulta_dados, abrir=True)
        except Exception as e:
            self._mostrar_erro(f"Erro ao imprimir: {e}")


    def _mostrar_erro(self, mensagem: str):
        self.msg_label.configure(text=mensagem, text_color="#dc3545")

    def _mostrar_sucesso(self, mensagem: str):
        self.msg_label.configure(text=mensagem, text_color="#28a745")

    # ============ NAVEGACAO ============

    def _limpar_conteudo(self):
        """Limpa todos os widgets do frame de conteudo dinamico"""
        for widget in self.conteudo_frame.winfo_children():
            widget.destroy()
        # Resetar botao avancar para padrao (pode ter sido alterado no passo 6)
        self.avancar_btn.configure(text="AVANÇAR →", command=self.proximo_passo)

    def proximo_passo(self):
        """Avanca para o proximo passo do formulario"""
        if self.modo_encaixe:
            sequencia = [
                self._renderizar_passo_1,
                self._renderizar_passo_2,
                self._renderizar_passo_3,
                self._renderizar_passo_4,
                self._renderizar_passo_5,
            ]
        else:
            sequencia = [
                self._renderizar_passo_1,
                self._renderizar_passo_2,
                self._renderizar_passo_3,
                self._renderizar_passo_4,
                self._renderizar_passo_5,
                self._renderizar_passo_6,
            ]

        if self.passo < len(sequencia):
            self.passo += 1
            sequencia[self.passo - 1]()
            self._atualizar_indicador()
            self.voltar_btn.configure(state="normal" if self.passo > 1 else "disabled")

    def passo_anterior(self):
        """Volta para o passo anterior do formulario"""
        if self.modo_encaixe:
            sequencia = [
                self._renderizar_passo_1,
                self._renderizar_passo_2,
                self._renderizar_passo_3,
                self._renderizar_passo_4,
                self._renderizar_passo_5,
            ]
        else:
            sequencia = [
                self._renderizar_passo_1,
                self._renderizar_passo_2,
                self._renderizar_passo_3,
                self._renderizar_passo_4,
                self._renderizar_passo_5,
                self._renderizar_passo_6,
            ]

        if self.passo > 1:
            self.passo -= 1
            sequencia[self.passo - 1]()
            self._atualizar_indicador()
            self.voltar_btn.configure(state="normal" if self.passo > 1 else "disabled")
            self.avancar_btn.configure(text="AVANÇAR →", command=self.proximo_passo)

    def fechar(self):
        try:
            self.janela.destroy()
        except:
            pass

