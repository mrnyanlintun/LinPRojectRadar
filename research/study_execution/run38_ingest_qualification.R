#!/usr/bin/env Rscript
# Run 38 R-ingestion qualification for the frozen analysis dataset.
#
# Formal statistics for this praxis remain in R. This script is the INGESTION AND VALIDATION
# entry point only: it proves that R can consume the frozen, deidentified, checksummed CSV
# without manual cleanup. It deliberately performs NO inferential analysis and NO hypothesis
# test. Running it on dry-run data is a schema qualification, never a result.
#
# Usage:
#   Rscript run38_ingest_qualification.R <dataset.csv> <manifest.json>
#
# Base R only, no packages: the qualification must run on a bare R installation so it cannot
# fail for a reason that has nothing to do with the dataset. sha256 is taken from the system
# sha256sum utility rather than a package, for the same reason.

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 2L) stop("usage: run38_ingest_qualification.R <dataset.csv> <manifest.json>")
csv_path <- args[[1L]]; man_path <- args[[2L]]

checks <- list()
chk <- function(ok, label, detail = "") {
  checks[[length(checks) + 1L]] <<- list(ok = isTRUE(ok), label = label, detail = detail)
  cat(sprintf("  %s  %s%s\n", if (isTRUE(ok)) "PASS" else "FAIL", label,
              if (!isTRUE(ok) && nzchar(detail)) paste0("   ", detail) else ""))
}

# ---- a minimal JSON reader. The manifest is machine-written with a flat, known shape; adding
# a package dependency to read it would defeat the point of a bare-R qualification.
read_manifest <- function(path) {
  txt <- paste(readLines(path, warn = FALSE), collapse = "")
  get_str <- function(key) {
    m <- regmatches(txt, regexpr(sprintf('"%s"[[:space:]]*:[[:space:]]*"[^"]*"', key), txt))
    if (!length(m)) return(NA_character_)
    sub('^.*:[[:space:]]*"', "", sub('"$', "", m))
  }
  get_num <- function(key) {
    m <- regmatches(txt, regexpr(sprintf('"%s"[[:space:]]*:[[:space:]]*[0-9]+', key), txt))
    if (!length(m)) return(NA_integer_)
    as.integer(sub('^.*:[[:space:]]*', "", m))
  }
  list(sha256 = get_str("sha256"), schema_version = get_str("schema_version"),
       row_count = get_num("row_count"), column_count = get_num("column_count"),
       row_grain = get_str("row_grain"), null_representation = get_str("null_representation"),
       simulation_version = get_str("simulation_version"),
       participant_package = get_str("participant_package"),
       freeze_candidate_commit = get_str("freeze_candidate_commit"))
}

man <- read_manifest(man_path)

cat("=== checksum ===\n")
sha_out <- tryCatch(system2("sha256sum", shQuote(csv_path), stdout = TRUE), error = function(e) NA)
actual <- if (length(sha_out) && !is.na(sha_out[[1L]])) sub("[[:space:]].*$", "", sha_out[[1L]]) else NA
chk(!is.na(actual) && identical(actual, man$sha256),
    "dataset sha256 matches the freeze manifest", paste("manifest", man$sha256, "actual", actual))

cat("=== ingestion ===\n")
# na.strings is the manifest's declared null token; no other cleanup is applied, which is the
# property under test.
d <- read.csv(csv_path, stringsAsFactors = FALSE, na.strings = man$null_representation,
              check.names = TRUE, encoding = "UTF-8")
chk(is.data.frame(d) && nrow(d) > 0L, "R reads the CSV with no manual cleanup",
    paste("rows", nrow(d)))
chk(identical(nrow(d), man$row_count), "row count matches the manifest",
    paste(nrow(d), "vs", man$row_count))
chk(identical(ncol(d), man$column_count), "column count matches the manifest",
    paste(ncol(d), "vs", man$column_count))

cat("=== schema version and provenance ===\n")
chk("schema_version" %in% names(d) && all(d$schema_version == man$schema_version),
    "every row carries the manifest schema_version")
chk("simulation_version" %in% names(d) && all(d$simulation_version == man$simulation_version),
    "every row carries the frozen simulation version")
chk("participant_package" %in% names(d) && all(d$participant_package == man$participant_package),
    "every row carries the participant package identity")
chk("freeze_candidate_commit" %in% names(d) &&
      all(d$freeze_candidate_commit == man$freeze_candidate_commit),
    "every row carries the freeze candidate commit")
chk("record_class" %in% names(d) && !any(is.na(d$record_class)) &&
      all(d$record_class %in% c("TEST_ONLY", "STUDY")),
    "record_class is present and within its closed vocabulary")

cat("=== required columns and types ===\n")
required <- c("study_participant_id", "scenario_id", "period", "sequence_number",
              "pre_action", "pre_confidence", "pre_locked_at", "reveal_at",
              "ai_recommended_action", "final_action", "disposition", "final_confidence",
              "final_submitted_at", "action_revised", "revision_direction",
              "confidence_change", "confidence_direction")
chk(all(required %in% names(d)), "every required analysis column is present",
    paste("missing:", paste(setdiff(required, names(d)), collapse = ", ")))
chk(is.numeric(d$pre_confidence) && is.numeric(d$final_confidence),
    "confidence columns ingest as numeric without coercion")
chk(is.numeric(d$confidence_change) && is.numeric(d$sequence_number),
    "confidence_change and sequence_number ingest as numeric")
chk(is.numeric(d$action_revised) || is.logical(d$action_revised),
    "action_revised ingests as a numeric/logical indicator")

