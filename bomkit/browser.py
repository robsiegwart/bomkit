'''
Interactive TUI browser for bomkit, powered by Textual.

Launched via ``python -m bomkit [directory]`` or ``bomkit [directory]``.
Arrow keys navigate the list; Enter drills into an assembly or opens a part detail
view; Escape / Left arrow goes back.  T/P/A/S show BOM analysis overlays.
'''

from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

import pandas as pd
from rich.markup import escape as markup_escape
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import ScrollableContainer
from textual.screen import ModalScreen, Screen
from textual.widgets import Footer, Header, Label, ListItem, ListView, Static

if TYPE_CHECKING:
    from .BOM import BOM


def _resolve(item):
    '''Follow an ItemLink to its target; return plain items unchanged.'''
    return item.target if hasattr(item, 'target') else item


def _get_name(item) -> str:
    '''Return the Name for any BOM item (Item or BOM), handling missing/NaN.'''
    raw = getattr(item, 'Name', None)
    if raw is None:
        return ''
    try:
        return '' if pd.isna(raw) else str(raw)
    except TypeError:
        return str(raw)


def _collect_assemblies(bom: BOM, result: list | None = None) -> list:
    '''Recursively collect all BOM nodes in depth-first order.'''
    if result is None:
        result = []
    result.append(bom)
    for sub in bom.assemblies:
        _collect_assemblies(sub, result)
    return result


# ---------------------------------------------------------------------------
# Content modal — overlay shown by T / P / A / S key bindings
# ---------------------------------------------------------------------------

