"""
tela_agenda_medico.py - Agenda completa do médico
Permite selecionar um médico e visualizar todas as suas consultas,
com filtros por status e opção de cancelar agendamentos.
"""
import customtkinter as ctk
from typing import Optional
from config_manager import ExcelManager
from utils import date_br

COR_FUNDO = "#2b2b2b"
COR_TEXTO = "#ffffff"
COR_DESTAQUE = "#1f6aa5"
COR_SUCESSO = "#28a745"
COR_ERRO = "#dc3545"
COR_AVISO = "#ffc107"


class TelaAgendaMedico:
    """Janela da agenda completa de um médico"""
    
    def __init__(self, excel: ExcelManager, usuario: str = "Sistema"):
        self.excel = excel
        self.usuario = usuario
        self.janela = None
        self.filtro_atual = "ATIVO"  # "ATIVO", "CANCELADO", "TODAS"
        
        self._criar_janela()
        self._carregar_medicos()
    
    def _criar_janela(self):
        """Cria a janela da agenda do médico"""
        self.janela = ctk.CTkToplevel()
        self.janela.title("📋 AGENDA DO MÉDICO")
        self.janela.geometry("850x600")
        self.janela.resizable(True, True)
        self.janela.minsize(700, 500)
        self.janela.protocol("WM_DELETE_WINDOW", self._fechar)
        
        # Frame principal
        self.frame = ctk.CTkFrame(self.janela, fg_color=COR_FUNDO)
        self.frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # === TÍTULO ===
        titulo_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        titulo_frame.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            titulo_frame,
            text="📋 AGENDA DO MÉDICO",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COR_TEXTO
        ).pack(side="left")
        
        # === SELEÇÃO DE MÉDICO ===
        medico_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        medico_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            medico_frame,
            text="Selecione o médico:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=COR_TEXTO
        ).pack(side="left", padx=(0, 10))
        
        self.medico_var = ctk.StringVar(value="")
        self.medico_menu = ctk.CTkOptionMenu(
            medico_frame,
            variable=self.medico_var,
            values=[],
            command=self._ao_selecionar_medico,
            fg_color="#444444",
            button_color=COR_DESTAQUE,
            button_hover_color="#1a5a8c",
            text_color=COR_TEXTO,
            width=250
        )
        self.medico_menu.pack(side="left", padx=(0, 15))
        
        # Botões direita
        btn_frame_dir = ctk.CTkFrame(medico_frame, fg_color="transparent")
        btn_frame_dir.pack(side="right")

        ctk.CTkButton(
            btn_frame_dir,
            text="🖨️ IMPRIMIR",
            command=self._imprimir_agenda,
            fg_color="#555555",
            hover_color="#666666",
            text_color=COR_TEXTO,
            width=100,
            height=30,
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
            height=30,
            font=ctk.CTkFont(size=11)
        ).pack(side="right", padx=(5, 0))

        ctk.CTkButton(
            btn_frame_dir,
            text="🔄 ATUALIZAR",
            command=self._carregar_agenda,
            fg_color=COR_DESTAQUE,
            hover_color="#1a5a8c",
            text_color=COR_TEXTO,
            width=100,
            height=30,
            font=ctk.CTkFont(size=11)
        ).pack(side="right")
        
        # === FILTROS DE STATUS ===
        filtro_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        filtro_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            filtro_frame,
            text="Filtrar:",
            font=ctk.CTkFont(size=12),
            text_color="#aaaaaa"
        ).pack(side="left", padx=(0, 10))
        
        self.filtro_btns = {}
        for filtro, texto in [("ATIVO", "✅ Ativas"), ("CANCELADO", "❌ Canceladas"), ("TODAS", "📋 Todas")]:
            btn = ctk.CTkButton(
                filtro_frame,
                text=texto,
                command=lambda f=filtro: self._aplicar_filtro(f),
                fg_color=COR_SUCESSO if filtro == "ATIVO" else "#444444",
                hover_color=COR_DESTAQUE,
                text_color=COR_TEXTO,
                width=110,
                height=28,
                font=ctk.CTkFont(size=11)
            )
            btn.pack(side="left", padx=(0, 5))
            self.filtro_btns[filtro] = btn
        
        # Separador
        ctk.CTkFrame(self.frame, height=2, fg_color="#444444").pack(fill="x", pady=(5, 10))
        
        # === RESULTADOS ===
        self.resultados_container = ctk.CTkScrollableFrame(
            self.frame, fg_color="transparent"
        )
        self.resultados_container.pack(fill="both", expand=True)
        
        # Indicador de carregamento
        self.loading_label = ctk.CTkLabel(
            self.resultados_container,
            text="Selecione um médico para ver a agenda",
            font=ctk.CTkFont(size=14),
            text_color="#888888"
        )
        self.loading_label.pack(pady=30)
        
        # === RODAPÉ ===
        ctk.CTkFrame(self.frame, height=1, fg_color="#444444").pack(fill="x", pady=(10, 5))
        
        self.status_label = ctk.CTkLabel(
            self.frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="#aaaaaa"
        )
        self.status_label.pack()
        
        # Centralizar
        self.janela.update_idletasks()
        largura = self.janela.winfo_width()
        altura = self.janela.winfo_height()
        x = (self.janela.winfo_screenwidth() // 2) - (largura // 2)
        y = (self.janela.winfo_screenheight() // 2) - (altura // 2)
        self.janela.geometry(f"{largura}x{altura}+{x}+{y}")
    
    def _carregar_medicos(self):
        """Carrega lista de médicos no dropdown"""
        medicos = self.excel.get_medicos()
        if medicos:
            self.medico_menu.configure(values=medicos)
            self.medico_var.set(medicos[0])
            self._carregar_agenda()
    
    def _ao_selecionar_medico(self, escolha):
        """Callback ao selecionar um médico"""
        self._carregar_agenda()

    def _imprimir_agenda(self):
        """Gera PDF da agenda do médico e abre para impressão"""
        medico = self.medico_var.get()
        if not medico:
            import tkinter.messagebox as mb
            mb.showwarning("Aviso", "Selecione um médico antes de imprimir.",
                           parent=self.janela)
            return
        try:
            from impressao import imprimir_agenda_medico
            if self.filtro_atual == "TODAS":
                agenda = self.excel.get_agenda(medico=medico, status=None)
            else:
                agenda = self.excel.get_agenda(medico=medico, status=self.filtro_atual)
            imprimir_agenda_medico(agenda, medico, filtro=self.filtro_atual, abrir=True)
        except Exception as e:
            import tkinter.messagebox as mb
            mb.showerror("Erro ao imprimir", f"Não foi possível gerar o PDF:\n{e}",
                         parent=self.janela)
    def _imprimir_visao(self):
        """Imprime uma visão geral da agenda do médico em PDF."""
        try:
            from impressao import imprimir_lista
            medico = self.medico_var.get()
            if not medico:
                import tkinter.messagebox as mb
                mb.showwarning("Aviso", "Selecione um médico antes de imprimir.", parent=self.janela)
                return
            agenda = self.excel.get_agenda(medico=medico, status=None) if self.filtro_atual == "TODAS" else self.excel.get_agenda(medico=medico, status=self.filtro_atual)
            itens = []
            for _, row in agenda.iterrows():
                itens.append({
                    'Data': row.get('data', ''),
                    'Hora': row.get('hora', ''),
                    'Paciente': row.get('paciente', ''),
                    'Tipo': row.get('tipo_consulta', ''),
                    'Observação': row.get('observacao', ''),
                })
            imprimir_lista(itens, titulo=f"Visão da Agenda - {medico}", abrir=True)
        except Exception as e:
            import tkinter.messagebox as mb
            mb.showerror("Erro ao imprimir", f"Não foi possível gerar o PDF:\n{e}", parent=self.janela)

    def _aplicar_filtro(self, filtro: str):
        """Aplica filtro de status"""
        self.filtro_atual = filtro
        
        # Atualizar cores dos botões de filtro
        for f, btn in self.filtro_btns.items():
            if f == filtro:
                btn.configure(fg_color=COR_DESTAQUE)
            else:
                btn.configure(fg_color="#444444")
        
        self._carregar_agenda()
    
    def _carregar_agenda(self):
        """Carrega a agenda do médico selecionado"""
        medico = self.medico_var.get()
        if not medico:
            self.loading_label.configure(text="Selecione um médico para ver a agenda")
            self.status_label.configure(text="")
            return
        
        # Limpar resultados anteriores
        for widget in self.resultados_container.winfo_children():
            widget.destroy()
        
        # Buscar dados
        try:
            if self.filtro_atual == "TODAS":
                agenda = self.excel.get_agenda(medico=medico, status=None)
            else:
                agenda = self.excel.get_agenda(medico=medico, status=self.filtro_atual)
        except Exception as e:
            self.loading_label = ctk.CTkLabel(
                self.resultados_container,
                text=f"Erro ao carregar dados: {str(e)}",
                font=ctk.CTkFont(size=14),
                text_color=COR_ERRO
            )
            self.loading_label.pack(pady=30)
            return
        
        # Atualizar status
        total = len(agenda) if not agenda.empty else 0
        self.status_label.configure(text=f"Total: {total} consulta(s) | Médico: {medico} | Filtro: {self.filtro_atual}")
        
        if agenda.empty:
            ctk.CTkLabel(
                self.resultados_container,
                text="📭 Nenhuma consulta encontrada com este filtro",
                font=ctk.CTkFont(size=14),
                text_color="#888888"
            ).pack(pady=30)
            return
        
        # Ordenar por data e hora (decrescente)
        try:
            agenda = agenda.sort_values(['data', 'hora'], ascending=[False, False])
        except:
            pass
        
        # === CABEÇALHO DA TABELA ===
        cabecalho = ctk.CTkFrame(self.resultados_container, fg_color="transparent")
        cabecalho.pack(fill="x", pady=(0, 5))
        
        colunas = [
            ("ID", 40),
            ("Data", 90),
            ("Hora", 55),
            ("Paciente", 180),
            ("Tipo", 120),
            ("Status", 80),
            ("Compareceu", 80),
            ("Ações", 100),
        ]
        
        for texto, largura in colunas:
            ctk.CTkLabel(
                cabecalho,
                text=texto,
                font=ctk.CTkFont(size=10, weight="bold"),
                text_color="#888888",
                width=largura
            ).pack(side="left")
        
        # === LISTA DE CONSULTAS ===
        for _, consulta in agenda.iterrows():
            self._criar_linha_consulta(consulta)
    
    def _criar_linha_consulta(self, consulta):
        """Cria uma linha de consulta na tabela"""
        id_agenda = int(consulta.get('id', 0))
        paciente = consulta.get('paciente', '')
        medico = consulta.get('medico', '')
        tipo = consulta.get('tipo_consulta', '')
        data = consulta.get('data', '')
        hora = consulta.get('hora', '')
        status = consulta.get('status', '')
        compareceu = consulta.get('compareceu', 'FALSE')
        observacao = consulta.get('observacao', '')
        
        # Formatar data
        if data and len(data) >= 10:
            data_formatada = data[8:10] + '/' + data[5:7] + '/' + data[:4]
        else:
            data_formatada = data
        
        # Determinar cores
        if status == 'ATIVO':
            cor_status = COR_SUCESSO
        elif status == 'CANCELADO':
            cor_status = COR_ERRO
        else:
            cor_status = COR_AVISO
        
        # Linha
        linha = ctk.CTkFrame(self.resultados_container, fg_color="#333333", corner_radius=3)
        linha.pack(fill="x", pady=2)
        
        # Colunas
        ctk.CTkLabel(
            linha,
            text=str(id_agenda),
            font=ctk.CTkFont(size=10),
            text_color="#888888",
            width=40
        ).pack(side="left")
        
        ctk.CTkLabel(
            linha,
            text=data_formatada,
            font=ctk.CTkFont(size=12),
            text_color=COR_TEXTO,
            width=90
        ).pack(side="left")
        
        ctk.CTkLabel(
            linha,
            text=hora,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COR_TEXTO,
            width=55
        ).pack(side="left")
        
        ctk.CTkLabel(
            linha,
            text=paciente,
            font=ctk.CTkFont(size=12),
            text_color=COR_TEXTO,
            width=180,
            anchor="w"
        ).pack(side="left")
        
        ctk.CTkLabel(
            linha,
            text=tipo,
            font=ctk.CTkFont(size=11),
            text_color=COR_TEXTO,
            width=95,
            anchor="w"
        ).pack(side="left")
        
        ctk.CTkLabel(
            linha,
            text=status,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=cor_status,
            width=80
        ).pack(side="left")
        
        compareceu_text = "✅ Sim" if compareceu == "TRUE" else "☐ Não"
        cor_comp = COR_SUCESSO if compareceu == "TRUE" else "#888888"
        ctk.CTkLabel(
            linha,
            text=compareceu_text,
            font=ctk.CTkFont(size=11),
            text_color=cor_comp,
            width=80
        ).pack(side="left")
        
        # Botão de ação
        if status == "ATIVO":
            acoes_frame = ctk.CTkFrame(linha, fg_color="transparent")
            acoes_frame.pack(side="right", padx=(0, 2))

            btn_editar = ctk.CTkButton(
                acoes_frame,
                text="✏️ EDITAR",
                command=lambda idx=id_agenda, row=consulta: self._abrir_edicao(idx, row),
                fg_color=COR_DESTAQUE,
                hover_color="#1a5a8c",
                text_color=COR_TEXTO,
                width=82,
                height=26,
                font=ctk.CTkFont(size=10, weight="bold")
            )
            btn_editar.pack(side="right", padx=(0, 4))

            btn_acao = ctk.CTkButton(
                acoes_frame,
                text="❌ CANCELAR",
                command=lambda idx=id_agenda: self._confirmar_cancelamento(idx),
                fg_color=COR_ERRO,
                hover_color="#c82333",
                text_color=COR_TEXTO,
                width=85,
                height=26,
                font=ctk.CTkFont(size=10, weight="bold")
            )
            btn_acao.pack(side="right")
        else:
            ctk.CTkLabel(
                linha,
                text="—",
                font=ctk.CTkFont(size=11),
                text_color="#666666",
                width=90
            ).pack(side="right", padx=(0, 2))

        observacao = str(consulta.get('observacao', '') or '').strip()
        if observacao:
            ctk.CTkLabel(
                linha,
                text=f"📝 {observacao}",
                font=ctk.CTkFont(size=10),
                text_color=COR_AVISO,
                wraplength=420,
                justify="left",
                anchor="w"
            ).pack(fill="x", padx=(40, 15), pady=(2, 6))

    def _abrir_edicao(self, id_agenda: int, row):
        """Abre o modal de edição da consulta."""
        from tela_edicao_consulta import TelaEdicaoConsulta

        # Monta dicionário com dados atuais
        consulta_dict = {
            'id':            id_agenda,
            'paciente':      str(row.get('paciente', '')),
            'medico':        str(row.get('medico', '')),
            'tipo_consulta': str(row.get('tipo_consulta', 'Normal')),
            'data':          str(row.get('data', '')),
            'hora':          str(row.get('hora', '')),
            'encaixe':       str(row.get('encaixe', 'FALSE')),
            'observacao':    str(row.get('observacao', '') or ''),
            'status':        str(row.get('status', '')),
        }

        TelaEdicaoConsulta(
            excel=self.excel,
            consulta=consulta_dict,
            usuario=self.usuario,
            callback_salvo=self._carregar_agenda,
            parent=self.janela,
        )

    
    def _confirmar_cancelamento(self, id_agenda: int):
        """Abre diálogo de confirmação para cancelar consulta"""
        janela = ctk.CTkToplevel(self.janela)
        janela.title("Confirmar Cancelamento")
        janela.geometry("380x200")
        janela.resizable(False, False)
        janela.transient(self.janela)
        janela.grab_set()
        
        frame = ctk.CTkFrame(janela, fg_color=COR_FUNDO)
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        ctk.CTkLabel(
            frame,
            text="❌ Cancelar Consulta",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=COR_ERRO
        ).pack(pady=(0, 10))
        
        ctk.CTkLabel(
            frame,
            text=f"Tem certeza que deseja cancelar a consulta #{id_agenda}?",
            font=ctk.CTkFont(size=13),
            text_color=COR_TEXTO
        ).pack(pady=(0, 5))
        
        ctk.CTkLabel(
            frame,
            text="Esta ação não pode ser desfeita.",
            font=ctk.CTkFont(size=11),
            text_color="#888888"
        ).pack(pady=(0, 15))
        
        msg_label = ctk.CTkLabel(
            frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=COR_SUCESSO
        )
        msg_label.pack()
        
        botoes_frame = ctk.CTkFrame(frame, fg_color="transparent")
        botoes_frame.pack(fill="x")
        
        ctk.CTkButton(
            botoes_frame,
            text="VOLTAR",
            command=janela.destroy,
            fg_color="#555555",
            hover_color="#666666",
            text_color=COR_TEXTO,
            width=100
        ).pack(side="left")
        
        def cancelar():
            try:
                self.excel.cancelar_consulta(id_agenda, self.usuario)
                msg_label.configure(
                    text=f"✅ Consulta #{id_agenda} cancelada com sucesso!",
                    text_color=COR_SUCESSO
                )
                janela.after(1200, janela.destroy)
                # Recarregar a agenda
                self._carregar_agenda()
            except Exception as e:
                msg_label.configure(
                    text=f"❌ Erro ao cancelar: {str(e)}",
                    text_color=COR_ERRO
                )
        
        ctk.CTkButton(
            botoes_frame,
            text="✅ SIM, CANCELAR",
            command=cancelar,
            fg_color=COR_ERRO,
            hover_color="#c82333",
            text_color=COR_TEXTO,
            width=140
        ).pack(side="right")
    
    def _fechar(self):
        """Fecha a janela"""
        try:
            self.janela.destroy()
        except:
            pass

