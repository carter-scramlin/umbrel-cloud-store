/*
 * SPDX-FileCopyrightText: 2026 Carter Cloud
 * SPDX-License-Identifier: AGPL-3.0-or-later
 */
package com.owncloud.android.umbreldrive

import android.app.Activity
import android.content.ActivityNotFoundException
import android.content.Intent
import android.os.Bundle
import android.widget.CheckBox
import android.widget.EditText
import android.widget.RadioButton
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.edit
import androidx.core.net.toUri
import com.owncloud.android.R

class RemoteAccessActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.umbrel_remote_access)
        title = getString(R.string.umbrel_remote_title)
        val prefs = RemoteAccessPreferences.store(this)
        val local = findViewById<EditText>(R.id.umbrel_local_address)
        val tailnet = findViewById<EditText>(R.id.umbrel_tailnet_address)
        val remote = findViewById<RadioButton>(R.id.umbrel_use_tailnet)
        val http = findViewById<CheckBox>(R.id.umbrel_allow_http)
        val error = findViewById<TextView>(R.id.umbrel_remote_error)
        if (savedInstanceState == null) {
            local.setText(prefs.getString("local", RemoteAccessPreferences.LOCAL_DEFAULT))
            tailnet.setText(prefs.getString("tailnet", ""))
            remote.isChecked = prefs.getBoolean("remote", false)
            findViewById<RadioButton>(R.id.umbrel_use_local).isChecked = !remote.isChecked
            http.isChecked = prefs.getBoolean("http", false)
        }
        findViewById<android.view.View>(R.id.umbrel_open_tailscale).setOnClickListener {
            val launch = packageManager.getLaunchIntentForPackage("com.tailscale.ipn")
                ?: Intent(
                    Intent.ACTION_VIEW,
                    "https://play.google.com/store/apps/details?id=com.tailscale.ipn".toUri()
                )
            try {
                startActivity(launch)
            } catch (_: ActivityNotFoundException) {
                error.setText(R.string.umbrel_remote_no_browser)
            }
        }
        findViewById<android.view.View>(R.id.umbrel_save_remote).setOnClickListener {
            try {
                val localAddress = RemoteAccessAddress.normalize(local.text.toString(), http.isChecked)
                val tailnetAddress = tailnet.text.toString().trim().let {
                    if (it.isEmpty() && !remote.isChecked) "" else RemoteAccessAddress.normalize(it, http.isChecked)
                }
                prefs.edit {
                    putString("local", localAddress)
                    putString("tailnet", tailnetAddress)
                    putBoolean("remote", remote.isChecked)
                    putBoolean("http", http.isChecked)
                }
                setResult(
                    Activity.RESULT_OK,
                    Intent().putExtra(
                        RemoteAccessPreferences.ADDRESS_EXTRA,
                        if (remote.isChecked) tailnetAddress else localAddress
                    )
                )
                finish()
            } catch (_: IllegalArgumentException) {
                error.setText(R.string.umbrel_remote_invalid)
            }
        }
    }
}
