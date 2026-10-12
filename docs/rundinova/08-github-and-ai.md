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
- `RUNDINOVA_GITHUB_INSTALLATION_ID`
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

No model provider or API credential is currently configured for the production
site. Before enabling AI reviews, choose a provider and configure its key in a
protected integration setting. Send only the repository information needed for
the review and document the selected provider's data-retention terms.
