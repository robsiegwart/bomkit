'''
Run the program from the command line via python module mode.

> python -m pyBOM FOLDER ACTION

    FOLDER      the folder name containing Excel files
    ACTION      the property to call on the ``BOM`` object

'''

import sys
import argparse
from .BOM import BOM


def main():
    sys.stdout.reconfigure(encoding='utf-8')

    # Browser mode: no args → use cwd; bare path arg → use that directory
    if len(sys.argv) == 1:
        from .browser import run_browser
        run_browser(directory='.')
        return

    if len(sys.argv) == 2 and not sys.argv[1].startswith('-'):
        from .browser import run_browser
        run_browser(directory=sys.argv[1])
        return

    parser = argparse.ArgumentParser(
        prog='pybom',
        description='Parse a folder of Excel Bill-of-Materials.'
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '-f', '--file',
        help='The name of a single Excel BOM file.',
        metavar='FILE'
    )
    group.add_argument(
        '-d', '--dir',
        help='The name of the folder containing Excel BOM files.',
        metavar='FOLDER'
    )
    group.add_argument(
        '-b', '--browse',
        nargs='?',
        const='.',
        metavar='FOLDER',
        help='Open the interactive TUI browser for a folder (default: cwd).',
    )

    parser.add_argument(
        'action',
        nargs='?',
        help='What to do with the resulting BOM.',
        default='tree'
    )

    ns = parser.parse_args()

    if ns.browse is not None:
        from .browser import run_browser
        run_browser(directory=ns.browse)
        return

    if ns.file:
        bom = BOM.single_file(ns.file)
    elif ns.dir:
        bom = BOM.from_folder(ns.dir)

    print(getattr(bom, ns.action))


if __name__ == '__main__':
    main()