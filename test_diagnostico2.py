"""Test 2: Test caminho_planilha edge cases and ExcelManager with bad paths"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test: caminho_planilha returns empty string when file doesn't exist
from caminho_planilha import carregar_caminho, salvar_caminho

# Ensure no config exists
if os.path.exists('caminho_planilha.json'):
    os.remove('caminho_planilha.json')

result = carregar_caminho()
print(f'1. carregar_caminho (sem config): "{result}" (tipo: {type(result).__name__})')

# Test: save a path to a file that doesn't exist
salvar_caminho('C:/caminho/que/nao/existe.xlsx')
result2 = carregar_caminho()
print(f'2. carregar_caminho (path nao existe): "{result2}" (tipo: {type(result2).__name__})')

# Test: ExcelManager with empty string
from config_manager import ExcelManager
try:
    em = ExcelManager(caminho='')
    print(f'3. ExcelManager("") - caminho: "{em.caminho}"')
except Exception as e:
    print(f'3. ERRO ExcelManager(""): {e}')
    import traceback; traceback.print_exc()

# Test: What app.py does
caminho_salvo = carregar_caminho()  # returns ""
caminho_planilha = caminho_salvo if caminho_salvo else None
print(f'4. app.py logic: caminho_salvo="{caminho_salvo}", caminho_planilha={caminho_planilha}')

try:
    em2 = ExcelManager(caminho=caminho_planilha)
    print(f'5. ExcelManager(None) - caminho: "{em2.caminho}"')
    # This creates agenda_esf.xlsx in the current directory
    exists = os.path.exists(em2.caminho)
    print(f'   Arquivo existe: {exists}')
except Exception as e:
    print(f'5. ERRO: {e}')
    import traceback; traceback.print_exc()

# Test: What happens with int vs str id comparison
import pandas as pd
try:
    em3 = ExcelManager('test_id.xlsx')
    # Add a record
    em3.agendar_consulta('Paciente A', 'Dr. João', 'Normal', '2026-07-28', '08:00', False, '', 'Sistema')
    
    # Read back with dtype=str
    df = pd.read_excel('test_id.xlsx', sheet_name='Agenda', dtype=str)
    print(f'6. ID type in DataFrame: {df["id"].dtype}, valor: "{df["id"].iloc[0]}"')
    
    # Compare int vs str
    id_int = 1
    id_str = '1'
    match_int = df[df['id'] == id_int]
    match_str = df[df['id'] == id_str]
    print(f'   Comparação com int={id_int}: {len(match_int)} resultados')
    print(f'   Comparação com str="{id_str}": {len(match_str)} resultados')
    print(f'   *** BUG: cancelar_consulta e marcar_presenca usam int, mas dados são str! ***')
    
    os.remove('test_id.xlsx')
except Exception as e:
    print(f'6. ERRO: {e}')
    import traceback; traceback.print_exc()

# Test: retirar_receita same issue
try:
    em4 = ExcelManager('test_id2.xlsx')
    em4.pedir_receita('Paciente B', 'obs', 'Sistema')
    
    df_r = pd.read_excel('test_id2.xlsx', sheet_name='Receitas', dtype=str)
    print(f'7. Receita ID type: {df_r["id"].dtype}, valor: "{df_r["id"].iloc[0]}"')
    
    id_int = 1
    match = df_r[df_r['id'] == id_int]
    print(f'   Comparação com int={id_int}: {len(match)} resultados (BUG!)')
    
    id_str = str(id_int)
    match2 = df_r[df_r['id'] == id_str]
    print(f'   Comparação com str="{id_str}": {len(match2)} resultados (correto)')
    
    os.remove('test_id2.xlsx')
except Exception as e:
    print(f'7. ERRO: {e}')
    import traceback; traceback.print_exc()

# Cleanup
for f in ['caminho_planilha.json', 'agenda_esf.xlsx']:
    if os.path.exists(f):
        os.remove(f)

print('\nDiagnóstico concluído!')
