import json
import os
import pandas as pd
from config_manager import ExcelManager
from impressao import imprimir_lista
from tela_agendamento import TelaAgendamento
from tela_busca import TelaBusca


def test_modalidade_medico_configurado(tmp_path):
    caminho = tmp_path / "agenda_test.xlsx"
    excel = ExcelManager(str(caminho))

    df = excel.get_config()
    df = pd.concat(
        [
            df,
            pd.DataFrame([
                {"tipo": "modalidade_medico", "chave": "gercon", "valor": "Dr. João"},
            ]),
        ],
        ignore_index=True,
    )
    excel.salvar_config(df)

    assert excel.get_modalidade_medico("GERCON") == "Dr. João"
    assert excel.get_modalidade_medico_chave("GERCON") == "dr_joao"


def test_horarios_normais_nao_sao_bloqueados_por_consultas_especiais(tmp_path):
    caminho = tmp_path / "agenda_test.xlsx"
    excel = ExcelManager(str(caminho))

    excel.agendar_consulta(
        paciente="Paciente A",
        medico="Dr. João",
        tipo_consulta="GERCON",
        data="2026-07-28",
        hora="08:00",
        encaixe=False,
        observacao="",
        usuario="Sistema",
    )

    horarios = excel.get_horarios_disponiveis("Dr. João", "2026-07-28", "Normal")

    assert "08:00" in horarios


def test_retirada_de_receita_atualiza_status(tmp_path):
    caminho = tmp_path / "agenda_test.xlsx"
    excel = ExcelManager(str(caminho))

    receita_id = excel.pedir_receita("Paciente B", "obs", "Sistema")
    excel.retirar_receita(receita_id, "Maria", observacao="Retirou", usuario="Sistema")

    receitas = excel.get_todas_receitas()
    receita = receitas[receitas['id'] == str(receita_id)].iloc[0]

    assert receita['status'] == 'RETIRADA'
    assert receita['quem_retirou'] == 'Maria'


def test_dados_do_paciente_sao_preservados_entre_etapas():
    tela = TelaAgendamento.__new__(TelaAgendamento)
    tela.paciente_nome = ""
    tela.observacao = ""

    class FakeEntry:
        def __init__(self, value):
            self._value = value

        def winfo_exists(self):
            return True

        def get(self):
            return self._value

    tela.paciente_entry = FakeEntry("João da Silva")
    tela.obs_entry = FakeEntry("Retorno às 10h")

    tela._capturar_dados_paciente()

    assert tela.paciente_nome == "João da Silva"
    assert tela.observacao == "Retorno às 10h"


def test_tipos_consultas_especiais_podem_ser_salvos(tmp_path):
    caminho = tmp_path / "agenda_test.xlsx"
    excel = ExcelManager(str(caminho))

    excel.salvar_tipo_consulta_especial(
        nome="Acolhimento",
        dia_semana="ter",
        turno="manha",
        medico="Dr. João",
        descricao="Acolhimento diário",
    )

    tipos = excel.get_tipos_consultas_especiais()
    assert any(item["nome"] == "Acolhimento" for item in tipos)
    regra = excel.get_regra_tipo_consulta("Acolhimento")
    assert regra["medico"] == "Dr. João"
    assert regra["dia_semana"] == "ter"


