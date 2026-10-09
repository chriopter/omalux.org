#!/usr/bin/env python3
"""Collect the camera presets and film profiles of a local Omalux checkout.

Writes src/data/cameras.json (per-camera presets), src/data/films.json (film profile
groups) and, where the catalogue has thumbnails for film profiles, public/cameras/.
Lookup tables and presets stay in the app checkout; only their names are recorded.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from xml.etree import ElementTree as ET

import catalogue

SITE = Path(__file__).resolve().parents[1]
MODULE_NAMES = {'lens': 'lens correction', 'colorin': 'input color profile',
                'temperature': 'white balance', 'exposure': 'exposure',
                'denoiseprofile': 'denoise (profiled)', 'sharpen': 'sharpen'}
THUMBNAIL_WIDTH = 240


def collect(app):
    root = app / 'catalog/camera'
    if not root.is_dir():
        raise ValueError(f'No camera catalogue at {root}')
    entries = []
    for path in sorted(root.rglob('*.dtpreset')):
        if path.relative_to(root).parts[0] in catalogue.FILM_GROUPS:
            continue
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


def lut_root(app, films):
    """The folder darktable's 3D LUT root has to be, read from what the presets select.

    Returns the folder relative to the checkout, or None when the presets do not say
    (no preset, not a LUT 3D preset) or do not agree.
    """
    roots = set()
    for film in films:
        for variant in film['variants']:
            selected = variant['preset'] and catalogue.lut_path_in_preset(variant['preset'])
            if not selected:
                return None
            lut = variant['lut'].relative_to(app).as_posix()
            if lut != selected and not lut.endswith('/' + selected):
                raise ValueError(f"{variant['preset']}: selects \"{selected}\", which is not "
                                 f"{lut}; the preset would not find its lookup table")
            roots.add(lut[:-len(selected)].rstrip('/'))
    return roots.pop() if len(roots) == 1 else None


def collect_films(app, staging):
    """Film groups for films.json; thumbnails are converted into `staging`."""
    root = app / 'catalog/camera'
    groups, images, image_bytes, file_bytes = [], 0, 0, 0
    for group in catalogue.FILM_GROUPS:
        films = catalogue.collect_films(root, group)
        if not films:
            continue
        out = []
        for film in films:
            variants = []
            for variant in film['variants']:
                files = [f for f in (variant['lut'], variant['preset']) if f]
                file_bytes += sum(f.stat().st_size for f in files)
                item = {'variant': variant['variant'],
                        'files': [f.relative_to(root / group).as_posix() for f in files]}
                if variant['description']:
                    item['description'] = variant['description']
                if variant['thumbnail']:
                    if not shutil.which('magick'):
                        raise ValueError('ImageMagick (magick) is required for film thumbnails')
                    name = catalogue.slug(f"{film['brand']} {film['name']} {variant['variant']}") + '.webp'
                    target = staging / group / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    subprocess.run(['magick', str(variant['thumbnail']), '-auto-orient', '-resize',
                                    f'{THUMBNAIL_WIDTH}x{THUMBNAIL_WIDTH}>', '-strip', '-quality', '80',
                                    str(target)], check=True)
                    size = subprocess.check_output(
                        ['magick', 'identify', '-format', '%w %h', str(target)], text=True)
                    width, height = map(int, size.split())
                    item['thumbnail'] = {'image': f'/cameras/{group}/{name}', 'width': width, 'height': height}
                    images += 1
                    image_bytes += target.stat().st_size
                variants.append(item)
            entry = {'name': film['name'], 'variants': variants}
            if film['brand']:
                entry['brand'] = film['brand']
            out.append(entry)
        groups.append({'id': group, 'label': catalogue.label(group),
                       'folder': f'catalog/camera/{group}',
                       'lut_root': lut_root(app, films), 'films': out})
    return groups, images, image_bytes, file_bytes


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--app', default=os.environ.get('OMALUX_APP_ROOT', str(SITE.parent / 'omalux')))
    args = parser.parse_args()
    app = Path(args.app).expanduser().resolve()
    try:
        entries = collect(app)
        # Stage thumbnails beside their destination; a failure keeps the previous ones.
        with tempfile.TemporaryDirectory(prefix='.cameras-stage-', dir=SITE) as staging:
            staged = Path(staging) / 'cameras'
            staged.mkdir()
            groups, images, image_bytes, file_bytes = collect_films(app, staged)
            destination = SITE / 'public/cameras'
            if destination.exists():
                shutil.rmtree(destination)
            if images:
                destination.parent.mkdir(exist_ok=True)
                staged.rename(destination)
    except (OSError, ValueError, ET.ParseError, subprocess.SubprocessError) as error:
        parser.exit(1, f'Generation failed; nothing was changed: {error}\n')
    write_json(SITE / 'src/data/cameras.json', entries)
    write_json(SITE / 'src/data/films.json', {'groups': groups})
    print(f'src/data/cameras.json: {len(entries)} camera presets')
    for entry in entries:
        print(f"  {entry['maker']} / {entry['model']}: {entry['module']}"
              f"{' · automatic' if entry['automatic'] else ''}")
    print(f'src/data/films.json: {len(groups)} film profile groups')
    for group in groups:
        profiles = sum(len(film['variants']) for film in group['films'])
        print(f"  {group['label']}: {len(group['films'])} films, {profiles} profiles, "
              f"3D LUT root: {group['lut_root'] or 'not stated by the presets'}")
    if groups:
        print(f'  public/cameras/: {images} thumbnails, {image_bytes / 1e6:.1f} MB')
        print(f'  not copied: lookup tables and presets, {file_bytes / 1e6:.1f} MB in the app checkout')


if __name__ == '__main__':
    main()
