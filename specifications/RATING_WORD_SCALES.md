# Rating word scales — how a rated word becomes a number

**Run 80.** This file states, for a person, every place the platform reads a **word** where a
measure needs a **number**. It is not one of the sixty-three module specifications; it is the
shared statement of one extraction-boundary rule that several of them depend on.

The authority is `server/app/extraction_merge.ORDINAL_WORD_SCALES`. The table below is checked
against that dictionary by `server/tools/test_run80.py`, so if one changes and the other does
not, a check goes red. Do not edit the table here by hand and expect it to stand.

## The CPARS past-performance scale

A Contractor Performance Assessment Reporting System (CPARS) evaluation states its ratings as
adjectives, because that is what the regulation requires it to state. `D26_past_performance_report`
is such a document. The four rating fields it carries are read on the standard five-level CPARS
scale, mapped onto the five-point scale `A6.4 run_contractor_performance` already enforces:

| Rating word     | Number |
|-----------------|--------|
| Exceptional     | 5      |
| Very Good       | 4      |
| Satisfactory    | 3      |
| Marginal        | 2      |
| Unsatisfactory  | 1      |

It applies to these extraction fields, and to no others:
`overall_rating`, `schedule_rating`, `cost_rating`, `quality_rating`.

## A word outside the scale is not coerced

**Only those five words are recognised.** A rating stating anything else — "Above Average",
"Pass", "N/A", "4 of 5" — is **not** mapped, **not** guessed at, and **not** turned into a
number. The field is treated as **absent**: no observation is written for it, no figure is
substituted for it, and the platform reports, per document and per field:

> `overall_rating in <file> is 'Above Average', which is not a rating on the scale this
> evaluation uses (Exceptional, Very Good, Satisfactory, Marginal, Unsatisfactory). The rating
> was not recognised, so this field is treated as absent and no figure is used in its place.
> The rest of the document still contributes.`

A measure that needed that rating abstains, which is the standing default. Inventing a level the
evaluation does not have would be a fabricated reading, and this platform does not produce one.

## The rest of the document still contributes

Before Run 80, one unreadable field refused the **whole document**: no observation row, no
`Document` row, nothing stored, and every other figure the document stated was discarded with it.
The owner ruled that behaviour out (Run 80 order, section 3, item 3). An unreadable field is now
absent by itself. See the docstring of `validate_numeric_fields` for what that ruling costs and
for the one case it deliberately does **not** cover: a value that reads as a number but sits
outside the field's permitted range still refuses the whole document, under Run 14's ruling.
