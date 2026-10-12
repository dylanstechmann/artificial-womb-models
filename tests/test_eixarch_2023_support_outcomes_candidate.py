import hashlib
import hashlib
import json
import unittest
from pathlib import Path

from wombmodels.observations import validate_dataset


ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "config/observations/eixarch_2023_support_outcomes_candidate.json"
INVENTORY = ROOT / "config/source_inventories/fetal_ovine_support_transition_2023_2026.json"


class Eixarch2023SupportOutcomesCandidateTests(unittest.TestCase):
    def setUp(self):
        self.dataset = json.loads(DATASET.read_text(encoding="utf-8"))
        self.validated = validate_dataset(self.dataset)

    def test_official_pmc_source_pin_and_bounded_supplement_screen(self):
        artifact = self.dataset["artifacts"][0]
        local_path = ROOT / artifact["local_path"]
        digest = hashlib.sha256(local_path.read_bytes()).hexdigest()
        self.assertEqual(digest, artifact["sha256"])
        self.assertTrue(all(row["source"]["sha256"] == digest
                            for row in self.dataset["observations"]))
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        source_record = next(item for item in inventory["records"]
                             if item["record_id"] == "eixarch_2023_entry_learning_curve")
        screen = source_record["primary_source_route_check_cycle286"]
        self.assertEqual(screen["supplementary_material_elements_in_efetch_xml"], 0)
        self.assertEqual(screen["associated_data_statement"], "Not applicable (PMC Associated Data section).")
        self.assertIn("does not establish global data absence", screen["interpretation_limit"])
        self.assertEqual(len(self.validated["observations"]), 50)

    def test_publisher_pdf_hash_and_visual_decision_keep_values_unchanged(self):
        pdf_artifact = next(item for item in self.dataset["artifacts"]
                            if item["artifact_id"] == "eixarch2023-publisher-pdf")
        pdf_path = ROOT / pdf_artifact["local_path"]
        self.assertEqual(hashlib.sha256(pdf_path.read_bytes()).hexdigest(), pdf_artifact["sha256"])
        assessment = json.loads((ROOT / "artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle287/figure3-visual-assessment-cycle287.json").read_text(encoding="utf-8"))
        self.assertEqual(assessment["candidate_counts_unchanged"]["observations"], 50)
        self.assertIn("Do not transcribe", assessment["intake_decision"])
        self.assertEqual(len(self.validated["observations"]), 50)

    def test_cycle288_complication_denominator_remains_arithmetic_only(self):
        audit = json.loads((ROOT / "artifacts/eixarch-2023-group-outcomes-2026-10-11-cycle288/table1-complication-denominator-audit-cycle288.json").read_text(encoding="utf-8"))
        self.assertEqual(audit["rows"][0]["implied_denominator_approx"], 6.993)
        self.assertEqual(audit["rows"][1]["implied_denominator_approx"], 7.0053)
        self.assertIn("does not define", audit["arithmetic_conclusion"])
        self.assertFalse(audit["candidate_effect"]["new_observations"])
        self.assertEqual(len(self.validated["observations"]), 50)

    def test_six_group_summary_rates_validate_without_individual_ids(self):
        self.assertEqual(len(self.validated["observations"]), 50)
        self.assertEqual(len(self.validated["cohort_coverage"]), 3)

        expected = {
            "eixarch2023-goal-1-3h-attainment": (25, "Experiments reaching their assigned survival goal"),
            "eixarch2023-goal-1-3h-cannulation-complications": (75, "Cannulation complications"),
            "eixarch2023-goal-4-24h-attainment": (70, "Experiments reaching their assigned survival goal"),
            "eixarch2023-goal-4-24h-cannulation-complications": (50, "Cannulation complications"),
            "eixarch2023-goal-48-168h-attainment": (80, "Experiments reaching their assigned survival goal"),
            "eixarch2023-goal-48-168h-cannulation-complications": (0, "Cannulation complications"),
        }
        expected_endpoints = {endpoint for _, endpoint in expected.values()}
        rate_records = [record for record in self.validated["observations"]
                        if record["assay"]["endpoint"] in expected_endpoints]
        self.assertEqual(len(rate_records), 6)
        for record in rate_records:
            with self.subTest(record_id=record["record_id"]):
                value, endpoint = expected[record["record_id"]]
                self.assertEqual(record["observation"]["value"], value)
                self.assertEqual(record["assay"]["endpoint"], endpoint)
                self.assertEqual(record["evidence_status"], "author_reported_summary")
                self.assertEqual(record["observation"]["replicate_role"], "summary_only")
                self.assertIsNone(record["independent_unit"]["id"])
                self.assertIsNone(record["observation"]["measurement_time"])
                self.assertIn("Abstract", record["source_locator"])

        self.assertFalse(self.validated.get("transitions"))
        self.assertTrue(any("not an 80% seven-day survival rate" in item
                            for item in self.validated["limitations"]))

    def test_table_one_complication_cells_crosscheck_abstract_rates_without_duplicates(self):
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        source_record = next(item for item in inventory["records"]
                             if item["record_id"] == "eixarch_2023_entry_learning_curve")
        transition = next(item for item in source_record["transition_events"]
                          if item["type"] == "entry_to_support")
        crosscheck = transition["cannulation_complications_table_1_crosscheck"]

        self.assertEqual(crosscheck["abstract_label"], "Cannulation complications")
        self.assertEqual(crosscheck["table_1_label"], "Complications surgical procedure")
        self.assertIn("not a duplicate observation", crosscheck["interpretation_limit"])
        self.assertIn("does not prove identical complication coding",
                      crosscheck["interpretation_limit"])
        self.assertEqual(len(crosscheck["groups"]), 3)
        for group in crosscheck["groups"]:
            with self.subTest(goal=group["goal_interval_hours"]):
                self.assertEqual(group["percent_from_table_count_and_group_n"],
                                 group["table_1_count"] / group["group_n"] * 100)
                self.assertEqual(group["abstract_reported_percent"],
                                 group["percent_from_table_count_and_group_n"])
                self.assertTrue(group["arithmetic_match"])
                rate_record_id = (f"eixarch2023-goal-{group['goal_interval_hours']['min']}-"
                                  f"{group['goal_interval_hours']['max']}h-cannulation-complications")
                rate_record = next(record for record in self.validated["observations"]
                                   if record["record_id"] == rate_record_id)
                self.assertEqual(rate_record["observation"]["value"],
                                 group["abstract_reported_percent"])
        self.assertEqual(len(self.validated["observations"]), 50)
        self.assertEqual(sum(record["assay"]["endpoint"] == "Cannulation complications"
                             for record in self.validated["observations"]), 3)

    def test_specific_complication_cells_preserve_denominator_mismatch_and_dashes(self):
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        source_record = next(item for item in inventory["records"]
                             if item["record_id"] == "eixarch_2023_entry_learning_curve")
        transition = next(item for item in source_record["transition_events"]
                          if item["type"] == "entry_to_support")
        reconciliation = transition["table_1_specific_complication_cell_reconciliation"]

        expected = {
            "Bubbles in the circuit": ["2 (25%)", "1 (14.3%)", "-"],
            "Vasospasm": ["-", "4 (57.1%)", "-"],
            "Decannulation": ["3 (37.5%)", "-", "-"],
            "Vessel lesion": ["1 (12.5%)", "-", "-"],
        }
        self.assertEqual(reconciliation["group_sizes"], [8, 10, 10])
        self.assertEqual(reconciliation["row_assessment_denominators"], "not separately reported")
        self.assertIn("Neither gives row-specific denominators", reconciliation["source_context"])
        self.assertIn("do not substitute group-n percentages", reconciliation["interpretation_limit"])
        self.assertEqual(len(reconciliation["table_rows"]), 4)
        mismatch_cells = []
        for row in reconciliation["table_rows"]:
            with self.subTest(source_label=row["source_label"]):
                self.assertEqual([cell["printed_cell"] for cell in row["cells_by_group"]],
                                 expected[row["source_label"]])
                for cell in row["cells_by_group"]:
                    if cell["printed_cell"] == "-":
                        self.assertIsNone(cell["count"])
                        self.assertIsNone(cell["printed_percent"])
                        self.assertEqual(cell["cell_status"],
                                         "source_dash_not_interpreted_as_zero")
                    elif cell["denominator_status"] == "arithmetic_implies_7_not_reported_group_n_10":
                        mismatch_cells.append(cell)
                        self.assertEqual(cell["implied_denominator"], 7)
                        self.assertEqual(cell["group_n"], 10)
                        self.assertEqual(round(cell["count"] / cell["implied_denominator"] * 100, 1),
                                         cell["printed_percent"])
                        self.assertNotEqual(cell["percent_if_group_n"], cell["printed_percent"])
                    else:
                        self.assertEqual(cell["denominator_status"], "arithmetic_matches_group_n")
                        self.assertEqual(cell["implied_denominator"], cell["group_n"])
                        self.assertEqual(round(cell["count"] / cell["implied_denominator"] * 100, 1),
                                         cell["printed_percent"])
                        self.assertEqual(cell["percent_if_group_n"], cell["printed_percent"])
        self.assertEqual(len(mismatch_cells), 2)
        self.assertEqual(sum(cell["printed_cell"] == "-"
                             for row in reconciliation["table_rows"]
                             for cell in row["cells_by_group"]), 7)
        self.assertEqual(len(self.validated["observations"]), 50)
        self.assertFalse(any(any(label in record["assay"]["endpoint"]
                                 for label in ("Bubbles in the circuit", "Vasospasm",
                                               "Decannulation", "Vessel lesion"))
                             for record in self.validated["observations"]))

    def test_table_one_support_duration_means_keep_sem_and_group_scope(self):
        expected = {
            "1-3h": (1.48, 0.78, 8, (1, 3)),
            "4-24h": (11, 3.42, 10, (4, 24)),
            "48-168h": (72.6, 12.9, 10, (48, 168)),
        }
        duration_records = [record for record in self.validated["observations"]
                            if record["assay"]["endpoint"].startswith("Mean total survival time")]
        self.assertEqual(len(duration_records), 3)
        for record in duration_records:
            with self.subTest(record_id=record["record_id"]):
                group = record["record_id"].split("-goal-", 1)[1].split("-total-support", 1)[0]
                mean, sem, n, goal = expected[group]
                self.assertEqual(record["observation"]["value"], mean)
                self.assertEqual(record["observation"]["measurement_uncertainty"], sem)
                self.assertEqual(record["assay"]["unit"], "hours")
                self.assertEqual(record["observation"]["replicate_role"], "summary_only")
                self.assertIsNone(record["independent_unit"]["id"])
                self.assertIn(f"n={n}", record["independent_unit"]["hierarchy_note"])
                self.assertEqual((record["developmental_interval"]["start"],
                                  record["developmental_interval"]["end"]), goal)
                self.assertIn("Table 1", record["source_locator"])
                self.assertIn("means ± SEM", record["source_locator"])

    def test_later_adverse_outcomes_remain_separate_group_counts(self):
        expected = {
            "eixarch2023-goal-48-168h-postday1-complications": 4,
            "eixarch2023-goal-48-168h-terminal-hydrops": 3,
        }
        for record in self.validated["observations"]:
            if record["record_id"] not in expected:
                continue
            with self.subTest(record_id=record["record_id"]):
                self.assertEqual(record["observation"]["value"], expected[record["record_id"]])
                self.assertEqual(record["assay"]["measurement_role"], "adverse_effect")
                self.assertEqual(record["evidence_status"], "author_reported_summary")
                self.assertEqual(record["observation"]["replicate_role"], "summary_only")
                self.assertIsNone(record["independent_unit"]["id"])
                self.assertIn("Section 3 Results", record["source_locator"])
        self.assertTrue(set(expected).issubset({x["record_id"] for x in self.validated["observations"]}))
        frame = next(x for x in self.validated["cohort_coverage"]
                     if x["coverage_id"] == "eixarch2023-goal-48-168h-coverage")
        self.assertEqual(frame["disposition_completeness"], "unknown")
        self.assertEqual(frame["categories_mutually_exclusive"], "unknown")
        self.assertEqual(frame["categories_exhaustive"], "unknown")
        self.assertTrue(any("may overlap" in item["text"] for item in frame["selection_statements"]))

    def test_late_complication_record_uses_table_cell_as_secondary_source_locator(self):
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        source_record = next(item for item in inventory["records"]
                             if item["record_id"] == "eixarch_2023_entry_learning_curve")
        transition = next(item for item in source_record["transition_events"]
                          if item["type"] == "entry_to_support")
        complications = transition["post_day_1_findings_in_48_168h_group"]["complications"]
        crosscheck = complications["table_1_crosscheck"]
        self.assertEqual(crosscheck["candidate_record_id"],
                         "eixarch2023-goal-48-168h-postday1-complications")
        self.assertEqual(crosscheck["table_row_label"],
                         "Complications after 24 h survival #")
        self.assertEqual(crosscheck["table_printed_cell"], "4 (40%)")
        self.assertEqual(crosscheck["table_group_n"], 10)
        self.assertEqual(crosscheck["table_percent_from_count_and_group_n"], 40)
        self.assertIn(">24 h survival", crosscheck["table_footnote"])
        self.assertIn("after the first day", crosscheck["results_wording"])
        self.assertTrue(crosscheck["arithmetic_and_narrative_match"])
        self.assertIn("not duplicated", crosscheck["interpretation_limit"])

        record = next(item for item in self.validated["observations"]
                      if item["record_id"] == crosscheck["candidate_record_id"])
        self.assertEqual(record["observation"]["value"], 4)
        self.assertIn("Table 1", record["source_locator"])
        self.assertIn("4 (40%)", record["source_locator"])
        self.assertIn(">24 h survival", record["source_locator"])
        self.assertIn("four of ten", record["source_locator"])
        self.assertEqual(len(self.validated["observations"]), 50)

    def test_30_minute_physiology_summaries_keep_units_sem_and_timepoint(self):
        expected = {
            "1-3h": {"ph": (7.20, 0.06, "pH"), "flow": (45, 24, "mL/kg/min"),
                     "heart-rate": (134, 33, "bpm"), "n": 8, "goal": (1, 3)},
            "4-24h": {"ph": (7.31, 0.04, "pH"), "flow": (138, 23, "mL/kg/min"),
                      "heart-rate": (205, 8, "bpm"), "n": 10, "goal": (4, 24)},
            "48-168h": {"ph": (7.33, 0.02, "pH"), "flow": (196, 13, "mL/kg/min"),
                        "heart-rate": (182, 8, "bpm"), "n": 10, "goal": (48, 168)},
        }
        records = [record for record in self.validated["observations"]
                   if "-30min-" in record["record_id"]]
        self.assertEqual(len(records), 9)
        for record in records:
            with self.subTest(record_id=record["record_id"]):
                group = record["record_id"].split("-goal-", 1)[1].split("-30min-", 1)[0]
                endpoint = record["record_id"].split("-30min-", 1)[1]
                value, sem, unit = expected[group][endpoint]
                n, goal = expected[group]["n"], expected[group]["goal"]
                self.assertEqual(record["observation"]["value"], value)
                self.assertEqual(record["observation"]["measurement_uncertainty"], sem)
                self.assertEqual(record["assay"]["unit"], unit)
                self.assertEqual(record["observation"]["measurement_time"], 30)
                self.assertEqual(record["observation"]["measurement_time_unit"],
                                 "minutes after AP system connection")
                self.assertEqual(record["observation"]["replicate_role"], "summary_only")
                self.assertIsNone(record["independent_unit"]["id"])
                self.assertIn(f"n={n}", record["independent_unit"]["hierarchy_note"])
                self.assertIn("row-specific assessment n is not separately stated",
                              record["independent_unit"]["hierarchy_note"])
                self.assertEqual((record["developmental_interval"]["start"],
                                  record["developmental_interval"]["end"]), goal)
                self.assertIn("Table 1", record["source_locator"])
                self.assertIn("means ± SEM", record["source_locator"])

    def test_whole_experiment_physiology_summaries_are_not_trajectories(self):
        expected = {
            "1-3h": {
                "ph": (7.22, 0.07, "pH", "7.22", "0.07"),
                "lactate": (6.2, 1.22, "mmol/L", "6.2", "1.22"),
                "heart-rate": (222, 11, "bpm", "222", "11"),
                "circuit-flow": (124, 12, "mL/kg/min", "124", "12"),
            },
            "4-24h": {
                "ph": (7.29, 0.03, "pH", "7.29", "0.03"),
                "lactate": (3.82, 0.78, "mmol/L", "3.82", "0.78"),
                "heart-rate": (186, 9, "bpm", "186", "9"),
                "circuit-flow": (115, 11, "mL/kg/min", "115", "11"),
            },
            "48-168h": {
                "ph": (7.35, 0.01, "pH", "7.35", "0.01"),
                "lactate": (2.5, 0.38, "mmol/L", "2.50", "0.38"),
                "heart-rate": (177, 5, "bpm", "177", "5"),
                "circuit-flow": (161, 8, "mL/kg/min", "161", "8"),
            },
        }
        records = [record for record in self.validated["observations"]
                   if "-whole-experiment-" in record["record_id"]]
        self.assertEqual(len(records), 12)
        for record in records:
            with self.subTest(record_id=record["record_id"]):
                group = record["record_id"].split("-goal-", 1)[1].split("-whole-experiment-", 1)[0]
                key = record["record_id"].split("-whole-experiment-", 1)[1]
                value, sem, unit, _, _ = expected[group][key]
                self.assertEqual(record["observation"]["value"], value)
                self.assertEqual(record["observation"]["measurement_uncertainty"], sem)
                self.assertEqual(record["assay"]["unit"], unit)
                self.assertEqual(record["observation"]["measurement_time"], "whole experiment")
                self.assertEqual(record["observation"]["replicate_role"], "summary_only")
                self.assertIsNone(record["independent_unit"]["id"])
                self.assertIn("row-specific assessment n are not provided",
                              record["independent_unit"]["hierarchy_note"])
                self.assertIn("Figure 3 caption", record["source_locator"])
                self.assertIn("Section 2.2.6", record["source_locator"])

    def test_transition_context_measures_stay_separate_from_support_outcomes(self):
        expected = {
            "1-3h": {
                "exit-surgery-duration": (33.5, 3.3, "min", "33.5", "3.3"),
                "cannulation-duration": (8.04, 2.95, "min", "8.04", "2.95"),
                "preconnection-heart-rate": (182, 18, "bpm", "182", "18"),
            },
            "4-24h": {
                "exit-surgery-duration": (44.1, 5.1, "min", "44.1", "5.1"),
                "cannulation-duration": (8.11, 0.93, "min", "8.11", "0.93"),
                "preconnection-heart-rate": (168, 10, "bpm", "168", "10"),
            },
            "48-168h": {
                "exit-surgery-duration": (34.3, 5.1, "min", "34.3", "5.1"),
                "cannulation-duration": (6.89, 0.40, "min", "6.89", "0.40"),
                "preconnection-heart-rate": (143, 6, "bpm", "143", "6"),
            },
        }
        records = [record for record in self.validated["observations"]
                   if record["record_id"].endswith(("-exit-surgery-duration", "-cannulation-duration",
                                                     "-preconnection-heart-rate"))]
        self.assertEqual(len(records), 9)
        for record in records:
            with self.subTest(record_id=record["record_id"]):
                suffix = next(key for group_values in expected.values() for key in group_values
                              if record["record_id"].endswith("-" + key))
                group = record["record_id"].split("-goal-", 1)[1][:-len(suffix) - 1]
                value, sem, unit, _, _ = expected[group][suffix]
                self.assertEqual(record["observation"]["value"], value)
                self.assertEqual(record["observation"]["measurement_uncertainty"], sem)
                self.assertEqual(record["assay"]["unit"], unit)
                self.assertEqual(record["observation"]["replicate_role"], "summary_only")
                self.assertIsNone(record["independent_unit"]["id"])
                self.assertIn("Table 1", record["source_locator"])
                self.assertIn("Section 2.2.6", record["source_locator"])
        hr_records = [record for record in records
                      if record["record_id"].endswith("-preconnection-heart-rate")]
        self.assertTrue(all(record["observation"]["measurement_time"] == "before AP system connection"
                            for record in hr_records))

    def test_cannulation_technique_counts_preserve_labels_and_group_scope(self):
        expected = {
            "1-3h": {"direct-cut-down": (6, "6 (75%)"),
                     "sequential-technique": (2, "2 (25%)"),
                     "st-vasospasm-prevention": (0, "0")},
            "4-24h": {"direct-cut-down": (0, "0"),
                      "sequential-technique": (5, "5 (50%)"),
                      "st-vasospasm-prevention": (5, "5 (50%)")},
            "48-168h": {"direct-cut-down": (0, "0"),
                        "sequential-technique": (0, "0"),
                        "st-vasospasm-prevention": (10, "10 (100%)")},
        }
        records = [record for record in self.validated["observations"]
                   if "-cannulation-technique-" in record["record_id"]]
        self.assertEqual(len(records), 9)
        for record in records:
            with self.subTest(record_id=record["record_id"]):
                group, suffix = record["record_id"].split("-goal-", 1)[1].split(
                    "-cannulation-technique-", 1)
                count, printed = expected[group][suffix]
                self.assertEqual(record["observation"]["value"], count)
                self.assertEqual(record["observation"]["replicate_role"], "summary_only")
                self.assertIsNone(record["independent_unit"]["id"])
                self.assertIn("Table 1, Cannulation technique used", record["source_locator"])
                self.assertIn("Cannulation technique used:", record["assay"]["endpoint"])
                frame = next(x for x in self.validated["cohort_coverage"]
                             if x["coverage_id"].replace("-coverage", "") in record["record_id"])
                declaration = next(x for x in frame["declarations"]
                                   if x["reported_label"] == record["assay"]["endpoint"])
                self.assertEqual(declaration["value"], count)
                self.assertIn(printed, declaration["note"])
                self.assertEqual(frame["categories_mutually_exclusive"], "unknown")
                self.assertEqual(frame["categories_exhaustive"], "unknown")

    def test_technique_and_complication_trend_is_not_treated_as_causal(self):
        source_record = next(item for item in json.loads(INVENTORY.read_text(encoding="utf-8"))["records"]
                             if item["record_id"] == "eixarch_2023_entry_learning_curve")
        transition = source_record["transition_events"][0]
        crosswalk = transition["technique_complication_co_trend"]
        self.assertEqual(crosswalk["technique_group_data_ref"],
                         "cannulation_technique_counts_by_group")
        self.assertIn("after several experiments", crosswalk["methods_sequence_summary"])
        self.assertEqual(crosswalk["individual_technique_to_outcome_cross_tab"], "not reported")
        self.assertEqual(crosswalk["technique_assignment_design"].startswith(
            "The Methods describe technique refinement over successive experiments"), True)
        self.assertEqual(crosswalk["causal_effect_status"],
                         "not_identifiable_from_group_summaries")
        self.assertIn("not an estimate of technique effect", crosswalk["interpretation_limit"])
        self.assertEqual(len(crosswalk["table_group_links"]), 3)
        expected_rates = [75, 50, 0]
        expected_cells = ["6 (75%)", "5 (50%)", "0"]
        expected_group_ns = [8, 10, 10]
        for index, (link, technique_group, rate, cell, group_n) in enumerate(zip(
                crosswalk["table_group_links"],
                transition["cannulation_technique_counts_by_group"],
                expected_rates, expected_cells, expected_group_ns)):
            with self.subTest(goal=link["goal_interval_hours"]):
                self.assertEqual(link["goal_interval_hours"], technique_group["goal_interval_hours"])
                self.assertEqual(link["technique_group_index"], index)
                self.assertEqual(crosswalk["abstract_complication_percent_by_group"][
                    link["technique_group_index"]], rate)
                self.assertEqual(link["procedure_complication_printed_cell"], cell)
                self.assertEqual(technique_group["group_n"], group_n)
        self.assertEqual(len(self.validated["observations"]), 50)

    def test_goal_attainment_counts_are_distinguished_from_reported_dispositions(self):
        source_record = next(item for item in json.loads(INVENTORY.read_text(encoding="utf-8"))["records"]
                             if item["record_id"] == "eixarch_2023_entry_learning_curve")
        crosswalk = source_record["goal_attainment_disposition_crosswalk"]
        self.assertEqual(crosswalk["count_status"],
                         "goal_attainment_counts_arithmetically_derived_from_reported_percentages_and_group_denominators")
        self.assertIn("does not separately enumerate euthanasia counts",
                      crosswalk["goal_attainment_to_protocol_disposition"])
        expected = [((1, 3), 8, 25, 2, 6), ((4, 24), 10, 70, 7, 3),
                    ((48, 168), 10, 80, 8, 2)]
        for group, (interval, group_n, rate, attained, not_attained) in zip(
                crosswalk["groups"], expected):
            with self.subTest(interval=interval):
                self.assertEqual((group["goal_interval_hours"]["min"],
                                  group["goal_interval_hours"]["max"]), interval)
                self.assertEqual((group["group_n"], group["goal_attainment_percent"],
                                  group["derived_goal_attainment_count"],
                                  group["derived_not_reaching_goal_count"]),
                                 (group_n, rate, attained, not_attained))
                self.assertEqual(group["nonattainment_disposition"], "not_reported_by_group")
        self.assertEqual(crosswalk["individual_disposition_linkage"], "not_reported")
        self.assertIn("not deaths", crosswalk["interpretation_limit"])
        self.assertEqual(len(self.validated["observations"]), 50)

    def test_middle_goal_interval_label_variant_is_preserved(self):
        source_record = next(item for item in json.loads(INVENTORY.read_text(encoding="utf-8"))["records"]
                             if item["record_id"] == "eixarch_2023_entry_learning_curve")
        event = source_record["transition_events"][0]
        qualification = event["group_interval_label_variation"]
        self.assertEqual(qualification["canonical_group_label"], "4–24 h")
        labels = {item["locator"]: item["printed_label"]
                  for item in qualification["labels_by_locator"]}
        self.assertEqual(labels["Abstract > Methods"], "4–24 h")
        self.assertEqual(labels["Section 2, Materials and Methods"], "4–24 h")
        self.assertEqual(labels["Table 1 middle-group column header"], "4–24 h")
        self.assertEqual(labels["Section 3, Results, complication-group comparison"], "3–24 h")
        self.assertEqual(labels["Table 1 statistical footnote"], "3–24 h")
        self.assertIn("Do not change group denominators",
                      qualification["interpretation_limit"])
        self.assertEqual(len(self.validated["observations"]), 50)

    def test_group_denominators_and_broad_goal_windows_remain_separate(self):
        expected = {
            "eixarch2023-goal-1-3h-coverage": (8, (1, 3), {"25%", "75%"}),
            "eixarch2023-goal-4-24h-coverage": (10, (4, 24), {"70%", "50%"}),
            "eixarch2023-goal-48-168h-coverage": (10, (48, 168), {"80%", "0%"}),
        }
        self.assertEqual(sum(frame["denominator"]["value"]
                             for frame in self.validated["cohort_coverage"]), 28)
        for frame in self.validated["cohort_coverage"]:
            with self.subTest(coverage_id=frame["coverage_id"]):
                n, goal, rates = expected[frame["coverage_id"]]
                self.assertEqual(frame["denominator"]["value"], n)
                self.assertEqual(frame["denominator"]["value_status"], "reported")
                endpoint_rates = {item["value"] for item in frame["declarations"]
                                  if item["category"] == "endpoint_measure"
                                  and item["quantity_kind"] == "percentage"}
                self.assertEqual(endpoint_rates, rates)
                group_records = [record for record in self.validated["observations"]
                                 if record["record_id"].startswith(frame["coverage_id"].replace("-coverage", ""))]
                self.assertEqual(len(group_records), 18 if goal == (48, 168) else 16)
                duration_values = {item["value"] for item in frame["declarations"]
                                   if item["category"] == "endpoint_measure"
                                   and item["reported_label"].startswith("Mean total survival time")}
                self.assertEqual(len(duration_values), 1)
                physiology = [item for item in frame["declarations"]
                              if item["category"] == "endpoint_measure"
                              and item["reported_label"].startswith(("pH 30 min", "Circuit flow 30 min",
                                                                     "Heart rate 30 min"))]
                self.assertEqual(len(physiology), 3)
                self.assertTrue(all("not separately stated" in item["note"] for item in physiology))
                whole_experiment = [item for item in frame["declarations"]
                                    if item["category"] == "endpoint_measure"
                                    and item["reported_label"].endswith("(mean ± SEM)")
                                    and item["reported_label"].startswith(("pH whole", "Lactate whole",
                                                                           "Heart rate whole", "Circuit flow whole"))]
                self.assertEqual(len(whole_experiment), 4)
                self.assertTrue(all("not provided" in item["note"] for item in whole_experiment))
                context = [item for item in frame["declarations"]
                           if item["category"] == "endpoint_measure"
                           and item["reported_label"].startswith(("Duration EXIT surgery",
                                                                  "Duration of cannulation",
                                                                  "Heart rate before connection"))]
                self.assertEqual(len(context), 3)
                technique = [item for item in frame["declarations"]
                             if item["category"] == "endpoint_measure"
                             and item["reported_label"].startswith("Cannulation technique used:")]
                self.assertEqual(len(technique), 3)

                if goal == (48, 168):
                    success = next(record for record in self.validated["observations"]
                                   if record["record_id"] == "eixarch2023-goal-48-168h-attainment")
                    self.assertEqual((success["developmental_interval"]["start"],
                                      success["developmental_interval"]["end"]), goal)
                    self.assertIn("individual target not reported",
                                  success["observation"]["measurement_time_unit"])
                    self.assertIn("not an 80% rate reaching 168 h",
                                  frame["declarations"][1]["note"])

    def test_inventory_links_candidate_and_keeps_other_cohorts_separate(self):
        inventory = json.loads(INVENTORY.read_text(encoding="utf-8"))
        source_record = next(item for item in inventory["records"]
                             if item["record_id"] == "eixarch_2023_entry_learning_curve")
        intake = source_record["machine_readable_candidate_intake"]
        self.assertEqual(intake["path"], "config/observations/eixarch_2023_support_outcomes_candidate.json")
        self.assertEqual(intake["record_count"], 50)
        self.assertEqual(intake["coverage_frame_count"], 3)
        self.assertEqual(intake["bundle_path"],
                         "artifacts/eixarch-2023-group-outcomes-2026-10-10-v11")
        self.assertEqual(intake["bundle_input_sha256"],
                         "d269ac58a496f8a28cc61064c79178857e7b1d1034e5530c31709ba8a1130154")
        self.assertIn("No individual identifiers", intake["boundary"])
        transition = source_record["transition_events"][0]
        self.assertEqual(transition["goal_attainment_percent_by_group"], [25, 70, 80])
        self.assertEqual(transition["cannulation_complications_percent_by_group"], [75, 50, 0])
        self.assertEqual(transition["cannulation_complications_source_locator"],
                         "Abstract; §3 Results")
        availability = source_record["public_data_availability_followup"]
        self.assertEqual(availability["checked_on"], "2026-10-10")
        self.assertEqual(len(availability["surfaces_checked"]), 4)
        pdf_screen = next(item for item in availability["surfaces_checked"]
                          if item["surface"] == "MDPI-hosted primary full-text PDF")
        self.assertIn("'Not applicable'", pdf_screen["finding"])
        self.assertIn("no Supplementary Materials section", pdf_screen["finding"])
        self.assertIn("n=7", pdf_screen["finding"])
        html_screen = next(item for item in availability["surfaces_checked"]
                           if item["surface"] == "Publisher HTML article page")
        self.assertIn("No conclusion drawn", html_screen["finding"])
        self.assertIn("does not prove", availability["search_boundary"])
        self.assertIn("No author was contacted", availability["search_boundary"])
        learning_curve = transition["learning_curve_reproducibility_statement"]
        self.assertEqual(learning_curve["reported_count"], 15)
        self.assertEqual(learning_curve["count_unit"], "in-vivo experiments")
        self.assertEqual(learning_curve["reported_cohort_total"], 28)
        self.assertEqual(learning_curve["reported_table_group_sizes"], [8, 10, 10])
        self.assertEqual(learning_curve["mapping_to_reported_groups"], "not specified")
        self.assertEqual(learning_curve["reproducibility_criterion"], "not defined in this statement")
        self.assertIn("unresolved", learning_curve["relation_of_15_to_28"])
        self.assertIn("Do not convert 15 into a proportion",
                      learning_curve["interpretation_limit"])
        late_findings = transition["post_day_1_findings_in_48_168h_group"]
        self.assertEqual(late_findings["complications"]["n"], 4)
        self.assertEqual(late_findings["complications"]["denominator"], 10)
        self.assertEqual(late_findings["hydrops_at_experiment_end"]["n"], 3)
        self.assertEqual(late_findings["hydrops_at_experiment_end"]["denominator"], 10)
        duration_records = {
            (record["developmental_interval"]["start"], record["developmental_interval"]["end"]): record
            for record in self.validated["observations"]
            if record["assay"]["endpoint"].startswith("Mean total survival time")
        }
        self.assertEqual(len(transition["mean_total_support_hours_by_group"]), 3)
        for summary in transition["mean_total_support_hours_by_group"]:
            goal = (summary["goal_interval_hours"]["min"], summary["goal_interval_hours"]["max"])
            with self.subTest(duration_goal=goal):
                record = duration_records[goal]
                self.assertEqual(record["observation"]["value"], summary["mean_hours"])
                self.assertEqual(record["observation"]["measurement_uncertainty"],
                                 summary["reported_plus_minus"])
                self.assertEqual(summary["dispersion"], "SEM")
        for summary in transition["thirty_minute_physiology_summary_by_group"]:
            goal = (summary["goal_interval_hours"]["min"], summary["goal_interval_hours"]["max"])
            for key, record_suffix in (("pH_30min_after_connection", "-ph"),
                                       ("circuit_flow_mL_per_kg_per_min_30min_after_connection", "-flow"),
                                       ("heart_rate_30min_after_connection", "-heart-rate")):
                record = next(x for x in self.validated["observations"]
                              if "-30min-" in x["record_id"]
                              and x["record_id"].endswith(record_suffix)
                              and (x["developmental_interval"]["start"],
                                   x["developmental_interval"]["end"]) == goal)
                self.assertEqual(record["observation"]["value"], summary[key]["mean"])
                self.assertEqual(record["observation"]["measurement_uncertainty"],
                                 summary[key]["reported_plus_minus"])
                self.assertEqual(summary[key]["dispersion"], "SEM")
                self.assertEqual(float(summary[key]["source_mean_lexeme"]), summary[key]["mean"])
                self.assertEqual(float(summary[key]["source_plus_minus_lexeme"]),
                                 summary[key]["reported_plus_minus"])
                self.assertEqual(float(summary[key]["source_mean_lexeme"]), summary[key]["mean"])
                self.assertEqual(float(summary[key]["source_plus_minus_lexeme"]),
                                 summary[key]["reported_plus_minus"])
        for summary in transition["whole_experiment_physiology_summary_by_group"]:
            goal = (summary["goal_interval_hours"]["min"], summary["goal_interval_hours"]["max"])
            for key, suffix in (("pH", "ph"), ("lactate", "lactate"),
                                ("heart_rate", "heart-rate"), ("circuit_flow", "circuit-flow")):
                record = next(x for x in self.validated["observations"]
                              if x["record_id"].endswith("-whole-experiment-" + suffix)
                              and (x["developmental_interval"]["start"],
                                   x["developmental_interval"]["end"]) == goal)
                self.assertEqual(record["observation"]["value"], summary[key]["mean"])
                self.assertEqual(record["observation"]["measurement_uncertainty"],
                                 summary[key]["reported_plus_minus"])
                self.assertEqual(summary[key]["dispersion"], "SEM")
                self.assertEqual(float(summary[key]["source_mean_lexeme"]), summary[key]["mean"])
                self.assertEqual(float(summary[key]["source_plus_minus_lexeme"]),
                                 summary[key]["reported_plus_minus"])
        long_group = next(x for x in transition["whole_experiment_physiology_summary_by_group"]
                          if x["goal_interval_hours"] == {"min": 48, "max": 168})
        self.assertEqual(long_group["lactate"]["source_significance_marker"], "**")
        self.assertIn("not recalculated", long_group["lactate"]["significance_note"])
        for summary in transition["transition_context_summary_by_group"]:
            goal = (summary["goal_interval_hours"]["min"], summary["goal_interval_hours"]["max"])
            for key, suffix in (("exit_surgery_duration", "exit-surgery-duration"),
                                ("cannulation_duration", "cannulation-duration"),
                                ("heart_rate_before_connection", "preconnection-heart-rate")):
                record = next(x for x in self.validated["observations"]
                              if x["record_id"].endswith("-" + suffix)
                              and (x["developmental_interval"]["start"],
                                   x["developmental_interval"]["end"]) == goal)
                self.assertEqual(record["observation"]["value"], summary[key]["mean"])
                self.assertEqual(record["observation"]["measurement_uncertainty"],
                                 summary[key]["reported_plus_minus"])
                self.assertEqual(float(summary[key]["source_mean_lexeme"]), summary[key]["mean"])
                self.assertEqual(float(summary[key]["source_plus_minus_lexeme"]),
                                 summary[key]["reported_plus_minus"])
                self.assertEqual(record["assay"]["unit"], summary[key]["unit"])
        for summary in transition["cannulation_technique_counts_by_group"]:
            goal = (summary["goal_interval_hours"]["min"], summary["goal_interval_hours"]["max"])
            for key, cell in summary["technique_cells"].items():
                record_id = f"eixarch2023-goal-{goal[0]}-{goal[1]}h-cannulation-technique-{key.replace('_','-')}"
                record = next(x for x in self.validated["observations"]
                              if x["record_id"] == record_id)
                self.assertEqual(record["observation"]["value"], cell["count"])
                self.assertEqual(cell["source_label"], record["assay"]["endpoint"].split(": ", 1)[1])
                declaration = next(d for f in self.validated["cohort_coverage"]
                                   if (f["denominator"]["value"] == summary["group_n"]
                                       and f["reported_group_label"].startswith(f"{goal[0]}-{goal[1]} h"))
                                   for d in f["declarations"]
                                   if d["reported_label"] == record["assay"]["endpoint"])
                self.assertIn(cell["printed_source_cell"], declaration["note"])
        denominator_screen = source_record["transition_events"][0]["table_1_percentage_denominator_screen"]
        self.assertEqual(denominator_screen["denominator_status"],
                         "Table footnote defines values as means ± SEM or n (%), but does not explain why these two percentages imply a denominator of seven rather than the stated group n of ten.")
        self.assertEqual(self.dataset["source_revision"]["review_status"], "candidate")
        self.assertEqual(intake["status"], "candidate_group_summary_transcription")


if __name__ == "__main__":
    unittest.main()
