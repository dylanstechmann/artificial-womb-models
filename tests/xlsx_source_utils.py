"""Small stdlib-only OOXML reader for pinned source-workbook regression tests."""

import posixpath
import xml.etree.ElementTree as ET
import zipfile


MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
DOC_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PACKAGE_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"


def xlsx_sheet_cells(path):
    """Return ``sheet -> cell -> {value, formula}`` for an XLSX file."""
    q = lambda name: f"{{{MAIN_NS}}}{name}"
    with zipfile.ZipFile(path) as archive:
        members = set(archive.namelist())
        shared_strings = []
        if "xl/sharedStrings.xml" in members:
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            shared_strings = ["".join(node.itertext()) for node in root.findall(q("si"))]

        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        targets = {
            relation.attrib["Id"]: relation.attrib["Target"]
            for relation in relationships.findall(f"{{{PACKAGE_REL_NS}}}Relationship")
        }
        result = {}
        for sheet in workbook.find(q("sheets")):
            target = targets[sheet.attrib[f"{{{DOC_REL_NS}}}id"]]
            sheet_path = (target.lstrip("/") if target.startswith("/")
                          else posixpath.normpath(posixpath.join("xl", target)))
            root = ET.fromstring(archive.read(sheet_path))
            cells = {}
            for cell in root.iter(q("c")):
                raw = cell.findtext(q("v"))
                cell_type = cell.attrib.get("t")
                if cell_type == "s" and raw is not None:
                    value = shared_strings[int(raw)]
                elif cell_type == "inlineStr":
                    value = "".join(cell.find(q("is")).itertext())
                elif raw is None:
                    value = None
                elif cell_type in ("str", "e"):
                    value = raw
                elif cell_type == "b":
                    value = raw == "1"
                else:
                    value = float(raw)
                formula = cell.findtext(q("f"))
                cells[cell.attrib["r"]] = {
                    "value": value,
                    "formula": f"={formula}" if formula is not None else None,
                }
            result[sheet.attrib["name"]] = cells
        return result
