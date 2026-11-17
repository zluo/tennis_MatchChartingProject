# Solutions Nextio

A responsive, dependency-free company home page. The collection links to Baseline Tennis Analytics and Yahoo Finance as the current Trading resource. External links open in new tabs. The market illustration is decorative and does not represent live prices.

## Local preview

From the repository root:

```sh
python3 -m http.server 8001 --directory solutions-nextio/dist
```

Open http://localhost:8001. No installation or build step is required. Google Fonts is optional; system fonts provide a fallback.

## Edit

- `dist/index.html`: company copy, product links, and illustrative SVG artwork.
- `dist/style.css`: responsive styles, keyboard focus states, and reduced-motion handling.
- `dist/favicon.svg`: Nextio monogram.
- `.openai/hosting.json`: Sites identity and static deployment configuration.

The tennis dashboard remains a separate site. Its data files are not copied into this project. Update the Trading link in `index.html` when a dedicated application is available.
