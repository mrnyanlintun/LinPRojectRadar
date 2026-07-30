# Reference sources — NOT deployment artifacts

`Code_v10.36_editor_head.gs` is **editor HEAD, not the deployed version, and must not be
checksummed as a deployment artifact.**

Details:

- It declares `API_VERSION = 'lin-project-radar-backend-v10.36-roster-json'`.
- The live endpoint reports `lin-project-radar-backend-v10.29-geocode`.
- It was supplied as a `.docx` and extracted from Word XML. The extracted text is **not verifiable
  as byte identical** to the console original: paragraph breaks were reconstructed from `</w:p>`
  markers, and a Word round trip does not preserve line endings, trailing whitespace or tab
  structure faithfully. Character content itself survived intact (19 em dashes U+2014 and one
  U+00B7; zero U+FFFD replacement characters), so the earlier concern about mangled non-ASCII does
  not apply. The fidelity objection is structural, not character level.
- It declares three different versions of itself in its own header: `v10.26-drop-cat12` in the
  banner comment, `v10.31-milestones` in the deploy instruction, and `v10.36-roster-json` in
  `API_VERSION`.

Permitted use: parsing dispatcher structure as a labelled cross-check.

Prohibited use: as the deployed contract, as the basis of a SHA-256 provenance record, or as
evidence of what any deployment serves.

Deployed snapshots belong in `apps_script/deployed/version-NNN/`, taken as plain text from the
Apps Script console.
