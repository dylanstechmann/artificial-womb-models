"""Check published metadata, nested sampling units and provenance in the public study collection."""
import csv
import hashlib
import json
import os
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest
from importlib.util import find_spec
from pathlib import Path
from unittest.mock import patch

from local_evidence import requires_local_evidence

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "studies" / "public-evidence"
DOPPLER_SOURCE = ROOT / "artifacts" / "public-inputs-v2" / "Dataset_S2.csv"
COA_SOURCES = ROOT / "artifacts" / "coa-sources"
COA_FIGURE = COA_SOURCES / "coa-figure-2.png"
HAS_FIGURE_DEPS = find_spec("PIL") is not None
HAS_MODEL_DEPS = HAS_FIGURE_DEPS and all(find_spec(name) for name in ("numpy", "scipy"))

def rows(path):
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream, delimiter="\t"))

class PublicStudyCollectionTests(unittest.TestCase):
    def test_receipts_and_local_paths(self):
        def digest(path):
            return hashlib.sha256(path.read_bytes()).hexdigest()
        snapshot = DIRECTORY / "bibliography"
        search = json.loads((snapshot / "receipt.json").read_bytes())
        bibliography = rows(snapshot / "records.tsv")
        self.assertEqual(len(bibliography), len({(r["source"], r["id"]) for r in bibliography}))
        self.assertEqual(len(bibliography), search["unique_source_id_pairs"])
        for label, entry in search["searches"].items():
            self.assertEqual(entry["hits"], sum(label in r["searches"].split(",") for r in bibliography))
        self.assertEqual(digest(snapshot / "records.tsv"), search["records_sha256"])
        self.assertEqual(digest(DIRECTORY / "discover.py"), search["script_sha256"])
        audit = DIRECTORY / "audit"
        receipt = json.loads((audit / "receipt.json").read_bytes())
        self.assertEqual(digest(DIRECTORY / "audit.py"), receipt["implementation_sha256"])
        self.assertEqual(digest(DIRECTORY / "inputs.json"), receipt["input_manifest_sha256"])
        for name, checksum in receipt["outputs_sha256"].items():
            self.assertEqual(digest(audit / name), checksum, name)
        for row in rows(DIRECTORY / "studies.tsv"):
            data = row["data_or_local_record"]
            if data and not data.startswith("https://"):
                self.assertTrue((DIRECTORY / data).is_file(), data)
        index = subprocess.check_output([sys.executable, str(DIRECTORY / "local_index.py")], text=True)
        self.assertEqual(index, (DIRECTORY / "local-index.tsv").read_text(encoding="utf-8"))

    def test_individuals_and_reference_material(self):
        audit = DIRECTORY / "audit"
        samples = rows(audit / "samples.tsv")
        self.assertEqual((len(samples), len({s["sheep"] for s in samples})), (36, 9))
        self.assertEqual([s["gsm"] for s in samples if s["paper_qc"] == "excluded_low_counts"], ["GSM8473189"])
        animals = rows(audit / "ovine_animals.tsv")
        self.assertEqual(len(animals), 5)
        self.assertEqual(sum(float(r["mean_distance_late"]) < float(r["mean_distance_early"]) for r in animals), 4)
        traces = rows(audit / "human_traces.tsv")
        self.assertEqual(len(traces), 8)
        self.assertTrue(all(r["cases"] == "7" for r in traces))
        self.assertEqual(sum(int(r["time_velocity_pairs"]) for r in traces), 10210)

    def test_doppler_frozen_receipt(self):
        result = DIRECTORY / "doppler"
        receipt = json.loads((result / "receipt.json").read_bytes())
        self.assertEqual((receipt["participants"], receipt["traces"]), (7, 56))
        self.assertEqual(receipt["duplicate_timestamps_collapsed"], 28)
        for name, digest in receipt["implementation_sha256"].items():
            self.assertEqual(hashlib.sha256((DIRECTORY / name).read_bytes()).hexdigest(), digest)
        manifest = (DIRECTORY / "inputs.json").read_bytes()
        self.assertEqual(hashlib.sha256(manifest).hexdigest(), receipt["input_manifest_sha256"])
        self.assertIn(receipt["source"], json.loads(manifest))
        for name, digest in receipt["outputs_sha256"].items():
            self.assertEqual(hashlib.sha256((result / name).read_bytes()).hexdigest(), digest)
        summary = rows(result / "by-site.tsv")
        self.assertEqual(len({row["site"] for row in summary}), 8)
        self.assertEqual(sum(int(row["lower_template_rmse"]) for row in summary), 56)

    def test_coa_plot_and_replay_have_distinct_agreement_results(self):
        summaries = {}
        for directory in ("doppler-figure", "coa-replay"):
            result = DIRECTORY / directory
            receipt = json.loads((result / "receipt.json").read_bytes())
            for name, digest in receipt["implementation_sha256"].items():
                self.assertEqual(hashlib.sha256((DIRECTORY / name).read_bytes()).hexdigest(), digest)
            summary = result / "by-site.tsv"
            self.assertEqual(hashlib.sha256(summary.read_bytes()).hexdigest(), receipt["outputs_sha256"][summary.name])
            summaries[directory] = {row["site"]: row for row in rows(summary)}
        figure = summaries["doppler-figure"]
        replay = summaries["coa-replay"]
        self.assertEqual(len(figure), 8)
        self.assertEqual(set(figure), set(replay))
        for site, row in replay.items():
            self.assertLess(float(row["solver_max_difference_cm_s"]), 0.01)
            self.assertEqual(row["published_peak_cm_s"], figure[site]["published_model_peak_cm_s"])
            self.assertEqual(figure[site]["pixels_scored"], "723")
        for site in ("Mitral Valve", "Tricuspid Valve"):
            self.assertGreater(float(replay[site]["replay_vs_published_rmse_cm_s"]), 15)

    def test_doppler_withholds_participant_and_preserves_signed_endpoints(self):
        with patch.object(sys, "path", [str(DIRECTORY), *sys.path]):
            benchmark = runpy.run_path(str(DIRECTORY / "doppler_benchmark.py"))
        phase_samples = benchmark["phase_samples"]
        signed, collapsed = phase_samples([1.0, 2.0, 2.0, 3.0], [-4.0, 0.0, 0.0, 8.0])
        self.assertEqual((signed[0], signed[50], signed[100], signed[150], signed[-1]), (-4, -2, 0, 4, 8))
        self.assertEqual(collapsed, 1)
        with self.assertRaisesRegex(ValueError, "duplicate velocities disagree"):
            phase_samples([0, 1, 1], [0, 2, 3])
        traces = {case: {"artery": [value] * len(signed), "valve": [-2 * value] * len(signed)}
                  for case, value in (("a", 1), ("b", 3), ("c", 8))}
        scores = benchmark["score_folds"](traces)
        self.assertEqual(scores["c"]["artery"]["rmse"], 6)
        self.assertEqual(scores["c"]["valve"]["rmse"], 12)

    @requires_local_evidence("public-inputs-v2")
    def test_doppler_replays_from_pinned_source(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "result"
            subprocess.run([sys.executable, str(DIRECTORY / "doppler_benchmark.py"),
                            str(DOPPLER_SOURCE), str(output)], check=True)
            for name in ("by-site.tsv", "receipt.json"):
                self.assertEqual((output / name).read_bytes(), (DIRECTORY / "doppler" / name).read_bytes())

    @requires_local_evidence("public-inputs-v2", "coa-sources")
    @unittest.skipUnless(HAS_FIGURE_DEPS, "figure extraction needs Pillow")
    def test_doppler_figure_replays_from_pinned_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "result"
            subprocess.run([sys.executable, str(DIRECTORY / "doppler_figure.py"),
                            str(DOPPLER_SOURCE), str(COA_FIGURE), str(output)], check=True)
            self.assertEqual((output / "by-site.tsv").read_bytes(),
                             (DIRECTORY / "doppler-figure" / "by-site.tsv").read_bytes())

    @unittest.skipUnless(HAS_MODEL_DEPS, "model replay needs NumPy, SciPy and Pillow")
    def test_coa_velocity_mapping_uses_distinct_flow_states_and_areas(self):
        with patch.object(sys, "path", [str(DIRECTORY), *sys.path]):
            replay = runpy.run_path(str(DIRECTORY / "coa_replay.py"))
        states = list(range(73))
        states[28] = -28
        constants = [1.0] * 163
        constants[23], constants[41], constants[51], constants[61] = 2, 4, 5, 3
        # Known answers from the archived C state legend and Figure 4 conversions.
        expected = {
            "Aortic Valve": 2.5,
            "Pulmonary Valve": 3.2,
            "Mitral Valve": 1.0,
            "Tricuspid Valve": 5.0,
            "Aortic Isthmus": -164.311962,
            "Ductus Arteriosus": 502.813172,
            "Umbilical Artery": 508.781722,
            "Middle Cerebral Artery": 2355.690169,
        }
        actual = replay["velocity_outputs"](states, constants)
        self.assertEqual(actual.keys(), expected.keys())
        for site, value in expected.items():
            with self.subTest(site=site):
                self.assertAlmostEqual(actual[site], value, places=6)

    @requires_local_evidence("coa-sources")
    @unittest.skipUnless(HAS_MODEL_DEPS and shutil.which("cc"), "model replay needs its scientific dependencies and cc")
    def test_coa_model_replays_from_pinned_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "result"
            subprocess.run([sys.executable, str(DIRECTORY / "coa_replay.py"),
                            str(COA_SOURCES / "FETAL_MODEL_CoA.c"), str(COA_FIGURE), str(output)],
                           check=True, env={**os.environ, "OPENBLAS_NUM_THREADS": "1"})
            actual = {row["site"]: row for row in rows(output / "by-site.tsv")}
        expected = {row["site"]: row for row in rows(DIRECTORY / "coa-replay" / "by-site.tsv")}
        self.assertEqual(actual.keys(), expected.keys())
        for site, reference in expected.items():
            for metric, value in reference.items():
                if metric == "site":
                    continue
                # About two figure columns in phase and 0.05 cm/s for computed velocities.
                tolerance = 0.003 if metric.endswith("_phase") else 0.05
                with self.subTest(site=site, metric=metric):
                    self.assertAlmostEqual(float(actual[site][metric]), float(value), delta=tolerance)
            self.assertLess(float(actual[site]["solver_max_difference_cm_s"]), 0.01, site)
