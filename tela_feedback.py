"""
tela_feedback.py - Tela de Feedback e Suporte
Permite usuários reportar erros ou solicitar melhorias via e-mail (Brevo API)
"""
import customtkinter as ctk
import threading
import urllib.request
import json
import webbrowser
from typing import Optional
from datetime import datetime

COR_FUNDO = "#2b2b2b"
COR_TEXTO = "#ffffff"
COR_DESTAQUE = "#1f6aa5"
COR_SUCESSO = "#28a745"
COR_ERRO = "#dc3545"
COR_AVISO = "#ffc107"

# Configuração do envio de e-mail via Brevo
# A API Key fica em _secrets.py (ignorado pelo .gitignore — nunca vai pro GitHub)
try:
    from _secrets import BREVO_API_KEY
except ImportError:
    BREVO_API_KEY = ""  # Fallback: usará o cliente de e-mail local

EMAIL_DESTINO = "thepablitoshouse@gmail.com"
EMAIL_REMETENTE = "suporte@agendadoresf.app"
NOME_REMETENTE = "AgendadorESF Feedback"

TIPOS = [
    ("🐛", "Reportar um Bug", "#dc3545"),
    ("✨", "Solicitar Melhoria", "#1f6aa5"),
    ("❓", "Dúvida / Suporte", "#ffc107"),
    ("💡", "Ideia Nova", "#28a745"),
]


