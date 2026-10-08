#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
site_root="$(cd -- "$script_dir/.." && pwd)"
app_root="${OMALUX_APP_ROOT:-$site_root/../omalux}"
if [[ ${1:-} == --help || ${1:-} == -h ]]; then
  echo 'Usage: screenshot.sh [INPUT_PHOTO [OUTPUT_PNG [filters|styles]]]'
  echo 'Capture the current darktable frontend at 1x scale (the offscreen 2x capture draws only part of the window); requires the native build dependencies and a desktop session for GTK/OpenCL.'
  exit 0
fi
python3 - "$app_root" "$site_root" "$@" <<'PY'
import json, os, pathlib, shutil, subprocess, sys, tempfile
root = pathlib.Path(sys.argv[1]).resolve()
site = pathlib.Path(sys.argv[2]).resolve()
args = sys.argv[3:]
if not (root / "development/start").is_file():
    raise SystemExit("App checkout not found; set OMALUX_APP_ROOT to the Omalux repository")
if len(args) > 3:
    raise SystemExit('Expected [INPUT_PHOTO [OUTPUT_PNG [filters|styles]]]')
source = pathlib.Path(args[0] if args else root / 'assets/images/beach-volleyball.jpg').resolve()
output = pathlib.Path(args[1] if len(args) > 1 else site / 'public/app-screenshot-dark.png').resolve()
panel = args[2] if len(args) > 2 else 'filters'
if not source.is_file() or output.suffix != '.png' or source == output or panel not in ('filters', 'styles'):
    raise SystemExit('Invalid input image, output PNG or panel')
with tempfile.TemporaryDirectory(prefix='omalux-website-shot-') as tmp:
    tmp = pathlib.Path(tmp)
    capture = tmp / 'capture.png'
    script = tmp / 'steps.json'
    steps = [{'panel': 1 if panel == 'styles' else 0}, {'capture': str(capture)}]
    script.write_text(json.dumps(steps))
    env = os.environ | {'QT_QPA_PLATFORM': 'offscreen', 'QT_SCALE_FACTOR': '1',
        'QT_FORCE_STDERR_LOGGING': '1', 'QT_QUICK_BACKEND': 'rhi', 'QSG_RHI_BACKEND': 'opengl', 'XDG_CONFIG_HOME': str(tmp / 'config'),
        'OMALUX_SMOKE_SCRIPT': str(script)}
    # A private development session preserves the user's current image and settings.
    subprocess.run([str(root / 'development/start'), str(source)], cwd=root, env=env, check=True, timeout=240)
    if not capture.is_file() or not capture.stat().st_size:
        raise SystemExit('Capture failed; previous screenshot retained')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=output.parent, suffix='.png', delete=False) as f:
        staged = pathlib.Path(f.name)
    try:
        shutil.copyfile(capture, staged)
        staged.chmod(0o644)
        staged.replace(output)
    finally:
        staged.unlink(missing_ok=True)
print(f'Screenshot saved: {output}')
PY
