"""
impressao.py - Geração de PDFs para impressão de agendas e comprovantes de consulta
Formatos suportados:
  - Agenda do Dia: A4 retrato
  - Agenda do Médico: A4 paisagem
  - Comprovante Térmico: 80mm de largura
  - Comprovante A4: 3 comprovantes por folha A4 retrato, recortáveis
"""
import os
import sys
import tempfile
import subprocess
from datetime import datetime
from typing import Any, Dict, List, Optional
from utils import normalize_text

# ─── ReportLab ───────────────────────────────────────────────────────────────
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, HRFlowable, KeepTogether
)
from reportlab.pdfgen import canvas as pdfgen_canvas

# ─── Constantes de layout ────────────────────────────────────────────────────
LARGURA_TERMICA = 80 * mm          # largura da bobina térmica
MARGEM_TERMICA = 5 * mm

COR_AZUL        = colors.HexColor("#1f6aa5")
COR_AZUL_CLARO  = colors.HexColor("#d6e8f5")
COR_CINZA_ESCURO= colors.HexColor("#333333")
COR_CINZA       = colors.HexColor("#666666")
COR_CINZA_CLARO = colors.HexColor("#f2f2f2")
COR_VERDE       = colors.HexColor("#28a745")
COR_AMARELO     = colors.HexColor("#ffc107")
COR_BRANCO      = colors.white
COR_PRETO       = colors.black

NOME_UBS = "ESF - Agenda"          # nome exibido nos documentos


# ─── Abertura do PDF ─────────────────────────────────────────────────────────

def _abrir_pdf(caminho: str):
    """Abre o PDF no visualizador padrão do sistema operacional."""
    try:
        if sys.platform == "win32":
            os.startfile(caminho)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", caminho])
        else:
            subprocess.Popen(["xdg-open", caminho])
    except Exception as e:
        print(f"Não foi possível abrir o PDF automaticamente: {e}\nArquivo: {caminho}")


def _tmp_pdf(prefixo: str) -> str:
    """Cria um arquivo temporário .pdf e retorna seu caminho."""
    fd, caminho = tempfile.mkstemp(suffix=".pdf", prefix=prefixo)
    os.close(fd)
    return caminho


def imprimir_lista(itens: List[Dict[str, Any]], titulo: str, abrir: bool = True, destino_dir: Optional[str] = None) -> str:
    """Gera um PDF simples para exibir uma lista de dados em qualquer tela de visualização."""
    caminho = os.path.join(destino_dir or tempfile.gettempdir(), f"{normalize_text(titulo) or 'lista'}.pdf")
    estilos = _estilos()

    doc = SimpleDocTemplate(
        caminho,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title=titulo,
    )

    elementos = []
    elementos.append(Paragraph(f"🏥 {NOME_UBS}", estilos["titulo"]))
    elementos.append(Paragraph(titulo, ParagraphStyle("titulo_lista", parent=estilos["subtitulo"], fontSize=12, fontName="Helvetica-Bold", textColor=COR_CINZA_ESCURO)))
    elementos.append(Paragraph(f"Impresso em: {_agora_str()}", estilos["subtitulo"]))
    elementos.append(Spacer(1, 4 * mm))

    if not itens:
        elementos.append(Paragraph("Nenhum dado para exibir.", estilos["subtitulo"]))
    else:
        headers = list(itens[0].keys()) if itens else []
        tabela = [[str(h) for h in headers]]
        for item in itens:
            tabela.append([str(item.get(h, "")) for h in headers])
        table = Table(tabela, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), COR_AZUL),
            ('TEXTCOLOR', (0, 0), (-1, 0), COR_BRANCO),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 0.3, COR_CINZA),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [COR_BRANCO, COR_CINZA_CLARO]),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        elementos.append(table)

    doc.build(elementos)
    if abrir:
        _abrir_pdf(caminho)
    return caminho


# ─── Estilos comuns ──────────────────────────────────────────────────────────

