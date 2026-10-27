import argparse
import functools
import http.server
import sys
from pathlib import Path

from .check import find_problems
from .load import SoPError, load_sop
from .site import build_site


def main() -> None:
    parser = argparse.ArgumentParser(
        prog='ismir2026-sop', description='Check the SoP content and build the static site.',
    )
    parser.add_argument('--content', type=Path, default=Path('content'), help='content directory (default: content)')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('check', help='report problems, e.g. misspelled [[Role]] mentions')
    build = sub.add_parser('build', help='check, then write the site')
    build.add_argument('--out', type=Path, default=Path('_site'), help='output directory (default: _site)')
    serve = sub.add_parser('serve', help='build, then serve the site locally')
    serve.add_argument('--out', type=Path, default=Path('_site'), help='output directory (default: _site)')
    serve.add_argument('--port', type=int, default=8000, help='port (default: 8000)')
    args = parser.parse_args()

    try:
        sop = load_sop(args.content)
    except SoPError as e:
        sys.exit(f'error: {e}')
    problems = find_problems(sop)
    if problems:
        print(f'{len(problems)} problem(s):', file=sys.stderr)
        for p in problems:
            print(f'  - {p}', file=sys.stderr)
        sys.exit(1)

    if args.command == 'check':
        print(f'OK: {len(sop.roles)} roles, {len(sop.sessions)} sessions.')
        return
    build_site(sop, args.out)
    print(f'Built {len(sop.sessions)} sessions into {args.out}/')
    if args.command == 'serve':
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=args.out)
        with http.server.ThreadingHTTPServer(('localhost', args.port), handler) as server:
            print(f'Serving at http://localhost:{args.port}/ (Ctrl+C to stop)')
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass
