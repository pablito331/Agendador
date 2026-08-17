"""
utils.py - Funções auxiliares para o ESF Gerenciador de Agenda
"""
import unicodedata
import re
from datetime import datetime
from typing import Optional

# Cache de normalização para performance
_normalize_cache = {}

def now() -> datetime:
    """Retorna datetime atual com timezone local"""
    return datetime.now().replace(microsecond=0)

def timestamp_str(dt: Optional[datetime] = None) -> str:
    """Formata datetime para string ISO: 2024-01-15 14:30:00"""
    dt = dt or now()
    return dt.strftime("%Y-%m-%d %H:%M:%S")

def date_str(dt: Optional[datetime] = None) -> str:
    """Formata data: 2024-01-15"""
    dt = dt or now()
    return dt.strftime("%Y-%m-%d")

def time_str(dt: Optional[datetime] = None) -> str:
    """Formata hora: 14:30"""
    dt = dt or now()
    return dt.strftime("%H:%M")

def date_br(dt: Optional[datetime] = None) -> str:
    """Formata data brasileira: 15/01/2024"""
    dt = dt or now()
    return dt.strftime("%d/%m/%Y")

def normalize_text(text: str) -> str:
    """
    Remove acentos, converte para minúsculas, remove pontuação.
    Usa cache para performance em buscas repetitivas.
    Exemplo: "João Silva" -> "joao silva"
    """
    if not text:
        return ""
    
    key = text
    if key in _normalize_cache:
        return _normalize_cache[key]
    
    # Remove acentos
    nfkd = unicodedata.normalize('NFKD', str(text))
    text_ascii = nfkd.encode('ASCII', 'ignore').decode('ASCII')
    
    # Remove caracteres especiais mantendo letras, números e espaços
    text_clean = re.sub(r'[^\w\s]', ' ', text_ascii)
    
    # Múltiplos espaços -> um espaço
    text_clean = re.sub(r'\s+', ' ', text_clean)
    
    # Lowercase e trim
    result = text_clean.strip().lower()
    
    _normalize_cache[key] = result
    return result

def search_match(term: str, text: str) -> bool:
    """
    Verifica se term está contido em text (busca parcial, sem acentos, case-insensitive)
    """
    if not term or not text:
        return False
    term_norm = normalize_text(term)
    text_norm = normalize_text(text)
    return term_norm in text_norm

def validate_required(value, field_name: str) -> Optional[str]:
    """Valida campo obrigatório. Retorna None se OK, ou mensagem de erro."""
    if not value or not str(value).strip():
        return f"{field_name} é obrigatório"
    return None

def validate_time(hour_str: str) -> bool:
    """Valida formato HH:MM"""
    if not re.match(r'^\d{2}:\d{2}$', hour_str):
        return False
    try:
        h, m = map(int, hour_str.split(':'))
        return 0 <= h <= 23 and 0 <= m <= 59
    except:
        return False

def get_weekday_name(date_obj: datetime) -> str:
    """Retorna nome do dia da semana em português"""
    dias = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 
            'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']
    return dias[date_obj.weekday()]

def get_modalidade_rules() -> dict:
    """
    Regras fixas das modalidades conforme especificação.
    Retorna dict: {tipo: {dia_semana: int, turno: str}}
    """
    return {
        'Domiciliar': {'weekday': 3, 'turno': 'manha'},    # Quinta
        'GERCON': {'weekday': 2, 'turno': 'manha'},         # Quarta
        'Criança': {'weekday': 2, 'turno': 'tarde'},        # Quarta
        'Gestante': {'weekday': 1, 'turno': 'manha'},       # Terça
    }

MODALIDADES_SEM_REGRA = ['Normal']  # Essas usam seleção livre

def clear_normalize_cache():
    """Limpa o cache de normalização (útil em testes)"""
    _normalize_cache.clear()

