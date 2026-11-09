import unittest
from datetime import datetime, timezone, timedelta
from futebol200.advanced import analyze_extra

NOW=datetime(2026,11,8,tzinfo=timezone.utc)
def base(**kw):
    d={'source':'provedor-autorizado','retrieved_at_utc':NOW.isoformat(),
       'history':[{'corners_home':5,'corners_away':5,'yellow_cards_home':2,
                   'yellow_cards_away':3,'shots_home':12,'shots_away':10,
                   'shots_on_target_home':5,'shots_on_target_away':3} for _ in range(10)]}
    d.update(kw)
    return d

class AdvancedTests(unittest.TestCase):
    def test_calculates_all_four_categories(self):
        r=analyze_extra(base(),now=NOW)
        self.assertEqual(r['status'],'NO_RECOMMENDATION')
        for name in ('corners','yellow_cards','shots','shots_on_target'):
            self.assertIn('over_'+name+'_'+str({'corners':8.5,'yellow_cards':3.5,'shots':19.5,'shots_on_target':7.5}[name]),r['probabilities'])
    def test_missing_history_abstains(self):
        self.assertEqual(analyze_extra(base(history=[]),now=NOW)['status'],'NO_RECOMMENDATION')
    def test_live_stale_abstains(self):
        r=analyze_extra(base(mode='live',live={'minute':30},retrieved_at_utc=(NOW-timedelta(minutes=20)).isoformat()),now=NOW)
        self.assertIn('desatualizados',r['reason'])
    def test_live_current_still_abstains(self):
        r=analyze_extra(base(mode='live',live={'minute':30}),now=NOW)
        self.assertEqual(r['status'],'NO_RECOMMENDATION')
    def test_rejects_fake_negative_stats(self):
        r=analyze_extra(base(history=[{'corners_home':-1,'corners_away':4}]*10),now=NOW)
        self.assertEqual(r['coverage']['corners']['valid_matches'],0)
    def test_candidate_not_final_recommendation(self):
        r=analyze_extra(base(),{'over_corners_8.5':2.0},now=NOW)
        self.assertEqual(r['status'],'MODEL_CANDIDATE')

if __name__=='__main__': unittest.main()
