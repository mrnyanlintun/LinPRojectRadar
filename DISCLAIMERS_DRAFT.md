# Disclaimers by account type. DRAFT. REQUIRES LIN'S REVIEW BEFORE ANY OF IT IS PUBLISHED.

**Nothing in this file is live.** These are drafts of the liability notices that vary by account
type, written for review under the standing rule that liability and consent language is never
adopted on a session's own judgement. No live surface has been changed to carry this text, and
the operational notice currently live in `index.html` is untouched by this file.

Two related facts, for the reviewer:

- The operational notice at `index.html` (login expander and footer variant) is itself still
  marked in comments as drafted and not yet reviewed, and it **can now display**: `auth.js` sets
  the operational class from the login response, so an operational account sees that unreviewed
  text today. Reviewing this file is also the opportunity to review or replace that.
- Both export paths (`assets/js/export.js` and `server/app/research_export.py`) carry no notice,
  attribution, or copyright at all. The exported file is the artifact most likely to leave the
  platform and be read by someone who never saw a footer. Whether a notice belongs in the export
  is a decision this draft flags but does not make.

The mechanism these drafts would ride on already exists and is verified: `.notice-research` is
the default and shows before sign-in, because restrictive text is the fail-safe direction, and
`body.og-account-operational` switches to the operational variant only after the server resolves
the caller as operational.

---

## 1. Research variant (also the pre-sign-in default)

> **Notice: academic research instrument.** Opus Gubernatio is a proof of concept developed
> solely for doctoral research and demonstration. It is not a commercial service and is provided
> as is, without warranty of any kind, express or implied.
>
> All project data is synthetic. No real project, agency, employer, contractor, or vendor is
> referenced. Do not upload confidential, proprietary, personally identifiable, or otherwise
> sensitive information, or any document relating to an actual project.
>
> Uploaded content is sent to third-party artificial intelligence services for extraction and is
> stored in research infrastructure. Analytical outputs are advisory. They are not a validated
> compliance determination, a contractual direction, or a diagnosis of a live project. The
> operator disclaims all liability arising from or relating to uploaded content to the fullest
> extent permitted by law.

## 2. Operational variant

> **Notice.** Opus Gubernatio is provided as is, without warranty of any kind, express or
> implied.
>
> Analytical outputs are advisory. They are not a validated compliance determination, a
> contractual direction, or a diagnosis of a live project.
>
> Uploaded content is sent to third-party artificial intelligence services for extraction and is
> stored in the platform. You are responsible for confirming that you are authorized to upload
> each document, and for your organization's data handling, confidentiality, and records
> obligations. The operator disclaims all liability arising from or relating to uploaded content
> to the fullest extent permitted by law.

The operational variant deliberately does **not** say synthetic data only, does **not** say no
real project is referenced, and does **not** tell the user not to submit actual project
documents: an operational user uploading real project documents is the designed case, and each
of those statements would be false for them.

## 3. Constant in both states

Attribution, on two lines:

> Doctor of Engineering
> The School of Engineering and Applied Science of The George Washington University

Copyright:

> © 2026 Nyan Lin Tun. All rights reserved. Opus Gubernatio™ and the associated framework,
> software, and documentation are the intellectual property of the author. Unauthorized
> reproduction, distribution, or use is prohibited.

Note for review: the copyright line's phrase "the associated framework" survives from before the
framework name was retired. Whether it stays is a legal wording decision, so it is flagged here
rather than edited.

## 4. Out of scope for this draft

Consent text is untouched everywhere. The consent placeholders in `index.html` are correctly
marked as drafts and need IRB approval, not an editor.
