/*
 * SPDX-FileCopyrightText: 2026 Carter Cloud
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */
package com.owncloud.android.umbreldrive;

import java.net.URI;

public final class LoginBrowserPolicy {
    private LoginBrowserPolicy() {
    }

    public static boolean isAllowed(String value, boolean allowHttp) {
        URI uri = parse(value);
        return uri != null && uri.getHost() != null && !uri.getHost().isEmpty() && uri.getRawUserInfo() == null &&
            ("https".equalsIgnoreCase(uri.getScheme()) || (allowHttp && "http".equalsIgnoreCase(uri.getScheme())));
    }

    public static boolean isAllowedForServer(String value, String server, boolean allowHttp) {
        URI origin = parse(server);
        return origin != null && isAllowed(server, allowHttp) &&
            isAllowed(value, allowHttp && "http".equalsIgnoreCase(origin.getScheme()));
    }

    public static boolean usesAuthTab(String value) {
        URI uri = parse(value);
        return uri != null && "https".equalsIgnoreCase(uri.getScheme());
    }

    private static URI parse(String value) {
        if (value == null) {
            return null;
        }
        try {
            return URI.create(value);
        } catch (IllegalArgumentException error) {
            return null;
        }
    }
}
