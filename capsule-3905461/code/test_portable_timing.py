"""Protect the agreed break boundary, session separation and matched unit."""
import copy, unittest
from portable_timing import minutes, validate

def record(fixed=0, gaps=()):
    return {'fixed_seconds':fixed, 'streams':[{'gap_seconds':list(gaps)}]}

class TimingBoundaries(unittest.TestCase):
    def test_exactly_45_minutes_is_a_break(self):
        self.assertEqual(minutes(record(gaps=[45*60]),45),0)
        self.assertEqual(minutes(record(gaps=[45*60]),60),45)
    def test_short_gap_is_included_in_full(self):
        self.assertEqual(minutes(record(gaps=[44*60]),45),44)
    def test_backward_clock_does_not_add_time(self):
        self.assertEqual(minutes(record(gaps=[-600,120]),45),2)
    def test_fixed_work_is_not_thresholded(self):
        self.assertEqual(minutes(record(fixed=90*60),15),90)
    def test_separate_streams_do_not_gain_an_interstream_gap(self):
        r={'fixed_seconds':0,'streams':[{'gap_seconds':[60]},{'gap_seconds':[120]}]}
        self.assertEqual(minutes(r,45),3)
    def test_duplicate_pair_member_is_rejected(self):
        rows=[dict(record(),run_id=f'{c}_{i:02d}') for c in ['code','model'] for i in range(1,8)]
        validate(rows)
        rows[-1]['run_id']=rows[-2]['run_id']
        with self.assertRaises(ValueError):validate(rows)

if __name__=='__main__':unittest.main()
