/*
 * SPDX-FileCopyrightText: 2026 Carter Cloud
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */
package com.owncloud.android.umbreldrive

import java.net.URI

object RemoteAccessAddress {
    private const val MAX_PORT = 65535

    @JvmStatic
    fun normalize(value: String, allowHttp: Boolean): String {
        val input = value.trim()
        require(input.isNotEmpty())
        val uri = URI.create(if (input.contains("://")) input else "https://$input")
        val scheme = uri.scheme?.lowercase()
        require(scheme == "https" || (scheme == "http" && allowHttp))
        require(!uri.host.isNullOrBlank() && uri.rawUserInfo == null)
        require(uri.rawQuery == null && uri.rawFragment == null)
        require(uri.port == -1 || uri.port in 1..MAX_PORT)
        require(!uri.rawPath.orEmpty().contains('\\'))
        require(uri.path.split('/').none { it == "." || it == ".." })
        return URI(scheme, null, uri.host, uri.port, uri.path.trimEnd('/'), null, null).toASCIIString()
    }
}
