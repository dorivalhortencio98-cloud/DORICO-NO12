import unittest
from futebol200.engine import analyze,match_probabilities

class EngineTests(unittest.TestCase):
    def test_probs(self):
        p=match_probabilities(1.5,1.0)
        self.assertAlmostEqual(p['home_win']+p['draw']+p['away_win'],1,places=6)
        self.assertAlmostEqual(p['over_2.5']+p['under_2.5'],1,places=6)
    def test_no_data(self):
        a=analyze([],1,2,{'over_1.5':2.0})
        self.assertEqual(a.status,'NO_RECOMMENDATION')
    def test_no_odds(self):
        matches=[]
        for i in range(6):
            matches.append({'status':'FINISHED','utcDate':f'2026-10-{i+1:02d}',
                'homeTeam':{'id':1},'awayTeam':{'id':2},
                'score':{'fullTime':{'home':2,'away':1}}})
        a=analyze(matches,1,2)
        self.assertEqual(a.status,'NO_RECOMMENDATION')

if __name__=='__main__': unittest.main()
