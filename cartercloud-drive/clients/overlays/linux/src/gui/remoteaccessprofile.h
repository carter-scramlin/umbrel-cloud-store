/*
 * SPDX-FileCopyrightText: 2026 Carter Cloud
 * SPDX-License-Identifier: GPL-2.0-or-later
 */
#pragma once
#include <QString>
#include <QSettings>

namespace OCC {
class RemoteAccessProfile
{
public:
    QString local = QStringLiteral("https://umbrel.local:8390");
    QString tailnet;
    bool remote = false;
    bool allowHttp = false;
    [[nodiscard]] static QString normalizedAddress(const QString &input, bool allowHttp);
    [[nodiscard]] static QString tailscaleState(const QByteArray &json, bool success);
    [[nodiscard]] QString selectedAddress() const;
    [[nodiscard]] static RemoteAccessProfile load(QSettings &settings);
    [[nodiscard]] bool save(QSettings &settings) const;
};
}
