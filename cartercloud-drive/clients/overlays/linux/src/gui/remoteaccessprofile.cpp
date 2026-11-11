/*
 * SPDX-FileCopyrightText: 2026 Carter Cloud
 * SPDX-License-Identifier: GPL-2.0-or-later
 */
#include "remoteaccessprofile.h"
#include <QJsonDocument>
#include <QJsonObject>
#include <QUrl>

namespace OCC {
QString RemoteAccessProfile::normalizedAddress(const QString &input, bool allowHttp)
{
    auto value = input.trimmed();
    if (value.isEmpty()) {
        return {};
    }
    if (!value.contains(QStringLiteral("://"))) {
        value.prepend(QStringLiteral("https://"));
    }
    const QUrl url(value, QUrl::StrictMode);
    if (!url.isValid() || url.host().isEmpty() || url.authority().contains(QLatin1Char('@'))
        || url.hasQuery() || url.hasFragment() || url.port() == 0
        || (url.scheme() != QStringLiteral("https") && !(allowHttp && url.scheme() == QStringLiteral("http")))) {
        return {};
    }
    const auto segments = url.path().split(QLatin1Char('/'));
    if (segments.contains(QStringLiteral("..")) || segments.contains(QStringLiteral(".")) || url.path().contains(QLatin1Char('\\'))) {
        return {};
    }
    auto normalized = url.toString(QUrl::FullyEncoded);
    while (normalized.endsWith(QLatin1Char('/'))) {
        normalized.chop(1);
    }
    return normalized;
}

QString RemoteAccessProfile::selectedAddress() const
{
    return normalizedAddress(remote ? tailnet : local, allowHttp);
}

RemoteAccessProfile RemoteAccessProfile::load(QSettings &settings)
{
    RemoteAccessProfile result;
    result.local = settings.value(QStringLiteral("UmbrelRemote/local"), result.local).toString();
    result.tailnet = settings.value(QStringLiteral("UmbrelRemote/tailnet")).toString();
    result.remote = settings.value(QStringLiteral("UmbrelRemote/remote"), false).toBool();
    result.allowHttp = settings.value(QStringLiteral("UmbrelRemote/http"), false).toBool();
    return result;
}

bool RemoteAccessProfile::save(QSettings &settings) const
{
    const auto localAddress = normalizedAddress(local, allowHttp);
    const auto tailnetAddress = tailnet.trimmed().isEmpty() && !remote ? QString() : normalizedAddress(tailnet, allowHttp);
    if (localAddress.isEmpty() || (remote && tailnetAddress.isEmpty()) || (!tailnet.trimmed().isEmpty() && tailnetAddress.isEmpty())) {
        return false;
    }
    settings.setValue(QStringLiteral("UmbrelRemote/local"), localAddress);
    settings.setValue(QStringLiteral("UmbrelRemote/tailnet"), tailnetAddress);
    settings.setValue(QStringLiteral("UmbrelRemote/remote"), remote);
    settings.setValue(QStringLiteral("UmbrelRemote/http"), allowHttp);
    settings.sync();
    return settings.status() == QSettings::NoError;
}

QString RemoteAccessProfile::tailscaleState(const QByteArray &json, bool success)
{
    if (!success) {
        return {};
    }
    const auto doc = QJsonDocument::fromJson(json);
    if (!doc.isObject()) {
        return {};
    }
    const auto state = doc.object().value(QStringLiteral("BackendState")).toString();
    return QStringList{QStringLiteral("Running"), QStringLiteral("NeedsLogin"), QStringLiteral("Stopped")}.contains(state) ? state : QString();
}
}
