'''
Run the program from the command line via python module mode.

> python -m bomkit [PATH] [ACTION]

    PATH        a folder (multi-file layout) or a single Excel file
                (single-file layout) containing BOM data. Defaults to the
                current directory.
    ACTION      the property to call on the resulting ``BOM`` object. If
                omitted, opens the interactive TUI browser instead.

'''

import glob
import os
import sys
import argparse
from .BOM import BOM


def _load_bom(path: str) -> BOM:
    '''
    Load a BOM from *path*, which may be either a folder (multi-file layout)
    or a single ``.xlsx`` file (single-file layout).
    '''
    path = os.path.abspath(path)
    try:
        if os.path.isfile(path):
            return BOM.single_file(path)
        return _load_from_directory(path)
    except FileNotFoundError:
        print(f"Error: No BOM data found in {path}")
        print("Expected either a 'Parts list.xlsx' file plus assembly files "
              "(multi-file layout), or a single Excel file (single-file layout).")
        sys.exit(1)
    except Exception as e:
        print(f'Error loading BOM: {e}')
        sys.exit(1)


def _load_from_directory(directory: str) -> BOM:
    '''
    Load a BOM from *directory*. Tries the multi-file layout first; if no
    parts-list file is found and the directory contains exactly one
    ``.xlsx`` file, falls back to treating that file as a single-file BOM
    (a multi-file layout always needs at least two .xlsx files, so a lone
    file is unambiguously the single-file case).
    '''
    try:
        return BOM.from_folder(directory)
    except FileNotFoundError:
        xlsx_files = [
            f for f in glob.glob(os.path.join(directory, '*.xlsx'))
            if not os.path.basename(f).startswith(('_', '~'))
        ]
        if len(xlsx_files) == 1:
            return BOM.single_file(xlsx_files[0])
        raise


def main():
    sys.stdout.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(
        prog='bomkit',
        description='Parse a folder or Excel file of Bill-of-Materials data.'
    )
    parser.add_argument(
        'path',
        nargs='?',
        default='.',
        metavar='PATH',
        help='Folder or Excel file containing BOM data (default: current directory).'
    )
    parser.add_argument(
        'action',
        nargs='?',
        default=None,
        help='What to do with the resulting BOM. If omitted, opens the '
             'interactive TUI browser.'
    )

    ns = parser.parse_args()
    bom = _load_bom(ns.path)

    if ns.action is None:
        from .browser import run_browser
        run_browser(bom)
        return

    print(getattr(bom, ns.action))


if __name__ == '__main__':
    main()
