#!/usr/bin/env python3
"""Render the website's style catalogue through a local Omalux/darktable checkout."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from xml.etree import ElementTree as ET

import catalogue

SITE = Path(__file__).resolve().parents[1]
THUMB_BOX = (320, 240)


def web_image(source, destination, box=(640, 480), quality=88):
    destination.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['magick', str(source), '-auto-orient', '-resize', f'{box[0]}x{box[1]}>',
                    '-strip', '-quality', str(quality), str(destination)], check=True)
    size = subprocess.check_output(['magick', 'identify', '-format', '%w %h', str(destination)], text=True)
    width, height = map(int, size.split())
    if not 0 < width <= box[0] or not 0 < height <= box[1]:
        raise ValueError(f'Invalid preview dimensions: {destination}')
    return {'width': width, 'height': height}


def draft_renders(app, style_root, ids, renders):
    """The exporter's manifest without the engine: the catalogue's own small thumbnails and
    what the style files say. For checking the page layout, not for publishing."""
    version, items = '', []
    for id in ids:
        folder = style_root / Path(id).parent
        info = ET.parse(style_root / id).getroot()
        thumbnail = folder / 'thumbnail.jpg'
        if not thumbnail.is_file():
            items.append({'id': id, 'error': 'no thumbnail.jpg'})
            continue
        (renders / id).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(thumbnail, renders / (id + '.png'))
        try:
            version = json.loads((folder / 'style.json').read_text())['preview']['darktable_version']
        except (OSError, KeyError, ValueError):
            pass
        items.append({
            'id': id, 'name': info.findtext('info/name') or Path(id).parent.name,
            'description': info.findtext('info/description') or '',
            'modules': [{'name': catalogue.MODULE_NAMES.get(op, op), 'enabled': plugin.findtext('enabled') == '1'}
                        for plugin in info.iter('plugin') for op in [plugin.findtext('operation') or '']],
        })
    shutil.copyfile(app / 'assets/images/beach-volleyball.jpg', renders / 'original.png')
    (renders / 'catalog.json').write_text(json.dumps({'darktable_version': version, 'styles': items}))


def generate(app, draft=False):
    launcher = app / 'development/start'
    source = app / 'assets/images/beach-volleyball.jpg'
    if not (draft or launcher.is_file()) or not source.is_file():
        raise ValueError('Expected an Omalux checkout with development/start and the shared beach image')
    if not shutil.which('magick'):
        raise ValueError('ImageMagick (magick) is required')
    style_root = app / 'catalog/styles'
    styles = sorted(style_root.rglob('style.dtstyle'))
    if not styles:
        raise ValueError('No style bundles found')
    ids = [p.relative_to(style_root).as_posix() for p in styles]
    public = SITE / 'public'
    public.mkdir(exist_ok=True)
    # Temporary render/session data never enter public/ or the repository.
    with tempfile.TemporaryDirectory(prefix='omalux-gallery-') as tmp:
        work = Path(tmp)
        renders = work / 'renders'
        renders.mkdir()
        env = {k: v for k, v in os.environ.items()
               if not k.startswith(('OMALUX_', 'QT_QPA_', 'QT_QUICK_', 'QSG_'))}
        env.update(OMALUX_PREVIEW_DIR=str(renders), OMALUX_PREVIEW_IDS=json.dumps(ids),
                   OMALUX_STYLES_DIR=str(style_root), XDG_CONFIG_HOME=str(work / 'config'),
                   QT_QPA_PLATFORM='offscreen', QT_FORCE_STDERR_LOGGING='1', LC_ALL='C.UTF-8')
        if draft:
            print(f'Draft: {len(ids)} styles from the catalogue thumbnails, no engine…', flush=True)
            draft_renders(app, style_root, ids, renders)
        else:
            print(f'Rendering {len(ids)} styles with local darktable…', flush=True)
            subprocess.run([str(launcher), str(source)], cwd=app, env=env, check=True,
                           timeout=max(600, 20 * len(ids)))
        manifest = json.loads((renders / 'catalog.json').read_text())
        catalog = {p['id']: p for p in manifest['styles']}
        # Stage the entire replacement next to its destination, on the same filesystem.
        with tempfile.TemporaryDirectory(prefix='.styles-stage-', dir=SITE) as staging:
            staged = Path(staging) / 'styles'
            staged.mkdir()
            web_image(renders / 'original.png', staged / 'original.webp')
            for id in ids:
                item = catalog[id]
                if item.get('error'):
                    raise ValueError(f"{id}: {item['error']}")
                folder = Path(id).parent
                output = folder / 'preview.webp'
                dimensions = web_image(renders / (id + '.png'), staged / output)
                # The grid's small rendition; preview.webp stays the comparison image.
                web_image(renders / (id + '.png'), staged / folder / 'thumb.webp', THUMB_BOX, 80)
                family, subgroup = catalogue.style_groups(folder)
                group = ' · '.join(filter(None, (family, subgroup)))
                modules = [{'name': m['name'], 'enabled': m['enabled']} for m in item.get('modules', [])]
                bundle = dict(version=1, name=catalogue.check_public_text(item['name'], id), group=group,
                              family=family, subgroup=subgroup,
                              description=catalogue.check_public_text(item['description'], id),
                              modules=modules,
                              preview=dict(source='assets/images/beach-volleyball.jpg',
                                           darktable_version=manifest['darktable_version'], **dimensions))
                (staged / folder / 'style.json').write_text(
                    json.dumps(bundle, ensure_ascii=False, indent=2) + '\n')
                print(f"  {item['name']}: {dimensions['width']} × {dimensions['height']}", flush=True)
            images = [p.stat().st_size for p in staged.rglob('*.webp')]
            destination = public / 'styles'
            backup = Path(staging) / 'previous'
            if destination.exists():
                destination.rename(backup)
            try:
                staged.rename(destination)
            except BaseException:
                if backup.exists():
                    backup.rename(destination)
                raise
    print(f'Updated public/styles/ with {len(ids)} looks: {len(images)} images, '
          f'{sum(images) / 1e6:.1f} MB. Run npm run build, review, then commit.')
    if draft:
        print('This is a draft from the catalogue thumbnails. Do not publish it; '
              'run again without --draft.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--app', type=Path, default=Path(os.environ.get('OMALUX_APP_ROOT', SITE.parent / 'omalux')),
                        help='Omalux checkout (default: ../omalux or OMALUX_APP_ROOT)')
    parser.add_argument('--draft', action='store_true',
                        help='skip the engine and use the catalogue thumbnails; for layout checks only')
    args = parser.parse_args()
    # Prevent competing runs from replacing each other's output. File lives outside Git.
    lock_path = SITE / 'node_modules/.style-generation.lock'
    lock_path.parent.mkdir(exist_ok=True)
    with lock_path.open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            parser.exit(1, 'Another style generation is running\n')
        try:
            generate(args.app.expanduser().resolve(), args.draft)
        except (OSError, ValueError, KeyError, ET.ParseError, subprocess.SubprocessError) as error:
            parser.exit(1, f'Generation failed; previous gallery retained: {error}\n')


if __name__ == '__main__':
    main()
