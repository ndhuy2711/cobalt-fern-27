# SCIO clone: MVP delivery plan

**Decision document — trial exploration in progress.** This is a plan for a working digital-signage product, not a pixel-for-pixel copy of every SCIO page. The Screens and Files/Assets observations below come from our trial account; playlist and schedule workflows will be checked before submission.

## 1. Product understanding and the first customer journey

The core job is to let an operator manage what many screens show, when they show it, and whether the screens are healthy. The first journey I would ship is: create an account and location → pair a player to a screen → upload an image or video → make a playlist → assign it to the screen → see playback and device status. A second journey adds a recurring schedule and fallback content.

In the trial account's [Screens onboarding view](evidence/product/dashboard.png), the first task is to prepare a device and obtain a six-digit pairing code. The page offers desktop players for people without signage hardware, followed by “Pair Screen & Assign Content,” “Create Content,” and an optional playlist. That is a useful signal that the product's first success moment is a working screen, not a completed content library.

The trial [Files/Assets Home](evidence/product/assets.png) shows nine content cards, including templates, ESPN News, and Houston Weather. Upload Files, Create, New Folder, Apps, Templates, and Feeds are separate entry points; the library also offers Images, Videos, Docs, and Apps filters, Favorites, and Shared with me. The Get Started panel remains visible here, connecting content work back to screen pairing. I would give a new account a few usable starter examples and keep content type and source explicit in the data model. The MVP can ship uploaded images/videos and static starter templates; live app and feed integrations follow later.

This sequence follows the product's own [screen setup guide](https://support.optisigns.com/hc/en-us/articles/360016374813-Set-up-add-a-screen), [playlist guide](https://support.optisigns.com/hc/en-us/articles/28295104605843-How-to-Create-Use-Playlists), and [schedule guide](https://support.optisigns.com/hc/en-us/articles/360016981853-Creating-and-Using-Schedules-with-OptiSigns). In particular, the schedule guide documents screen-local time zones, overlap precedence, and default content when no event is active. Those are playback rules, not merely calendar UI details.

**Trial-account evidence still to add:** screenshots or notes from Playlists and Schedule, including one attempt to publish content to a screen or preview player. This will distinguish observed behavior from help-article descriptions.

## 2. Scope decision

**MVP platform:** browser management portal and one browser/kiosk player that can run on a supported laptop or Android browser. One account can have multiple locations and screens. Start with a single tenant per account; design tenant IDs into every record. A dedicated native player and hardware-specific controls follow after the first release.

| Ship in MVP | Why it is needed |
| --- | --- |
| Account, owner/editor/viewer roles, locations | Operators need a safe boundary for multi-location work. |
| Pairing code, screen inventory, tags, heartbeat and last-seen time | Without a paired and observable player, content management cannot be verified. |
| Image/video upload, metadata, folders, replace asset, static starter examples | These are the smallest useful content primitives. Starter examples make the first-use library useful; replacing an asset should update screens using it. |
| Ordered playlists, per-item duration, one simple two-zone layout | Provides both rotation and basic layout control without a full designer. |
| One-time and weekly content schedules, screen-local time zone, conflict policy, fallback content | Covers normal dayparting and makes empty or overlapping periods deterministic. |
| Publish/preview, versioned player manifest, local cache and offline continuation | Operators must know what will play; screens must keep playing during temporary disconnection. |

