from pathlib import Path
import csv
import json
import math
import statistics
import tempfile
import unittest
from collections import defaultdict

from wombmodels.observations import observation_report, validate_dataset

ROOT=Path(__file__).resolve().parents[1]
DATASET=ROOT/'config/observations/peers_2024_iugr_table2_pilot_candidate.json'
INVENTORY=ROOT/'config/source_inventories/fetal_ovine_support_transition_2023_2026.json'
SUMMARY=ROOT/'config/source_inventories/peers_2024_iugr_table2_pilot_reconstruction.csv'

class Peers2024IugrPilotCandidateTests(unittest.TestCase):
    def setUp(self):
        self.dataset=json.loads(DATASET.read_text(encoding='utf-8'))
        self.validated=validate_dataset(self.dataset)

    def test_candidate_keeps_three_pilot_animals_separate_and_transcribes_ten_fields(self):
        by_animal=defaultdict(dict)
        for row in self.validated['observations']:
            by_animal[row['independent_unit']['id']][row['assay']['endpoint']]=row['observation']['value']
        self.assertEqual(len(self.validated['observations']),30)
        self.assertEqual(set(by_animal),{'IUGR Animal 1','IUGR Animal 2','IUGR Animal 3'})
        self.assertEqual({len(fields) for fields in by_animal.values()},{10})
        self.assertEqual([by_animal[f'IUGR Animal {n}']['Length of the run on EXTEND'] for n in range(1,4)],[23,8,11])
        self.assertEqual([by_animal[f'IUGR Animal {n}']['Weight at cannulation'] for n in range(1,4)],[0.75,0.81,0.72])
        self.assertEqual([by_animal[f'IUGR Animal {n}']['Number of transfusions during EXTEND support'] for n in range(1,4)],[0,0,2])
        self.assertTrue(all(row['independent_unit']['parent_id']=='peers_2024_iugr_extend_pilot'
                            for row in self.validated['observations']))
        self.assertFalse(any('Brain weight' in endpoint or 'MRI' in endpoint or 'histology' in endpoint
                             for fields in by_animal.values() for endpoint in fields))

    def test_seven_numeric_group_summaries_recompute_from_source_rows(self):
        with SUMMARY.open(newline='',encoding='utf-8') as stream:
            checks=list(csv.DictReader(stream))
        self.assertEqual(len(checks),7)
        endpoint_map={
          'Age at cannulation (days)':'Age at cannulation',
          'Weight at cannulation (kg)':'Weight at cannulation',
          'Age at necropsy (days)':'Age at necropsy',
          'Weight at necropsy (kg)':'Weight at necropsy',
          'Length of the run (days)':'Length of the run on EXTEND',
          'Growth rate(g/kg/J)':'Growth rate(g/kg/J)',
          'Number of transfusions':'Number of transfusions during EXTEND support'
        }
        for check in checks:
            values=[r['observation']['value'] for r in self.validated['observations']
                    if r['assay']['endpoint']==endpoint_map[check['source_table_row']]]
            self.assertEqual(len(values),int(check['n']))
            self.assertAlmostEqual(statistics.mean(values),float(check['reconstructed_mean_from_displayed_rows']),places=6)
            self.assertAlmostEqual(statistics.stdev(values)/math.sqrt(len(values)),float(check['reconstructed_sem_from_displayed_rows']),places=6)
            self.assertEqual(check['sem_check_status'],'reproduced_to_published_precision')

    def test_table1_pilot_exclusion_and_inventory_link_are_preserved(self):
        self.assertIn('explicitly excluded from the paper',' '.join(self.dataset['limitations']))
        self.assertIn('included for interest',self.validated['cohort_coverage'][0]['selection_definition'])
        inventory=json.loads(INVENTORY.read_text(encoding='utf-8'))
        record=next(r for r in inventory['records'] if r['record_id']=='peers_2024_extend_outcomes')
        self.assertEqual(record['iugr_pilot_intake']['record_count'],30)
        self.assertEqual(record['iugr_pilot_intake']['status'],'separate_candidate_source_table_transcription')

    def test_csv_export_preserves_source_labeled_pilot_rows(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'intake'
            observation_report(DATASET,output)
            with (output/'observation_records.csv').open(newline='',encoding='utf-8') as stream:
                rows=list(csv.DictReader(stream))
        self.assertEqual(len(rows),30)
        self.assertEqual({row['independent_unit_id'] for row in rows},{'IUGR Animal 1','IUGR Animal 2','IUGR Animal 3'})

if __name__=='__main__':
    unittest.main()
