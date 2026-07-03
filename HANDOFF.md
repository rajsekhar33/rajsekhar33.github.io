# Website redesign — handoff notes

## Goal
Redesign Rajsekhar Mohapatra's academic personal website (previously an old free
HTML5 template hosted at `/u/rm3395/WWW/public` on Coma) and host the new
version on GitHub Pages at **https://rajsekhar33.github.io**. Files should live
on the user's laptop going forward, not on Coma. The old Coma-hosted page
should eventually redirect to the new GitHub Pages site.

## Current status: BLOCKED on GitHub Pages deployment
The new site has been built, transferred to the user's laptop, committed, and
pushed to GitHub — but the Pages deployment is currently failing with a
generic GitHub-side error, so **https://rajsekhar33.github.io still 404s.**

Last seen error (Actions tab, job "Deploy to GitHub Pages", step
`actions/deploy-pages@v5`):
```
Getting Pages deployment status...
Error: Deployment failed, try again later.
```
This looks transient (common on first-ever Pages deployment for a repo) but
has not yet been confirmed resolved. Settings → Pages → Source is correctly
set to **"Deploy from a branch" / `main`**.

### Next steps to try (in order)
1. On the failed Actions run, click **Re-run jobs** → **Re-run failed jobs**.
2. If that fails again, trigger a fresh deployment instead of retrying the
   same one:
   ```bash
   git commit --allow-empty -m "Retrigger Pages deployment"
   git push
   ```
3. If it still fails, check https://www.githubstatus.com for a Pages/Actions
   outage.
4. Once live, actually load the URL and click through every page —this has
   **not yet been visually verified in a real browser**. All the QA so far
   was: internal link/asset existence check via a script, and manual
   inspection of the two supplied photos. No browser was available in the
   Coma session to render the CSS/JS/dark-mode toggle/mobile nav.

## Key facts / decisions already made
| Item | Decision |
|---|---|
| GitHub username | `rajsekhar33` (confirmed exact match by user) |
| Repo name | `rajsekhar33.github.io` (required exact match for a personal "user site") |
| Live URL (once working) | `https://rajsekhar33.github.io` |
| Tech stack | Plain static HTML/CSS/JS, no framework, no build step |
| Design | "Modern minimal academic": serif (Source Serif 4) headings + Inter body, light/dark toggle, sticky nav, responsive mobile menu |
| Old site (reference only, still live) | `/u/rm3395/WWW/public` on Coma — untouched except a temporary uploaded headshot file was removed from it (see below) |
| Local repo path | User ran `scp -r rm3395@coma:/u/rm3395/Public/rajsekhar33.github.io ~/rajsekhar33.github.io` — confirm actual local path in the new session, may differ |
| Email used on site | `rmohapatra@princeton.edu` (inferred from old obfuscated "rmohapatra[AT]princeton[dot]edu" — **not yet explicitly confirmed by user**) |
| GitHub link on homepage | Points to `github.com/rajsekhar33` — **not yet explicitly confirmed as the user's real profile** |
| Headshot | User supplied `DSC_1212-EDIT.jpg`; cropped/resized into `assets/img/headshot.jpg` (500×500, hero) and `assets/img/headshot-small.jpg` (160×160, nav avatar); EXIF stripped |

## Content decisions the user should confirm or revisit
- **`data_share.html` was dropped entirely.** The old page linked to
  `MHD_data_share.tar.gz` and `Stats.tar.gz`, but neither file exists anywhere
  under `/u/rm3395/WWW/public` on Coma. If the user has these files elsewhere,
  we should add the page back with working links (or a Zenodo/GitHub link
  instead).
- **The old `#banner` image (`Cornell_library.jpg`) was dropped.** It was used
  as a decorative banner across every page of the old site, but its
  context/caption was unclear (unsure if it's meant to represent Princeton,
  Cornell, or something else), so it was left out rather than guessed. Ask the
  user if/where they'd like it (or a different photo) reintroduced.
- Two personal hiking photos (`Colorado_hike.jpg`, `sesto_hike.jpg`) existed in
  the old site's root but were unused/orphaned there too — not carried over.
  Could be added to an "about" section if the user wants a more personal
  touch.
- Added a link from `research.html`'s "Stratified turbulence" (PhD) section to
  `movies/stratified-turbulence.html` — that movies page existed on the old
  site but nothing actually linked to it. Confirm this is wanted.

## Full new-site structure (as built)
```
rajsekhar33.github.io/
├── index.html            (Home: hero, bio, latest-news card)
├── research.html         (Postdoc / PhD / Bachelor's research, grouped with inline pub lists)
├── publications.html     (Full publication list: Submitted / Published)
├── conferences.html
├── outreach.html         (incl. 2 YouTube embeds + IISc open-day photo)
├── contact.html
├── movies/
│   ├── bachelor-thesis.html       (8 YouTube embeds)
│   └── stratified-turbulence.html (4 YouTube embeds)
├── assets/
│   ├── css/style.css     (all design tokens/colors/dark-mode live here)
│   ├── js/main.js        (dark-mode toggle + mobile nav toggle)
│   └── img/ (headshot.jpg, headshot-small.jpg, outreach-iisc.jpg)
├── favicon.png
└── Rajsekhar_CV.pdf
```
All internal links/asset references were validated with a script (no broken
links as of the last build).

## Outstanding tasks for the new session
1. **Unblock the GitHub Pages deployment** (see steps above) and confirm the
   site actually renders correctly at https://rajsekhar33.github.io — check
   layout, dark-mode toggle, mobile nav, and that all six main pages plus the
   two movies pages load.
2. **Set up the redirect** from the old Coma-hosted page
   (`/u/rm3395/WWW/public`) to the new GitHub Pages site — this was the user's
   original ask ("just redirect my old webpage to the new github webpage")
   and has not been done yet. Likely approach: replace `index.html` (and
   maybe the other old pages) at `/u/rm3395/WWW/public` with a simple HTML
   meta-refresh / JS redirect to `https://rajsekhar33.github.io`, or check
   whether Coma's web server config supports a server-level redirect instead.
3. Confirm the still-open content decisions above (data share page, banner
   image, email address, GitHub profile URL).
4. Once the user confirms the local copy is good and the site is live, clean
   up the build artifacts left on Coma:
   - `/u/rm3395/Public/rajsekhar33.github.io` (the working copy that was
     `scp`'d to the laptop)
   - The original unprocessed headshot backup left in this session's
     scratchpad (ephemeral, likely auto-cleaned, but flagging for
     completeness)

## Environment note for the new session
This work was previously done from a Claude Code session running on Coma
(shared server, `/u/rm3395/...` paths), which had **no connected browser and
no `gh` CLI**, so GitHub Actions/Pages troubleshooting had to be done by
manually copy-pasting screenshots and logs from the user. Running the new
session on the user's laptop with browser access granted should make this
much faster — Claude can directly check the Pages settings, Actions logs, and
render the live site.
