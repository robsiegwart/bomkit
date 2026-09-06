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
# single_file() — "long" format (single "Parts list" + "BOMs" pair)
# ---------------------------------------------------------------------------

def test_single_file_long_detected_from_dict(long_df):
    bom = BOM.single_file(long_df)
    assert len(bom.assemblies) == 1   # Sub is a child assembly
    assert len(bom.parts) == 1        # P1 is a direct part


def test_single_file_long_detected_from_xlsx(long_xlsx):
    bom = BOM.single_file(long_xlsx)
    assert len(bom.assemblies) == 1
    assert len(bom.parts) == 1


def test_single_file_long_aggregate_multiplies_through_levels(long_df):
    bom = BOM.single_file(long_df)
    agg = bom.aggregate
    assert agg["P1"] == 1
    assert agg["P2"] == 6   # 3 per Sub × 2 Subs
    assert agg["P3"] == 2   # 1 per Sub × 2 Subs


def test_single_file_long_cots_treated_as_part_not_assembly(long_df):
    bom = BOM.single_file(long_df)
    pns = {p.PN for p in bom.flat}
    assert "P3" in pns   # COTS-typed row, not split into the assembly hierarchy
    assert bom.parts_db.get("P3") is not None


def test_single_file_long_assembly_name_from_parts_list(long_df):
    bom = BOM.single_file(long_df)
    sub = bom.assemblies[0]
    assert sub.PN == "Sub"
    assert sub.Name == "Sub assembly"


def test_single_file_long_missing_type_column_raises(long_df):
    del long_df["Parts list"]["Type"]
    with pytest.raises(ValueError):
        BOM.single_file(long_df)


def test_single_file_long_summary_works_on_subassembly(long_df):
    # Regression check for BOM.summary using self.root.parts_db
    bom = BOM.single_file(long_df)
    sub = bom.assemblies[0]
    df = sub.summary
    assert isinstance(df, pd.DataFrame)


def test_single_file_extra_sheet_alongside_boms_raises(long_df):
    # A "BOMs" sheet mixed with additional per-sheet assemblies is ambiguous
    # (is it the long format with a stray extra sheet, or the default format
    # with one assembly literally named "BOMs"?) and must be rejected rather
    # than silently misinterpreted as the default per-sheet format.
    long_df["ExtraAssembly"] = pd.DataFrame([{"PN": "P2", "QTY": 1}])
    with pytest.raises(ValueError):
        BOM.single_file(long_df)


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