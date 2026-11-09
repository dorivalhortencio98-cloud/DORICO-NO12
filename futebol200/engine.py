"""Cálculos pré-jogo. Não confundir probabilidades modeladas com certezas."""
import math
from dataclasses import dataclass, asdict

@dataclass
class Analysis:
    status: str
    market: str | None
    probability: float | None
    fair_odds: float | None
    offered_odds: float | None
    expected_value: float | None
    reason: str
    sample_home: int
    sample_away: int
    model: str = 'Poisson independente (aproximação)'

    def json(self):
        return asdict(self)


def poisson(k, lam):
    return math.exp(-lam) * lam**k / math.factorial(k)


def match_probabilities(home_goals, away_goals, max_goals=12):
    # Tail mass is folded into the last bucket for normalization.
    h = [poisson(k, home_goals) for k in range(max_goals)]
    a = [poisson(k, away_goals) for k in range(max_goals)]
    h.append(max(0.0, 1 - sum(h)))
    a.append(max(0.0, 1 - sum(a)))
    cells = [(i, j, h[i]*a[j]) for i in range(len(h)) for j in range(len(a))]
    p_home = sum(p for i,j,p in cells if i>j)
    p_draw = sum(p for i,j,p in cells if i==j)
    p_away = sum(p for i,j,p in cells if i<j)
    p_btts = (1-math.exp(-home_goals))*(1-math.exp(-away_goals))
    total = home_goals + away_goals
    output = {'home_win':p_home, 'draw':p_draw, 'away_win':p_away,
              'double_chance_1x':p_home+p_draw, 'double_chance_x2':p_draw+p_away,
              'btts_yes':p_btts, 'btts_no':1-p_btts}
    for threshold in (0.5,1.5,2.5,3.5,4.5):
        n = int(threshold)
        under = sum(poisson(k,total) for k in range(n+1))
        output[f'over_{threshold}'] = 1-under
        output[f'under_{threshold}'] = under
    return output


def _team_samples(matches, team_id, home):
    out=[]
    for m in matches:
        if m.get('status') != 'FINISHED':
            continue
        ht, at = m.get('homeTeam') or {}, m.get('awayTeam') or {}
        score=(m.get('score') or {}).get('fullTime') or {}
        hg, ag=score.get('home'),score.get('away')
        if not isinstance(hg,int) or not isinstance(ag,int):
            continue
        if home and ht.get('id')==team_id:
            out.append((m.get('utcDate',''),hg,ag))
        if not home and at.get('id')==team_id:
            out.append((m.get('utcDate',''),ag,hg))
    return sorted(out,reverse=True)


def analyze(matches, home_id, away_id, odds=None, min_samples=5, recent=10,
            minimum_edge=0.04, minimum_probability=0.55):
    """Use only finished games, with home/away splits; abstain without odds."""
    home=_team_samples(matches,home_id,True)[:recent]
    away=_team_samples(matches,away_id,False)[:recent]
    if len(home)<min_samples or len(away)<min_samples:
        return Analysis('NO_RECOMMENDATION',None,None,None,None,None,
                        'Histórico insuficiente de jogos em casa/fora.',len(home),len(away))
    if not odds:
        return Analysis('NO_RECOMMENDATION',None,None,None,None,None,
                        'Sem odds verificadas: não é possível avaliar vantagem.',len(home),len(away))
    ha=sum(x[1] for x in home)/len(home)
    hd=sum(x[2] for x in home)/len(home)
    aa=sum(x[1] for x in away)/len(away)
    ad=sum(x[2] for x in away)/len(away)
    lam_h=max(.05,(ha+ad)/2)
    lam_a=max(.05,(aa+hd)/2)
    probabilities=match_probabilities(lam_h,lam_a)
    candidates=[]
    for market, raw_odd in odds.items():
        if market not in probabilities:
            continue
        try:
            odd=float(raw_odd)
        except (TypeError,ValueError):
            continue
        if not (1.01 <= odd <= 100):
            continue
        p=probabilities[market]
        edge=p-1/odd
        ev=p*odd-1
        if p>=minimum_probability and edge>=minimum_edge and ev>0:
            candidates.append((ev,market,p,odd))
    if not candidates:
        return Analysis('NO_RECOMMENDATION',None,None,None,None,None,
                        'Nenhum mercado com vantagem estimada suficiente.',len(home),len(away))
    ev,market,p,odd=max(candidates)
    return Analysis('MODEL_CANDIDATE',market,round(p,4),round(1/p,3),odd,round(ev,4),
                    'Candidato matemático; requer validação das odds, qualidade dos dados e calibração do modelo.',
                    len(home),len(away))
