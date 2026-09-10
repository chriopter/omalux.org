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

The scripts build the current native app if needed and capture its real QML window with the shared beach photograph at 1280×820 logical pixels and 2× display scale (2560×1640 PNG). They use separate temporary app settings and darktable databases. The running editing session stays untouched. GTK/OpenCL still require a working desktop session, although the Qt window is captured offscreen. Native build dependencies and Python 3 are required. Existing outputs survive failed captures.

Review both images before committing. The gallery alternates editing and style views; page light/dark switching changes the website colors, not the captured application's theme.

## Deployment

Deploy the existing Cloudflare Worker `omalux-org` from this repository:

```sh
npm run build
npx wrangler deploy
```

Workers Builds is connected to `chriopter/omalux.org`, branch `main`, with root directory `/`, build command `npm run build` and deploy command `npx wrangler deploy`. Pushes to this repository trigger website builds. The app repository no longer contains the website. Include all paths (`*`) for build triggers.