class ContentModal(ModalScreen):
    '''Scrollable overlay that displays the text output of a BOM command.'''

    DEFAULT_CSS = '''
    ContentModal {
        align: center middle;
    }
    ContentModal > ScrollableContainer {
        background: $surface;
        border: thick $primary;
        width: 90%;
        height: 80%;
        padding: 1 2;
        overflow: auto auto;
    }
    '''

    BINDINGS = [
        Binding('escape', 'dismiss', 'Close', show=True),
        Binding('q', 'dismiss', 'Close', show=True),
    ]

    def __init__(self, title: str, content: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self._modal_title = title
        self._content = content

    def compose(self) -> ComposeResult:
        with ScrollableContainer():
            yield Static(f'[bold]{markup_escape(self._modal_title)}[/bold]\n\n{markup_escape(self._content)}')

    def on_mount(self) -> None:
        lines = self._content.split('\n')
        max_len = max(
            max((len(line) for line in lines), default=0),
            len(self._modal_title),
        ) + 2
        self.query_one(Static).styles.width = max_len


# ---------------------------------------------------------------------------
# Screens
# ---------------------------------------------------------------------------

class AssemblyScreen(Screen):
    '''A navigable list of the children of one BOM node.'''

    BINDINGS = [
        Binding('escape', 'back', 'Back', show=True),
        Binding('left', 'back', 'Back', show=False),
        Binding('q', 'app.quit', 'Quit', show=True),
    ]

    def __init__(self, bom: BOM, root_bom: BOM, **kwargs) -> None:
        super().__init__(**kwargs)
        self.bom = bom
        self.root_bom = root_bom
        self._items = [_resolve(c) for c in bom.children]
        self._qtys = [bom.QTY(item.PN) for item in self._items]
        _max_qty = max(self._qtys, default=1)
        self._qty_col_width = len(f'({_max_qty})   ') if _max_qty > 1 else 0

    # ------------------------------------------------------------------
    # Compose / lifecycle
    # ------------------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Header()
        if self._items:
            yield ListView(
                *[
                    ListItem(Label(self._label(item, self._qtys[i])), id=f'item_{i}')
                    for i, item in enumerate(self._items)
                ]
            )
        else:
            yield Static('(no items)')
        yield Footer()

    def on_mount(self) -> None:
        self.app.sub_title = self.app._breadcrumb()

    def on_screen_resume(self) -> None:
        self.app.sub_title = self.app._breadcrumb()

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        idx = int(event.item.id.split('_', 1)[1])
        item = self._items[idx]
        if getattr(item, 'item_type', None) == 'assembly':
            self.app.push_screen(AssemblyScreen(item, self.root_bom))
        else:
            self.app.push_screen(PartScreen(item.PN, self.root_bom))

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_back(self) -> None:
        if self.bom is not self.app.root_bom:
            self.app.pop_screen()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _label(self, item, qty: int) -> str:
        pn = getattr(item, 'PN', '?')
        is_assembly = getattr(item, 'item_type', None) == 'assembly'
        prefix = '[A]' if is_assembly else '[P]'
        name = _get_name(item)
        if self._qty_col_width > 0:
            qty_str = f'({qty})   '.ljust(self._qty_col_width) if qty > 1 else ' ' * self._qty_col_width
        else:
            qty_str = ''
        pn_safe = markup_escape(str(pn)).ljust(20)
        name_safe = markup_escape(name)
        if is_assembly:
            return f'{prefix} {qty_str}[bold cyan]{pn_safe}[/bold cyan]{name_safe}'
        return f'{prefix} {qty_str}{pn_safe}{name_safe}'


class PartScreen(Screen):
    '''Displays all database properties for a single part.'''

    BINDINGS = [
        Binding('escape', 'app.pop_screen', 'Back', show=True),
        Binding('left', 'app.pop_screen', 'Back', show=False),
        Binding('q', 'app.quit', 'Quit', show=True),
    ]

    def __init__(self, pn: str, root_bom: BOM, **kwargs) -> None:
        super().__init__(**kwargs)
        self.pn = pn
        self.root_bom = root_bom

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(self._build_content())
        yield Footer()

    def on_mount(self) -> None:
        self.app.sub_title = self.app._breadcrumb()

    def _build_content(self) -> str:
        parts_db = self.root_bom.parts_db
        if parts_db is not None:
            row = parts_db.df[parts_db.df['PN'] == self.pn]
            if not row.empty:
                props = row.iloc[0].to_dict()
                lines = []
                for key, value in props.items():
                    try:
                        if pd.isna(value):
                            continue
                    except TypeError:
                        pass
                    lines.append(f'{key:<20}{value}')
                return '\n'.join(lines)
        return f'PN: {self.pn}\n(no properties found in parts database)'


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

class BomBrowserApp(App):
    '''Textual TUI browser for a bomkit hierarchy.'''

    TITLE = 'bomkit Browser'
    ENABLE_COMMAND_PALETTE = False

    BINDINGS = [
        Binding('t', 'tree', 'Tree', show=True),
        Binding('p', 'parts', 'Parts', show=True),
        Binding('a', 'assemblies', 'Assemblies', show=True),
        Binding('s', 'summary', 'Summary', show=True),
    ]

    def __init__(self, bom: BOM) -> None:
        super().__init__()
        self.root_bom = bom

    def on_mount(self) -> None:
        self.push_screen(AssemblyScreen(self.root_bom, self.root_bom))

    def _breadcrumb(self) -> str:
        '''Build a " > "-separated path from the current screen stack.'''
        segments = []
        for screen in self.screen_stack:
            if isinstance(screen, AssemblyScreen):
                segments.append(screen.bom.PN or 'Root')
            elif isinstance(screen, PartScreen):
                segments.append(screen.pn)
        return ' > '.join(segments)

    # ------------------------------------------------------------------
    # BOM analysis actions — bound to T / P / A / S
    # ------------------------------------------------------------------

    def action_tree(self) -> None:
        self.push_screen(ContentModal('BOM Tree', str(self.root_bom.tree)))

    def action_parts(self) -> None:
        bom = self.root_bom
        counts = bom.aggregate
        if not counts:
            content = 'No parts found.'
        else:
            df = bom.parts_db.df.copy()
            df = df[df['PN'].isin(counts)].dropna(axis=1, how='all')
            content = df.to_string(index=False)
        self.push_screen(ContentModal('Parts List', content))

    def action_assemblies(self) -> None:
        bom = self.root_bom
        rows = [(asm.PN or '', _get_name(asm)) for asm in _collect_assemblies(bom)]
        if not rows:
            content = 'No assemblies found.'
        else:
            pn_width = max(len(r[0]) for r in rows) + 2
            has_names = any(r[1] for r in rows)
            if has_names:
                content = '\n'.join(f'{pn:{pn_width}}{name}' for pn, name in rows)
            else:
                content = '\n'.join(pn for pn, _ in rows)
        self.push_screen(ContentModal('Assemblies', content))

    def action_summary(self) -> None:
        bom = self.root_bom
        try:
            df = bom.summary.dropna(axis=1, how='all')
            content = df.to_string(index=False)
        except Exception as e:
            content = f'Error: {e}'
        self.push_screen(ContentModal('BOM Summary', content))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run_browser(directory: str = '.') -> None:
    '''
    Load BOMs from *directory* and open the interactive TUI browser.

    :param str directory: Path to the folder containing BOM Excel files.
                          Defaults to the current working directory.
    '''
    from .BOM import BOM

    directory = os.path.abspath(directory)
    try:
        bom = BOM.from_folder(directory)
    except FileNotFoundError:
        print(f"Error: No 'Parts list.xlsx' found in {directory}")
        print('Make sure the directory contains BOM Excel files.')
        sys.exit(1)
    except Exception as e:
        print(f'Error loading BOM: {e}')
        sys.exit(1)

    BomBrowserApp(bom).run()
