import unittest
from development_durations import measure_rows


def row(index, start, end, minutes):
    return dict(table=1, row=index, start=start, end=end, minutes=minutes)


class ReviewMinutesTests(unittest.TestCase):
    def test_review_counts_but_long_break_does_not(self):
        result = measure_rows([row(2,'12:25','12:29',4), row(3,'12:32','12:40',8), row(4,'14:09','14:16',7)])
        self.assertEqual(result['constituent_minutes'], 19)
        self.assertEqual(result['review_minutes'], 3)
        self.assertEqual(result['recorded_development_minutes'], 22)

    def test_exact_threshold_is_break_and_backward_clock_is_not_added(self):
        result = measure_rows([row(2,'12:00','12:01',1), row(3,'12:46','12:47',1), row(4,'09:00','09:02',2)])
        self.assertEqual(result['recorded_development_minutes'], 4)
        self.assertEqual(result['review_intervals'][-1]['classification'], 'session boundary')

    def test_invalid_clock_row_cannot_create_overlapping_review(self):
        with self.assertRaisesRegex(ValueError, 'clarification required'):
            measure_rows([row(34,'20:16','20:18',2), row(35,'20:21','20:02',0), row(36,'20:13','20:14',1)])


if __name__ == '__main__':
    unittest.main()
