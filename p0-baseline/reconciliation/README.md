# Reconciliation reports

Written by `server/tools/import_from_drive.py` to `<timestamp>/report.md` and `report.json`.

The import is not considered successful until a report shows zero **unexplained** discrepancies.
Differences with a known cause (an unparseable `project.json`, a history file whose name carries
no period) appear under "Explained differences" rather than being counted as clean, so a count
difference is never silent.

No report is present yet: the import has not been run against Drive, because
`GOOGLE_SERVICE_ACCOUNT_JSON` has not been supplied.
