# Umbrel Drive 1.1.1 browser fix

A local reproduction of the 1.1.0 package returned alternating HTTP 500 and 200
login pages when a second Redis occupied the generic redis DNS alias on the same
Docker network. Logs showed Redis authentication and session errors. Isolated
Compose tests and Basic-auth DAV checks had not covered that deployment condition.

Version 1.1.1 uses unique database/cache aliases. A deployment config override
replaces the legacy dbhost before entrypoint initialization, preserving existing
data. The health check now loads the login page rather than checking only the
installation-status endpoint.

The regression test deliberately occupies both generic db and redis aliases with
a conflicting service. Repeated login-page rendering, cookie/Origin/CSRF sign-in,
authenticated file access, setup-page rendering, and a forced container restart
passed. The seven file/sharing/version/trash/quota tests also passed, as did Umbrel
package linting (zero errors; one intentional Redis hardening warning).

Runtime commit: d1992b9bc6b3cc63c0d583cac4be9d1b42ba0cf3.
Native Linux and signed Android binaries are unchanged.

The full release workflow passed:
https://github.com/carter-scramlin/umbrel-cloud-store/actions/runs/42563659825

Version 1.1.1 was installed through Umbrel on an amd64 device running
umbrelOS 2.1.0-beta.1. Live HTTPS tests passed repeated login-page
rendering, cookie/Origin/CSRF sign-in, authenticated Files access, and the device
setup page through both the LAN address and the hostname used in the reported
failure. They used a process-local certificate pin with hostname validation;
certificate warnings were not bypassed and system trust was not changed.

The browser connector itself could not inspect the owner's tab, so this is live
HTTP browser-session verification, not a claim of automated GUI/JavaScript QA.

The previous Home/Umbrel Drive folder connection was restored through native app
settings. Cookie-based HTTPS login, Files access, and setup-page checks passed
again after its automatic restart. The app reached ready and logged the Files
connection without browser 500 or Redis authentication errors in the checked logs.
