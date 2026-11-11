/*
 * SPDX-FileCopyrightText: 2026 Carter Cloud
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */
package com.owncloud.android.umbreldrive

import org.junit.Assert.assertEquals
import org.junit.Assert.assertThrows
import org.junit.Test

class RemoteAccessAddressTest {
    @Test
    fun `default is HTTPS and preserves port`() {
        assertEquals(
            "https://umbrel.tail123.ts.net:8390",
            RemoteAccessAddress.normalize("umbrel.tail123.ts.net:8390/", false)
        )
    }

    @Test
    fun `HTTP requires explicit choice`() {
        assertThrows(IllegalArgumentException::class.java) {
            RemoteAccessAddress.normalize("http://100.88.1.2:8391", false)
        }
        assertEquals("http://100.88.1.2:8391", RemoteAccessAddress.normalize("http://100.88.1.2:8391/", true))
    }

    @Test
    fun `accepts IPv6 and base paths`() {
        assertEquals(
            "https://[fd7a:115c:a1e0::1]:8390/drive",
            RemoteAccessAddress.normalize("https://[fd7a:115c:a1e0::1]:8390/drive/", false)
        )
    }

    @Test
    fun `rejects credentials ambiguous paths and non HTTP URLs`() {
        listOf(
            "", "ftp://server", "https://user:password@server", "https://server?q=secret",
            "https://server#part", "https://server:0", "https://server:65536",
            "https://server/a/../b", "https://server/\\file", "https://server/%2e%2e/b", "not a host"
        ).forEach { value ->
            assertThrows(value, IllegalArgumentException::class.java) { RemoteAccessAddress.normalize(value, true) }
        }
    }
}
