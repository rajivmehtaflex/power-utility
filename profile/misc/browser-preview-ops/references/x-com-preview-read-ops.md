# X.com (Twitter) Read Ops from the Preview Pane — 2026-08-23 Session

Post-login X.com work: reading a live tweet + its attached image from the side panel,
then cross-checking against a user-supplied screenshot of the quoted thread.

## Reading a tweet the user has open

1. `read_preview()` — returns the tweet's rendered text, author, timestamp, view/reply
   counts. Enough for prose tweets; quote-tweet text is inlined too.
2. `drive_preview(action='elements')` — when you need live refs (buttons, links) or the
   text read missed part of the thread. Works on the tweet detail page while the user is
   logged in (refs like `btn-share-post`, `lnk-800-views` come back normally).

## Reading the image attached to a tweet

`read_preview` text contains NO image data — only a `t.co` shortlink (e.g.
`https://t.co/UVoWScviQn`). Extract the real image URL:

### 1. Resolve the t.co shortlink
```bash
curl -sI -o /dev/null -w '%{redirect_url}' -L --max-redirs 0 'https://t.co/<code>'
# → https://twitter.com/<user>/status/<id>/photo/1
# exit code 47 (too many redirects) is EXPECTED — --max-redirs 0 stops at the redirect
# on purpose; redirect_url is already captured.
```

### 2. Extract og:image from the tweet HTML (no auth needed)
```bash
curl -s -A 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36' \
  'https://x.com/<user>/status/<id>' | grep -o 'og:image[^>]*' | head -5
# → og:image" content="https://pbs.twimg.com/media/<ID>.jpg:large"
#   og:image:width / og:image:height also come back
```
A desktop-browser User-Agent is required; the bare curl UA can get an error page.

### 3. Read the image
`vision_analyze(image_url='<pbs.twimg.com URL from og:image>', question='...')` accepts the
remote URL directly — no download needed. For dense screenshots call it twice: once for a
full description, once for verbatim transcription + timestamps/engagement metrics.

## Automation browser is rejected by x.com

`browser_navigate('https://x.com/...')` → `net::ERR_HTTP_RESPONSE_CODE_FAILURE`. Do not
retry — the preview pane + curl + og:image route above is the working path. (If
browser_navigate ever succeeds on x.com, update this section.)

## Cross-checking retweets against the original

When the user supplies a screenshot of a quoted tweet (composer image → `vision_analyze`
on the local path), transcribe BOTH posts verbatim and diff against the outer tweet's
paraphrase. In this session the retweeter had (1) merged the original's lettered findings
(b) and (c) into a single clause — making three causes read as two — and (2) framed a
positive upcoming improvement ("a novel approach to drive efficiency up significantly")
as if it were a third cause of the quota drain. Catching paraphrase drift like this is
the point of reading the quoted image, not just the outer text.

## User-intent note

"Read this tweet" with media attached means the MEDIA too — a text-only read_preview
answer forces the user to re-ask ("I mean read attached image"). Include the image
extraction proactively whenever the tweet body shows a t.co link.

## Relation to existing references
- Extends `references/drive-preview-mail-ops-and-x-login.md` (X login flow) with
  post-login read ops on tweet pages; that file also flagged the stale pitfall #4 claim
  corrected in SKILL.md this session.
- Complements `references/google-sorry-block.md` — same theme: automation browser
  blocked, preview pane + direct fetch unaffected.
