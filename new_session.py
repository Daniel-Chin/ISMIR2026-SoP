"""Generate boilerplate JSON + MD for a new session in content/sessions/."""

import json
import re
from pathlib import Path

SESSIONS = Path(__file__).parent / 'content' / 'sessions'

TEMPLATE = '''{{
  "name": {name},
  "the_idea_markdown_path": {md},
  "staffing": [
    {{"role": "TODO", "count": 1}}
  ],
  "runsheet": [
    {{
      "time_info": "T",
      "roles": ["TODO"],
      "short_description": "TODO",
      "more_info": ""
    }}
  ]
}}
'''


def main() -> None:
    name = input('Session Type: ').strip()
    index = int(input('Index for sorting: ').strip())

    stem = f'{index:02d}-' + re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    json_path = SESSIONS / f'{stem}.json'
    md_path = SESSIONS / f'{stem}.md'
    for p in (json_path, md_path):
        if p.exists():
            raise SystemExit(f'{p} already exists')

    json_path.write_text(TEMPLATE.format(
        name=json.dumps(name, ensure_ascii=False),
        md=json.dumps(md_path.name),
    ))
    md_path.write_text('...\n')
    print(f'Created {json_path}\nCreated {md_path}')


if __name__ == '__main__':
    main()
