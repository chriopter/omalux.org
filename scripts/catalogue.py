"""What the generators assume about the app's catalogue, kept in one place.

Both generators read an Omalux checkout (`catalog/styles`, `catalog/camera`) and write only
web images and metadata into this repository. Change the tables below when the catalogue
layout changes; nothing else in the generators names a folder or a metadata field.
"""
import base64
import binascii
import json
import re
import zlib
from pathlib import Path
from xml.etree import ElementTree as ET

# Folder name -> label, where title-casing the folder name would be wrong.
LABELS = {'dhh': 'DHH'}

# Folders of catalog/camera that hold film profiles (a lookup table for darktable's LUT 3D
# module plus a preset that selects it) instead of per-camera presets.
FILM_GROUPS = ('dhh',)

# Film profiles are discovered from JSON metadata below the group folder. A file describes
# one profile (an object), or several (a list, or an object with one of LIST_KEYS).
# Group-level files named in IGNORED_METADATA are skipped.
LIST_KEYS = ('films', 'profiles', 'entries')
IGNORED_METADATA = ('group.json', 'README.json')
NAME_KEYS = ('name', 'title')
FILM_KEYS = ('film', 'stock')            # the film stock; default: the name without its variant
VARIANT_KEYS = ('variant',)              # default: a trailing one-letter word of the name
BRAND_KEYS = ('brand', 'maker', 'family')  # optional sub-heading, e.g. the film manufacturer
LUT_KEYS = ('lut', 'cube')               # path relative to the metadata file
PRESET_KEYS = ('preset', 'dtpreset')
THUMBNAIL_KEYS = ('thumbnail', 'preview')
DESCRIPTION_KEYS = ('description',)
# Used when the metadata names no file: files beside the metadata file, in this order.
# `{stem}` is the metadata file's name without `.json`.
LUT_DEFAULTS = ('{stem}.cube', 'profile.cube', 'look.cube')
PRESET_DEFAULTS = ('{stem}.dtpreset', 'profile.dtpreset', 'preset.dtpreset')
THUMBNAIL_DEFAULTS = ('{stem}.jpg', 'thumbnail.jpg')

# Only these kinds of file are ever named on the site.
PUBLISHED_SUFFIXES = {'.cube', '.png', '.dtpreset', '.dtstyle', '.icc'}

# darktable's module names, for the draft gallery built without the engine.
MODULE_NAMES = {'bilat': 'local contrast', 'colisa': 'contrast brightness saturation',
                'colorbalancergb': 'color balance rgb', 'exposure': 'exposure', 'grain': 'grain',
                'lut3d': 'LUT 3D', 'nlmeans': 'astrophoto denoise', 'rgbcurve': 'rgb curve',
                'toneequal': 'tone equalizer', 'vignette': 'vignetting', 'sharpen': 'sharpen'}


def label(folder):
    """The name shown for a catalogue folder."""
    return LABELS.get(folder.lower(), folder.replace('-', ' ').title())


def style_groups(folder):
    """Family and sub-group of a look from its bundle folder, relative to catalog/styles.

    `film/film-kodak` is family Film; `series/movie/series-movie-roseglass` is family Series,
    sub-group Movie; a bundle directly in catalog/styles (`neutral`) belongs to Essentials.
    """
    parts = Path(folder).parts[:-1]
    if not parts:
        return 'Essentials', ''
    return label(parts[0]), ' · '.join(label(part) for part in parts[1:])


def slug(text):
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')


def check_public_text(value, where):
    """Refuse text that would publish a path of this machine."""
    if re.search(r'(^|[\s"\'(])(/|~/|[A-Za-z]:\\)|\.\./|\.private', value):
        raise ValueError(f'{where}: "{value}" looks like a local path and is not published')
    return value


def first(entry, keys):
    for key in keys:
        if entry.get(key) not in (None, ''):
            return entry[key]
    return None


def lut_path_in_preset(preset_file):
    """The lookup table a LUT 3D preset selects, as darktable stores it: relative to the
    3D LUT root folder. None when the file is not a LUT 3D preset or cannot be read."""
    try:
        preset = ET.parse(preset_file).getroot().find('preset')
        if preset is None or (preset.findtext('operation') or '').strip() != 'lut3d':
            return None
        params = (preset.findtext('op_params') or '').strip()
        if params.startswith('gz'):
            data = zlib.decompress(base64.b64decode(params[4:]))
        else:
            data = bytes.fromhex(params)
        return data[:512].split(b'\0', 1)[0].decode('utf-8') or None
    except (ET.ParseError, ValueError, binascii.Error, zlib.error, UnicodeDecodeError):
        return None


def _resolve(folder, entry, keys, defaults, stem, required, where):
    named = first(entry, keys)
    if named is not None:
        path = (folder / str(named)).resolve()
        if not path.is_file():
            raise ValueError(f'{where}: "{named}" does not exist')
        return path
    for pattern in defaults:
        path = folder / pattern.format(stem=stem)
        if path.is_file():
            return path
    if required:
        tried = ', '.join(pattern.format(stem=stem) for pattern in defaults)
        raise ValueError(f'{where}: no lookup table. Name it with "{keys[0]}" '
                         f'or put one of {tried} beside the metadata file')
    return None


