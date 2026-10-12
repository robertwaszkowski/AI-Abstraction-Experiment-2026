import unittest,zipfile
from pathlib import Path
from tempfile import TemporaryDirectory
import calculate_metrics as cm

class DurationSummaryTests(unittest.TestCase):
    def test_total_row_does_not_duplicate_constituents(self):
        ns='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
        def row(*cells):
            return '<w:tr>'+''.join('<w:tc><w:p><w:r><w:t>'+x+'</w:t></w:r></w:p></w:tc>' for x in cells)+'</w:tr>'
        xml='<w:document xmlns:w="'+ns+'"><w:body><w:tbl>'+row('12:25','12:29','4 min')+row('12:32','12:40','8 min')+row('SUMA','','12 min')+'</w:tbl></w:body></w:document>'
        with TemporaryDirectory() as tmp:
            p=Path(tmp)/'table.docx'
            with zipfile.ZipFile(p,'w') as z:z.writestr('word/document.xml',xml)
            self.assertEqual(cm.constituent_docx_durations(p),[4,8])
            # This repair does not silently redefine the event-count outcome.
            self.assertEqual(sum(bool(cm.DURATION_ROW.fullmatch(x)) for x in cm.docx_lines(p)),3)
            spec = cm.ExperimentSpec('code_02','T02',2,'Model -> Code',2,'Code',True,
                                     'test','duration_rows',None,'duration_rows')
            minutes, events, _, _ = cm.measure_prompts(spec, Path(tmp), 45)
            self.assertEqual(minutes, 15)  # 4 + 3 review + 8; summary is not added.
            self.assertEqual(events, 3)  # Established source-specific event count.

    def test_decimal_minutes_and_zero_duration_are_preserved(self):
        ns='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
        xml='<w:document xmlns:w="'+ns+'"><w:body>'+''.join('<w:p><w:r><w:t>'+x+'</w:t></w:r></w:p>' for x in ['1,5 min','0 min','2.25 minutes'])+'</w:body></w:document>'
        with TemporaryDirectory() as tmp:
            p=Path(tmp)/'durations.docx'
            with zipfile.ZipFile(p,'w') as z:z.writestr('word/document.xml',xml)
            self.assertEqual(cm.constituent_docx_durations(p),[1.5,0,2.25])

if __name__=='__main__':unittest.main()
