import pandas as pd
import pytest


@pytest.fixture
def simple_df():
    # One assembly, flat (no sub-assemblies)
    parts_list = pd.DataFrame([
        {"PN": "P1", "Name": "Bearing"},
        {"PN": "P2", "Name": "Board"},
        {"PN": "P3", "Name": "Bracket"},
        {"PN": "P4", "Name": "Shaft"},
        {"PN": "P5", "Name": "Screw"},
        {"PN": "P6", "Name": "Wheel"},
        {"PN": "P7", "Name": "Nut"},
    ])
    assembly = pd.DataFrame([
        {"PN": "P2", "QTY": 1},
        {"PN": "P1", "QTY": 2},
        {"PN": "P5", "QTY": 2},
        {"PN": "P7", "QTY": 2},
    ])
    return {"Parts list": parts_list, "Assembly": assembly}


@pytest.fixture
def simple_xlsx(tmp_path, simple_df):
    fn = tmp_path / "bom.xlsx"
    with pd.ExcelWriter(fn, engine="openpyxl") as w:
        for name, df in simple_df.items():
            df.to_excel(w, sheet_name=name, index=False)
    return fn


@pytest.fixture
def nested_df():
    # Top assembly references a sub-assembly (Sub) used 2 times.
    # Expected aggregates: P1=1, P2=3*2=6, P3=1*2=2
    parts_list = pd.DataFrame([
        {"PN": "P1", "Name": "Bearing"},
        {"PN": "P2", "Name": "Board"},
        {"PN": "P3", "Name": "Bracket"},
    ])
    top = pd.DataFrame([
        {"PN": "P1", "QTY": 1},
        {"PN": "Sub", "QTY": 2},
    ])
    sub = pd.DataFrame([
        {"PN": "P2", "QTY": 3},
        {"PN": "P3", "QTY": 1},
    ])
    return {"Parts list": parts_list, "Top": top, "Sub": sub}


@pytest.fixture
def bom_folder(tmp_path, simple_df):
    # Multi-file layout: Parts list.xlsx + Assembly.xlsx
    with pd.ExcelWriter(tmp_path / "Parts list.xlsx", engine="openpyxl") as w:
        simple_df["Parts list"].to_excel(w, index=False)
    with pd.ExcelWriter(tmp_path / "Assembly.xlsx", engine="openpyxl") as w:
        simple_df["Assembly"].to_excel(w, index=False)
    return tmp_path


@pytest.fixture
def long_df():
    # "Long" single-file format: Top assembly references a sub-assembly (Sub)
    # used 2 times, same structure/expected aggregates as nested_df (P1=1,
    # P2=6, P3=2), but as a single "Parts list" + "BOMs" pair.
    parts_list = pd.DataFrame([
        {"PN": "P1",  "Name": "Bearing",       "Type": "Part"},
        {"PN": "P2",  "Name": "Board",         "Type": "Part"},
        {"PN": "P3",  "Name": "Bracket",       "Type": "COTS"},
        {"PN": "Top", "Name": "Top assembly",  "Type": "Assembly"},
        {"PN": "Sub", "Name": "Sub assembly",  "Type": "Assembly"},
    ])
    boms = pd.DataFrame([
        {"Assy PN": "Top", "PN": "P1",  "QTY": 1},
        {"Assy PN": "Top", "PN": "Sub", "QTY": 2},
        {"Assy PN": "Sub", "PN": "P2",  "QTY": 3},
        {"Assy PN": "Sub", "PN": "P3",  "QTY": 1},
    ])
    return {"Parts list": parts_list, "BOMs": boms}


@pytest.fixture
def long_xlsx(tmp_path, long_df):
    fn = tmp_path / "bom_long.xlsx"
    with pd.ExcelWriter(fn, engine="openpyxl") as w:
        for name, df in long_df.items():
            df.to_excel(w, sheet_name=name, index=False)
    return fn


@pytest.fixture
def nested_bom_folder(tmp_path):
    '''Multi-file folder where the root assembly contains one part and one sub-assembly.'''
    parts = pd.DataFrame([
        {"PN": "P1", "Name": "Bearing"},
        {"PN": "P2", "Name": "Board"},
        {"PN": "P3", "Name": "Bracket"},
    ])
    top = pd.DataFrame([
        {"PN": "P1", "QTY": 1},
        {"PN": "Sub", "QTY": 2},
    ])
    sub = pd.DataFrame([
        {"PN": "P2", "QTY": 3},
        {"PN": "P3", "QTY": 1},
    ])
    with pd.ExcelWriter(tmp_path / "Parts list.xlsx", engine="openpyxl") as w:
        parts.to_excel(w, index=False)
    with pd.ExcelWriter(tmp_path / "Top.xlsx", engine="openpyxl") as w:
        top.to_excel(w, index=False)
    with pd.ExcelWriter(tmp_path / "Sub.xlsx", engine="openpyxl") as w:
        # Sheet name differs from PN — should become Sub.Name
        sub.to_excel(w, sheet_name="Sub Assembly", index=False)
    return tmp_path