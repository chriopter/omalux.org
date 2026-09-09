# Preset gallery

The `/presets` page lists every bundled Omalux look, grouped like the app, with search, an original-image toggle and a before/after comparison. The catalogue is rendered into the page at build time; browser controls need no API or darktable installation.

## Refresh manually

```sh
npm run generate:presets
# Alternatively, choose the app checkout:
npm run generate:presets -- --app /path/to/omalux
npm run build
```

The default app checkout is `../omalux`; `OMALUX_APP_ROOT` also overrides it. Use a current checkout with the batch catalogue exporter. Requirements: Python 3 on Linux, ImageMagick (`magick`) and the app's usual Qt/native build and local darktable dependencies. The app launcher rebuilds its adapter against the installed darktable version when necessary.

The script reads `presets/**/preset.dtstyle`, uses the shared `assets/images/beach-volleyball.jpg`, and renders all looks in one offscreen Omalux/darktable process. Its private session does not change the editor's history or bundled app thumbnails. Missing dependencies or failed renders abort generation.

Outputs in `public/presets/`:

- `<bundle>/preset.json`: name, group, description, style modules and preview provenance/dimensions.
- `<bundle>/preview.webp`: the styled image, fitted within 640 × 480 pixels without cropping or stretching (currently 640 × 427).
- `original.webp`: the shared engine baseline before applying a style.

Bundle paths mirror the app's preset folders, for example `experimental/experimental-nightstreet/`. Image names are fixed conventions, so JSON does not repeat the bundle ID or image URL. `preview.source` and `preview.darktable_version` record how each image was rendered.

The page discovers `**/preset.json` at build time through `src/lib/presets.ts`, derives image URLs from the folders and sorts the groups. There is no central `index.json` to maintain. Missing bundle previews fail the build.

Only web images and catalogue metadata are copied. Styles, LUTs and machine-local paths remain in the app checkout. Generation stages every output before replacing the old catalogue; failed renders retain the old gallery. Concurrent generator runs are rejected. Re-running removes stale generated entries as part of replacement.

Review the gallery, then commit and push the generated files together with any page changes. The regular website build uses the committed catalogue and never invokes darktable. New app presets appear after the next manual refresh and deployment. Example looks remain labelled as in development; the beach preview does not promise identical behavior on every source photograph.
