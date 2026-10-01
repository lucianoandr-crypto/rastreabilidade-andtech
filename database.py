import psycopg2
import datetime

CRIPTO_MAP = {
    '1': 'L', '2': 'U', '3': 'C', '4': 'I', '5': 'A', 
    '6': 'N', '7': 'O', '8': 'P', '9': 'H', '0': 'D'
}

def criptografar_str(texto_numerico):
    return "".join(CRIPTO_MAP[digito] for digito in texto_numerico)

def obter_semana_mes(data):
    primeiro_dia = data.replace(day=1)
    dia_ajustado = data.day + primeiro_dia.weekday()
    return int((dia_ajustado - 1) / 7) + 1

def conectar_banco():
    """
    Conecta diretamente ao banco de dados PostgreSQL na nuvem do Neon.
    """
    # Linha de conexão oficial da ANDTECH para o cluster Neon na nuvem
    DATABASE_URL = "postgresql://neondb_owner:npg_yx3h6ofrpDjL@ep-red-art-b4okq8qs-pooler.c-6.us-east-2.aws.neon.tech/neondb?sslmode=require"
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        print(f"❌ Erro ao conectar ao Neon: {e}")
        return None

def buscar_proximo_sequencial(cursor, iniciais_modelo, ano_cripto, mes_cripto, week_cripto):
    padrao = f"{iniciais_modelo}{ano_cripto}{mes_cripto}{week_cripto}%"
    cursor.execute("SELECT serial FROM produtos WHERE serial LIKE %s", (padrao,))
    existentes = []
    for r in cursor.fetchall():
        serial_texto = r[0] 
        ultimos_dois = serial_texto[-2:]
        if ultimos_dois.isdigit(): 
            existentes.append(int(ultimos_dois))
    return max(existentes) + 1 if existentes else 1
