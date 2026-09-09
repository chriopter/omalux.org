# omalux.org

The website for [Omalux](https://github.com/chriopter/omalux), an independent interface for darktable.

[Live site](https://omalux.org) · [Development and deployment](docs/development.md)

```sh
npm ci
npm run dev
```

Requires Node.js 22.12 or newer. Build with `npm run build`.

- `src/pages/index.astro` — landing page.
- `public/` — screenshots and website assets.
- `scripts/screenshots.sh` — capture the app from a sibling `../omalux` checkout, or set `OMALUX_APP_ROOT`.

The app repository references screenshots through their public website URLs.

- `npm run generate:presets` — render the preset gallery using local darktable and the sibling app checkout. See [Preset gallery](docs/presets.md).
