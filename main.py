"""CLI de diagnóstico e análise; sem interface gráfica."""
import argparse
import json
from futebol200.provider import get,APIError
from futebol200.engine import analyze

def main():
    p=argparse.ArgumentParser(description='FUTEBOL200 PRO - motor técnico')
    p.add_argument('--competition',default='BSA',help='Código da competição (ex.: BSA, PL)')
    p.add_argument('--home-id',type=int,required=True)
    p.add_argument('--away-id',type=int,required=True)
    p.add_argument('--odds-file',help='JSON com odds verificadas por mercado')
    args=p.parse_args()
    odds=None
    if args.odds_file:
        with open(args.odds_file,encoding='utf-8') as f:
            odds=json.load(f)
    try:
        data=get(f'/competitions/{args.competition}/matches?status=FINISHED')
        result=analyze(data.get('matches',[]),args.home_id,args.away_id,odds)
        print(json.dumps(result.json(),ensure_ascii=False,indent=2))
    except (APIError,ValueError) as exc:
        print('ERRO:',exc)
        raise SystemExit(1)

if __name__=='__main__':
    main()
