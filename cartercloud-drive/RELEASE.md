# Umbrel Drive 1.1.1 — browser sign-in fix

Fix Internal Server Error on the login page when other Umbrel apps have services
named redis or db. Drive now uses its own unique network aliases for Redis and
PostgreSQL. Existing installations receive a database-host override before startup;
accounts, files, credentials, and Files folder selections are preserved.

The app health check now exercises the login page as well as installation status.
Regression coverage performs cookie/CSRF browser sign-in, loads Files and the setup
page, and repeats after restart while conflicting generic service names are present.

Native client binaries are unchanged at version 1.0.0. The community app retains
its 1.1 Files integration; see FEATURES.md and TESTING.md for coverage and limits.
