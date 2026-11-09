"""Entradas padronizadas para fontes adicionais autorizadas.

NÃO coleta dados de sites sem API/licença. Não calcula mercados sem dados.
"""
from dataclasses import dataclass

@dataclass
class ExternalStats:
    source: str
    retrieved_at_utc: str
    competition: str
    fixture_id: str
    corners_home: int | None = None
    corners_away: int | None = None
    yellows_home: int | None = None
    yellows_away: int | None = None
    shots_home: int | None = None
    shots_away: int | None = None
    injuries_home: list | None = None
    injuries_away: list | None = None
    lineups_confirmed: bool = False
    live_minute: int | None = None

    def supported(self):
        return {k: getattr(self,k) is not None for k in (
            'corners_home','corners_away','yellows_home','yellows_away',
            'shots_home','shots_away','injuries_home','injuries_away','live_minute')}
