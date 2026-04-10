---
name: repo-eval
description: Evaluate a single GitHub repository for adoption. Reads README, manifest, activity, and CI to produce a technical verdict. Use when the user asks "is X worth using", "evaluate owner/repo", "what does this project actually do". Argument is owner/name or a github.com URL.
argument-hint: <owner/name or github URL>
context: fork
agent: repo-deep-dive
allowed-tools: WebFetch Bash(gh *)
---

# Repo evaluation

Run a deep-dive on a single GitHub repository.

## Task

Target: $ARGUMENTS

1. Normalize the input to `owner/name`. If the user passed a full URL, extract the path. If they passed only a topic name, stop and ask which repo.
2. Apply the repo-deep-dive investigation steps from your system prompt.
3. Return the structured evaluation. Save a copy to `digests/repo-${0}.md` (replace `/` with `-` in the filename).
