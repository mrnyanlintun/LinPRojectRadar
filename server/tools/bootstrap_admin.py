#!/usr/bin/env python3
"""
One-off bootstrap of the first ResearchAdmin account.

Every path that creates a participant requires an admin session (`a_adminparticipantcreate`
calls `_require_admin`, research_identity.py:475). Before any participant exists there is no
admin session to hold, so the system cannot create its own first account. This script is the
only way through that, and it is deliberately a script rather than an action: an unauthenticated
account-creation endpoint on a live deployment would be a standing hole, whereas a script has to
be run by someone who already holds the database credential.

THE GUARD. It refuses to run if a ResearchAdmin already exists, in any state — active or
deactivated. That is what stops this from becoming a way to mint a second admin later, and it is
why the check is on `role == 'ResearchAdmin'` alone and not on `is_active`: a deactivated admin
is evidence that the bootstrap already happened, and silently re-running past it would produce
an admin the account-admin surface never issued.

It does not hash the password itself. It calls `hash_access_token` / `issue_access_token` from
research_identity, so the stored hash is byte-identical to one written by the normal admin path
and the sign-in comparison cannot diverge from it.

The account created is `account_type='operational'` and carries BOTH sign-in paths:
  - username + password -> a_login (research_identity.py:245)
  - Google SSO on google_email -> a_ssologin (research_identity.py:340), which refuses any
    account whose account_type is 'research' — hence operational, not merely a convenience.

Run (from server/):

    DATABASE_URL=postgresql+psycopg://... python tools/bootstrap_admin.py \
        --google-email you@example.com --username admin

The password is generated unless --password is given, and is printed ONCE. Only its hash is
stored; a lost password is reset through `setpassword`, never recovered.
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from app.research_identity import (
    ROLE_ADMIN,
    hash_access_token,
    issue_access_token,
)
from app.research_models import Participant, new_ulid  # noqa: F401  (new_ulid via default)


def main() -> int:
    ap = argparse.ArgumentParser(description="Create the first ResearchAdmin account.")
    ap.add_argument("--google-email", required=True,
                    help="Google address for SSO sign-in. Stored lowercased.")
    ap.add_argument("--username", default="admin",
                    help="Sign-in username. Stored as pseudonymous_code. Default: admin")
    ap.add_argument("--display-name", default=None,
                    help="Display label for the operational account. Defaults to the username.")
    ap.add_argument("--password", default=None,
                    help="Initial password. Generated if omitted. Printed once either way.")
    args = ap.parse_args()

    if not os.environ.get("DATABASE_URL"):
        print("DATABASE_URL is not set. Refusing to guess a target database.", file=sys.stderr)
        return 2

    # Via settings, not os.environ directly: Render hands out a bare `postgresql://` URL, which
    # SQLAlchemy resolves to psycopg2 — a driver this build does not install. settings.py
    # already normalises that to the psycopg 3 dialect, and duplicating the rule here would
    # give the bootstrap path its own way of failing to connect.
    from app.settings import load_settings

    engine = create_engine(load_settings().database_url, future=True)
    Session = sessionmaker(bind=engine, future=True)

    with Session() as session:
        # The guard. Any ResearchAdmin at all, active or not.
        existing = session.scalars(
            select(Participant).where(Participant.role == ROLE_ADMIN)
        ).all()
        if existing:
            print("REFUSED: a ResearchAdmin already exists. This script bootstraps the first "
                  "one only.", file=sys.stderr)
            for p in existing:
                print(f"  - {p.pseudonymous_code} ({p.participant_id}) "
                      f"account_type={p.account_type} is_active={p.is_active}", file=sys.stderr)
            print("Create further admins through adminparticipantcreate with an admin session.",
                  file=sys.stderr)
            return 1

        email = args.google_email.strip().lower()
        if session.scalar(select(Participant).where(
                func.lower(Participant.google_email) == email)):
            print(f"REFUSED: {email} is already linked to another participant.", file=sys.stderr)
            return 1

        username = args.username.strip()
        if session.scalar(select(Participant).where(
                Participant.pseudonymous_code == username)):
            print(f"REFUSED: pseudonymous_code already in use: {username}", file=sys.stderr)
            return 1

        supplied = (args.password or "").strip()
        plaintext, token_hash = (supplied, hash_access_token(supplied)) if supplied \
            else issue_access_token()

        participant = Participant(
            pseudonymous_code=username,
            role=ROLE_ADMIN,
            account_type="operational",
            access_token_hash=token_hash,
            display_name=(args.display_name or username),
            google_email=email,
            is_active=True,
            completion_status="not_started",
        )
        session.add(participant)
        session.flush()
        pid = participant.participant_id

        # Audited like any other creation, with the actor named as the script rather than a
        # participant_id, because there is no caller to attribute it to. `audit()` is not used:
        # it takes a participant_id meaning "who this is about", and conflating that with "who
        # did it" here would make the first admin look self-created by an existing session.
        from app.research_models import AuditEvent
        session.add(AuditEvent(
            event_type="participant_created",
            participant_id=pid,
            event_metadata={
                "created_by": "tools/bootstrap_admin.py",
                "role": ROLE_ADMIN,
                "pseudonymous_code": username,
                "account_type": "operational",
                "google_email_linked": True,
                "bootstrap": True,
            },
        ))
        session.commit()

    print("")
    print("=" * 66)
    print("  ResearchAdmin created. These credentials are shown ONCE.")
    print("=" * 66)
    print(f"  participant_id : {pid}")
    print(f"  username       : {username}")
    print(f"  password       : {plaintext}")
    print(f"  google_email   : {email}")
    print(f"  role           : {ROLE_ADMIN}")
    print(f"  account_type   : operational")
    print("=" * 66)
    print("  Only the hash is stored. This password cannot be retrieved again;")
    print("  a lost one is reset through the setpassword action, never recovered.")
    print("  Google SSO on the address above is the second, equivalent path in.")
    print("=" * 66)
    print("")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
