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
- The sign-in page's **attribution** was a shorter form. It is no longer: on 2026-08-02 Lin
  approved the section 3 sentence for that surface too, and the sign-in box and the access-denied
  panel now carry it verbatim.
- The sign-in page's **copyright** is still a shorter form, `© 2026 Nyan Lin Tun. All rights
  reserved.`, and stays that way. The 2026-08-02 revision changed the wording each surface
  carries, not which surfaces carry the full copyright paragraph.
- The access-denied panel carries its own one-line notice, `Access restricted to authorized use.
  This platform is an academic proof-of-concept; no warranty is provided.` It is a third notice
  variant, is not derived from section 1 or 2, and was not part of any approval. Flagged, not
  edited: replacing it would mean composing or selecting liability wording.
- Four developer-facing pages (`calibration/verify.html`, `tools/export_lib.html`, `tests.html`,
  `assets/visualizations/pceif_neural_signal_flow.html`) carried a fused attribution-plus-advisory
  sentence of their own. On 2026-08-02 each was replaced by two sentences quoted verbatim from the
  approved text: the advisory sentence from section 2 and the attribution sentence from section 3.
  No new wording was composed for them.

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

Attribution, one sentence. Revised and approved by Lin on 2026-08-02:

> Developed as part of doctoral research at the School of Engineering and Applied Science, The
> George Washington University. The university is not a party to this notice and does not endorse
> or warrant the platform.

Copyright. Revised and approved by Lin on 2026-08-02:

> © 2026 Nyan Lin Tun. All rights reserved. Opus Gubernatio and the associated software and
> documentation are the intellectual property of the author. Unauthorized reproduction,
> distribution, or use is prohibited.

Three things changed on 2026-08-02, and none of them may be reintroduced:

- **"the associated framework" is gone.** `NAMING_AUTHORITY.md` states there is deliberately no
  framework, and the About page says so in prose. The old copyright line asserted one existed.
- **The trademark symbol is gone.** It is not "Opus Gubernatio™" anywhere.
- **The attribution is a sentence, and it states what the relationship is not.** It previously sat
  as a bare title block directly beneath a liability disclaimer, which read as though the
  university were issuing or standing behind the notice. The sign-in box carried the same defect
  in shorter form, as a middot-separated line, `The George Washington University · Doctor of
  Engineering praxis research`. Both are replaced by the sentence above, verbatim.

Do not compose a shorter form of either blockquote for a constrained surface. A surface either
carries the approved sentence whole or does not carry it.

## 4. Out of scope for this draft

Consent text is untouched everywhere. The consent placeholders in `index.html` are correctly
marked as drafts and need IRB approval, not an editor.
