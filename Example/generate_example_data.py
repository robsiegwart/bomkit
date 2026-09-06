'''
Generates the demo BOM data under Example/, for both the multi-file and
single-file input methods (see the README).

This is the single source of truth for the example data: don't hand-edit the
.xlsx files under Example/ directly, edit this script and re-run it instead,
so the two layouts never drift apart.

Usage:
    python Example/generate_example_data.py
'''
import os

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))

PARTS_LIST = pd.DataFrame([
    {"PN": "SK1001-01", "Name": "Deck",      "Description": 'Pavement Pro 9" Maple Deck',       "Supplier": "Grindstone Supply Co.", "Supplier PN": "BRX-02",    "Pkg QTY": 1,  "Pkg Price": 67.95},
    {"PN": "SK1002-01", "Name": "Truck",     "Description": "HollowKing Standard Trucks",       "Supplier": "Grindstone Supply Co.", "Supplier PN": "TR1-A",     "Pkg QTY": 1,  "Pkg Price": 28.95},
    {"PN": "SK1003-01", "Name": "Bearing",   "Description": "ABEC-7 Steel Bearings",            "Supplier": "BoltRun Hardware",      "Supplier PN": "74295-954", "Pkg QTY": 1,  "Pkg Price": 3.49},
    {"PN": "SK1004-01", "Name": "Wheel",     "Description": "SlickCore 54mm Cruiser Wheels",    "Supplier": "Grindstone Supply Co.", "Supplier PN": "WHL-PRX",   "Pkg QTY": 8,  "Pkg Price": 44.95},
    {"PN": "SK1005-01", "Name": "Screw",     "Description": "10-32, 1”, Phillips",              "Supplier": "BoltRun Hardware",      "Supplier PN": "92220A",    "Pkg QTY": 25, "Pkg Price": 12.49},
    {"PN": "SK1006-01", "Name": "Nut",       "Description": "10-32",                            "Supplier": "BoltRun Hardware",      "Supplier PN": "95479A",    "Pkg QTY": 25, "Pkg Price": 9.89},
    {"PN": "SK1007-01", "Name": "Grip tape", "Description": "SuperStick 9”",                    "Supplier": "Grindstone Supply Co.", "Supplier PN": "GTSS99",    "Pkg QTY": 1,  "Pkg Price": 8.95},
])

# PN -> (sheet name used in the multi-file layout, assembly DataFrame)
ASSEMBLIES = {
    "SKA-100": ("Skateboard", pd.DataFrame([
        {"PN": "SK1001-01", "QTY": 1},
        {"PN": "TR-01",     "QTY": 2},
        {"PN": "SK1005-01", "QTY": 8},
        {"PN": "SK1006-01", "QTY": 8},
        {"PN": "SK1007-01", "QTY": 1},
    ])),
    "TR-01": ("Truck assembly", pd.DataFrame([
        {"PN": "SK1002-01", "QTY": 1},
        {"PN": "WH-01",     "QTY": 2},
    ])),
    "WH-01": ("Wheel assembly", pd.DataFrame([
        {"PN": "SK1004-01", "QTY": 1},
        {"PN": "SK1003-01", "QTY": 2},
    ])),
}

# Root assembly first, matching how the single-file workbook is named/ordered
ROOT_PN = "SKA-100"


def write_multi_file(directory: str) -> None:
    os.makedirs(directory, exist_ok=True)
    PARTS_LIST.to_excel(os.path.join(directory, "Parts List.xlsx"), index=False)
    for pn, (sheet_name, df) in ASSEMBLIES.items():
        df.to_excel(os.path.join(directory, f"{pn}.xlsx"), sheet_name=sheet_name, index=False)


def write_single_file(directory: str) -> None:
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, f"{ROOT_PN}.xlsx")
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        PARTS_LIST.to_excel(writer, sheet_name="Parts list", index=False)
        for pn, (_, df) in ASSEMBLIES.items():
            df.to_excel(writer, sheet_name=pn, index=False)

def write_single_file_long(directory: str) -> None:
    '''
    "Long" single-file layout: one workbook with a "Parts list" tab (parts
    and assemblies together, distinguished by a "Type" column) and a "BOMs"
    tab holding every assembly's line items in one long-format table, keyed
    by an "Assy PN" column.
    '''
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, f"{ROOT_PN}.xlsx")

    parts = PARTS_LIST.copy()
    parts.insert(1, "Type", "Part")

    assemblies = pd.DataFrame([
        {"PN": pn, "Name": name, "Type": "Assembly"}
        for pn, (name, _) in ASSEMBLIES.items()
    ])
    parts_list = pd.concat([parts, assemblies], ignore_index=True)[parts.columns]

    boms = pd.concat([
        df.assign(**{"Assy PN": pn})[["Assy PN", "PN", "QTY"]]
        for pn, (_, df) in ASSEMBLIES.items()
    ], ignore_index=True)

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        parts_list.to_excel(writer, sheet_name="Parts list", index=False)
        boms.to_excel(writer, sheet_name="BOMs", index=False)


if __name__ == "__main__":
    write_multi_file(os.path.join(HERE, "Multi-file"))
    write_single_file(os.path.join(HERE, "Single-file"))
    write_single_file_long(os.path.join(HERE, "Single-file-long"))
    print("Wrote example data to Example/Multi-file, Example/Single-file and Example/Single-file-long")