cat("=== categorical levels ===\n")
lv <- function(col, allowed) {
  v <- d[[col]]; v <- v[!is.na(v)]
  chk(all(v %in% allowed), sprintf("%s stays inside its closed vocabulary", col),
      paste("unexpected:", paste(unique(setdiff(v, allowed)), collapse = ", ")))
}
lv("revision_direction", c("none", "toward_ai", "away_from_ai", "lateral"))
lv("confidence_direction", c("increase", "decrease", "unchanged"))
lv("completion_state", c("complete", "pre_only", "revealed_not_decided", "not_started"))
lv("disposition", c("accept", "accept_with_conditions", "modify", "reject", "defer",
                    "request_evidence", "escalate", "transfer_authority"))

cat("=== unique key and population ===\n")
key <- paste(d$study_participant_id, d$scenario_id, d$period, sep = "|")
chk(!any(duplicated(key)), "participant x project x period is unique",
    paste("duplicates:", sum(duplicated(key))))
per_participant <- table(d$study_participant_id)
chk(all(per_participant %% 1 == 0) && length(per_participant) > 0L,
    "at least one participant is present", paste("participants:", length(per_participant)))
proj_per <- tapply(d$scenario_id, d$study_participant_id, function(x) length(unique(x)))
chk(all(proj_per == 6L), "every participant covers 6 projects",
    paste(paste(names(proj_per), proj_per, collapse = "; ")))
periods_ok <- tapply(seq_len(nrow(d)), paste(d$study_participant_id, d$scenario_id),
                     function(i) identical(sort(unique(d$period[i])),
                                           sort(c("P1","P2","P3","P4","P5","P6"))))
chk(all(unlist(periods_ok)), "every participant-project covers periods P1..P6")
chk(all(per_participant == 36L), "every participant contributes 36 project-period rows",
    paste(paste(names(per_participant), per_participant, collapse = "; ")))

cat("=== missingness ===\n")
must_not_be_na <- c("study_participant_id", "scenario_id", "period", "record_class",
                    "schema_version", "simulation_version")
chk(all(vapply(must_not_be_na, function(c) !any(is.na(d[[c]])), logical(1))),
    "no key or provenance column is missing on any row")
complete <- d[d$completion_state == "complete", , drop = FALSE]
chk(nrow(complete) == 0L || !any(is.na(complete$final_action)),
    "no completed row is missing its final action")

cat("=== impossible transitions ===\n")
ts <- function(x) as.POSIXct(x, tz = "UTC", tryFormats = c("%Y-%m-%dT%H:%M:%S%z",
                                                            "%Y-%m-%dT%H:%M:%S"))
pre <- ts(d$pre_locked_at); rev <- ts(d$reveal_at); fin <- ts(d$final_submitted_at)
chk(all(is.na(pre) | is.na(rev) | rev >= pre), "no reveal precedes its preliminary lock")
chk(all(is.na(rev) | is.na(fin) | fin >= rev), "no final decision precedes its reveal")
chk(all(is.na(d$deliberation_seconds) | d$deliberation_seconds >= 0),
    "no negative deliberation duration")
chk(all(is.na(rev) | !is.na(pre)), "no revealed row lacks a preliminary lock")
chk(all(is.na(fin) | !is.na(rev)), "no final decision lacks a reveal")

cat("=== derivability of the planned dependent variables ===\n")
# Recomputed in R from the columns alone. This proves the dataset carries enough information to
# derive them, which is the whole point of the qualification. It is NOT an effect estimate.
recomputed <- ifelse(is.na(d$pre_action) | is.na(d$final_action), NA_integer_,
                     as.integer(d$pre_action != d$final_action))
chk(all(is.na(recomputed) == is.na(d$action_revised)) &&
      all(recomputed == d$action_revised, na.rm = TRUE),
    "action revision indicator is re-derivable in R from pre/final action")
dir2 <- ifelse(is.na(recomputed) | is.na(d$ai_recommended_action), NA_character_,
        ifelse(recomputed == 0L, "none",
        ifelse(d$final_action == d$ai_recommended_action, "toward_ai",
        ifelse(d$pre_action == d$ai_recommended_action, "away_from_ai", "lateral"))))
chk(all(dir2 == d$revision_direction, na.rm = TRUE) &&
      all(is.na(dir2) == is.na(d$revision_direction)),
    "revision direction relative to the AI is re-derivable in R")
cshift <- d$final_confidence - d$pre_confidence
chk(all(cshift == d$confidence_change, na.rm = TRUE),
    "confidence change is re-derivable in R from the two confidence columns")
chk(!any(is.na(d$disposition[d$completion_state == "complete"])),
    "AI disposition is present on every completed decision")

cat("=== deidentification ===\n")
forbidden <- c("email", "name", "login", "employee", "ip_address", "ip_hash",
               "access_token", "session_token", "google_email", "display_name")
hits <- forbidden[vapply(forbidden, function(f) any(grepl(f, names(d), fixed = TRUE)),
                         logical(1))]
chk(length(hits) == 0L, "no column name names a direct identifier",
    paste(hits, collapse = ", "))
chr_cols <- names(d)[vapply(d, is.character, logical(1))]
email_like <- vapply(chr_cols, function(c)
  any(grepl("[[:alnum:]._%+-]+@[[:alnum:].-]+\\.[[:alpha:]]{2,}", d[[c]])), logical(1))
chk(!any(email_like), "no cell contains an email-shaped string",
    paste(chr_cols[email_like], collapse = ", "))

passed <- sum(vapply(checks, function(c) c$ok, logical(1)))
cat("\n")
cat(sprintf("RESULT: %d/%d checks passed\n", passed, length(checks)))
if (passed != length(checks)) quit(status = 1L)
