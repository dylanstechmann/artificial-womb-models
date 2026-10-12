import hashlib
import json
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/"artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle303"
DATA=ROOT/"config/observations/eixarch_2026_ep09_20_il6_candidate.json"
class EixarchEP0920IL6Cycle303Tests(unittest.TestCase):
 def test_pinned_primary_poster_and_crossref_hashes(self):
  a=json.loads((ART/"il6-intake-and-linkage-cycle303.json").read_text(encoding="utf-8"))
  self.assertEqual(hashlib.sha256((ART/"ep09-20-poster-source.pdf").read_bytes()).hexdigest(),a["source"]["poster_sha256"])
  self.assertEqual(hashlib.sha256((ART/"crossref-ep09-20.json").read_bytes()).hexdigest(),a["source"]["crossref_sha256"])
  self.assertEqual(a["source"]["crossref_relation"],{})
 def test_group_counts_and_sampling_schedule_are_source_scoped(self):
  a=json.loads((ART/"il6-intake-and-linkage-cycle303.json").read_text(encoding="utf-8"))
  i=a["intake"]
  self.assertEqual(i["reported_study_n"],20)
  self.assertEqual(i["coating_group_counts"],{"albumin_heparin":6,"albumin_based":7,"PMEA":7})
  self.assertEqual(i["group_count_sum"],20)
  self.assertEqual(i["sample_times_hours"],[0,6,24,48,72,144])
  self.assertEqual(i["per_timepoint_n"],"not reported")
 def test_plot_values_are_qualitative_and_raw_denominators_remain_missing(self):
  d=json.loads(DATA.read_text(encoding="utf-8"))
  self.assertEqual(len(d["observations"]),5)
  self.assertTrue(all(isinstance(o["observation"]["value"],str) for o in d["observations"]))
  self.assertTrue(all("not printed" in o["observation"].get("measurement_uncertainty","") for o in d["observations"][:3]))
  self.assertTrue(any("nonuniform" in item for item in d["limitations"]))
  self.assertEqual([x["denominator"]["value"] for x in d["cohort_coverage"]],[20,6,7,7])
 def test_overlap_is_possible_but_does_not_license_pooling(self):
  a=json.loads((ART/"il6-intake-and-linkage-cycle303.json").read_text(encoding="utf-8"))
  x=a["cross_poster_compatibility"]
  self.assertEqual(x["EP09_31"]["relationship"],"Possible overlap/subset with EP09.20 n=20; no shared IDs or experiment dates.")
  self.assertTrue(x["EP09_22"]["compatibility_if_same_cohort"]["all_GA_within_EP09_20_range"])
  self.assertTrue(x["EP09_22"]["compatibility_if_same_cohort"]["all_support_durations_meet_EP09_20_6_day_criterion"])
  self.assertFalse(x["counts_may_be_summed"])
  self.assertFalse(x["independent_replication_established"])
 def test_candidate_intake_validation_receipt(self):
  a=json.loads((ART/"il6-intake-and-linkage-cycle303.json").read_text(encoding="utf-8"))
  r=json.loads((ART/"validate-ep09-20/receipt.json").read_text(encoding="utf-8"))
  self.assertEqual(a["candidate_intake"]["validation_input_sha256"],r["input_sha256"])
  self.assertEqual(a["candidate_intake"]["validation_status"],"passed; local poster hash verified")
if __name__=="__main__":unittest.main()
