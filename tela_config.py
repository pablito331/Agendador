"""
tela_config.py - Tela de Configuracoes
Edita medicos, horarios, modalidades e limites de encaixes na aba Config
"""
import customtkinter as ctk
import pandas as pd
import os
from typing import Optional
from config_manager import ExcelManager, COLUNAS_CONFIG
from utils import validate_required, normalize_text

COR_FUNDO = "#2b2b2b"
COR_TEXTO = "#ffffff"
COR_DESTAQUE = "#1f6aa5"
COR_SUCESSO = "#28a745"
COR_ERRO = "#dc3545"


class TelaConfig:
    """Tela de configuracoes do sistema"""
    
    def __init__(self, excel: ExcelManager, usuario: str = "Sistema", app_ref=None):
        self.excel = excel
        self.usuario = usuario
        self.app_ref = app_ref
        self.janela = None
        self.df_config = None
        self._abrir()
    
    def _abrir(self):
        """Abre a janela de configuracoes"""
        parent = getattr(self.app_ref, '_root', None) if self.app_ref else None
        self.janela = ctk.CTkToplevel(master=parent)
        self.janela.title("CONFIGURACOES")
        self.janela.geometry("700x550")
        self.janela.resizable(True, True)
        self.janela.minsize(600, 400)
        self.janela.protocol("WM_DELETE_WINDOW", self._fechar)
        
        self.frame = ctk.CTkFrame(self.janela, fg_color=COR_FUNDO)
        self.frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        titulo_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        titulo_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            titulo_frame,
            text="CONFIGURACOES",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COR_TEXTO
        ).pack(side="left")
        
        ctk.CTkButton(
            titulo_frame,  
            text="SALVAR TUDO",
            command=self._salvar,
            fg_color=COR_SUCESSO,
            hover_color="#218838",
            text_color=COR_TEXTO,
            height=30,
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="right")

        self.df_config = self.excel.get_config()

        planilha_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        planilha_frame.pack(fill="x", pady=(0, 15))

        self.planilha_label = ctk.CTkLabel(
            planilha_frame,
            text=f"Planilha atual: {os.path.basename(self.excel.caminho)}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COR_TEXTO,
            anchor="w",
            wraplength=440,
            justify="left"
        )
        self.planilha_label.pack(side="left", fill="x", expand=True)

        if self.app_ref and hasattr(self.app_ref, '_selecionar_planilha'):
            ctk.CTkButton(
                planilha_frame,
                text="Mudar planilha",
                command=self._selecionar_planilha,
                fg_color=COR_DESTAQUE,
                hover_color="#1a5a8c",
                text_color=COR_TEXTO,
                height=30,
                font=ctk.CTkFont(size=12, weight="bold")
            ).pack(side="right")
        
        self.abas = ctk.CTkTabview(self.frame, fg_color=COR_FUNDO)
        self.abas.pack(fill="both", expand=True)
        
        self.aba_medicos = self.abas.add("Medicos")
        self._criar_aba_medicos()
        
        self.aba_horarios = self.abas.add("Horarios")
        self._criar_aba_horarios()
        
        self.aba_horarios_especiais = self.abas.add("Horarios Especiais")
        self._criar_aba_horarios_especiais()
        
        self.aba_modalidades = self.abas.add("Modalidades")
        self._criar_aba_modalidades()
        
        self.janela.update_idletasks()
        largura = self.janela.winfo_width()
        altura = self.janela.winfo_height()
        x = (self.janela.winfo_screenwidth() // 2) - (largura // 2)
        y = (self.janela.winfo_screenheight() // 2) - (altura // 2)
        self.janela.geometry(f"+{x}+{y}")
        
        self._carregar_medicos()
        self._carregar_horarios()
        self._carregar_horarios_especiais()
        self._carregar_modalidades()
        self._carregar_tipos_especiais()
    
    def _criar_aba_medicos(self):
        frame = ctk.CTkScrollableFrame(self.aba_medicos, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=5, pady=5)
        ctk.CTkLabel(frame, text="Medicos Cadastrados", font=ctk.CTkFont(size=14, weight="bold"), text_color=COR_TEXTO).pack(anchor="w", pady=(0, 10))
        self.medicos_container = ctk.CTkFrame(frame, fg_color="transparent")
        self.medicos_container.pack(fill="x")
        ctk.CTkButton(frame, text="Adicionar Medico", command=self._adicionar_medico, fg_color=COR_DESTAQUE, hover_color="#1a5a8c", text_color=COR_TEXTO, height=35, font=ctk.CTkFont(size=12)).pack(pady=(15, 0))
    
    def _criar_aba_horarios(self):
        frame = ctk.CTkScrollableFrame(self.aba_horarios, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=5, pady=5)
        ctk.CTkLabel(frame, text="Horarios por Medico / Dia / Turno", font=ctk.CTkFont(size=14, weight="bold"), text_color=COR_TEXTO).pack(anchor="w", pady=(0, 10))
        ctk.CTkLabel(frame, text="Formato: HH:MM,HH:MM,HH:MM (separados por virgula)", font=ctk.CTkFont(size=11), text_color="#888888").pack(anchor="w", pady=(0, 10))
        self.horarios_container = ctk.CTkFrame(frame, fg_color="transparent")
        self.horarios_container.pack(fill="x")
    
    def _criar_aba_modalidades(self):
        frame = ctk.CTkScrollableFrame(self.aba_modalidades, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=5, pady=5)
        ctk.CTkLabel(frame, text="Modalidades de Consulta", font=ctk.CTkFont(size=14, weight="bold"), text_color=COR_TEXTO).pack(anchor="w", pady=(0, 10))
        ctk.CTkLabel(frame, text="Selecione o médico padrão para cada modalidade especializada.", font=ctk.CTkFont(size=11), text_color="#888888").pack(anchor="w", pady=(0, 10))
        self.modalidades_container = ctk.CTkFrame(frame, fg_color="transparent")
        self.modalidades_container.pack(fill="x")

        ctk.CTkLabel(frame, text="Tipos especiais", font=ctk.CTkFont(size=14, weight="bold"), text_color=COR_TEXTO).pack(anchor="w", pady=(20, 8))
        ctk.CTkLabel(frame, text="Adicione consultas especiais para definir dia, turno e médico responsável.", font=ctk.CTkFont(size=11), text_color="#888888").pack(anchor="w", pady=(0, 8))
        ctk.CTkButton(frame, text="Adicionar tipo especial", command=self._adicionar_tipo_consulta_especial, fg_color=COR_DESTAQUE, hover_color="#1a5a8c", text_color=COR_TEXTO, height=32, font=ctk.CTkFont(size=12)).pack(anchor="w", pady=(0, 10))
        self.tipos_especiais_container = ctk.CTkFrame(frame, fg_color="transparent")
        self.tipos_especiais_container.pack(fill="x")
    
    def _criar_aba_horarios_especiais(self):
        frame = ctk.CTkScrollableFrame(self.aba_horarios_especiais, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=5, pady=5)
        ctk.CTkLabel(frame, text="Horarios das Modalidades Especiais", font=ctk.CTkFont(size=14, weight="bold"), text_color=COR_TEXTO).pack(anchor="w", pady=(0, 10))
        ctk.CTkLabel(frame, text="Formato: HH:MM,HH:MM,HH:MM (separados por virgula)", font=ctk.CTkFont(size=11), text_color="#888888").pack(anchor="w", pady=(0, 10))
        ctk.CTkLabel(frame, text="Cada modalidade tem seu proprio conjunto de horarios, separados das consultas normais.", font=ctk.CTkFont(size=11), text_color="#ffc107").pack(anchor="w", pady=(0, 10))
        self.horarios_especiais_container = ctk.CTkFrame(frame, fg_color="transparent")
        self.horarios_especiais_container.pack(fill="x")

    def _get_medicos_dict(self):
        df_medicos = self.df_config[self.df_config['tipo'] == 'medico']
        return dict(zip(df_medicos['chave'], df_medicos['valor']))

    def _get_medicos(self):
        return sorted(self._get_medicos_dict().values())

    def _get_config_valor(self, tipo: str, chave: str) -> str:
        df = self.df_config[(self.df_config['tipo'] == tipo) & (self.df_config['chave'] == chave)]
        if df.empty:
            return ''
        return df.iloc[0]['valor']

    def _carregar_medicos(self):
        for widget in self.medicos_container.winfo_children():
            widget.destroy()
        medicos = self._get_medicos_dict()
        self._medico_entries = []
        if not medicos:
            ctk.CTkLabel(self.medicos_container, text="Nenhum medico cadastrado", font=ctk.CTkFont(size=12), text_color="#888888").pack(pady=10)
            return
        for chave, nome in medicos.items():
            linha = ctk.CTkFrame(self.medicos_container, fg_color="#333333", corner_radius=5)
            linha.pack(fill="x", pady=3)
            entry = ctk.CTkEntry(linha, textvariable=ctk.StringVar(value=nome), font=ctk.CTkFont(size=13), fg_color="#444444", border_color="#555555", text_color=COR_TEXTO, height=32)
            entry.pack(side="left", fill="x", expand=True, padx=(10, 5), pady=5)
            entry._config_chave = chave
            ctk.CTkButton(linha, text="X", command=lambda k=chave: self._remover_medico(k), fg_color=COR_ERRO, hover_color="#c82333", width=35, height=32).pack(side="right")
            self._medico_entries.append(entry)
        self._carregar_modalidades()
    
    def _carregar_horarios(self):
        for widget in self.horarios_container.winfo_children():
            widget.destroy()
        medicos = self._get_medicos_dict()
        DIAS = ['seg', 'ter', 'qua', 'qui', 'sex']
        TURNOS = ['manha', 'tarde']
        DIAS_NOME = {'seg': 'Segunda', 'ter': 'Terca', 'qua': 'Quarta', 'qui': 'Quinta', 'sex': 'Sexta'}
        TURNOS_NOME = {'manha': 'Manha', 'tarde': 'Tarde'}
        self._horario_entries = {}
        for chave_medico, nome_medico in medicos.items():
            for dia in DIAS:
                for turno in TURNOS:
                    chave_horario = f"{chave_medico}_{dia}_{turno}"
                    horarios_str = self._get_config_valor('horario', chave_horario)
                    if not horarios_str:
                        horarios = self.excel.get_horarios(chave_medico, dia, turno)
                        horarios_str = ','.join(horarios) if horarios else ''
                    linha = ctk.CTkFrame(self.horarios_container, fg_color="#333333", corner_radius=3)
                    linha.pack(fill="x", pady=2)
                    ctk.CTkLabel(linha, text=f"{nome_medico} - {DIAS_NOME[dia]} ({TURNOS_NOME[turno]}):", font=ctk.CTkFont(size=11), text_color="#aaaaaa", width=200, anchor="w").pack(side="left", padx=5)
                    entry = ctk.CTkEntry(linha, textvariable=ctk.StringVar(value=horarios_str), font=ctk.CTkFont(size=11), fg_color="#444444", border_color="#555555", text_color=COR_TEXTO, height=28)
                    entry.pack(side="left", fill="x", expand=True, padx=5, pady=3)
                    entry._config_chave = chave_horario
                    self._horario_entries[chave_horario] = entry
    
    def _carregar_horarios_especiais(self):
        """Carrega os campos de horarios para cada modalidade especial"""
        for widget in self.horarios_especiais_container.winfo_children():
            widget.destroy()
        
        self._horarios_especiais_entries = {}
        
        # Config: chave_modalidade -> (nome_exibicao, dia_semana, turno)
        modalidades_config = [
            ("domiciliar", "Domiciliar (Qui - Manhã)", "qui", "manha"),
            ("gercon", "GERCON (Qua - Manhã)", "qua", "manha"),
            ("crianca", "Criança (Qua - Tarde)", "qua", "tarde"),
            ("gestante", "Gestante (Ter - Manhã)", "ter", "manha"),
        ]
        
        for chave_mod, nome_exib, dia, turno in modalidades_config:
            chave_horario = f"{chave_mod}_{dia}_{turno}"
            # Busca horario existente ou gera padrao
            horarios_str = self._get_config_valor('horario_modalidade', chave_horario)
            if not horarios_str:
                horarios = self.excel.get_horarios_modalidade(chave_mod, dia, turno)
                horarios_str = ','.join(horarios) if horarios else '08:00,08:30,09:00,09:30,10:00,10:30,11:00,11:30'
            
            linha = ctk.CTkFrame(self.horarios_especiais_container, fg_color="#333333", corner_radius=3)
            linha.pack(fill="x", pady=2)
            ctk.CTkLabel(
                linha, 
                text=f"{nome_exib}:", 
                font=ctk.CTkFont(size=11), 
                text_color="#aaaaaa", 
                width=220, 
                anchor="w"
            ).pack(side="left", padx=5)
            entry = ctk.CTkEntry(
                linha, 
                textvariable=ctk.StringVar(value=horarios_str), 
                font=ctk.CTkFont(size=11), 
                fg_color="#444444", 
                border_color="#555555", 
                text_color=COR_TEXTO, 
                height=28
            )
            entry.pack(side="left", fill="x", expand=True, padx=5, pady=3)
            entry._config_chave = chave_horario
            entry._config_tipo = 'horario_modalidade'
            self._horarios_especiais_entries[chave_horario] = entry

    def _carregar_modalidades(self):
        for widget in self.modalidades_container.winfo_children():
            widget.destroy()
        if not hasattr(self, '_modalidade_vars'):
            self._modalidade_vars = {}
        medicos = self._get_medicos()
        for chave, nome in [("domiciliar", "Domiciliar"), ("gercon", "GERCON"), ("crianca", "Criança"), ("gestante", "Gestante")]:
            valor = self._get_config_valor('modalidade_medico', chave)
            linha = ctk.CTkFrame(self.modalidades_container, fg_color="#333333", corner_radius=3)
            linha.pack(fill="x", pady=3)
            ctk.CTkLabel(linha, text=f"{nome}:", font=ctk.CTkFont(size=12, weight="bold"), text_color=COR_TEXTO, width=100).pack(side="left", padx=10)
            var = ctk.StringVar(value=valor or (medicos[0] if medicos else ""))
            if medicos:
                menu = ctk.CTkOptionMenu(linha, variable=var, values=medicos, fg_color="#444444", button_color=COR_DESTAQUE, button_hover_color="#1a5a8c", text_color=COR_TEXTO)
                menu.pack(side="left", fill="x", expand=True, padx=5, pady=5)
            else:
                entry = ctk.CTkEntry(linha, textvariable=var, font=ctk.CTkFont(size=12), fg_color="#444444", border_color="#555555", text_color=COR_TEXTO, height=32)
                entry.pack(side="left", fill="x", expand=True, padx=5, pady=5)
            self._modalidade_vars[chave] = var

    def _carregar_tipos_especiais(self):
        for widget in self.tipos_especiais_container.winfo_children():
            widget.destroy()

        tipos = self.excel.get_tipos_consultas_especiais()
        if not tipos:
            ctk.CTkLabel(self.tipos_especiais_container, text="Nenhum tipo especial cadastrado ainda.", font=ctk.CTkFont(size=12), text_color="#888888").pack(anchor="w", pady=10)
            return

        for regra in tipos:
            nome = regra.get('nome', '')
            chave = normalize_text(nome).replace(' ', '_')
            linha = ctk.CTkFrame(self.tipos_especiais_container, fg_color="#333333", corner_radius=3)
            linha.pack(fill="x", pady=3)
            texto = f"{nome} • {regra.get('dia_semana','')} • {regra.get('turno','manha')} • {regra.get('medico','')}"
            if regra.get('descricao'):
                texto += f" • {regra.get('descricao')}"
            ctk.CTkLabel(linha, text=texto, font=ctk.CTkFont(size=11), text_color=COR_TEXTO, wraplength=480, justify="left", anchor="w").pack(side="left", fill="x", expand=True, padx=10, pady=8)
            ctk.CTkButton(linha, text="Remover", command=lambda k=chave: self._remover_tipo_consulta_especial(k), fg_color=COR_ERRO, hover_color="#c82333", text_color=COR_TEXTO, width=80, height=28).pack(side="right", padx=8, pady=8)

    def _adicionar_tipo_consulta_especial(self):
        janela = ctk.CTkToplevel(self.janela)
        janela.title("Adicionar tipo especial")
        janela.geometry("480x340")
        janela.transient(self.janela)
        janela.grab_set()
        frame = ctk.CTkFrame(janela, fg_color=COR_FUNDO)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text="Nome do tipo especial:", font=ctk.CTkFont(size=13), text_color=COR_TEXTO).pack(anchor="w")
        nome_entry = ctk.CTkEntry(frame, height=35, font=ctk.CTkFont(size=13), fg_color="#333333", border_color="#555555", text_color=COR_TEXTO)
        nome_entry.pack(fill="x", pady=(5, 10))

        medicos = self._get_medicos()
        ctk.CTkLabel(frame, text="Médico responsável:", font=ctk.CTkFont(size=13), text_color=COR_TEXTO).pack(anchor="w")
        medico_var = ctk.StringVar(value=medicos[0] if medicos else "")
        medico_menu = ctk.CTkOptionMenu(frame, variable=medico_var, values=medicos, fg_color="#444444", button_color=COR_DESTAQUE, button_hover_color="#1a5a8c", text_color=COR_TEXTO)
        medico_menu.pack(fill="x", pady=(5, 10))

        ctk.CTkLabel(frame, text="Dia da semana:", font=ctk.CTkFont(size=13), text_color=COR_TEXTO).pack(anchor="w")
        dia_var = ctk.StringVar(value="seg")
        dia_menu = ctk.CTkOptionMenu(frame, variable=dia_var, values=["seg", "ter", "qua", "qui", "sex", "sab", "dom"], fg_color="#444444", button_color=COR_DESTAQUE, button_hover_color="#1a5a8c", text_color=COR_TEXTO)
        dia_menu.pack(fill="x", pady=(5, 10))

        ctk.CTkLabel(frame, text="Turno:", font=ctk.CTkFont(size=13), text_color=COR_TEXTO).pack(anchor="w")
        turno_var = ctk.StringVar(value="manha")
        turno_menu = ctk.CTkOptionMenu(frame, variable=turno_var, values=["manha", "tarde"], fg_color="#444444", button_color=COR_DESTAQUE, button_hover_color="#1a5a8c", text_color=COR_TEXTO)
        turno_menu.pack(fill="x", pady=(5, 10))

        ctk.CTkLabel(frame, text="Descrição (opcional):", font=ctk.CTkFont(size=13), text_color=COR_TEXTO).pack(anchor="w")
        desc_entry = ctk.CTkEntry(frame, height=35, font=ctk.CTkFont(size=13), fg_color="#333333", border_color="#555555", text_color=COR_TEXTO)
        desc_entry.pack(fill="x", pady=(5, 10))

        msg_label = ctk.CTkLabel(frame, text="", font=ctk.CTkFont(size=12), text_color=COR_ERRO)
        msg_label.pack()

        botoes = ctk.CTkFrame(frame, fg_color="transparent")
        botoes.pack(fill="x", pady=(10, 0))
        ctk.CTkButton(botoes, text="Cancelar", command=janela.destroy, fg_color="#555555", text_color=COR_TEXTO, width=100).pack(side="left")

        def salvar():
            nome = nome_entry.get().strip()
            if not nome:
                msg_label.configure(text="Nome é obrigatório", text_color=COR_ERRO)
                return
            if not medico_var.get().strip():
                msg_label.configure(text="Selecione um médico", text_color=COR_ERRO)
                return
            self.excel.salvar_tipo_consulta_especial(
                nome=nome,
                dia_semana=dia_var.get(),
                turno=turno_var.get(),
                medico=medico_var.get(),
                descricao=desc_entry.get().strip(),
            )
            self.df_config = self.excel.get_config()
            self._carregar_tipos_especiais()
            janela.destroy()

        ctk.CTkButton(botoes, text="Salvar", command=salvar, fg_color=COR_SUCESSO, text_color=COR_TEXTO, width=100).pack(side="right")

    def _remover_tipo_consulta_especial(self, chave: str):
        from tkinter import messagebox
        if not messagebox.askyesno("Confirmar", f"Remover tipo especial '{chave}'?"):
            return
        self.df_config = self.df_config[~((self.df_config['tipo'] == 'tipo_consulta_especial') & (self.df_config['chave'] == chave))]
        self.df_config = self.df_config.drop_duplicates(subset=['tipo', 'chave'], keep='last')
        self.excel.salvar_config(self.df_config)
        self.df_config = self.excel.get_config()
        self._carregar_tipos_especiais()
    
    def _adicionar_medico(self):
        janela = ctk.CTkToplevel(self.janela)
        janela.title("Adicionar Medico")
        janela.geometry("400x200")
        janela.transient(self.janela)
        janela.grab_set()
        frame = ctk.CTkFrame(janela, fg_color=COR_FUNDO)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        ctk.CTkLabel(frame, text="Nome do medico:", font=ctk.CTkFont(size=13), text_color=COR_TEXTO).pack(anchor="w")
        nome_entry = ctk.CTkEntry(frame, placeholder_text="Ex: Dr. Carlos", height=35, font=ctk.CTkFont(size=13), fg_color="#333333", border_color="#555555", text_color=COR_TEXTO)
        nome_entry.pack(fill="x", pady=(5, 10))
        nome_entry.focus()
        msg_label = ctk.CTkLabel(frame, text="", font=ctk.CTkFont(size=12), text_color=COR_ERRO)
        msg_label.pack()
        botoes = ctk.CTkFrame(frame, fg_color="transparent")
        botoes.pack(fill="x", pady=(10, 0))
        ctk.CTkButton(botoes, text="CANCELAR", command=janela.destroy, fg_color="#555555", text_color=COR_TEXTO, width=100).pack(side="left")
        
        def salvar():
            nome = nome_entry.get().strip()
            erro = validate_required(nome, "Nome")
            if erro:
                msg_label.configure(text=erro)
                return
            from utils import normalize_text
            chave = "dr_" + normalize_text(nome).replace(' ', '_').replace('.', '')
            nova_linha = pd.DataFrame([{'tipo': 'medico', 'chave': chave, 'valor': nome}])
            self.df_config = pd.concat([self.df_config, nova_linha], ignore_index=True)

            def criar_horarios_base(inicio: str) -> str:
                horas = []
                hora, minuto = map(int, inicio.split(':'))
                for _ in range(8):
                    horas.append(f"{hora:02d}:{minuto:02d}")
                    minuto += 20
                    if minuto >= 60:
                        minuto -= 60
                        hora += 1
                return ','.join(horas)

            for dia in ['seg', 'ter', 'qua', 'qui', 'sex']:
                for turno, inicio in [('manha', '08:00'), ('tarde', '13:00')]:
                    h = criar_horarios_base(inicio)
                    nova_linha = pd.DataFrame([{'tipo': 'horario', 'chave': f"{chave}_{dia}_{turno}", 'valor': h}])
                    self.df_config = pd.concat([self.df_config, nova_linha], ignore_index=True)
            msg_label.configure(text="Medico adicionado!", text_color=COR_SUCESSO)
            janela.after(1000, janela.destroy)
            self._carregar_medicos()
            self._carregar_horarios()
            self._carregar_modalidades()
        
        ctk.CTkButton(botoes, text="SALVAR", command=salvar, fg_color=COR_SUCESSO, text_color=COR_TEXTO, width=100).pack(side="right")
    
    def _remover_medico(self, chave: str):
        from tkinter import messagebox
        if not messagebox.askyesno("Confirmar", f"Remover medico '{chave}' e todos seus horarios?"):
            return
        self.df_config = self.df_config[~self.df_config['chave'].str.startswith(chave)]
        self._carregar_medicos()
        self._carregar_horarios()
        self._carregar_modalidades()
        self._carregar_modalidades()
    
    def _selecionar_planilha(self):
        if self.app_ref and hasattr(self.app_ref, '_selecionar_planilha'):
            self.app_ref._selecionar_planilha()
            self.excel = self.app_ref.excel
            self.planilha_label.configure(text=f"Planilha: {os.path.basename(self.excel.caminho)}")
            self.df_config = self.excel.get_config()
            self._carregar_medicos()
            self._carregar_horarios()
            self._carregar_modalidades()

    def _salvar(self):
        try:
            if hasattr(self, '_medico_entries'):
                for entry in self._medico_entries:
                    chave = getattr(entry, '_config_chave', None)
                    if chave:
                        idx = self.df_config[self.df_config['chave'] == chave].index
                        if not idx.empty:
                            self.df_config.loc[idx[0], 'valor'] = entry.get()
            if hasattr(self, '_horario_entries'):
                for chave, entry in self._horario_entries.items():
                    idx = self.df_config[self.df_config['chave'] == chave].index
                    if not idx.empty:
                        self.df_config.loc[idx[0], 'valor'] = entry.get()
            if hasattr(self, '_modalidade_vars'):
                for chave, var in self._modalidade_vars.items():
                    idx = self.df_config[(self.df_config['tipo'] == 'modalidade_medico') & (self.df_config['chave'] == chave)].index
                    if not idx.empty:
                        self.df_config.loc[idx[0], 'valor'] = var.get()
                    elif var.get().strip():
                        nova_linha = pd.DataFrame([{'tipo': 'modalidade_medico', 'chave': chave, 'valor': var.get().strip()}])
                        self.df_config = pd.concat([self.df_config, nova_linha], ignore_index=True)
            if hasattr(self, '_horarios_especiais_entries'):
                for chave, entry in self._horarios_especiais_entries.items():
                    tipo = getattr(entry, '_config_tipo', 'horario_modalidade')
                    idx = self.df_config[(self.df_config['tipo'] == tipo) & (self.df_config['chave'] == chave)].index
                    valor = entry.get()
                    if not idx.empty:
                        self.df_config.loc[idx[0], 'valor'] = valor
                    elif valor.strip():
                        nova_linha = pd.DataFrame([{'tipo': tipo, 'chave': chave, 'valor': valor}])
                        self.df_config = pd.concat([self.df_config, nova_linha], ignore_index=True)
            self.df_config = self.df_config.drop_duplicates(subset=['tipo', 'chave'], keep='last')
            self.excel.salvar_config(self.df_config)
            self.excel.registrar_log('EDITAR_CONFIG', 'Configuracoes atualizadas', self.usuario)
            from tkinter import messagebox
            messagebox.showinfo("Sucesso", "Configuracoes salvas com sucesso!")
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Erro", f"Erro ao salvar: {str(e)}")
    
    def _fechar(self):
        try:
            self.janela.destroy()
        except:
            pass
