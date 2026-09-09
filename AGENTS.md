# Working on omalux.org

This repository contains the Omalux website only. The app lives at https://github.com/chriopter/omalux.

- Keep documentation in root `docs/`, except the main README.md and this single AGENTS.md.
- Credit darktable and its contributors. Do not imply official affiliation.
- Website screenshots show the current development UI; keep preview labels accurate.
- Use `OMALUX_APP_ROOT` for a non-sibling app checkout when generating screenshots.

## Website development

### Development

When starting the dev server, use background mode:

```
astro dev --background
```

Manage the background server with `astro dev stop`, `astro dev status`, and `astro dev logs`.

### Documentation

Full documentation: https://docs.astro.build

Consult these guides before working on related tasks:

- [Adding pages, dynamic routes, or middleware](https://docs.astro.build/en/guides/routing/)
- [Working with Astro components](https://docs.astro.build/en/basics/astro-components/)
- [Using React, Vue, Svelte, or other framework components](https://docs.astro.build/en/guides/framework-components/)
- [Adding or managing content](https://docs.astro.build/en/guides/content-collections/)
- [Adding styles or using Tailwind](https://docs.astro.build/en/guides/styling/)
- [Supporting multiple languages](https://docs.astro.build/en/guides/internationalization/)
