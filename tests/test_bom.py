import pytest
import pandas as pd

from bomkit import BOM
from bomkit.BOM import fn_base


# ---------------------------------------------------------------------------
# fn_base utility
# ---------------------------------------------------------------------------

def test_fn_base_simple():
    assert fn_base("file.xlsx") == "file"


def test_fn_base_dotted_name():
    # Name contains dots before the extension
    assert fn_base("Foo_12.34.xlsx") == "Foo_12.34"


def test_fn_base_list():
    assert fn_base(["a.xlsx", "b.xlsx"]) == ["a", "b"]


# ---------------------------------------------------------------------------
# single_file() — input variants
# ---------------------------------------------------------------------------

def test_single_file_from_dict(simple_df):
    bom = BOM.single_file(simple_df)
    assert "P1" in [n.name for n in bom.flat]


def test_single_file_from_xlsx(simple_xlsx):
    bom = BOM.single_file(simple_xlsx)
    assert "P1" in [n.name for n in bom.flat]


def test_single_file_from_excel_file_object(simple_xlsx):
    ef = pd.ExcelFile(simple_xlsx)
    bom = BOM.single_file(ef)
    assert "P1" in [n.name for n in bom.flat]


def test_single_file_raises_for_one_sheet(tmp_path):
    fn = tmp_path / "one_sheet.xlsx"
    df = pd.DataFrame([{"PN": "P1", "Name": "Part"}])
    with pd.ExcelWriter(fn, engine="openpyxl") as w:
        df.to_excel(w, sheet_name="Parts list", index=False)
    with pytest.raises(Exception):
        BOM.single_file(fn)


# ---------------------------------------------------------------------------
# BOM properties — flat (single-level) BOM
# ---------------------------------------------------------------------------

def test_parts_returns_direct_parts(simple_df):
    bom = BOM.single_file(simple_df)
    pns = {p.PN for p in bom.parts}
    assert {"P1", "P2", "P5", "P7"} == pns


def test_assemblies_empty_for_flat_bom(simple_df):
    bom = BOM.single_file(simple_df)
    assert bom.assemblies == []


def test_flat_contains_all_parts(simple_df):
    bom = BOM.single_file(simple_df)
    pns = {p.name for p in bom.flat}
    assert pns == {"P1", "P2", "P5", "P7"}


def test_qty(simple_df):
    bom = BOM.single_file(simple_df)
    assert bom.QTY("P1") == 2
    assert bom.QTY("P5") == 2


def test_qty_unknown_part_returns_zero(simple_df):
    bom = BOM.single_file(simple_df)
    assert bom.QTY("NONEXISTENT") == 0


def test_aggregate_quantities(simple_df):
    bom = BOM.single_file(simple_df)
    agg = bom.aggregate
    assert agg["P1"] == 2
    assert agg["P5"] == 2


def test_tree_is_string_containing_parts(simple_df):
    bom = BOM.single_file(simple_df)
    tree = bom.tree
    assert isinstance(tree, str)
    assert "P1" in tree


def test_dot_output(simple_df):
    bom = BOM.single_file(simple_df)
    dot = bom.dot
    assert isinstance(dot, str)
    assert len(dot) > 0


def test_summary_dataframe(simple_df):
    bom = BOM.single_file(simple_df)
    df = bom.summary
    assert isinstance(df, pd.DataFrame)
    assert "Total QTY" in df.columns
    assert "Purchase QTY" in df.columns
    p1_qty = df.loc[df["PN"] == "P1", "Total QTY"].iloc[0]
    assert p1_qty == 2


# ---------------------------------------------------------------------------
# Nested assemblies
# ---------------------------------------------------------------------------

def test_nested_assemblies_structure(nested_df):
    bom = BOM.single_file(nested_df)
    assert len(bom.assemblies) == 1   # Sub is a child assembly
    assert len(bom.parts) == 1        # P1 is a direct part


def test_nested_flat_includes_sub_parts(nested_df):
    bom = BOM.single_file(nested_df)
    pns = {p.name for p in bom.flat}
    assert pns == {"P1", "P2", "P3"}


def test_aggregate_multiplies_through_levels(nested_df):
    bom = BOM.single_file(nested_df)
    agg = bom.aggregate
    assert agg["P1"] == 1
    assert agg["P2"] == 6   # 3 per Sub × 2 Subs
    assert agg["P3"] == 2   # 1 per Sub × 2 Subs


# ---------------------------------------------------------------------------
# from_folder()
# ---------------------------------------------------------------------------

def test_from_folder_builds_bom(bom_folder):
    bom = BOM.from_folder(str(bom_folder))
    assert bom is not None
    assert "P1" in [p.name for p in bom.flat]


# ---------------------------------------------------------------------------
# PartsDB
# ---------------------------------------------------------------------------

def test_parts_db_get_known(simple_df):
    bom = BOM.single_file(simple_df)
    item = bom.parts_db.get("P1")
    assert item is not None
    assert item.PN == "P1"


def test_parts_db_get_unknown_returns_none(simple_df):
    bom = BOM.single_file(simple_df)
    assert bom.parts_db.get("UNKNOWN") is None


def test_parts_db_fields(simple_df):
    bom = BOM.single_file(simple_df)
    fields = bom.parts_db.fields
    assert "PN" in fields
    assert "Name" in fields


# ---------------------------------------------------------------------------
# BOM.Name — assembly display name from Excel sheet name
# ---------------------------------------------------------------------------


def test_from_file_name_set_from_meaningful_sheet_name(tmp_path, simple_df):
    fn = tmp_path / 'TR-01.xlsx'
    with pd.ExcelWriter(fn, engine='openpyxl') as w:
        simple_df['Assembly'].to_excel(w, sheet_name='Truck assembly', index=False)
    bom = BOM._from_file(fn)
    assert bom.Name == 'Truck assembly'


def test_from_file_name_is_none_for_generic_sheet_name(tmp_path, simple_df):
    fn = tmp_path / 'Assembly.xlsx'
    with pd.ExcelWriter(fn, engine='openpyxl') as w:
        simple_df['Assembly'].to_excel(w, index=False)  # defaults to 'Sheet1'
    bom = BOM._from_file(fn)
    assert bom.Name is None


def test_from_file_name_is_none_when_sheet_matches_pn(tmp_path, simple_df):
    fn = tmp_path / 'TR-01.xlsx'
    with pd.ExcelWriter(fn, engine='openpyxl') as w:
        simple_df['Assembly'].to_excel(w, sheet_name='TR-01', index=False)
    bom = BOM._from_file(fn)
    assert bom.Name is None