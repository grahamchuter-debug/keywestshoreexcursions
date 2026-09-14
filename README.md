# Key West Shore Excursions (World 2.0)

Preservation-led static rebuild for `keywestshoreexcursions.com`.

## Stack

- Cloudflare Workers Static Assets
- Python site builder (`scripts/build_site.py`)
- Server-visible HTML in `public/`
- Worker router: HTTPS apex, extensionless URLs, real 404

## Commands

```bash
npm install
npm run build
npm run check
npm run dev
npm run deploy
```

## Preview only (Phase 29B)

Deploy the Worker for preview. Do **not** attach `keywestshoreexcursions.com` until cutover — the live Pages project `key-west-shore-excursions` still owns custom domains.

## Commerce

None. Editorial planning guides only.
