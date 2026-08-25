# Secrets, Variables, Keys

## gh secret (Actions/Dependabot/Codespaces secrets)

Levels: repository (default), environment (`-e`), organization (`-o`), user (`-u`). Values are **locally encrypted** before upload. Apps: `-a actions|agents|codespaces|dependabot`.

```bash
gh secret list -R OWNER/REPO
gh secret set MYSECRET -R OWNER/REPO --body "$VALUE"     # or: gh secret set MYSECRET < file
gh secret set MYSECRET --env production                   # deployment-environment secret
gh secret set -f .env                                     # bulk from dotenv file
gh secret delete MYSECRET -R OWNER/REPO
```

Org-level visibility: `--visibility all|private|selected` + `--repos r1,r2`; `--no-repos-selected` for none.

## gh variable (Actions/Dependabot variables — plaintext)

```bash
gh variable list -R OWNER/REPO
gh variable get VARNAME
gh variable set VARNAME --body "value" [-e env | -o org]
gh variable delete VARNAME          # alias: gh variable remove
```

## gh ssh-key / gh gpg-key (account keys)

```bash
gh ssh-key list                          # keys on the active account
gh ssh-key add ~/.ssh/id_ed25519.pub --title "laptop"
gh gpg-key list
gh gpg-key add mykey.asc                 # armored public key file
```
These target the **active authenticated account** — run `gh auth switch` first if needed.