def _estilos():
    base = getSampleStyleSheet()
    estilos = {
        "titulo": ParagraphStyle(
            "titulo", parent=base["Normal"],
            fontSize=16, fontName="Helvetica-Bold",
            textColor=COR_AZUL, alignment=TA_CENTER, spaceAfter=4
        ),
        "subtitulo": ParagraphStyle(
            "subtitulo", parent=base["Normal"],
            fontSize=10, fontName="Helvetica",
            textColor=COR_CINZA, alignment=TA_CENTER, spaceAfter=2
        ),
        "cabecalho_tabela": ParagraphStyle(
            "cabecalho_tabela", parent=base["Normal"],
            fontSize=8, fontName="Helvetica-Bold",
            textColor=COR_BRANCO, alignment=TA_CENTER
        ),
        "celula": ParagraphStyle(
            "celula", parent=base["Normal"],
            fontSize=9, fontName="Helvetica",
            textColor=COR_PRETO, alignment=TA_LEFT
        ),
        "celula_centro": ParagraphStyle(
            "celula_centro", parent=base["Normal"],
            fontSize=9, fontName="Helvetica",
            textColor=COR_PRETO, alignment=TA_CENTER
        ),
        "rodape": ParagraphStyle(
            "rodape", parent=base["Normal"],
            fontSize=7, fontName="Helvetica",
            textColor=COR_CINZA, alignment=TA_CENTER
        ),
        # térmico
        "term_titulo": ParagraphStyle(
            "term_titulo", parent=base["Normal"],
            fontSize=13, fontName="Helvetica-Bold",
            textColor=COR_PRETO, alignment=TA_CENTER, spaceAfter=2
        ),
        "term_label": ParagraphStyle(
            "term_label", parent=base["Normal"],
            fontSize=9, fontName="Helvetica-Bold",
            textColor=COR_PRETO, alignment=TA_LEFT
        ),
        "term_valor": ParagraphStyle(
            "term_valor", parent=base["Normal"],
            fontSize=9, fontName="Helvetica",
            textColor=COR_PRETO, alignment=TA_LEFT
        ),
        "term_rodape": ParagraphStyle(
            "term_rodape", parent=base["Normal"],
            fontSize=8, fontName="Helvetica",
            textColor=COR_CINZA, alignment=TA_CENTER
        ),
    }
    return estilos


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _formatar_data(data_str: str) -> str:
    """Converte YYYY-MM-DD para DD/MM/YYYY."""
    if not data_str:
        return ""
    s = str(data_str).strip()
    if len(s) >= 10 and s[4] == "-":
        return f"{s[8:10]}/{s[5:7]}/{s[:4]}"
    return s


def _agora_str() -> str:
    return datetime.now().strftime("%d/%m/%Y %H:%M")


# ═══════════════════════════════════════════════════════════════════════════════
#  AGENDA DO DIA — A4 Retrato
# ═══════════════════════════════════════════════════════════════════════════════

