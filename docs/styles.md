# Style gallery

The `/styles` page lists every bundled Omalux look by family, with search, an original-image toggle and a before/after comparison. A family is the first folder below `catalog/styles` (`film`, `series`, `dhh`); deeper folders are its sub-groups (`series/movie`). Each family is a filter with its number of looks, and a family with sub-groups offers them as a second row once it is chosen. A family of more than 24 looks uses a denser grid and, while all families are listed, shows its first ten looks and a button to the rest. The address keeps the choice: `/styles#dhh`, `/styles#series/movie`. The catalogue is rendered into the page at build time; browser controls need no API or darktable installation.

## Refresh manually

```sh
npm run generate:styles
# Alternatively, choose the app checkout:
npm run generate:styles -- --app /path/to/omalux
npm run build
```

The default app checkout is `../omalux`; `OMALUX_APP_ROOT` also overrides it. Use a current checkout with the batch catalogue exporter. Requirements: Python 3 on Linux, ImageMagick (`magick`) and the app's usual Qt/native build and local darktable dependencies. The app launcher rebuilds its adapter against the installed darktable version when necessary.

The script reads `catalog/styles/**/style.dtstyle`, uses the shared `assets/images/beach-volleyball.jpg`, and renders all looks in one offscreen Omalux/darktable process. Its private session does not change the editor's history or bundled app thumbnails. Missing dependencies or failed renders abort generation.

Outputs in `public/styles/`:

- `<bundle>/style.json`: name, family, sub-group, description, style modules and preview provenance/dimensions.
- `<bundle>/thumb.webp`: the same image within 320 × 240 pixels for the grid. The page offers both and the browser takes the one that fits the card; a bundle without it (generated before it existed) uses `preview.webp` alone.
- `<bundle>/preview.webp`: the styled image, fitted within 640 × 480 pixels without cropping or stretching (currently 640 × 427).
- `original.webp`: the shared engine baseline before applying a style.

Bundle paths mirror the catalogue's style folders, for example `experimental/experimental-nightstreet/`. Image names are fixed conventions, so JSON does not repeat the bundle ID or image URL. `preview.source` and `preview.darktable_version` record how each image was rendered.

The page discovers `**/style.json` at build time through `src/lib/styles.ts`, derives image URLs from the folders and sorts the families. There is no central `index.json` to maintain. Missing bundle previews fail the build.

Folder names become labels by title case; `scripts/catalogue.py` holds the exceptions (`dhh` reads “DHH”) and everything else the generators assume about the catalogue layout. The sentence under a family heading is site copy in `src/lib/styles.ts`.

`npm run generate:styles -- --draft` skips the engine and builds the gallery from each bundle's own `thumbnail.jpg` and what the `.dtstyle` says. It is for checking the layout against a catalogue that cannot be rendered yet; the images are small and it must not be published.

Only web images and catalogue metadata are copied. Styles, LUTs and machine-local paths remain in the app checkout. Generation stages every output before replacing the old catalogue; failed renders retain the old gallery. Concurrent generator runs are rejected. Re-running removes stale generated entries as part of replacement.

Review the gallery, then commit and push the generated files together with any page changes. The regular website build uses the committed catalogue and never invokes darktable. New app styles appear after the next manual refresh and deployment. Example looks remain labelled as in development; the beach preview does not promise identical behavior on every source photograph.