**After MVP:** monthly/custom recurrence; nested playlists; social and third-party app integrations; template designer; billing; SSO; advanced analytics; remote power/volume/brightness; HDMI-CEC and RS-232; native players for multiple OS families. These have materially different implementation or support costs. The [operational schedule guide](https://support.optisigns.com/hc/en-us/articles/28598173096723-How-To-Create-and-Use-Operational-Schedules-HDMI-CEC-RS-232) describes hardware and plan-specific behavior, so it should be a separate workstream rather than a checkbox in the content scheduler.

## 3. The system I would build

```text
Management portal ── HTTPS API ── PostgreSQL (tenants, screens, content, schedules)
        │                 │
        │                 ├── Object storage (original media and optimized variants)
        │                 └── Worker queue (media inspection and manifest generation)
        │
        └── Player API ── Browser/kiosk player (manifest, local cache, heartbeat)
```

Use a TypeScript web portal and API so the team shares types for assignments and schedules. The player fetches an immutable, versioned manifest containing media URLs, playlist timing, layout, and the schedule resolved for its screen and time zone. It acknowledges the manifest version it is displaying and keeps the last usable version offline. The server records desired version, acknowledged version, heartbeat, and playback errors separately; an “online” indicator alone does not prove the correct content is showing.

Core records: `Organization`, `Membership`, `Location`, `Screen`, `Device`, `ContentItem`, `Asset`, `Playlist`, `PlaylistItem`, `Layout`, `Schedule`, `ScheduleEvent`, `Assignment`, `PublishedManifest`, `Heartbeat`. A playlist item references a typed content item; an uploaded asset or starter template supplies it in the MVP, while a future app connector can use the same reference. Every query is scoped by organization. Pairing codes expire quickly and become revocable player credentials after pairing. Uploads use short-lived signed URLs; media validation occurs before publish.

The schedule resolver uses the **screen's IANA time zone**, records a clear overlap order, and always returns a fallback. The Help Center says a one-time event can override a recurring event and the most recently changed recurring event wins when two recurring events overlap. I would turn those into explicit, tested rules and show conflicts before publication. A publish operation either produces a valid manifest or leaves the last published version in place.

## 4. Delivery order and estimate

Assume **four engineers** (two full-stack, one player-focused, one backend/media), a PM/designer at half time, and QA at half time from week 5. Estimates are calendar weeks with parallel work; they include code review and basic tests. The MVP target is **14–16 weeks**, including roughly 20% uncertainty reserve for device and playback integration.

| Weeks | Milestone and exit evidence | Why this order |
| --- | --- | --- |
| 1–2 | Trial research, clickable flow, domain model, player/API contract, test devices | The player contract and scheduling rules are expensive to change later. |
| 3–4 | Auth, tenant boundary, location and screen records, expiring pairing flow | Establishes the identity of each screen before publishing content. |
| 5–7 | Asset upload/processing, playlist editing, basic layout preview | Gives operators something real to assign and exposes codec problems early. |
| 7–9 | Publish and assignment, manifest versions, online player playback, heartbeat | First end-to-end vertical slice: upload → publish → visible screen. |
| 9–11 | Weekly/one-time schedules, time zones, overlap warnings, fallback | Builds on the working player and makes scheduling behavior testable. |
| 11–13 | Offline cache, retry/reconnect, role checks, bulk screen assignment | Reliability and multi-location operations before broad rollout. |
| 14–16 | Pilot with representative screens, accessibility, load/soak tests, fixes, release | Real devices and networks reveal issues unit tests cannot. |

The highest-risk path is **player sync and media playback**, so it starts before the portal feature set is complete. A two-week spike in weeks 1–2 must prove pairing, signed media download, and playback on the chosen test hardware. If it fails, I would narrow formats or choose a controlled player platform before building richer scheduling UI.

The estimate is about **50 engineer-weeks**: 6 for account/screen foundations, 9 for assets/playlist/layout, 12 for player sync and offline behavior, 7 for scheduling, 8 for integration and quality, plus roughly 8 for uncertainty. Four engineers could complete 50 engineer-weeks in 12.5 ideal weeks; discovery, dependencies, pilot feedback, and release work extend the calendar target to 14–16 weeks. I would re-estimate after the week-2 player spike and the first pilot.

## 5. Acceptance measures and risks

- A new operator can pair a test screen and display an uploaded image or video within 10 minutes, without developer help.
- Publishing a changed playlist reaches an online player within 60 seconds; the portal shows the version the player acknowledged.
- A player keeps showing its last published content for 24 hours without network access and recovers without duplicate or stale assignments.
- At schedule boundaries, playback changes within one minute in the screen's time zone; conflict precedence and fallback have automated tests, including daylight-saving transitions.
- Tenant isolation, pairing-code expiry, upload validation, and role checks are release gates.

Main risks: codec differences across hardware, intermittent networks, schedule time zones and daylight-saving changes, growing media storage cost, and misleading “online” status. The pilot uses several device types and locations; if the browser player cannot satisfy a venue's requirements, the next phase is a native player adapter rather than a rewrite of the portal or content model.

## 6. Unexpected product finding and plan change

I expected the first-run portal to lead with a media library or layout editor. Instead, the [trial account's first Screens view](evidence/product/dashboard.png) leads with device preparation, a six-digit pairing code, and a desktop path for users without a device; creating a playlist is explicitly optional in its checklist. This changed my sequence: the first engineering milestone is a pairable player and a visible screen, and the portal is built around the first publish-to-screen journey. The player spike starts in week 1, before a rich asset or playlist editor. It also supports choosing a browser/kiosk player as the first target, because the product gives new users a desktop way to try the journey.

## 7. How I would spend the planning exercise's eight hours

1. **2 hours:** use the trial product as an operator and record the key journeys and unexpected finding.
2. **1 hour:** cross-check the Help Center and list feature boundaries.
3. **2 hours:** decide MVP scope, domain model, and architecture tradeoffs.
4. **2 hours:** estimate milestones, dependencies, staffing, and failure points.
5. **1 hour:** review the plan against observed UI, remove unsupported claims, and prepare the live discussion.
