# Social Platform Research Access Policy

Updated for RUOS Content Intelligence v0.3.

## YouTube
Preferred automated path: official YouTube Data API.

- `search.list` discovers videos by query, language, region and time/order parameters.
- Search results are discovery objects, so persistent video details/statistics are fetched via `videos.list` before metric evidence is stored.
- Public discovery can use an API key; private/owned actions require OAuth where applicable.
- RUOS env: `CI_YOUTUBE_API_KEY`.
- Web/manual fallback is allowed when no key is configured, but automated collection must not scrape private data or fabricate statistics.

## Instagram
Two separate data planes:

1. **Owned** — official Instagram API for the connected Red Umbrella professional account. Connector implemented; Meta authorization pending.
2. **Competitive** — public research only until an official authorized surface provides the exact data needed.

Competitive evidence may store only publicly observed fields. Never infer or label public competitor data as private `reach`, `saves`, `shares`, `retention`, `profile_actions` or `conversion`.

## TikTok
For an agency/commercial research engine, do **not** depend on TikTok Research API. TikTok states commercial users are not eligible for Research Tools.

Primary RUOS path:
- TikTok Creative Center / TikTok One Inspiration
- Top Ads / creative patterns / keywords / trends where publicly or account-authorized visible
- Store only metrics explicitly displayed by TikTok

Caveat: Top Ads represents selected/authorized advertiser creatives; it is not a complete census of all top-performing TikTok content.

## LinkedIn
LinkedIn is strategically valuable for B2B intent, consulting, executive language and organizational buyers, but RUOS must not assume unrestricted API search of all public posts.

Official APIs can retrieve/create posts under scoped permissions, especially for authenticated members and organizations where the member has appropriate roles. Competitive discovery therefore defaults to public web research; owned Red Umbrella company-page analytics/post retrieval can later use an approved LinkedIn app and organization permissions.

## Common rules
- public != owned
- visible != inferred
- discovery result != performance proof
- do not invent missing metrics
- canonicalize URLs and deduplicate before ingest
- cross-source corroboration is required before labeling a trend/pattern strong
- first-party customer evidence may increase commercial priority even without high public engagement