class TelaFeedback:
    """Tela de feedback e suporte para usuários"""

    def __init__(self, usuario: str = "Sistema", versao_app: str = ""):
        self.usuario = usuario
        self.versao_app = versao_app
        self.janela = None
        self._abrir()

    def _abrir(self):
        if self.janela and self._esta_ativa():
            self.janela.lift()
            self.janela.focus_force()
            return

        self.janela = ctk.CTkToplevel()
        self.janela.title("💬 Feedback e Suporte")
        self.janela.geometry("520x640")
        self.janela.resizable(False, False)
        self.janela.protocol("WM_DELETE_WINDOW", self._fechar)

        self.janela.update_idletasks()
        w = self.janela.winfo_width()
        h = self.janela.winfo_height()
        x = (self.janela.winfo_screenwidth() // 2) - (w // 2)
        y = (self.janela.winfo_screenheight() // 2) - (h // 2)
        self.janela.geometry(f"+{x}+{y}")

        self._construir_interface()

    def _construir_interface(self):
        outer = ctk.CTkScrollableFrame(self.janela, fg_color=COR_FUNDO)
        outer.pack(fill="both", expand=True, padx=20, pady=20)

        # === Cabeçalho ===
        header = ctk.CTkFrame(outer, fg_color="#333333", corner_radius=10)
        header.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            header,
            text="💬 Feedback & Suporte",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COR_TEXTO,
        ).pack(pady=(12, 2))

        ctk.CTkLabel(
            header,
            text="Reporte um erro, envie uma sugestão ou tire uma dúvida.\nResponderemos pelo e-mail informado.",
            font=ctk.CTkFont(size=11),
            text_color="#aaaaaa",
            justify="center",
        ).pack(pady=(0, 12))

        # === Tipo de feedback ===
        ctk.CTkLabel(
            outer, text="Tipo de feedback:", font=ctk.CTkFont(size=12, weight="bold"), text_color=COR_TEXTO
        ).pack(anchor="w", pady=(0, 5))

        self.tipo_var = ctk.StringVar(value=TIPOS[0][1])
        tipo_frame = ctk.CTkFrame(outer, fg_color="transparent")
        tipo_frame.pack(fill="x", pady=(0, 12))
        tipo_frame.columnconfigure(0, weight=1)
        tipo_frame.columnconfigure(1, weight=1)

        for i, (icone, texto, cor) in enumerate(TIPOS):
            ctk.CTkRadioButton(
                tipo_frame,
                text=f"{icone}  {texto}",
                variable=self.tipo_var,
                value=texto,
                font=ctk.CTkFont(size=12),
                text_color=COR_TEXTO,
                fg_color=cor,
            ).grid(row=i // 2, column=i % 2, sticky="w", padx=5, pady=4)

        # === Nome (opcional) ===
        ctk.CTkLabel(
            outer, text="Seu nome (opcional):", font=ctk.CTkFont(size=12, weight="bold"), text_color=COR_TEXTO
        ).pack(anchor="w")

        self.nome_entry = ctk.CTkEntry(
            outer,
            placeholder_text="Ex: Maria Enfermeira",
            height=35,
            font=ctk.CTkFont(size=12),
            fg_color="#333333",
            border_color="#555555",
            text_color=COR_TEXTO,
        )
        self.nome_entry.pack(fill="x", pady=(5, 10))

        # === E-mail de resposta (opcional) ===
        ctk.CTkLabel(
            outer, text="Seu e-mail para resposta (opcional):", font=ctk.CTkFont(size=12, weight="bold"), text_color=COR_TEXTO
        ).pack(anchor="w")

        self.email_entry = ctk.CTkEntry(
            outer,
            placeholder_text="Ex: maria@saude.gov.br",
            height=35,
            font=ctk.CTkFont(size=12),
            fg_color="#333333",
            border_color="#555555",
            text_color=COR_TEXTO,
        )
        self.email_entry.pack(fill="x", pady=(5, 10))

        # === Título ===
        ctk.CTkLabel(
            outer, text="Título / Resumo:*", font=ctk.CTkFont(size=12, weight="bold"), text_color=COR_TEXTO
        ).pack(anchor="w")

        self.titulo_entry = ctk.CTkEntry(
            outer,
            placeholder_text="Ex: Tela de receitas abre vazia",
            height=35,
            font=ctk.CTkFont(size=12),
            fg_color="#333333",
            border_color="#555555",
            text_color=COR_TEXTO,
        )
        self.titulo_entry.pack(fill="x", pady=(5, 10))

        # === Descrição ===
        ctk.CTkLabel(
            outer, text="Descrição detalhada:*", font=ctk.CTkFont(size=12, weight="bold"), text_color=COR_TEXTO
        ).pack(anchor="w")

        self.descricao_text = ctk.CTkTextbox(
            outer,
            height=120,
            font=ctk.CTkFont(size=12),
            fg_color="#333333",
            border_color="#555555",
            text_color=COR_TEXTO,
            wrap="word",
        )
        self.descricao_text.pack(fill="x", pady=(5, 5))

        ctk.CTkLabel(
            outer,
            text="Para bugs: descreva o que aconteceu e como reproduzir.",
            font=ctk.CTkFont(size=10),
            text_color="#888888",
        ).pack(anchor="w", pady=(0, 12))

        # === Mensagem de status ===
        self.msg_label = ctk.CTkLabel(
            outer, text="", font=ctk.CTkFont(size=12), text_color=COR_AVISO
        )
        self.msg_label.pack(pady=(0, 8))

        # === Botões ===
        btn_frame = ctk.CTkFrame(outer, fg_color="transparent")
        btn_frame.pack(fill="x")

        ctk.CTkButton(
            btn_frame,
            text="CANCELAR",
            command=self._fechar,
            fg_color="#555555",
            hover_color="#666666",
            text_color=COR_TEXTO,
            width=110,
            height=40,
        ).pack(side="left")

        self.btn_enviar = ctk.CTkButton(
            btn_frame,
            text="📤 Enviar Feedback",
            command=self._enviar,
            fg_color=COR_DESTAQUE,
            hover_color="#1a5a8c",
            text_color=COR_TEXTO,
            width=160,
            height=40,
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.btn_enviar.pack(side="right")

        ctk.CTkLabel(
            outer,
            text="* campos obrigatórios",
            font=ctk.CTkFont(size=10),
            text_color="#666666",
        ).pack(pady=(8, 0))

    def _enviar(self):
        titulo = self.titulo_entry.get().strip()
        descricao = self.descricao_text.get("1.0", "end").strip()
        tipo = self.tipo_var.get()
        nome = self.nome_entry.get().strip() or "Anônimo"
        email_resp = self.email_entry.get().strip()

        if not titulo:
            self.msg_label.configure(text="⚠️ Preencha o título.", text_color=COR_AVISO)
            self.titulo_entry.focus()
            return
        if not descricao or len(descricao) < 10:
            self.msg_label.configure(text="⚠️ Descreva com mais detalhes.", text_color=COR_AVISO)
            self.descricao_text.focus()
            return

        if not BREVO_API_KEY:
            # Fallback: abrir cliente de e-mail nativo
            self._fallback_mailto(titulo, descricao, tipo, nome, email_resp)
            return

        self.msg_label.configure(text="⏳ Enviando...", text_color=COR_AVISO)
        self.btn_enviar.configure(state="disabled", text="Enviando...")

        threading.Thread(
            target=self._enviar_via_brevo,
            args=(titulo, descricao, tipo, nome, email_resp),
            daemon=True,
        ).start()

    def _enviar_via_brevo(self, titulo, descricao, tipo, nome, email_resp):
        """Envia e-mail via Brevo API em thread separada"""
        try:
            agora = datetime.now().strftime("%d/%m/%Y %H:%M")
            corpo_html = f"""
<div style="font-family:Arial,sans-serif;max-width:600px;padding:20px">
  <h2 style="color:#1f6aa5">💬 Novo Feedback - AgendadorESF</h2>
  <table style="width:100%;border-collapse:collapse">
    <tr><td style="padding:8px;background:#f5f5f5;font-weight:bold;width:160px">Tipo</td><td style="padding:8px;border:1px solid #ddd">{tipo}</td></tr>
    <tr><td style="padding:8px;background:#f5f5f5;font-weight:bold">Título</td><td style="padding:8px;border:1px solid #ddd"><strong>{titulo}</strong></td></tr>
    <tr><td style="padding:8px;background:#f5f5f5;font-weight:bold">Nome</td><td style="padding:8px;border:1px solid #ddd">{nome}</td></tr>
    <tr><td style="padding:8px;background:#f5f5f5;font-weight:bold">E-mail</td><td style="padding:8px;border:1px solid #ddd">{email_resp or 'Não informado'}</td></tr>
    <tr><td style="padding:8px;background:#f5f5f5;font-weight:bold">Versão</td><td style="padding:8px;border:1px solid #ddd">v{self.versao_app}</td></tr>
    <tr><td style="padding:8px;background:#f5f5f5;font-weight:bold">Data</td><td style="padding:8px;border:1px solid #ddd">{agora}</td></tr>
  </table>
  <h3>Descrição:</h3>
  <div style="background:#f5f5f5;padding:15px;border-left:4px solid #1f6aa5;white-space:pre-wrap">{descricao}</div>
</div>
"""
            payload = json.dumps({
                "sender": {"name": NOME_REMETENTE, "email": EMAIL_REMETENTE},
                "to": [{"email": EMAIL_DESTINO}],
                "replyTo": {"email": email_resp} if email_resp else {"email": EMAIL_REMETENTE},
                "subject": f"[AgendadorESF Feedback] {tipo}: {titulo}",
                "htmlContent": corpo_html,
            }).encode("utf-8")

            req = urllib.request.Request(
                "https://api.brevo.com/v3/smtp/email",
                data=payload,
                headers={
                    "api-key": BREVO_API_KEY,
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                method="POST",
            )

            with urllib.request.urlopen(req, timeout=10) as resp:
                status = resp.status

            if status in (200, 201, 202):
                self.janela.after(0, lambda: self._sucesso())
            else:
                self.janela.after(0, lambda: self._erro(f"Status inesperado: {status}"))

        except Exception as e:
            self.janela.after(0, lambda: self._erro(str(e)))

    def _fallback_mailto(self, titulo, descricao, tipo, nome, email_resp):
        """Abre o cliente de e-mail nativo como fallback"""
        import urllib.parse
        assunto = urllib.parse.quote(f"[AgendadorESF Feedback] {tipo}: {titulo}")
        corpo = urllib.parse.quote(
            f"Tipo: {tipo}\nTítulo: {titulo}\nNome: {nome}\nVersão: v{self.versao_app}\n\n{descricao}"
        )
        webbrowser.open(f"mailto:{EMAIL_DESTINO}?subject={assunto}&body={corpo}")
        self.msg_label.configure(
            text="✅ Cliente de e-mail aberto! Complete o envio por lá.",
            text_color=COR_SUCESSO
        )
        self.janela.after(2500, self._fechar)

    def _sucesso(self):
        self.msg_label.configure(
            text="✅ Feedback enviado com sucesso! Obrigado!", text_color=COR_SUCESSO
        )
        self.btn_enviar.configure(state="normal", text="📤 Enviar Feedback")
        self.janela.after(2000, self._fechar)

    def _erro(self, msg: str):
        self.msg_label.configure(text=f"❌ Erro ao enviar: {msg}", text_color=COR_ERRO)
        self.btn_enviar.configure(state="normal", text="📤 Enviar Feedback")

    def _esta_ativa(self) -> bool:
        try:
            return bool(self.janela and self.janela.winfo_exists())
        except Exception:
            return False

    def mostrar(self):
        if self._esta_ativa():
            self.janela.deiconify()
            self.janela.lift()
            self.janela.focus_force()

    def destruir(self):
        self._fechar()

    def _fechar(self):
        try:
            if self.janela:
                self.janela.destroy()
        except Exception:
            pass
        self.janela = None
