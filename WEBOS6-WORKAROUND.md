# webOS 6 overlay and download workarounds

On an LG 55UP7670PUC running firmware 03.53.45 / SDK 6.5.3, SSAP accepted
overlay launch requests but a warm overlay did not navigate to the payload URL.
Closing its returned session and launching it again loaded the payload. The
download manager then accepted a download ticket but remained at zero bytes.
Staging the same reviewed payload files through the existing developer SSH
connection bypassed that second problem.

The changes add opt-in `--fresh-launch`, `--staged-dir`, and `--bind-ip` options,
concurrent HTTP serving, and debug status reporting back to the serving PC.
The original `autoroot.sh`, `main.js`, and `package.json` are unchanged. See the
README for prerequisites and usage. Related upstream report:
https://github.com/throwaway96/slopbro/issues/7.

## Validation

- The cold-launch page loaded and its native bridge was available on the TV.
- The staged payload ran as `uid=0(root)`; autoroot reported successful Homebrew
  Channel 0.7.3 installation and elevation, and its installed files were checked.
- Root SSH using the owner's local key was verified separately.
- Post-reboot persistence, startup, and visible Homebrew launch have **not yet
  been verified**. These results do not establish compatibility with every
  webOS 6 model or prove every supporting change was independently necessary.
- Offline checks: `python3 -m unittest discover -s tests -v`,
  `node tests/test_payload_lifetime.cjs`, and `git diff --check`.

## AI disclosure

This investigation, implementation, tests, and contribution write-up were
produced entirely by AI (OpenAI Codex), at the TV owner's direction. The owner
approved and performed the required TV pairing interactions. This disclosure
applies to this contribution; the existing upstream project retains its own
authorship and credits.

Upstream pull-request creation was restricted when this contribution was
prepared, so the patch is published on the owner's fork for review.
