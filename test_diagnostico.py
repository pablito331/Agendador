"""Script de diagnóstico para testar ExcelManager"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config_manager import ExcelManager

caminho = 'test_diag2.xlsx'
if os.path.exists(caminho):
    os.remove(caminho)

# Test 1: Create fresh spreadsheet
try:
    em = ExcelManager(caminho)
    print('1. Criação OK')
except Exception as e:
    print(f'1. ERRO ao criar: {e}')
    import traceback; traceback.print_exc()
    sys.exit(1)

# Test 2: Try scheduling
try:
    novo_id = em.agendar_consulta(
        paciente='Teste Paciente',
        medico='Dr. João',
        tipo_consulta='Normal',
        data='2026-07-28',
        hora='08:00',
        encaixe=False,
        observacao='teste',
        usuario='Sistema'
    )
    print(f'2. Agendamento OK - ID: {novo_id}')
except Exception as e:
    print(f'2. ERRO ao agendar: {e}')
    import traceback; traceback.print_exc()

# Test 3: Try searching
try:
    resultado = em.buscar_global('Teste')
    n_agenda = len(resultado['agenda'])
    n_receitas = len(resultado['receitas'])
    print(f'3. Busca OK - {n_agenda} resultados agenda, {n_receitas} resultados receitas')
except Exception as e:
    print(f'3. ERRO na busca: {e}')
    import traceback; traceback.print_exc()

# Test 4: Try recipe
try:
    rec_id = em.pedir_receita('Teste Paciente', 'obs teste', 'Sistema')
    print(f'4. Receita OK - ID: {rec_id}')
except Exception as e:
    print(f'4. ERRO na receita: {e}')
    import traceback; traceback.print_exc()

# Test 5: Try cancelar (id comparison)
try:
    em.cancelar_consulta(1, 'Sistema')
    print('5. Cancelamento OK')
except Exception as e:
    print(f'5. ERRO ao cancelar: {e}')
    import traceback; traceback.print_exc()

# Test 6: Try marcar presença
try:
    em.marcar_presenca(1, True, 'Sistema')
    print('6. Marcar presença OK')
except Exception as e:
    print(f'6. ERRO ao marcar presença: {e}')
    import traceback; traceback.print_exc()

# Test 7: Try get_config
try:
    medicos = em.get_medicos()
    print(f'7. Get médicos OK - {len(medicos)} médicos: {medicos}')
except Exception as e:
    print(f'7. ERRO ao buscar médicos: {e}')
    import traceback; traceback.print_exc()

# Test 8: Try get_horarios
try:
    horarios = em.get_horarios('dr_joao', 'seg', 'manha')
    print(f'8. Get horários OK - {len(horarios)} horários')
except Exception as e:
    print(f'8. ERRO ao buscar horários: {e}')
    import traceback; traceback.print_exc()

# Test 9: caminho_planilha
try:
    from caminho_planilha import salvar_caminho, carregar_caminho
    salvar_caminho(os.path.abspath(caminho))
    loaded = carregar_caminho()
    print(f'9. Caminho planilha OK - salvo/carregado: {loaded}')
except Exception as e:
    print(f'9. ERRO caminho planilha: {e}')
    import traceback; traceback.print_exc()

# Test 10: Test with None caminho (like when no path saved)
try:
    em2 = ExcelManager(caminho=None)
    print(f'10. ExcelManager(None) OK - caminho: {em2.caminho}')
except Exception as e:
    print(f'10. ERRO ExcelManager(None): {e}')
    import traceback; traceback.print_exc()

# Cleanup
for f in ['test_diag2.xlsx', 'caminho_planilha.json']:
    if os.path.exists(f):
        os.remove(f)

if os.path.exists('agenda_esf.xlsx') and os.path.getsize('agenda_esf.xlsx') < 100:
    # only remove if it was just created by test 10
    pass

print('\nTestes concluídos!')
