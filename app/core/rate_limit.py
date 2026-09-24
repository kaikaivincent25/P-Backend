"""
slowapi rate limiter, keyed by client IP.

Applied to POST /api/contact/ specifically (see routers/contact.py) — that's
the one public, unauthenticated, write endpoint capable of triggering an
outbound email and a DB write per request, so it's the one worth protecting
against a burst of automated submissions. Read endpoints are cheap and
public by design, so we don't rate-limit them by default.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
