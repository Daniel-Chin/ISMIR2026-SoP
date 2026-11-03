import argparse
import functools
import http.server
import sys
import traceback
from pathlib import Path

from .check import find_problems, find_warnings
from .idea_views import restamp, view_statuses
from .load import AI_GENERATED_DIR, SOPError, load_sop
from .site import build_site


def main() -> None:
    parser = argparse.ArgumentParser(
        prog='ismir2026-sop', description='Check the SOP content and build the static site.',
    )
    parser.add_argument('--content', type=Path, default=Path('content'), help='content directory (default: content)')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('check', help='report problems, e.g. misspelled [[Role]] mentions')
    build = sub.add_parser('build', help='check, then write the site')
    build.add_argument('--out', type=Path, default=Path('_site'), help='output directory (default: _site)')
    serve = sub.add_parser('serve', help='build, then serve the site locally')
    serve.add_argument('--out', type=Path, default=Path('_site'), help='output directory (default: _site)')
    serve.add_argument('--port', type=int, default=8000, help='port (default: 8000)')
    views = sub.add_parser('idea-views', help='list the AI-generated views of The Idea and whether they are up to date')
    views.add_argument('--stamp', type=Path, nargs='+', metavar='VIEW',
                       help='after (re)generating these views, mark them as made from the current Idea')
    args = parser.parse_args()

    try:
        sop = load_sop(args.content)
    except SOPError as e:
        traceback.print_exc()
        sys.exit(f'error: {e}')
    problems = find_problems(sop, args.content)
    if problems:
        print(f'{len(problems)} problem(s):', file=sys.stderr)
        for p in problems:
            print(f'  - {p}', file=sys.stderr)
        sys.exit(1)
    for w in find_warnings(sop, args.content):
        print(f'warning: {w}', file=sys.stderr)

    if args.command == 'idea-views':
        if args.stamp:
            restamp(sop, args.stamp)
            sop = load_sop(args.content)
        for v in view_statuses(sop, args.content.parent / AI_GENERATED_DIR):
            print(f'{v.state:10} {v.path}')
        return
    if args.command == 'check':
        print(f'OK: {len(sop.roles)} roles, {len(sop.sessions)} sessions.')
        return
    build_site(sop, args.out, args.content)
    print(f'Built {len(sop.sessions)} sessions into {args.out}/')
    if args.command == 'serve':
        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=args.out)
        with http.server.ThreadingHTTPServer(('localhost', args.port), handler) as server:
            print(f'Serving at http://localhost:{args.port}/ (Ctrl+C to stop)')
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass
