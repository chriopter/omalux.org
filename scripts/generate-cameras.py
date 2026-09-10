#!/usr/bin/env python3
"""Collect the camera presets of a local Omalux checkout into src/data/cameras.json."""
import argparse
import json
import os
from pathlib import Path
from xml.etree import ElementTree as ET

SITE = Path(__file__).resolve().parents[1]
MODULE_NAMES = {'lens': 'lens correction', 'colorin': 'input color profile',
                'temperature': 'white balance', 'exposure': 'exposure',
                'denoiseprofile': 'denoise (profiled)', 'sharpen': 'sharpen'}


def collect(app):
    root = app / 'catalog/camera'
    if not root.is_dir():
        raise ValueError(f'No camera catalogue at {root}')
    entries = []
    for path in sorted(root.rglob('*.dtpreset')):
        preset = ET.parse(path).getroot().find('preset')
        get = lambda tag: (preset.findtext(tag) or '').strip()
        operation = get('operation')
        profile = path.with_suffix('.icc')
        entries.append({
            'id': path.relative_to(root).with_suffix('').as_posix(),
            'name': get('name'),
            'description': get('description'),
            'maker': get('maker'),
            'model': get('model'),
            'module': MODULE_NAMES.get(operation, operation),
            'automatic': get('autoapply') == '1',
            'files': [path.name] + ([profile.name] if profile.is_file() else []),
        })
    if not entries:
        raise ValueError('No camera presets found')
    return entries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--app', default=os.environ.get('OMALUX_APP_ROOT', str(SITE.parent / 'omalux')))
    args = parser.parse_args()
    entries = collect(Path(args.app).resolve())
    destination = SITE / 'src/data/cameras.json'
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(entries, ensure_ascii=False, indent=2) + '\n')
    print(f'{destination.relative_to(SITE)}: {len(entries)} camera presets')
    for entry in entries:
        print(f"  {entry['maker']} / {entry['model']}: {entry['module']}"
              f"{' · automatic' if entry['automatic'] else ''}")


if __name__ == '__main__':
    main()