def imprimir_agenda_dia(
    agenda_por_medico: Dict[str, Any],
    data_str: str,
    abrir: bool = True
) -> str:
    """
    Gera PDF da agenda do dia agrupada por médico.

    Parâmetros
    ----------
    agenda_por_medico : dict
        {nome_medico: DataFrame com colunas hora, paciente, tipo_consulta, encaixe, status}
    data_str : str
        Data no formato YYYY-MM-DD
    abrir : bool
        Se True, abre o PDF no visualizador padrão

    Retorna
    -------
    str : caminho do arquivo PDF gerado
    """
    caminho = _tmp_pdf("agenda_dia_")
    estilos = _estilos()

    doc = SimpleDocTemplate(
        caminho,
        pagesize=A4,
        leftMargin=15 * mm, rightMargin=15 * mm,
        topMargin=15 * mm, bottomMargin=15 * mm,
        title=f"Agenda do Dia – {_formatar_data(data_str)}",
    )

    largura_util = A4[0] - 30 * mm  # 180mm

    elementos = []

    # Cabeçalho
    elementos.append(Paragraph(f"🏥 {NOME_UBS}", estilos["titulo"]))
    elementos.append(Paragraph(
        f"AGENDA DO DIA — {_formatar_data(data_str)}",
        ParagraphStyle("agd", parent=estilos["subtitulo"], fontSize=12,
                       fontName="Helvetica-Bold", textColor=COR_CINZA_ESCURO)
    ))
    elementos.append(Paragraph(f"Impresso em: {_agora_str()}", estilos["subtitulo"]))
    elementos.append(Spacer(1, 6 * mm))

    if not agenda_por_medico:
        elementos.append(Paragraph("Nenhuma consulta agendada para hoje.", estilos["subtitulo"]))
    else:
        # Colunas e larguras
        col_labels = ["Horário", "Paciente", "Tipo", "Encaixe", "Status"]
        col_widths = [20*mm, 72*mm, 30*mm, 20*mm, 22*mm]  # total ≈ 164mm (dentro de 180mm)
        padding_extra = (largura_util - sum(col_widths)) / len(col_widths)
        col_widths = [w + padding_extra for w in col_widths]

        total_geral = 0

        for medico, consultas in agenda_por_medico.items():
            if hasattr(consultas, 'empty') and consultas.empty:
                continue

            # Título do médico
            elementos.append(HRFlowable(width="100%", thickness=1, color=COR_AZUL, spaceAfter=2))
            total = len(consultas)
            encaixes = len(consultas[consultas.get('encaixe', '') == 'TRUE']) if hasattr(consultas, '__len__') else 0
            try:
                encaixes = len(consultas[consultas['encaixe'] == 'TRUE'])
            except Exception:
                encaixes = 0
            total_geral += total

            elementos.append(Paragraph(
                f"<b>{medico}</b> &nbsp;·&nbsp; {total} consulta(s) | {encaixes} encaixe(s)",
                ParagraphStyle("med", parent=estilos["subtitulo"], fontSize=10,
                               fontName="Helvetica-Bold", textColor=COR_AZUL,
                               alignment=TA_LEFT)
            ))
            elementos.append(Spacer(1, 2 * mm))

            # Cabeçalho da tabela
            dados_tabela = [col_labels]

            for _, row in consultas.iterrows():
                encaixe_val = str(row.get('encaixe', '')).upper()
                status_val  = str(row.get('status', ''))
                dados_tabela.append([
                    str(row.get('hora', '')),
                    str(row.get('paciente', '')),
                    str(row.get('tipo_consulta', '')),
                    "⚡ Sim" if encaixe_val == 'TRUE' else "Não",
                    status_val,
                ])

            tabela = Table(dados_tabela, colWidths=col_widths, repeatRows=1)
            tabela.setStyle(TableStyle([
                # Cabeçalho
                ('BACKGROUND',  (0, 0), (-1, 0), COR_AZUL),
                ('TEXTCOLOR',   (0, 0), (-1, 0), COR_BRANCO),
                ('FONTNAME',    (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE',    (0, 0), (-1, 0), 8),
                ('ALIGN',       (0, 0), (-1, 0), 'CENTER'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
                # Linhas de dados
                ('FONTNAME',    (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE',    (0, 1), (-1, -1), 8),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [COR_BRANCO, COR_CINZA_CLARO]),
                ('ALIGN',       (0, 1), (0, -1), 'CENTER'),  # horário
                ('ALIGN',       (2, 1), (-1, -1), 'CENTER'),
                ('VALIGN',      (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING',  (0, 1), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
                # Grade
                ('GRID',        (0, 0), (-1, -1), 0.3, COR_CINZA),
            ]))
            elementos.append(tabela)
            elementos.append(Spacer(1, 5 * mm))

        # Total geral
        elementos.append(HRFlowable(width="100%", thickness=0.5, color=COR_CINZA, spaceAfter=2))
        elementos.append(Paragraph(f"<b>Total geral: {total_geral} consulta(s)</b>", estilos["rodape"]))

    doc.build(elementos)

    if abrir:
        _abrir_pdf(caminho)

    return caminho


# ═══════════════════════════════════════════════════════════════════════════════
#  AGENDA DO MÉDICO — A4 Paisagem
# ═══════════════════════════════════════════════════════════════════════════════

def imprimir_agenda_medico(
    consultas,
    medico: str,
    filtro: str = "ATIVO",
    abrir: bool = True
) -> str:
    """
    Gera PDF da agenda de um médico em A4 paisagem.

    Parâmetros
    ----------
    consultas : DataFrame
        Colunas: id, data, hora, paciente, tipo_consulta, encaixe, status, compareceu
    medico : str
    filtro : str
        Filtro aplicado (para exibir no cabeçalho)
    abrir : bool
    """
    caminho = _tmp_pdf("agenda_medico_")
    estilos = _estilos()

    tamanho_pagina = landscape(A4)  # 297 × 210 mm
    doc = SimpleDocTemplate(
        caminho,
        pagesize=tamanho_pagina,
        leftMargin=15 * mm, rightMargin=15 * mm,
        topMargin=12 * mm, bottomMargin=12 * mm,
        title=f"Agenda – {medico}",
    )

    largura_util = tamanho_pagina[0] - 30 * mm  # ≈ 267mm

    elementos = []

    # Cabeçalho
    elementos.append(Paragraph(f"🏥 {NOME_UBS}", estilos["titulo"]))
    elementos.append(Paragraph(
        f"AGENDA DO MÉDICO — <b>{medico}</b> &nbsp;·&nbsp; Filtro: {filtro}",
        ParagraphStyle("amd", parent=estilos["subtitulo"], fontSize=11,
                       fontName="Helvetica-Bold", textColor=COR_CINZA_ESCURO)
    ))
    elementos.append(Paragraph(f"Impresso em: {_agora_str()}", estilos["subtitulo"]))
    elementos.append(Spacer(1, 5 * mm))

    total = 0

    if consultas is None or (hasattr(consultas, 'empty') and consultas.empty):
        elementos.append(Paragraph("Nenhuma consulta encontrada.", estilos["subtitulo"]))
    else:
        col_labels = ["ID", "Data", "Hora", "Paciente", "Tipo", "Encaixe", "Status", "Compareceu"]
        # Proporções das colunas
        col_widths = [14*mm, 24*mm, 18*mm, 80*mm, 38*mm, 22*mm, 28*mm, 28*mm]
        sobra = largura_util - sum(col_widths)
        col_widths[3] += sobra  # dar a sobra para o nome do paciente

        dados_tabela = [col_labels]

        try:
            consultas_ord = consultas.sort_values(['data', 'hora'], ascending=[True, True])
        except Exception:
            consultas_ord = consultas

        for _, row in consultas_ord.iterrows():
            total += 1
            encaixe_val = str(row.get('encaixe', '')).upper()
            comp_val    = str(row.get('compareceu', '')).upper()
            dados_tabela.append([
                str(int(row.get('id', 0))) if str(row.get('id', '')).replace('.', '').isdigit() else str(row.get('id', '')),
                _formatar_data(str(row.get('data', ''))),
                str(row.get('hora', '')),
                str(row.get('paciente', '')),
                str(row.get('tipo_consulta', '')),
                "⚡ Sim" if encaixe_val == 'TRUE' else "Não",
                str(row.get('status', '')),
                "✓ Sim" if comp_val == 'TRUE' else "—",
            ])

        tabela = Table(dados_tabela, colWidths=col_widths, repeatRows=1)
        tabela.setStyle(TableStyle([
            ('BACKGROUND',  (0, 0), (-1, 0), COR_AZUL),
            ('TEXTCOLOR',   (0, 0), (-1, 0), COR_BRANCO),
            ('FONTNAME',    (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',    (0, 0), (-1, 0), 8),
            ('ALIGN',       (0, 0), (-1, 0), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
            ('FONTNAME',    (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE',    (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [COR_BRANCO, COR_CINZA_CLARO]),
            ('ALIGN',       (0, 1), (0, -1), 'CENTER'),
            ('ALIGN',       (1, 1), (2, -1), 'CENTER'),
            ('ALIGN',       (5, 1), (-1, -1), 'CENTER'),
            ('VALIGN',      (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING',  (0, 1), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
            ('GRID',        (0, 0), (-1, -1), 0.3, COR_CINZA),
        ]))
        elementos.append(tabela)
        elementos.append(Spacer(1, 4 * mm))
        elementos.append(HRFlowable(width="100%", thickness=0.5, color=COR_CINZA, spaceAfter=2))
        elementos.append(Paragraph(f"<b>Total: {total} consulta(s)</b> &nbsp;|&nbsp; Médico: {medico} &nbsp;|&nbsp; Filtro: {filtro}", estilos["rodape"]))

    doc.build(elementos)

    if abrir:
        _abrir_pdf(caminho)

    return caminho


# ═══════════════════════════════════════════════════════════════════════════════
#  COMPROVANTE TÉRMICO — 80mm de largura
# ═══════════════════════════════════════════════════════════════════════════════

def _altura_termica(consulta: Dict[str, Any]) -> float:
    """Estima altura necessária para o comprovante térmico."""
    linhas_obs = 1 if consulta.get('observacao', '').strip() else 0
    return (70 + linhas_obs * 10) * mm


def imprimir_comprovante_termico(
    consulta: Dict[str, Any],
    abrir: bool = True
) -> str:
    """
    Gera PDF de comprovante de consulta no formato térmico (80mm).

    Parâmetros
    ----------
    consulta : dict
        Chaves: id, paciente, medico, tipo_consulta, data, hora, encaixe, observacao
    abrir : bool
    """
    caminho = _tmp_pdf("comprovante_termico_")

    # Dimensões da página térmica
    largura  = LARGURA_TERMICA
    altura   = _altura_termica(consulta)

    c = pdfgen_canvas.Canvas(caminho, pagesize=(largura, altura))
    c.setTitle("Comprovante de Consulta")

    def texto_center(y_mm, txt, font="Helvetica", size=9, cor=colors.black):
        c.setFont(font, size)
        c.setFillColor(cor)
        c.drawCentredString(largura / 2, y_mm * mm, txt)

    def texto_left(y_mm, txt, font="Helvetica", size=9, x_mm=5):
        c.setFont(font, size)
        c.setFillColor(colors.black)
        c.drawString(x_mm * mm, y_mm * mm, txt)

    def linha_h(y_mm, espessura=0.5, estilo="solid"):
        c.setStrokeColor(COR_CINZA)
        c.setLineWidth(espessura)
        if estilo == "dashed":
            c.setDash(3, 3)
        else:
            c.setDash()
        c.line(MARGEM_TERMICA, y_mm * mm, largura - MARGEM_TERMICA, y_mm * mm)
        c.setDash()

    # Posição inicial (de cima para baixo, em mm a partir do topo)
    # convertemos: y_pdf = altura_total_mm - y_mm_do_topo
    H = altura / mm  # altura total em mm

    y = H - 5
    texto_center(y, NOME_UBS, "Helvetica-Bold", 11, COR_AZUL)
    y -= 5
    texto_center(y, "COMPROVANTE DE CONSULTA", "Helvetica-Bold", 8)
    y -= 4
    linha_h(y, 1)
    y -= 5

    # Dados principais
    campos = [
        ("Paciente:", str(consulta.get('paciente', ''))),
        ("Médico:",   str(consulta.get('medico', ''))),
        ("Tipo:",     str(consulta.get('tipo_consulta', ''))),
        ("Data:",     _formatar_data(str(consulta.get('data', '')))),
        ("Horário:",  str(consulta.get('hora', ''))),
        ("Nº/ID:",    f"#{consulta.get('id', '')}"),
    ]

    encaixe_val = str(consulta.get('encaixe', '')).upper()
    if encaixe_val == 'TRUE':
        campos.insert(2, ("Tipo atend.:", "⚡ ENCAIXE"))

    for label, valor in campos:
        texto_left(y, label, "Helvetica-Bold", 8)
        texto_left(y, valor, "Helvetica", 8, x_mm=28)
        y -= 5.5

    obs = str(consulta.get('observacao', '') or '').strip()
    if obs:
        y -= 1
        linha_h(y, 0.3, "dashed")
        y -= 5
        texto_left(y, f"Obs.: {obs}", "Helvetica", 7.5)
        y -= 5

    y -= 2
    linha_h(y, 1)
    y -= 5
    texto_center(y, "Aguarde ser chamado.", "Helvetica-Bold", 8)
    y -= 4
    texto_center(y, _agora_str(), "Helvetica", 7, COR_CINZA)

    c.save()

    if abrir:
        _abrir_pdf(caminho)

    return caminho


# ═══════════════════════════════════════════════════════════════════════════════
#  COMPROVANTE A4 — 3 por página, recortáveis
# ═══════════════════════════════════════════════════════════════════════════════

def imprimir_comprovante_a4(
    consultas: List[Dict[str, Any]],
    abrir: bool = True
) -> str:
    """
    Gera PDF com comprovantes em A4 portrait: 3 por folha, separados por linha tracejada.

    Parâmetros
    ----------
    consultas : list[dict]
        Lista de dicionários de consulta (mesmo formato do térmico).
        Se passado apenas 1 item, preenche a 1ª seção; as outras ficam em branco.
    abrir : bool
    """
    caminho = _tmp_pdf("comprovante_a4_")

    largura_a4, altura_a4 = A4  # 210 × 297 mm
    margem = 10 * mm
    espacamento_interno = 5 * mm

    # Altura de cada seção (3 por página)
    secao_altura = (altura_a4 - 2 * margem) / 3

    # Garante que seja múltiplo de 3 enchendo com None
    while len(consultas) % 3 != 0:
        consultas.append(None)

    c = pdfgen_canvas.Canvas(caminho, pagesize=A4)
    c.setTitle("Comprovante de Consulta – A4")

    def desenhar_secao(cx, consulta: Optional[Dict[str, Any]], y_base: float, h_secao: float):
        """Desenha um comprovante dentro de uma seção da folha."""
        x_esq = margem
        x_dir = largura_a4 - margem
        largura_util = x_dir - x_esq

        # Linha tracejada no topo da seção (exceto a primeira)
        cx.setStrokeColor(COR_CINZA)
        cx.setLineWidth(0.5)
        cx.setDash(4, 4)
        cx.line(x_esq, y_base + h_secao, x_dir, y_base + h_secao)
        cx.setDash()

        if consulta is None:
            return

        # Faixa azul de cabeçalho
        cx.setFillColor(COR_AZUL)
        cx.rect(x_esq, y_base + h_secao - 12 * mm, largura_util, 12 * mm, fill=True, stroke=False)

        cx.setFillColor(COR_BRANCO)
        cx.setFont("Helvetica-Bold", 11)
        cx.drawCentredString(largura_a4 / 2, y_base + h_secao - 7.5 * mm, NOME_UBS)
        cx.setFont("Helvetica", 8)
        cx.drawCentredString(largura_a4 / 2, y_base + h_secao - 11 * mm, "COMPROVANTE DE CONSULTA")

        # Corpo — dois blocos lado a lado
        col_esq_x = x_esq + 3 * mm
        col_dir_x = x_esq + largura_util / 2 + 3 * mm
        y_corpo = y_base + h_secao - 15 * mm

        campos_esq = [
            ("Paciente", str(consulta.get('paciente', ''))),
            ("Médico",   str(consulta.get('medico', ''))),
            ("Data",     _formatar_data(str(consulta.get('data', '')))),
        ]
        campos_dir = [
            ("Tipo",    str(consulta.get('tipo_consulta', ''))),
            ("Horário", str(consulta.get('hora', ''))),
            ("Nº/ID",   f"#{consulta.get('id', '')}"),
        ]

        def par_label_valor(col_x, y, label, valor):
            cx.setFillColor(COR_CINZA)
            cx.setFont("Helvetica-Bold", 7.5)
            cx.drawString(col_x, y, label.upper())
            cx.setFillColor(COR_PRETO)
            cx.setFont("Helvetica", 9)
            cx.drawString(col_x, y - 4.5 * mm, valor[:35])  # trunca nome longo
            return y - 9 * mm

        y_e = y_corpo
        y_d = y_corpo
        for (le, ve), (ld, vd) in zip(campos_esq, campos_dir):
            y_e = par_label_valor(col_esq_x, y_e, le, ve)
            y_d = par_label_valor(col_dir_x, y_d, ld, vd)

        # Encaixe
        encaixe_val = str(consulta.get('encaixe', '')).upper()
        if encaixe_val == 'TRUE':
            y_e -= 1
            cx.setFillColor(COR_AMARELO)
            cx.setFont("Helvetica-Bold", 8)
            cx.drawString(col_esq_x, y_e, "⚡ ENCAIXE")
            y_e -= 5 * mm

        # Observação
        obs = str(consulta.get('observacao', '') or '').strip()
        if obs:
            cy = min(y_e, y_d) - 2 * mm
            cx.setStrokeColor(COR_CINZA)
            cx.setLineWidth(0.3)
            cx.setDash(2, 2)
            cx.line(x_esq + 3 * mm, cy, x_dir - 3 * mm, cy)
            cx.setDash()
            cy -= 4.5 * mm
            cx.setFillColor(COR_CINZA)
            cx.setFont("Helvetica-Bold", 7)
            cx.drawString(col_esq_x, cy, "OBS.:")
            cx.setFillColor(COR_PRETO)
            cx.setFont("Helvetica", 7.5)
            cx.drawString(col_esq_x + 10 * mm, cy, obs[:70])

        # Mensagem rodapé
        y_rodape = y_base + 3 * mm
        cx.setFillColor(COR_CINZA)
        cx.setFont("Helvetica", 7)
        cx.drawCentredString(largura_a4 / 2, y_rodape + 3.5 * mm, "Aguarde ser chamado.")
        cx.drawCentredString(largura_a4 / 2, y_rodape, f"Impresso em: {_agora_str()}")

    # Desenhar páginas
    for i in range(0, len(consultas), 3):
        grupo = consultas[i:i+3]  # 3 comprovantes por página

        for j, consulta in enumerate(grupo):
            # Seções de cima para baixo: 2, 1, 0  (y_base cresce de baixo para cima)
            y_base = margem + (2 - j) * secao_altura
            desenhar_secao(c, consulta, y_base, secao_altura)

        # Linha tracejada no topo da primeira seção (borda superior)
        c.setStrokeColor(COR_CINZA)
        c.setLineWidth(0.5)
        c.setDash(4, 4)
        c.line(margem, margem, largura_a4 - margem, margem)
        c.setDash()

        if i + 3 < len(consultas):
            c.showPage()

    c.save()

    if abrir:
        _abrir_pdf(caminho)

    return caminho


# ═══════════════════════════════════════════════════════════════════════════════
#  Funções de conveniência — ponte para a tela de agendamento
# ═══════════════════════════════════════════════════════════════════════════════

def comprovante_termico(consulta: Dict[str, Any], abrir: bool = True) -> str:
    """Alias direto para imprimir_comprovante_termico."""
    return imprimir_comprovante_termico(consulta, abrir=abrir)


def comprovante_a4(consulta: Dict[str, Any], abrir: bool = True) -> str:
    """Gera um comprovante A4 com a consulta duplicada (3× na folha)."""
    return imprimir_comprovante_a4([consulta, consulta, consulta], abrir=abrir)


def comprovante_a4_termico(consulta: Dict[str, Any], abrir: bool = True) -> str:
    """Gera comprovante A4 estilo térmico (2 tiras lado a lado, com linhas de corte)."""
    return imprimir_comprovante_a4_termico([consulta, consulta], abrir=abrir)


# ═══════════════════════════════════════════════════════════════════════════════
#  COMPROVANTE A4 ESTILO TÉRMICO — 2 tiras 80mm por folha, recortável
# ═══════════════════════════════════════════════════════════════════════════════

def imprimir_comprovante_a4_termico(
    consultas: List[Dict[str, Any]],
    abrir: bool = True
) -> str:
    """
    Imprime comprovantes no estilo térmico (80mm) dentro de uma folha A4 portrait,
    posicionando 2 tiras lado a lado com linhas de corte tracejadas.
    O usuário imprime em impressora normal e recorta ao longo das linhas.

    Layout em A4 portrait (210 × 297 mm):
    ┌────────────────────────────────────────┐
    │ ┌── tira 1 ──┐  ┊  ┌── tira 2 ──┐   │
    │ │   80 mm    │  ┊  │   80 mm    │   │
    │ │  conteúdo  │  ┊  │  conteúdo  │   │
    │ └────────────┘  ┊  └────────────┘   │
    └────────────────────────────────────────┘
      ← 10mm →← 80mm →← 15mm →← 80mm →← 25mm →
    Linhas de corte verticais: antes e depois de cada tira.
    Linha de corte horizontal: abaixo do conteúdo.

    Parâmetros
    ----------
    consultas : list[dict]
        Lista de consultas. Cada par de 2 ocupa uma página A4.
        Passando só 1 consulta, duplica automaticamente para preencher as 2 tiras.
    abrir : bool
    """
    # Garantir que temos sempre pares
    if not consultas:
        consultas = [{}]
    while len(consultas) % 2 != 0:
        consultas.append(consultas[-1])   # duplica o último para completar o par

    caminho = _tmp_pdf("comprovante_a4_termico_")

    largura_a4, altura_a4 = A4   # 595.28, 841.89 pt  ≈ 210 × 297 mm
    margem_esq   = 10 * mm
    largura_tira = 80 * mm
    gutter       = 15 * mm      # espaço entre as duas tiras (onde será feito o corte)
    margem_sup   = 10 * mm
    margem_inf   = 10 * mm

    # x de início de cada tira
    x_tira = [
        margem_esq,
        margem_esq + largura_tira + gutter,
    ]

    altura_util = altura_a4 - margem_sup - margem_inf

    c = pdfgen_canvas.Canvas(caminho, pagesize=A4)
    c.setTitle("Comprovante de Consulta – Estilo Térmico")

    def _linha_corte_v(x_pos: float, y_ini: float, y_fim: float):
        """Desenha linha tracejada vertical de corte."""
        c.saveState()
        c.setStrokeColor(COR_CINZA)
        c.setLineWidth(0.5)
        c.setDash(4, 4)
        c.line(x_pos, y_ini, x_pos, y_fim)
        c.restoreState()

    def _linha_corte_h(y_pos: float, x_ini: float, x_fim: float):
        """Desenha linha tracejada horizontal de corte."""
        c.saveState()
        c.setStrokeColor(COR_CINZA)
        c.setLineWidth(0.5)
        c.setDash(4, 4)
        c.line(x_ini, y_pos, x_fim, y_pos)
        c.restoreState()

    def _marca_tesoura(x: float, y: float):
        """Desenha um pequeno símbolo de tesoura ✂ para marcar pontos de corte."""
        c.saveState()
        c.setFont("Helvetica", 8)
        c.setFillColor(COR_CINZA)
        c.drawString(x - 4 * mm, y - 1.5 * mm, "✂")
        c.restoreState()

    def _desenhar_tira(x: float, consulta: Dict[str, Any]):
        """Desenha o conteúdo do comprovante dentro de uma tira de 80mm."""
        if not consulta:
            return

        pad = 4 * mm    # padding interno
        larg_interna = largura_tira - 2 * pad

        # Posição inicial (topo da área útil)
        y = altura_a4 - margem_sup

        # ── Faixa de cabeçalho azul ─────────────────────────────────────────
        cab_h = 10 * mm
        c.setFillColor(COR_AZUL)
        c.rect(x, y - cab_h, largura_tira, cab_h, fill=True, stroke=False)

        c.setFillColor(COR_BRANCO)
        c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(x + largura_tira / 2, y - 6 * mm, NOME_UBS)
        c.setFont("Helvetica", 7)
        c.drawCentredString(x + largura_tira / 2, y - 9.5 * mm, "COMPROVANTE DE CONSULTA")
        y -= cab_h + 3 * mm

        # ── Dados ────────────────────────────────────────────────────────────
        encaixe_val = str(consulta.get('encaixe', '')).upper()

        campos = [
            ("Paciente",  str(consulta.get('paciente', ''))),
            ("Médico",    str(consulta.get('medico', ''))),
            ("Tipo",      str(consulta.get('tipo_consulta', ''))),
            ("Data",      _formatar_data(str(consulta.get('data', '')))),
            ("Horário",   str(consulta.get('hora', ''))),
            ("Nº/ID",     f"#{consulta.get('id', '')}"),
        ]
        if encaixe_val == 'TRUE':
            campos.insert(2, ("Atend.",   "⚡ ENCAIXE"))

        for label, valor in campos:
            c.setFont("Helvetica-Bold", 7.5)
            c.setFillColor(COR_CINZA)
            c.drawString(x + pad, y, label + ":")

            c.setFont("Helvetica", 8)
            c.setFillColor(COR_PRETO)
            # truncar se necessário
            valor_exib = valor[:28] if len(valor) > 28 else valor
            c.drawString(x + pad + 18 * mm, y, valor_exib)
            y -= 5.5 * mm

        # ── Observação ───────────────────────────────────────────────────────
        obs = str(consulta.get('observacao', '') or '').strip()
        if obs:
            c.setStrokeColor(COR_CINZA)
            c.setLineWidth(0.3)
            c.setDash(2, 2)
            c.line(x + pad, y, x + largura_tira - pad, y)
            c.setDash()
            y -= 4 * mm
            c.setFont("Helvetica-Bold", 7)
            c.setFillColor(COR_CINZA)
            c.drawString(x + pad, y, "Obs.:")
            c.setFont("Helvetica", 7)
            c.setFillColor(COR_PRETO)
            c.drawString(x + pad + 10 * mm, y, obs[:36])
            y -= 5 * mm

        # ── Rodapé ───────────────────────────────────────────────────────────
        y -= 3 * mm
        c.setStrokeColor(COR_CINZA)
        c.setLineWidth(0.5)
        c.line(x + pad, y, x + largura_tira - pad, y)
        y -= 4 * mm
        c.setFont("Helvetica-Bold", 7.5)
        c.setFillColor(COR_CINZA_ESCURO)
        c.drawCentredString(x + largura_tira / 2, y, "Aguarde ser chamado.")
        y -= 4 * mm
        c.setFont("Helvetica", 6.5)
        c.setFillColor(COR_CINZA)
        c.drawCentredString(x + largura_tira / 2, y, _agora_str())

        # Retorna a posição Y mais baixa usada (para a linha de corte horizontal)
        return y - 4 * mm

    # ── Renderizar páginas ────────────────────────────────────────────────────
    for i in range(0, len(consultas), 2):
        par = consultas[i:i+2]

        y_mais_baixo = altura_a4 - margem_sup

        for j, consulta in enumerate(par):
            y_base = _desenhar_tira(x_tira[j], consulta)
            if y_base is not None and y_base < y_mais_baixo:
                y_mais_baixo = y_base

        # ── Linhas de corte verticais ─────────────────────────────────────────
        y_sup = altura_a4 - margem_sup + 5 * mm
        y_inf = y_mais_baixo - 4 * mm

        # Borda esquerda da tira 1
        _linha_corte_v(x_tira[0], y_inf, y_sup)
        _marca_tesoura(x_tira[0], y_sup)

        # Borda direita da tira 1 / esquerda do gutter
        _linha_corte_v(x_tira[0] + largura_tira, y_inf, y_sup)
        _marca_tesoura(x_tira[0] + largura_tira, y_sup)

        # Borda direita da tira 2
        _linha_corte_v(x_tira[1] + largura_tira, y_inf, y_sup)
        _marca_tesoura(x_tira[1] + largura_tira, y_sup)

        # ── Linha de corte horizontal (abaixo do conteúdo) ────────────────────
        x_ini = x_tira[0] - 5 * mm
        x_fim = x_tira[1] + largura_tira + 5 * mm
        _linha_corte_h(y_mais_baixo, x_ini, x_fim)
        _marca_tesoura(x_ini, y_mais_baixo)

        # ── Instrução de corte ────────────────────────────────────────────────
        c.setFont("Helvetica", 6)
        c.setFillColor(COR_CINZA)
        c.drawCentredString(largura_a4 / 2, y_mais_baixo - 5 * mm,
                            "✂  Recorte ao longo das linhas tracejadas  ✂")

        if i + 2 < len(consultas):
            c.showPage()

    c.save()

    if abrir:
        _abrir_pdf(caminho)

    return caminho
