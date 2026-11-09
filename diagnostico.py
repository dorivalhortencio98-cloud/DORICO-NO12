"""Diagnóstico de cobertura de dados sem inventar estatísticas ou odds."""
import argparse
import json
from futebol200.provider import get, APIError
from futebol200.engine import _team_samples, match_probabilities


def main():
    parser = argparse.ArgumentParser(description='Diagnóstico de probabilidades de gols')
    parser.add_argument('--competition', default='BSA')
    parser.add_argument('--home-id', type=int, required=True)
    parser.add_argument('--away-id', type=int, required=True)
    args = parser.parse_args()
    try:
        data = get(f'/competitions/{args.competition}/matches?status=FINISHED')
        matches = data.get('matches', [])
        home = _team_samples(matches, args.home_id, True)[:10]
        away = _team_samples(matches, args.away_id, False)[:10]
        report = {
            'competicao': args.competition,
            'fonte': 'Football-Data.org API v4',
            'partidas_recebidas': len(matches),
            'mandante_jogos_casa': len(home),
            'visitante_jogos_fora': len(away),
            'estatisticas_disponiveis': ['placares finais', 'mandante/visitante'],
            'estatisticas_nao_confirmadas': ['escanteios', 'cartoes', 'finalizacoes', 'desfalques', 'escalacoes', 'eventos ao vivo'],
            'recomendacao': 'NO_RECOMMENDATION',
            'aviso': 'Estimativas exploratorias, sem calibracao; nao constituem recomendacao de aposta.'
        }
        if len(home) >= 5 and len(away) >= 5:
            lam_h = max(.05, (sum(x[1] for x in home)/len(home) + sum(x[2] for x in away)/len(away))/2)
            lam_a = max(.05, (sum(x[1] for x in away)/len(away) + sum(x[2] for x in home)/len(home))/2)
            report['gols_esperados_modelo'] = {'mandante': round(lam_h, 3), 'visitante': round(lam_a, 3)}
            report['probabilidades_modeladas_percentual'] = {
                key: round(value*100, 2) for key, value in match_probabilities(lam_h, lam_a).items()
            }
        else:
            report['motivo'] = 'Amostra insuficiente: exigidos ao menos 5 jogos em casa e 5 fora.'
        print(json.dumps(report, ensure_ascii=False, indent=2))
    except APIError as exc:
        print(f'ERRO: {exc}')
        raise SystemExit(1)

if __name__ == '__main__':
    main()
