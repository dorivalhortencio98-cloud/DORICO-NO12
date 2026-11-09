"""Entrada de dados adicionais em arquivo JSON; sem chaves de API."""
import argparse
import json
from futebol200.advanced import analyze_extra

p = argparse.ArgumentParser()
p.add_argument('--stats-file', required=True)
p.add_argument('--odds-file')
args = p.parse_args()
with open(args.stats_file, encoding='utf-8') as f:
    stats=json.load(f)
odds=None
if args.odds_file:
    with open(args.odds_file, encoding='utf-8') as f:
        odds=json.load(f)
print(json.dumps(analyze_extra(stats, odds), ensure_ascii=False, indent=2))
