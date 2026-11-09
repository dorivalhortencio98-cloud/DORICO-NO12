"""Lista equipes de uma competição disponível na Football-Data.org."""
import argparse
from futebol200.provider import get, APIError


def main():
    parser = argparse.ArgumentParser(description='Listar IDs de times')
    parser.add_argument('--competition', default='BSA')
    args = parser.parse_args()
    try:
        data = get(f'/competitions/{args.competition}/teams')
        teams = sorted(data.get('teams', []), key=lambda t: t.get('name', ''))
        if not teams:
            print('Nenhum time retornado para esta competição/plano.')
            return
        print(f"Competição: {args.competition} | {len(teams)} times")
        print(f"{'ID':<8} TIME")
        for team in teams:
            print(f"{team['id']:<8} {team.get('name', 'Sem nome')}")
    except APIError as exc:
        print(f'ERRO: {exc}')
        raise SystemExit(1)

if __name__ == '__main__':
    main()
