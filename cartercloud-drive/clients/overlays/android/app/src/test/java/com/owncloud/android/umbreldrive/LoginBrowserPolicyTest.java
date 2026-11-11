/*
 * SPDX-FileCopyrightText: 2026 Carter Cloud
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */
package com.owncloud.android.umbreldrive;

import org.junit.Test;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

public class LoginBrowserPolicyTest {
    @Test
    public void httpsUsesAuthTabAndAllowsLoginQuery() {
        assertTrue(LoginBrowserPolicy.usesAuthTab("https://umbrel/login/v2/flow/token"));
        assertTrue(LoginBrowserPolicy.isAllowed("https://umbrel/login?token=fixture", false));
    }

    @Test
    public void httpRequiresOptInAndUsesStandardBrowser() {
        assertFalse(LoginBrowserPolicy.usesAuthTab("http://100.88.1.2:8391/login"));
        assertFalse(LoginBrowserPolicy.isAllowed("http://100.88.1.2:8391/login", false));
        assertTrue(LoginBrowserPolicy.isAllowed("http://100.88.1.2:8391/login", true));
    }

    @Test
    public void httpsCannotDowngradeEvenWhenHttpIsEnabledForAnotherProfile() {
        assertFalse(LoginBrowserPolicy.isAllowedForServer("http://server/login", "https://server", true));
        assertTrue(LoginBrowserPolicy.isAllowedForServer("http://server/login", "http://server", true));
        assertTrue(LoginBrowserPolicy.isAllowedForServer("https://server/login", "http://server", true));
        assertFalse(LoginBrowserPolicy.isAllowedForServer("http://server/login", "http://server", false));
    }

    @Test
    public void rejectsUnexpectedSchemesCredentialsAndMalformedUrls() {
        for (String value : new String[]{null, "", "not a URL", "file:///tmp/file", "javascript:alert(1)",
                "https://name:secret@server/login"}) {
            assertFalse(LoginBrowserPolicy.isAllowed(value, true));
        }
    }
}
