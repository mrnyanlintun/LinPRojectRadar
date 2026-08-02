# Disclaimers by account type. APPROVED AND LIVE.

**This file is the source of the live text.** Lin approved these variants as drafted on
2026-08-02 and they are now published. The filename keeps its original form because that is how
the approval refers to it; the word "draft" in the name is historical, not a status.

**The two variants below are live verbatim.** Section 1 shows to research accounts and before
sign-in; section 2 shows to operational accounts. Each appears on two surfaces, the sign-in
notice and the site footer, in both cases quoting the blockquotes below character for character.

**Edit here first.** `server/tools/test_disclaimers.py` extracts the blockquotes in sections 1
and 2 from this file and fails if the live text in `index.html` diverges from them by a single
character, so the reviewable text and the live text cannot drift apart. Changing the wording is
the researcher's decision; a session may not extend, strengthen, or add to it.

Still open, and unchanged by this approval:

- Both export paths (`assets/js/export.js` and `server/app/research_export.py`) carry no notice,
  attribution, or copyright at all. The exported file is the artifact most likely to leave the
  platform and be read by someone who never saw a footer. Whether a notice belongs in the export
  is a decision this file flags but does not make.
- The sign-in page's own attribution and copyright lines are shorter forms that do not match
  section 3 below. They were left alone: section 3 states what is constant across the two
  account types, and reconciling the sign-in page's separate lines to it is an editorial
  decision that was not part of this approval.

The mechanism these variants ride on is verified: `.notice-research` is the default and shows
before sign-in, because restrictive text is the fail-safe direction, and
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
