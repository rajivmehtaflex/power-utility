# Hugging Face upload — auth, staging gates, publication, and recovery

Publication is the highest-consequence operation in this skill. It runs only after validation and
packaging gates pass, and every rule below is enforced by
[../scripts/hub_publish.py](../scripts/hub_publish.py) with the same semantics the helper's tests
assert.

## Authentication and identity

- Tokens come exclusively from the local Hub configuration (`HF_TOKEN`/`HUGGINGFACEHUB_API_TOKEN`
  environment or the stored user token). Never accept a token as a conversation message, never write
  one to disk, manifests, receipts, or reports.
- Read access to the **source** and write authorization for the **destination** are separate checks;
  establish both independently before any transfer.
- When write authorization cannot be established without attempting publication, explain exactly what
  is needed (repo id, namespace permission) instead of attempting.
- Reuse already-granted authorization; do not re-ask for the same operation once authorized.

## Destination rules

- Confirm repository and visibility when creating a new repository; preserve existing visibility
  otherwise. Private test repositories are the default recommendation for a first publication.
- Reject source-equals-destination.
- For existing destinations: inspect conflicts first; replacing existing paths requires authorization
  that explicitly covers them; protect against concurrent writes with an expected-head (parent commit)
  check; a stale expected head aborts the run rather than force-pushing.

## Pre-upload gates (all mandatory)

1. License status recorded as `clear`, or `needs-evidence` resolved by an applicable alternate license
   or a recorded permission. `prohibited-under-recorded-terms` never publishes. Missing/ambiguous
   terms require clarification first.
2. Validation gates passed and recorded (see [validation.md](validation.md) §Staged reload).
3. Staged inventory verified: `artifact_manifest.py verify` immediately before upload; re-verify if
   anything in the stage directory changes.

## Transfer semantics

- Use the pinned Hub client's supported resumable blob transfer and coherent commit API.
- After a lost response or interrupted run, inspect remote state before retrying; never blind-retry a
  possibly-completed commit.
- Report empty repositories, partial transfers, and unfinished uploads exactly as what they are.

## Remote verification and receipt

After the commit resolves:

1. Verify the remote file set and content digests. When trustworthy server-side digests are available
   for a file, compare them; otherwise stream-download and hash locally — an ETag is never treated as
   a SHA-256.
2. Write a receipt **outside** the staged inventory containing: remote repository, resolved commit,
   manifest hash, per-file verification status, and the repository URL. No credentials, no signed
   URLs, no private prompts or outputs.
3. Keep the local verified package regardless of publication outcome; a failed upload never destroys
   the stage.

## Using the helper

```bash
python scripts/hub_publish.py publish \
  --stage <stage-dir> --manifest <stage-dir>/artifact-manifest.json \
  --repo-id <namespace/name> --visibility private --create \
  [--expected-head <sha>] [--allow-replace]
```

CLI flags mirror `publish_package(stage, manifest, repo_id, *, visibility, create, expected_head,
allow_replace=False)`. The function refuses to issue any write call until the access, license, and
manifest checks pass; its tests demonstrate that ordering.