def test_tela_busca_abre_retirada_de_receita_por_resultado(tmp_path, monkeypatch):
    caminho = tmp_path / "agenda_test.xlsx"
    excel = ExcelManager(str(caminho))
    receita_id = excel.pedir_receita("Paciente Busca", "obs", "Sistema")

    class FakeModalRetiradaReceita:
        def __init__(self, excel, receita, usuario=None, callback_sucesso=None, parent=None):
            self.excel = excel
            self.receita = receita
            self.usuario = usuario
            self.callback_sucesso = callback_sucesso
            self.parent = parent

    captured = {}

    def fake_construtor(excel, receita, usuario=None, callback_sucesso=None, parent=None):
        instance = FakeModalRetiradaReceita(excel, receita, usuario, callback_sucesso, parent)
        captured["instance"] = instance
        return instance

    monkeypatch.setattr("tela_receitas.ModalRetiradaReceita", fake_construtor)

    busca = TelaBusca.__new__(TelaBusca)
    busca.excel = excel
    busca.usuario = "Enfermeira"
    busca.janela = "FakeJanelaBusca"

    busca._abrir_retirada_receita({"id": receita_id, "paciente": "Paciente Busca"})

    assert captured["instance"].excel is excel
    assert captured["instance"].usuario == "Enfermeira"
    assert captured["instance"].receita["id"] == receita_id
    assert captured["instance"].receita["paciente"] == "Paciente Busca"
    assert captured["instance"].parent == "FakeJanelaBusca"


def test_carregar_caminho_resolve_planilha_relativa_ao_arquivo_de_config(tmp_path, monkeypatch):
    pasta_app = tmp_path / "versao_antiga"
    pasta_app.mkdir()
    planilha = pasta_app / "agenda_esf.xlsx"
    planilha.write_text("dummy", encoding="utf-8")

    config = pasta_app / "caminho_planilha.json"
    config.write_text(json.dumps({"caminho": "agenda_esf.xlsx"}), encoding="utf-8")

    pasta_execucao = tmp_path / "execucao"
    pasta_execucao.mkdir()
    monkeypatch.chdir(pasta_execucao)

    from caminho_planilha import carregar_caminho

    assert carregar_caminho() == str(planilha.resolve())


def test_carregar_caminho_encontra_planilha_na_pasta_pai_do_executavel(tmp_path, monkeypatch):
    pasta_raiz = tmp_path / "projeto_antigo"
    pasta_raiz.mkdir()
    planilha = pasta_raiz / "agenda_esf.xlsx"
    planilha.write_text("dummy", encoding="utf-8")

    pasta_execucao = pasta_raiz / "dist"
    pasta_execucao.mkdir()
    monkeypatch.chdir(pasta_execucao)

    real_exists = os.path.exists
    monkeypatch.setattr("caminho_planilha.sys.executable", str(pasta_execucao / "app.exe"))
    monkeypatch.setattr(
        "caminho_planilha.os.path.exists",
        lambda path: True if str(path) == str(pasta_execucao / "caminho_planilha.json") else real_exists(path),
    )

    config = pasta_execucao / "caminho_planilha.json"
    config.write_text(json.dumps({"caminho": "C:/arquivo/inexistente.xlsx"}), encoding="utf-8")

    from caminho_planilha import carregar_caminho

    assert carregar_caminho() == str(planilha.resolve())


def test_imprimir_lista_gera_pdf_temporario(tmp_path):
    caminho = imprimir_lista(
        [{"Paciente": "Ana", "Observação": "Retorno"}],
        titulo="Tela de teste",
        abrir=False,
        destino_dir=str(tmp_path),
    )

    assert os.path.exists(caminho)


def test_github_updater_detecta_versao_mais_recente(monkeypatch):
    class FakeResponse:
        def __init__(self, payload):
            self.payload = payload

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return json.dumps(self.payload).encode("utf-8")

    class FakeUrlLib:
        @staticmethod
        def urlopen(url, timeout=None):
            return FakeResponse({
                "tag_name": "v1.2.0",
                "html_url": "https://github.com/exemplo/projeto/releases/tag/v1.2.0",
                "assets": [],
                "body": "Nova versão teste"
            })

    monkeypatch.setattr("urllib.request.urlopen", FakeUrlLib.urlopen)

    from github_updater import GitHubUpdater

    updater = GitHubUpdater(repo="exemplo/projeto", current_version="1.0.0")
    info = updater.check_for_update()

    assert info is not None
    assert info["version"] == "1.2.0"
    assert info["url"].endswith("v1.2.0")