def collect_films(camera_root, group):
    """Film profiles of one group as a list of films with their variants.

    Raises ValueError with the offending file when the folder does not have the shape
    described at the top of this module.
    """
    root = camera_root / group
    if not root.is_dir():
        return []
    metadata = sorted(p for p in root.rglob('*.json') if p.name not in IGNORED_METADATA)
    if not metadata:
        files = sum(1 for p in root.rglob('*') if p.is_file())
        raise ValueError(
            f'{root} holds {files} files but no metadata (*.json). Film profiles are '
            f'discovered from JSON files; see scripts/catalogue.py for the expected shape')
    profiles = []
    for path in metadata:
        try:
            content = json.loads(path.read_text())
        except json.JSONDecodeError as error:
            raise ValueError(f'{path}: not valid JSON ({error})') from None
        many = isinstance(content, list)
        if isinstance(content, dict):
            listed = first(content, LIST_KEYS)
            if listed is not None:
                content, many = listed, True
            else:
                content = [content]
        if not isinstance(content, list) or not all(isinstance(e, dict) for e in content):
            raise ValueError(f'{path}: expected one profile (an object) or a list of profiles')
        # One file per film with its variants listed: {"name", "brand", "variants": [{"key", "name", "lut"}]}.
        expanded = []
        for entry in content:
            variants = entry.get('variants')
            if isinstance(variants, list) and variants and all(isinstance(v, dict) for v in variants):
                many = True
                for v in variants:
                    lut = str(v.get('lut') or '')
                    preset = Path(lut).with_suffix('.dtpreset').as_posix() if lut else None
                    item = {'name': v.get('name') or entry.get('name'), 'film': entry.get('name'),
                            'variant': v.get('key') or '', 'brand': entry.get('brand') or '', 'lut': lut or None}
                    if preset and (path.parent / preset).is_file():
                        item['preset'] = preset
                    picture = Path(lut).with_suffix('.jpg').as_posix() if lut else None
                    if picture and (path.parent / picture).is_file():
                        item['thumbnail'] = picture
                    expanded.append({k: val for k, val in item.items() if val is not None})
            else:
                expanded.append(entry)
        content = expanded
        for index, entry in enumerate(content):
            where = f'{path}[{index}]' if many else str(path)
            name = first(entry, NAME_KEYS)
            if not isinstance(name, str) or not name.strip():
                raise ValueError(f'{where}: no "{NAME_KEYS[0]}". Known fields: '
                                 f'{", ".join(NAME_KEYS + FILM_KEYS + VARIANT_KEYS + BRAND_KEYS + LUT_KEYS + PRESET_KEYS + THUMBNAIL_KEYS)}')
            name = name.strip()
            variant = first(entry, VARIANT_KEYS)
            film = first(entry, FILM_KEYS)
            if variant is None:
                match = re.fullmatch(r'(.+?)[\s_-]+([A-Za-z])', name)
                variant = match.group(2) if match else ''
                film = film or (match.group(1) if match else name)
            film = str(film or name).strip()
            # A file listing several profiles has no stem of its own to find files by.
            stem = slug(name) if many else path.stem
            lut = _resolve(path.parent, entry, LUT_KEYS, LUT_DEFAULTS, stem, True, where)
            preset = _resolve(path.parent, entry, PRESET_KEYS, PRESET_DEFAULTS, stem, False, where)
            thumbnail = _resolve(path.parent, entry, THUMBNAIL_KEYS, THUMBNAIL_DEFAULTS, stem, False, where)
            for file in (lut, preset):
                if file is None:
                    continue
                if file.suffix.lower() not in PUBLISHED_SUFFIXES:
                    raise ValueError(f'{where}: {file.name} is not a file kind the site names '
                                     f'({", ".join(sorted(PUBLISHED_SUFFIXES))})')
                if camera_root not in file.parents:
                    raise ValueError(f'{where}: {file} is outside the camera catalogue')
            profiles.append({
                'film': check_public_text(film, where),
                'variant': check_public_text(str(variant).strip(), where),
                'brand': check_public_text(str(first(entry, BRAND_KEYS) or '').strip(), where),
                'description': check_public_text(str(first(entry, DESCRIPTION_KEYS) or '').strip(), where),
                'lut': lut, 'preset': preset, 'thumbnail': thumbnail, 'where': where,
            })
    films = {}
    for profile in profiles:
        film = films.setdefault((profile['brand'], profile['film']),
                                {'name': profile['film'], 'brand': profile['brand'], 'variants': []})
        if any(v['variant'] == profile['variant'] for v in film['variants']):
            raise ValueError(f"{profile['where']}: a second profile for {profile['film']} "
                             f"variant \"{profile['variant']}\"")
        film['variants'].append(profile)
    ordered = sorted(films.values(), key=lambda f: (f['brand'].lower(), f['name'].lower()))
    for film in ordered:
        film['variants'].sort(key=lambda v: v['variant'])
    return ordered
