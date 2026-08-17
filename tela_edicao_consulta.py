"""
tela_edicao_consulta.py - Modal de edição de consulta agendada
Permite alterar: paciente, médico, tipo, data, horário, observação.
Os horários disponíveis são carregados dinamicamente ao mudar médico ou data.
"""
import calendar
import customtkinter as ctk
from datetime import datetime, date
from typing import Callable, Optional
from config_manager import ExcelManager, MODALIDADES_DISPONIVEIS

COR_FUNDO    = "#2b2b2b"
COR_TEXTO    = "#ffffff"
COR_DESTAQUE = "#1f6aa5"
COR_SUCESSO  = "#28a745"
COR_ERRO     = "#dc3545"
COR_AVISO    = "#ffc107"
COR_CAMPO    = "#333333"
COR_BORDA    = "#555555"

DIAS_SEMANA = ['seg', 'ter', 'qua', 'qui', 'sex', 'sab', 'dom']


class TelaEdicaoConsulta:
    """Modal de edição de uma consulta existente."""

    def __init__(
        self,
        excel: ExcelManager,
        consulta: dict,
        usuario: str = "Sistema",
        callback_salvo: Optional[Callable] = None,
        parent=None,
    ):
        """
        Parâmetros
        ----------
        excel : ExcelManager
        consulta : dict
            Dicionário com os dados atuais da consulta.
            Chaves esperadas: id, paciente, medico, tipo_consulta,
                              data, hora, encaixe, observacao, status
        usuario : str
        callback_salvo : callable | None
            Chamado após salvar com sucesso (para atualizar a tela pai).
        parent : CTkToplevel | None
        """
        self.excel          = excel
        self.consulta       = consulta
        self.usuario        = usuario
        self.callback_salvo = callback_salvo
        self.parent         = parent

        self._id = int(consulta.get('id', 0))

        # Estado de edição
        self._medico_atual    = str(consulta.get('medico', ''))
        self._data_atual      = str(consulta.get('data', ''))      # YYYY-MM-DD
        self._hora_atual      = str(consulta.get('hora', ''))
        self._tipo_atual      = str(consulta.get('tipo_consulta', 'Normal'))
        self._encaixe_atual   = str(consulta.get('encaixe', 'FALSE')).upper() == 'TRUE'

        self._mes_vis         = self._parse_data(self._data_atual) or date.today()
        self._mes_vis         = self._mes_vis.replace(day=1)
        self._data_sel        = self._parse_data(self._data_atual) or date.today()

        self._agenda_cache    = None
        self._horarios_cache  = {}

        self._criar_janela()

    # ─── Utilitários ────────────────────────────────────────────────────────

    @staticmethod
    def _parse_data(data_str: str) -> Optional[date]:
        try:
            return datetime.strptime(data_str[:10], "%Y-%m-%d").date()
        except Exception:
            return None

    @staticmethod
    def _formatar_data_br(data_str: str) -> str:
        d = TelaEdicaoConsulta._parse_data(data_str)
        return d.strftime("%d/%m/%Y") if d else data_str

    def _medico_chave(self, nome_medico: str) -> str:
        chaves = self.excel.get_medico_chaves()
        invertido = {v: k for k, v in chaves.items()}
        return invertido.get(nome_medico, "")

    def _horarios_disponiveis(self, medico: str, data_obj: date, tipo: str, hora_original: str) -> list:
        """Retorna horários livres para o médico/data/tipo, sempre incluindo o horário original."""
        data_str   = data_obj.strftime("%Y-%m-%d")
        dia_semana = DIAS_SEMANA[data_obj.weekday()]
        mk         = self._medico_chave(medico)

        if not mk:
            return [hora_original] if hora_original else []

        if self._agenda_cache is None:
            self._agenda_cache = self.excel.get_agenda(status='ATIVO')

        # Horários configurados
        horarios_conf = []
        for turno in ['manha', 'tarde']:
            key = (mk, dia_semana, turno)
            if key not in self._horarios_cache:
                self._horarios_cache[key] = self.excel.get_horarios(mk, dia_semana, turno)
            horarios_conf.extend(self._horarios_cache[key])

        # Ocupados (excluindo a própria consulta em edição)
        df = self._agenda_cache
        df_dia = df[(df['medico'] == medico) & (df['data'] == data_str)]
        # Remove a própria linha pelo id para não bloquear o horário original
        df_dia = df_dia[df_dia['id'] != str(self._id)]
        ocupados = df_dia['hora'].tolist() if not df_dia.empty else []

        livres = [h for h in horarios_conf if h not in ocupados]

        # Garante que o horário original sempre aparece
        if hora_original and hora_original not in livres:
            livres = [hora_original] + livres

        return livres

    # ─── Interface ──────────────────────────────────────────────────────────

    def _criar_janela(self):
        self.janela = ctk.CTkToplevel(self.parent)
        self.janela.title(f"✏️ Editar Consulta #{self._id}")
        self.janela.geometry("620x700")
        self.janela.resizable(False, False)
        if self.parent:
            self.janela.transient(self.parent)
        self.janela.grab_set()
        self.janela.protocol("WM_DELETE_WINDOW", self._fechar)
        self.janela.bind("<Escape>", lambda e: self._fechar())

        # Fundo
        frame = ctk.CTkScrollableFrame(self.janela, fg_color=COR_FUNDO)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        self._frame = frame

        # Título
        ctk.CTkLabel(
            frame,
            text=f"✏️  Editar Consulta  #{self._id}",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COR_DESTAQUE,
        ).pack(anchor="w", pady=(0, 4))

        ctk.CTkLabel(
            frame,
            text=f"Consulta original: {self._formatar_data_br(self._data_atual)}  {self._hora_atual}  |  {self._medico_atual}",
            font=ctk.CTkFont(size=11),
            text_color="#888888",
        ).pack(anchor="w", pady=(0, 14))

        # ── Paciente ────────────────────────────────────────────────────────
        self._secao("👤 Paciente", frame)
        self._paciente_entry = self._entry(frame, str(self.consulta.get('paciente', '')))

        # ── Tipo de consulta ────────────────────────────────────────────────
        self._secao("📋 Tipo de Consulta", frame)
        self._tipo_var = ctk.StringVar(value=self._tipo_atual)
        ctk.CTkOptionMenu(
            frame,
            variable=self._tipo_var,
            values=MODALIDADES_DISPONIVEIS,
            fg_color=COR_CAMPO,
            button_color=COR_DESTAQUE,
            button_hover_color="#1a5a8c",
            text_color=COR_TEXTO,
            command=self._ao_mudar_tipo,
        ).pack(fill="x", pady=(0, 10))

        # ── Médico ──────────────────────────────────────────────────────────
        self._secao("🩺 Médico", frame)
        medicos = self.excel.get_medicos()
        self._medico_var = ctk.StringVar(value=self._medico_atual)
        ctk.CTkOptionMenu(
            frame,
            variable=self._medico_var,
            values=medicos if medicos else [self._medico_atual],
            fg_color=COR_CAMPO,
            button_color=COR_DESTAQUE,
            button_hover_color="#1a5a8c",
            text_color=COR_TEXTO,
            command=self._ao_mudar_medico,
        ).pack(fill="x", pady=(0, 10))

        # ── Calendário de data ──────────────────────────────────────────────
        self._secao("📅 Data", frame)
        self._cal_frame = ctk.CTkFrame(frame, fg_color="transparent")
        self._cal_frame.pack(fill="x", pady=(0, 10))
        self._renderizar_calendario()

        # ── Horário ─────────────────────────────────────────────────────────
        self._secao("🕐 Horário", frame)
        self._hora_frame = ctk.CTkFrame(frame, fg_color="transparent")
        self._hora_frame.pack(fill="x", pady=(0, 10))
        self._renderizar_horarios()

        # ── Observação ──────────────────────────────────────────────────────
        self._secao("📝 Observação (opcional)", frame)
        self._obs_entry = self._entry(frame, str(self.consulta.get('observacao', '') or ''))

        # ── Mensagem de status ──────────────────────────────────────────────
        self._msg_label = ctk.CTkLabel(
            frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=COR_SUCESSO,
        )
        self._msg_label.pack(pady=(6, 0))

        # ── Botões ──────────────────────────────────────────────────────────
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(14, 0))

        ctk.CTkButton(
            btn_frame,
            text="✖ Cancelar",
            command=self._fechar,
            fg_color="#444444",
            hover_color="#555555",
            text_color="#aaaaaa",
            width=110,
            height=38,
            font=ctk.CTkFont(size=12),
        ).pack(side="left")

        ctk.CTkButton(
            btn_frame,
            text="✅ Salvar Alterações",
            command=self._salvar,
            fg_color=COR_SUCESSO,
            hover_color="#218838",
            text_color=COR_TEXTO,
            width=180,
            height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
        ).pack(side="right")

        # Centralizar
        self.janela.update_idletasks()
        w, h = self.janela.winfo_width(), self.janela.winfo_height()
        x = (self.janela.winfo_screenwidth()  // 2) - (w // 2)
        y = (self.janela.winfo_screenheight() // 2) - (h // 2)
        self.janela.geometry(f"+{x}+{y}")

    # ─── Helpers de UI ──────────────────────────────────────────────────────

    def _secao(self, titulo: str, parent):
        ctk.CTkLabel(
            parent,
            text=titulo,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#aaaaaa",
        ).pack(anchor="w", pady=(8, 2))

    def _entry(self, parent, valor: str) -> ctk.CTkEntry:
        e = ctk.CTkEntry(
            parent,
            height=36,
            font=ctk.CTkFont(size=13),
            fg_color=COR_CAMPO,
            border_color=COR_BORDA,
            text_color=COR_TEXTO,
        )
        e.insert(0, valor)
        e.pack(fill="x", pady=(0, 4))
        return e

    # ─── Calendário ─────────────────────────────────────────────────────────

    def _renderizar_calendario(self):
        for w in self._cal_frame.winfo_children():
            w.destroy()

        # Navegação de mês
        nav = ctk.CTkFrame(self._cal_frame, fg_color="transparent")
        nav.pack(fill="x", pady=(0, 4))

        ctk.CTkButton(nav, text="◀", width=34, height=28,
                      fg_color="#444444", hover_color="#555555",
                      command=self._mes_anterior).pack(side="left")

        ctk.CTkLabel(nav,
                     text=self._mes_vis.strftime("%B / %Y"),
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=COR_TEXTO).pack(side="left", padx=8)

        ctk.CTkButton(nav, text="▶", width=34, height=28,
                      fg_color="#444444", hover_color="#555555",
                      command=self._mes_posterior).pack(side="left")

        # Cabeçalho dias da semana
        dias_frame = ctk.CTkFrame(self._cal_frame, fg_color="transparent")
        dias_frame.pack(fill="x")
        for col, nome in enumerate(['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']):
            ctk.CTkLabel(dias_frame, text=nome,
                         font=ctk.CTkFont(size=9, weight="bold"),
                         text_color="#888888", width=54).grid(row=0, column=col, padx=2, pady=2)
            dias_frame.grid_columnconfigure(col, weight=1)

        # Grade de dias
        self._agenda_cache  = None   # invalida cache ao trocar mês
        self._horarios_cache = {}

        cal = calendar.Calendar(firstweekday=0)
        semanas = cal.monthdayscalendar(self._mes_vis.year, self._mes_vis.month)

        for row_i, semana in enumerate(semanas):
            for col_i, dia in enumerate(semana):
                if dia == 0:
                    ctk.CTkLabel(dias_frame, text="", fg_color="transparent",
                                 width=54, height=40).grid(row=row_i + 1, column=col_i, padx=2, pady=2)
                    continue

                data_dt   = date(self._mes_vis.year, self._mes_vis.month, dia)
                selecionada = data_dt == self._data_sel
                passada     = data_dt < date.today()

                cor_fg   = COR_DESTAQUE if selecionada else ("#555555" if passada else "#3a3a3a")
                cor_hov  = "#1a5a8c" if not passada else "#555555"
                estado   = "normal" if not passada else "disabled"

                ctk.CTkButton(
                    dias_frame,
                    text=str(dia),
                    width=54, height=40,
                    fg_color=cor_fg,
                    hover_color=cor_hov,
                    text_color=COR_TEXTO,
                    font=ctk.CTkFont(size=11, weight="bold" if selecionada else "normal"),
                    state=estado,
                    command=lambda d=data_dt: self._selecionar_data(d),
                ).grid(row=row_i + 1, column=col_i, padx=2, pady=2, sticky="nsew")

    def _mes_anterior(self):
        m = self._mes_vis
        if m.month == 1:
            self._mes_vis = m.replace(year=m.year - 1, month=12)
        else:
            self._mes_vis = m.replace(month=m.month - 1)
        self._renderizar_calendario()

    def _mes_posterior(self):
        m = self._mes_vis
        if m.month == 12:
            self._mes_vis = m.replace(year=m.year + 1, month=1)
        else:
            self._mes_vis = m.replace(month=m.month + 1)
        self._renderizar_calendario()

    def _selecionar_data(self, data_obj: date):
        self._data_sel = data_obj
        self._agenda_cache   = None
        self._horarios_cache = {}
        self._renderizar_calendario()
        self._renderizar_horarios()

    # ─── Horários ────────────────────────────────────────────────────────────

    def _renderizar_horarios(self):
        for w in self._hora_frame.winfo_children():
            w.destroy()

        medico    = self._medico_var.get() if hasattr(self, '_medico_var') else self._medico_atual
        hora_orig = self._hora_atual
        livres    = self._horarios_disponiveis(medico, self._data_sel, self._tipo_var.get() if hasattr(self, '_tipo_var') else self._tipo_atual, hora_orig)

        if not livres:
            ctk.CTkLabel(
                self._hora_frame,
                text="⚠️ Nenhum horário disponível nesta data para este médico.",
                font=ctk.CTkFont(size=11),
                text_color=COR_AVISO,
            ).pack(anchor="w")
            self._hora_selecionada = ctk.StringVar(value=hora_orig)
            return

        self._hora_selecionada = ctk.StringVar(value=self._hora_atual if self._hora_atual in livres else livres[0])

        grid = ctk.CTkFrame(self._hora_frame, fg_color="transparent")
        grid.pack(fill="x")

        for i, hora in enumerate(livres):
            selecionado = hora == self._hora_selecionada.get()
            btn = ctk.CTkButton(
                grid,
                text=hora,
                width=72, height=36,
                fg_color=COR_DESTAQUE if selecionado else "#3a3a3a",
                hover_color="#1a5a8c",
                text_color=COR_TEXTO,
                font=ctk.CTkFont(size=12, weight="bold" if selecionado else "normal"),
                command=lambda h=hora: self._selecionar_hora(h),
            )
            btn.grid(row=i // 5, column=i % 5, padx=4, pady=4)

    def _selecionar_hora(self, hora: str):
        self._hora_selecionada.set(hora)
        self._renderizar_horarios()

    # ─── Callbacks de mudança ───────────────────────────────────────────────

    def _ao_mudar_medico(self, _=None):
        self._agenda_cache   = None
        self._horarios_cache = {}
        self._renderizar_horarios()

    def _ao_mudar_tipo(self, _=None):
        self._renderizar_horarios()

    # ─── Salvar ──────────────────────────────────────────────────────────────

    def _salvar(self):
        paciente = self._paciente_entry.get().strip()
        if not paciente:
            self._msg("❌ Nome do paciente é obrigatório.", erro=True)
            return

        hora = getattr(self, '_hora_selecionada', None)
        hora_val = hora.get() if hora else ""
        if not hora_val:
            self._msg("❌ Selecione um horário.", erro=True)
            return

        campos = {
            'paciente':      paciente,
            'medico':        self._medico_var.get(),
            'tipo_consulta': self._tipo_var.get(),
            'data':          self._data_sel.strftime("%Y-%m-%d"),
            'hora':          hora_val,
            'observacao':    self._obs_entry.get().strip(),
        }

        try:
            self.excel.editar_consulta(self._id, campos, self.usuario)
            self._msg(f"✅ Consulta #{self._id} atualizada com sucesso!")
            if self.callback_salvo:
                self.callback_salvo()
            self.janela.after(1200, self._fechar)
        except Exception as e:
            self._msg(f"❌ Erro ao salvar: {e}", erro=True)

    def _msg(self, texto: str, erro: bool = False):
        cor = COR_ERRO if erro else COR_SUCESSO
        self._msg_label.configure(text=texto, text_color=cor)

    # ─── Fechar ───────────────────────────────────────────────────────────────

    def _fechar(self):
        try:
            self.janela.grab_release()
            self.janela.destroy()
        except Exception:
            pass
