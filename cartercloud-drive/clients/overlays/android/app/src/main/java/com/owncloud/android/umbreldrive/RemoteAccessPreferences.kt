/*
 * SPDX-FileCopyrightText: 2026 Carter Cloud
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */
package com.owncloud.android.umbreldrive

import android.content.Context

object RemoteAccessPreferences {
    const val ADDRESS_EXTRA = "umbrel_drive_address"
    const val LOCAL_DEFAULT = "https://umbrel.local:8390"

    @JvmStatic
    fun store(context: Context) = context.getSharedPreferences("umbrel_remote_access", Context.MODE_PRIVATE)

    @JvmStatic
    fun selectedAddress(context: Context): String {
        val prefs = store(context)
        val key = if (prefs.getBoolean("remote", false)) "tailnet" else "local"
        return prefs.getString(key, LOCAL_DEFAULT).orEmpty()
    }

    @JvmStatic
    fun allowsHttp(context: Context) = store(context).getBoolean("http", false)
}
