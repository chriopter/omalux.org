# omalux.org

The Omalux website, built with Astro and the Cloudflare adapter.
Extracted from https://github.com/chriopter/omalux at commit `717e2c9`. Earlier website history remains in the app repository.

## Development

Requires Node.js 22.12.0 or newer. From this repository’s root:

```bash
npm ci
npm run dev
```

Edit `src/pages/index.astro` for the landing page and `public/` for images
and other static assets. Run `npm run build` to check the production build.

Pages: `/` introduces the app, `/styles` is the gallery of looks (see
[styles.md](styles.md)), and `/cameras` lists the camera presets. Both pages
end with the steps to install their files in plain darktable and link to each
other. `/cameras` is built from `src/data/cameras.json` and `src/data/films.json`;
refresh both from an app checkout with `npm run generate:cameras` after the
camera catalogue changes.

### Film profiles

Folders of `catalog/camera` listed as film groups in `scripts/catalogue.py`
(`dhh`) hold film profiles: a lookup table for darktable's LUT 3D module and a
preset that selects it. They are left out of the per-camera lists and get a
section of their own, one entry per film with its variants. The generator finds
them through JSON metadata below the group folder: one file per profile, or a
file listing several. Per profile it reads the name, optionally the film, the
variant (otherwise a trailing one-letter word of the name, as in “… C”), a brand
for sub-headings, and the lookup table, preset and thumbnail (otherwise files
beside the metadata file). The accepted field and file names are tables at the
top of `scripts/catalogue.py`; a folder of another shape stops the generator
with the file and the reason, and nothing is written.

Where a profile has a thumbnail, it is converted to
`public/cameras/<group>/<film>-<variant>.webp` (240 pixels wide) and the films
are shown as cards; without thumbnails they are plain rows. The 3D LUT root
folder named in the instructions is read from what the presets select; when they
do not say, the page describes the setting without naming a folder.

Lookup tables, presets and styles are never copied to this site. Both pages
point to the app repository for the files. Names on the pages are the
catalogue's own; do not add names of other software or of source files to the
copy.

The Lux wordmark is `public/assets/omalux-logo.svg`; `public/favicon.svg` and
`public/favicon.ico` use its pixel sun. The header adapts the logo to the selected
light/dark theme and uses a sun/moon button to switch modes.

## Screenshot

The website and repository README share real screenshots of the current darktable-based development UI. The editing view is `public/app-screenshot-dark.png`; the style view is `public/app-styles-dark.png`. Both website themes use these same images, matching the app's current dark appearance. Keep the development-preview label visible.

Generate both from this repository root with the app checked out alongside it as `../omalux`, or set `OMALUX_APP_ROOT` to its absolute path:

```bash
scripts/screenshots.sh
# Or capture one view:
scripts/screenshot.sh ../omalux/assets/images/beach-volleyball.jpg /tmp/omalux-styles.png styles
```

The scripts build the current native app if needed and capture its real QML window with the shared beach photograph at 1280×820 pixels and 1× scale (1280×820 PNG); the offscreen capture at 2× draws only part of the window. They use separate temporary app settings and darktable databases. The running editing session stays untouched. GTK/OpenCL still require a working desktop session, although the Qt window is captured offscreen. Native build dependencies and Python 3 are required. Existing outputs survive failed captures.

Review both images before committing. The gallery alternates editing and style views; page light/dark switching changes the website colors, not the captured application's theme.

## Deployment

Deploy the existing Cloudflare Worker `omalux-org` from this repository:

```sh
npm run build
npx wrangler deploy
```

Workers Builds is connected to `chriopter/omalux.org`, branch `main`, with root directory `/`, build command `npm run build` and deploy command `npx wrangler deploy`. Pushes to this repository trigger website builds. The app repository no longer contains the website. Include all paths (`*`) for build triggers.
