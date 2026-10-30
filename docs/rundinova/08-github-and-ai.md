---
title: GitHub access and AI project reviews
---

# GitHub access and AI project reviews

## One GitHub connection for many projects

RundiNova stores one GitHub integration at deployment level. Repository records
contain only the repository URL and its link to a RundiNova Project; they never
store a token per project.

The preferred production credential is a GitHub App installation. Configure
these values in the private production environment file:

- `RUNDINOVA_GITHUB_APP_ID`
- `RUNDINOVA_GITHUB_INSTALLATIONS_JSON`, a private JSON map from GitHub owner
  (user or organization) to that owner's installation ID. For a single owner,
  the legacy `RUNDINOVA_GITHUB_INSTALLATION_ID` remains supported.
- `RUNDINOVA_GITHUB_APP_PRIVATE_KEY_B64` (base64-encoded PEM private key)

Install the app on each GitHub owner that holds RundiNova repositories. For the
current `JubuNiyokoDev/PartenerWanje` repository, that is the `JubuNiyokoDev`
account; install it separately on the `RundiNova` organization for repositories
owned there. Choose only the repositories the company intends to manage.

The app should request read-only repository permissions for Metadata, Contents,
Issues, Pull requests, and Actions. It does not need permission to push code,
merge pull requests, manage secrets, or edit workflows. Public repositories can
be read without a credential; a private repository must be included in an
installation authorized by its owner. An installation token is minted and
cached briefly by the server. The existing `RUNDINOVA_GITHUB_TOKEN` remains a
single-token fallback, but it can only reach repositories granted to that PAT.

When adding a project, create one `RundiNova Repository` record with its GitHub
URL and link it to the ERPNext Project. The shared installation credential is
then used for synchronization; no new credential is required per project.

## AI review workflow

The intended AI feature is an on-demand reviewer that reads repository context
and proposes work. It may summarize the README, project structure, recent
commits, open issues, pull requests, and workflow status. It should return a
project summary, blockers, risks, and draft tasks with acceptance criteria and
suggested owners.

The AI may not create tasks, assign people, edit GitHub issues, push code, or
merge pull requests without a person approving the specific action. The first
release should create selected approved tasks inside RundiNova only.

The implementation supports Gemini and Cohere. Select the provider with
`RUNDINOVA_AI_PROVIDER`; Cohere uses `COHERE_API_KEY` and `COHERE_MODEL`, while
Gemini uses `RUNDINOVA_GEMINI_API_KEY` and `RUNDINOVA_GEMINI_MODEL`. A Director can start an account-wide scan from a
repository record. RundiNova discovers repositories granted to that GitHub App
installation and queues a separate analysis job per repository. Project Leads
can review one repository at a time. Each repository record shows whether the
analysis is queued, running, complete, or failed. It reads bounded text files from the linked repository,
redacts common credential patterns. The user starts each review from the
repository form and confirms that source text will be sent to the configured
provider. Cohere analyses do not have live web grounding: external market claims
must be treated as hypotheses until verified, and no citations are presented as
verified. A human must review the report. The endpoint never creates or assigns
work.
