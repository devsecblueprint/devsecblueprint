# Content Announcements Runbook

Automatic announcements notify all users (in-app modal plus email) when a video is published or a new walkthrough is released. Link previews give shared video links a proper card on Discord, Slack, LinkedIn, and X.

Spec: `.kiro/specs/content-publish-announcements/`.

## How it works

| Content | Trigger | Link |
|---|---|---|
| Video | An admin moves a video to `PUBLISHED` (`POST /admin/videos/{id}/status`) | `/videos/preview/<slug>` |
| Walkthrough | A background scan (every 5 minutes) finds a new walkthrough ID in the content registry. It waits 15 minutes (the settle delay) so the deployed site has the page. | `/walkthroughs/preview/<id>` |

Announcements use absolute links (`FRONTEND_ORIGIN`) because the email template renders the link as-is. The public preview pages send logged-in members on to the full page.

Each item is announced at most once. A DynamoDB ledger (`ANNOUNCEMENTS_TABLE`) records every item, and an item must be claimed with a conditional write before anything is sent.

Ledger statuses: `PENDING` (walkthrough waiting out the settle delay), `SENDING`, `SENT`, `FAILED`, `BASELINED` (existing walkthrough, never announced).

## What the email says

Both kinds follow the same shape: an opening line, the title, the description, a few details, a closing question, then a button and a sign-off. Sections with no data are left out.

**Walkthrough**

```
Hi Damien,

Your next hands-on walkthrough is here.

<title>

<description from the walkthrough's metadata.json>

Level: Intermediate
Estimated time: 1 hr

Ready to put it into practice?

[ Start the walkthrough ]

Happy building,
The DevSec Blueprint
```

**Video:** "A new session is here.", the title, the description, Instructor, Length, Topics, "Available to Builder members." or "Free for all members.", "Ready to watch?", then a **Watch the session** button.

- The description is copied in full from what you entered (the walkthrough's `description` in `metadata.json`, or the video's description in the editor).
- The greeting uses the first name. A handle such as `damienjburks` is used as is.
- The wording, button labels and sign-off are all constants at the top of `backend/app/services/announcement_service.py`. To change the tone (for example "I've added a new walkthrough..." signed by you), edit them there.

## Turning it on (first time)

1. Apply Terraform and deploy the backend. `ANNOUNCEMENTS_ENABLED` defaults to `false`, so nothing is sent yet.
2. Confirm the SES account is out of sandbox mode, otherwise only verified recipients get email.
3. Open **Admin > Broadcasts > Automation** and click **Baseline walkthroughs**. This marks every walkthrough that exists today as already announced. Skipping this step is safe: the first scan after enabling also takes a baseline, but doing it explicitly lets you check the result first.
4. Set the Terraform variable `announcements_enabled = true` and apply.
5. Publish a test video and check the modal, the email, and the new row in the Automation tab.

## Link previews for video pages

Link crawlers read per-video tags from a CloudFront Key Value Store, written when a video is published or edited and removed when it is archived.

After the first deploy that creates the store, run the backfill once so videos that are already published get a card:

```
POST /admin/videos/edge-metadata/backfill
```

It is safe to repeat. Verify with:

```
curl -s -A "Discordbot/2.0" https://devsecblueprint.com/videos/preview/<slug> | grep og:
```

Platforms cache cards for links that were already shared. Re-post an old link with a throwaway query string (for example `?v=2`) to refresh it.

## Day-to-day operation

- **Automation tab** lists every ledger record with status, attempts, and the last error. A `SENT` row with a note means the broadcast went out but some emails failed. The note says how many.
- **Retry** is available on `FAILED` rows. It re-checks that the content is still published (or still in the registry) before sending.
- **Failed count** appears as a badge on the Broadcasts card on the admin dashboard.
- **Automatic broadcasts** show an "Auto" badge in History and can be deleted like manual ones.

## Failure behavior

| Situation | What happens |
|---|---|
| Broadcast could not be created | `FAILED`. Walkthroughs retry on later scans, up to 3 attempts. Videos need a manual Retry. |
| Some emails failed | Item is `SENT` with a note. It is not resent, to avoid duplicates for people who already got it. |
| Container restarted mid-send | The claim goes stale after 30 minutes and the item becomes `FAILED` with "Stale claim". It is never retried automatically, because some people may already have received it. Check Broadcast history, then decide whether to Retry. |
| Registry unavailable or empty | The scan does nothing. A missing registry is never treated as deleted walkthroughs. |
| Walkthrough removed before it was announced | Stays `PENDING` and is never announced. |
| Walkthrough edited after release | Nothing happens. Only new IDs are announced. |
| Key Value Store update fails | Logged. Publishing, editing, and archiving still succeed. Run the backfill to repair. |

## Turning it off

Set `announcements_enabled = false` and apply. The scan and the publish hook stop immediately. Manual broadcasts are unaffected. The link-preview store is independent of this flag.

## Known limits

- Emails are sent one at a time inside the API container, with no throttling or retry, and there is no unsubscribe link or bounce handling yet. An opt-out is the recommended next piece of work, since automatic mail goes to everyone on every publish.
- The list of recipients is read with a full table scan.
- Walkthrough announcements are delayed by the scan interval plus the settle delay (about 20 minutes at most).
