"""Cliente oficial football-data.org v4; chave somente em variável de ambiente."""
import json
import os
import urllib.request
import urllib.error

BASE='https://api.football-data.org/v4'

class APIError(RuntimeError):
    pass

def get(path):
    key=os.environ.get('FOOTBALL_DATA_TOKEN','').strip()
    if not key:
        try:
            import streamlit as st
            key=str(st.secrets.get('FOOTBALL_DATA_TOKEN','')).strip()
        except Exception:
            pass
    if not key:
        raise APIError('Defina FOOTBALL_DATA_TOKEN no ambiente. Não inclua a chave no código.')
    if not path.startswith('/') or '://' in path:
        raise ValueError('Caminho inválido')
    req=urllib.request.Request(BASE+path,headers={'X-Auth-Token':key,'Accept':'application/json'})
    try:
        with urllib.request.urlopen(req,timeout=20) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        raise APIError(f'API retornou HTTP {exc.code}; confira plano, limite e permissões.') from None
    except urllib.error.URLError as exc:
        raise APIError(f'Falha de conexão: {exc.reason}') from None
