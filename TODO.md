# TODO - Horários próprios para Modalidades + Encaixe Manual

## Etapas

### 1. `config_manager.py` - Método para buscar horários de modalidades
- [x] Adicionar `get_horarios_modalidade(modalidade, dia_semana, turno)` 
- [x] Adicionar `salvar_horario_modalidade(modalidade, dia_semana, turno, horarios_str)`

### 2. `tela_config.py` - Aba "Horários Especiais" para configurar horários das modalidades
- [x] Adicionar aba no Tabview com campos editáveis para cada modalidade
- [x] Domiciliar (Qui Manhã), GERCON (Qua Manhã), Criança (Qua Tarde), Gestante (Ter Manhã)
- [x] Salvar alterações no botão "SALVAR TUDO"

### 3. `tela_agendamento.py` - Encaixe com hora manual
- [x] No passo 4 (horário), quando `modo_encaixe=True`: mostrar campo de texto para digitar hora
- [x] Botões de sugestão: manhã (10:40, 11:00, 11:20, 11:40) / tarde (15:40, 16:00, 16:20, 16:40)
- [x] Não verificar conflitos - encaixe é independente
- [x] Validar formato HH:MM

### 4. `tela_agendamento.py` - Modalidades especiais usam horários próprios
- [x] `_contar_horarios_disponiveis`: usar `excel.get_horarios_modalidade()` para especiais
- [x] `_carregar_horarios_disponiveis`: mesma lógica
- [x] Só considerar como ocupados horários da mesma modalidade
- [x] `_renderizar_calendario_mes`: usar horários da modalidade para contar vagas

