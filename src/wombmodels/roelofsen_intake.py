"""Candidate transcription of source cells; no biological independence or fit."""
from __future__ import annotations

import csv
import io

from .artifacts import sha256
from .observations import validate_dataset

ARTICLE_URL = "https://link.springer.com/article/10.1007/s00204-026-04418-8"
SUPPLEMENT_URL = ("https://media.springernature.com/original/springer-static/esm/"
    "art%3A10.1007%2Fs00204-026-04418-8/MediaObjects/204_2026_4418_MOESM1_ESM.docx")
LICENSE_NOTE = "Article CC BY 4.0; source-specific reuse review pending"


def candidate_intake(tables, filename, source_digest):
    """Use already bounded, source-validated tables; retain literal numeric text."""
    artifact = {"artifact_id": "roelofsen-supplement-source", "uri": SUPPLEMENT_URL,
        "license": LICENSE_NOTE, "sha256": source_digest, "retrieved_on": "2026-10-09", "local_path": filename}
    cells, observations = [], []
    for table in tables:
        rows = list(csv.reader(io.StringIO(table["csv_raw"].decode("utf-8"))))
        slots = table["replicate_slots_per_set"]
        for row_number, row in enumerate(rows, 1):
            for column, lexeme in enumerate(row[1:], 2):
                set_index, slot_index = divmod(column-2, slots)
                record_id = f"roelofsen-o{table['object_index']}-{table['table_id'].lower()}-r{row_number}-c{column}"
                trajectory = table["object_index"] == 5
                time_text = row[0] if trajectory else "180"
                time_unit = table["measurement_time_unit"]
                source_set = table["source_set_titles"][set_index]
                locator = (f"{table['source_figure']}; word/embeddings/oleObject{table['object_index']}.bin"
                    f"::CONTENTS[4:]::{table['csv_member']}; CSV row {row_number}, column {column} (1-based, no header)")
                cells.append({"record_id":record_id, "object_index":table["object_index"], "source_figure":table["source_figure"],
                    "table_id":table["table_id"], "csv_member":table["csv_member"], "csv_sha256":sha256(table["csv_raw"]),
                    "row_1based":row_number, "column_1based":column, "set_id":table["source_set_ids"][set_index],
                    "source_set_title":source_set, "slot_1based":slot_index+1,
                    "source_row_label": "" if trajectory else row[0], "numeric_text":lexeme,
                    "value":float(lexeme), "reported_unit":"% of initial dose",
                    "measurement_time_numeric_text":time_text, "measurement_time_unit":time_unit,
                    "time_definition_source":table.get("axis_metadata_member") if trajectory else "Supplementary Fig. S10 caption",
                    "source_locator":locator})
                endpoint = ("Circulation percentage of initial dose: " if trajectory else "Tissue percentage of initial dose: ") + source_set
                observations.append({"schema_version":1, "record_id":record_id,
                    "evidence_status":"author_reported_summary", "species":"human", "stage_track":"organoid_or_tissue_model",
                    "developmental_interval":{"label":"Term placental tissue; exact donor gestational ages unqualified",
                        "time_unit":"not_reported", "start":None, "end":None, "stage_source_artifact_id":artifact["artifact_id"]},
                    "model_system":{"kind":"other", "label":"Ex vivo human placental perfusion; compounds in mixture; included successful experiments"},
                    "assay":{"name":"Published placental-perfusion " + table["source_figure"],
                        "endpoint":endpoint, "unit":"% of initial dose", "measurement_role":"function"},
                    "independent_unit":{"kind":"not_reported", "id":None, "parent_id":None,
                        "hierarchy_note":"Native slot and tissue-row labels retained as source locators; donor/experiment mapping across times, compartments, compounds and tissue is unverified."},
                    "observation":{"value":float(lexeme), "measurement_time":float(time_text),
                        "measurement_time_unit":time_unit, "comparator_id":None, "replicate_role":"not_reported",
                        "measurement_uncertainty":None},
                    "source":{key:artifact[key] for key in ("artifact_id","uri","license","sha256","retrieved_on")},
                    "limitations":["Original-value locator: " + locator + ".",
                        f"Source set: {source_set}; slot {slot_index+1}; source row label: {row[0] if not trajectory else 'none'}. Numeric lexeme: {lexeme}.",
                        "Author-processed source percentage, not an original instrument concentration or independently qualified donor observation.",
                        "Assay elapsed time is distinct from donor tissue age and embryo/fetal developmental time.",
                        "Selected successful experiments; starting attempts, failed/excluded attempts and inclusion reasons remain unqualified.",
                        "No within-slot, cross-compartment, cross-compound or tissue pairing is asserted; no uncertainty, rate, mass balance or model parameter is estimated."]})
    qualification = {"schema_version":1, "source_review_status":"candidate", "human_review":"pending",
        "n_transcribed_y_cells":len(cells), "n_verified_biological_unit_ids":0,
        "native_time_axis":"Time (min) metadata is explicitly referenced by each XY table.",
        "tissue_elapsed_time":"180 minutes from Supplementary Fig. S10 caption; not from a native X column.",
        "cohort":{"reported_included_biological_replicates":4, "starting_attempts":None,
            "failed_or_excluded_attempts":None, "selection":"Transfer-based successful-perfusion criterion, supplement paragraph 17.",
            "success_fraction":"not_estimable_from_inspected_tables"},
        "questions":[{"question":"Can the selected published percentage/time cells be traced to exact native source locations?",
            "status":"candidate_transcription_available; human review pending"},
            {"question":"Can within-donor circulation trajectories be linked to each other and tissue endpoints?", "status":"not_qualified"},
            {"question":"Can amount/rate accounting or dynamic transport parameters be fitted?", "status":"not_eligible_from_inspected_inputs"},
            {"question":"What fraction of starting attempts succeeds?", "status":"unknown_starting_and_excluded_roster"}],
        "missing":["Authenticated donor/experiment/replicate/subsample mapping and complete starting/excluded roster.",
            "Original concentration and calibration records, normalization denominators, volume/collection histories and correction ancestry.",
            "Cross-table linkage, uncertainty, prespecified analysis contract and source-specific human review."],
        "model_fit_performed":False, "biological_assay_performed":False, "developmental_continuity":"not_assessed"}
    data = {"schema_version":1, "dataset_id":"roelofsen-native-perfusion-candidate",
        "title":"Candidate native S9 circulation and S10 tissue percentage cells",
        "source_revision":{"revision_id":"roelofsen-native-agent-intake-2026-10-09",
            "citation":"Roelofsen et al. (2026), Comparison of ex vivo placenta perfusion and in vitro BeWo b30 cell models. Archives of Toxicology; Supplementary Figs. S9 and S10.",
            "source_kind":"peer_reviewed_human_invitro", "source_url":ARTICLE_URL,
            "review_status":"candidate", "reviewer":"", "reviewed_on":None, "review_note":""},
        "artifacts":[artifact], "observations":observations, "transitions":[],
        "limitations":["Native source slots are not authenticated biological identities; no independence or pairing is inferred.",
            "Source percentages are processed quantities; source scope and model-fit eligibility require human review.",
            "Included successful experiments do not establish a starting-cohort success rate or complete gestation."]}
    return cells, validate_dataset(data), qualification
