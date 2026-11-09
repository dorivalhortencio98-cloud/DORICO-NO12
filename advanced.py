"""Módulos adicionais do FUTEBOL200 PRO.

Recebe dados de provedores AUTORIZADOS em JSON. Não faz scraping nem inventa
estatísticas. Cálculos de contagens são modelos Poisson exploratórios.
"""
from datetime import datetime, timezone
from math import exp, factorial, isfinite
from statistics import mean

MARKETS = {'corners': (6.5, 7.5, 8.5, 9.5, 10.5, 11.5),
           'yellow_cards': (2.5, 3.5, 4.5, 5.5, 6.5),
           'shots': (15.5, 19.5, 23.5, 27.5),
           'shots_on_target': (5.5, 7.5, 9.5, 11.5)}

def _prob_over(lam, threshold):
    n = int(threshold)
    return max(0., min(1., 1 - sum(exp(-lam)*lam**k/factorial(k) for k in range(n+1))))

def _iso(value):
    if not isinstance(value, str):
        raise ValueError('Data UTC ausente')
    d = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if d.tzinfo is None:
        raise ValueError('Data sem fuso horário')
    return d.astimezone(timezone.utc)

def analyze_extra(payload, odds=None, *, now=None, min_samples=8, max_age_minutes=10):
    """Retorna probabilidades estimadas, qualidade e até um candidato, nunca promessa.

    Esquema: source, retrieved_at_utc, mode ('pre'|'live'), history (lista de
    jogos com corners_home/corners_away, yellow_cards_home/away, shots_home/away,
    shots_on_target_home/away), absences, lineups, live. Odds opcionais por chave
    over_corners_8.5 etc. Para ao vivo, apenas diagnostica; sem modelo temporal.
    """
    now = now or datetime.now(timezone.utc)
    result = {'status':'NO_RECOMMENDATION', 'reason':'', 'source':None,
              'mode':None, 'probabilities':{}, 'coverage':{}, 'context':{},
              'candidate':None, 'limitations':[]}
    if not isinstance(payload, dict) or not payload.get('source'):
        result['reason'] = 'Fonte identificada obrigatória.'
        return result
    result['source'] = payload['source']
    mode = payload.get('mode', 'pre')
    result['mode'] = mode
    if mode not in ('pre', 'live'):
        result['reason'] = 'Modo inválido.'
        return result
    try:
        stamp = _iso(payload.get('retrieved_at_utc'))
        age = (now-stamp).total_seconds()/60
    except (ValueError, TypeError):
        result['reason'] = 'Horário da fonte inválido ou ausente.'
        return result
    if age < -2:
        result['reason'] = 'Dados com horário no futuro.'
        return result
    result['context'] = {
        'absences': payload.get('absences'),
        'lineups': payload.get('lineups'),
        'live': payload.get('live') if mode == 'live' else None,
        'retrieved_at_utc':stamp.isoformat(), 'age_minutes':round(age,1)}
    if mode == 'live':
        if age > max_age_minutes:
            result['reason'] = 'Dados ao vivo desatualizados.'
        elif not isinstance(payload.get('live'), dict) or not isinstance(payload['live'].get('minute'), int):
            result['reason'] = 'Minuto e eventos ao vivo ausentes.'
        else:
            result['reason'] = 'Dados ao vivo recebidos; modelo de probabilidades condicionais ao minuto ainda não validado.'
        return result
    history = payload.get('history', [])
    if not isinstance(history, list):
        result['reason'] = 'Histórico inválido.'
        return result
    for kind, lines in MARKETS.items():
        a, b = kind+'_home', kind+'_away'
        values = []
        for item in history:
            if not isinstance(item,dict):
                continue
            x, y = item.get(a), item.get(b)
            if all(isinstance(z,int) and not isinstance(z,bool) and 0 <= z <= 100 for z in (x,y)):
                values.append(x+y)
        result['coverage'][kind] = {'valid_matches':len(values),'required':min_samples}
        if len(values) < min_samples:
            continue
        lam = mean(values)
        for line in lines:
            key = f'over_{kind}_{line}'
            result['probabilities'][key] = round(_prob_over(lam,line),4)
            result['probabilities'][f'under_{kind}_{line}'] = round(1-_prob_over(lam,line),4)
    if payload.get('absences') is None:
        result['limitations'].append('Desfalques não informados pela fonte.')
    if payload.get('lineups') is None:
        result['limitations'].append('Escalações não informadas pela fonte.')
    if not result['probabilities']:
        result['reason'] = 'Sem histórico suficiente de escanteios, cartões ou finalizações.'
        return result
    if not isinstance(odds,dict) or not odds:
        result['reason'] = 'Probabilidades exploratórias calculadas; sem odds verificadas, nenhuma entrada selecionada.'
        return result
    candidates=[]
    for key, prob in result['probabilities'].items():
        if key not in odds:
            continue
        try:
            odd=float(odds[key])
        except (TypeError,ValueError):
            continue
        if not isfinite(odd) or not (1.01 <= odd <= 100):
            continue
        edge = prob - 1/odd
        if prob >= .55 and edge >= .04 and prob*odd-1 > 0:
            candidates.append((prob*odd-1,key,prob,odd))
    if not candidates:
        result['reason'] = 'Nenhuma vantagem matemática suficiente nas odds informadas.'
        return result
    ev,key,prob,odd=max(candidates)
    result['status']='MODEL_CANDIDATE'
    result['candidate']={'market':key,'probability':prob,'offered_odds':odd,
                         'fair_odds':round(1/prob,3),'estimated_ev':round(ev,4)}
    result['reason']='Candidato experimental, não validado nem recomendado para aposta real.'
    result['limitations'].append('Modelo Poisson simples sem ajuste de adversários, árbitro, desfalques ou escalações.')
    return result
