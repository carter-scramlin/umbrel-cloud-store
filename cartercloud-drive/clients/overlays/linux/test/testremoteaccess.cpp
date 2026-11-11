/*
 * SPDX-FileCopyrightText: 2026 Carter Cloud
 * SPDX-License-Identifier: GPL-2.0-or-later
 */
#include "gui/remoteaccessprofile.h"
#include "gui/remoteaccessdialog.h"
#include <QCheckBox>
#include <QComboBox>
#include <QDialogButtonBox>
#include <QLineEdit>
#include <QPushButton>
#include <QSettings>
#include <QTemporaryDir>
#include <QtTest>

using namespace OCC;
class TestRemoteAccess : public QObject
{
    Q_OBJECT
    QTemporaryDir _settings;
private Q_SLOTS:
    void initTestCase()
    {
        QCoreApplication::setOrganizationName(QStringLiteral("UmbrelDriveTests"));
        QCoreApplication::setApplicationName(QStringLiteral("RemoteAccess"));
        QSettings::setDefaultFormat(QSettings::IniFormat);
        QSettings::setPath(QSettings::IniFormat, QSettings::UserScope, _settings.path());
    }
    void init()
    {
        QSettings settings;
        settings.clear();
    }
    void addressValidation()
    {
        QCOMPARE(RemoteAccessProfile::normalizedAddress(QStringLiteral("umbrel.tail123.ts.net:8390/"), false), QStringLiteral("https://umbrel.tail123.ts.net:8390"));
        QCOMPARE(RemoteAccessProfile::normalizedAddress(QStringLiteral("https://[fd7a:115c:a1e0::1]:8390/drive/"), false), QStringLiteral("https://[fd7a:115c:a1e0::1]:8390/drive"));
        QVERIFY(RemoteAccessProfile::normalizedAddress(QStringLiteral("http://100.88.1.2:8391"), false).isEmpty());
        QCOMPARE(RemoteAccessProfile::normalizedAddress(QStringLiteral("http://100.88.1.2:8391/"), true), QStringLiteral("http://100.88.1.2:8391"));
        for (const auto &invalid : {"", "ftp://server", "https://user:password@host", "https://host?secret", "https://host#part", "https://host:0", "https://host:65536", "https://host/a/../b", "https://host/%2e%2e/b", "https://host/\\file"}) {
            QVERIFY2(RemoteAccessProfile::normalizedAddress(QString::fromUtf8(invalid), true).isEmpty(), invalid);
        }
    }
    void preferencesDoNotSaveInvalidAddresses()
    {
        QSettings settings;
        RemoteAccessProfile profile;
        QVERIFY(profile.save(settings));
        profile.remote = true;
        QVERIFY(!profile.save(settings));
        QVERIFY(!RemoteAccessProfile::load(settings).remote);
        profile.tailnet = QStringLiteral("https://umbrel.tail123.ts.net:8390");
        QVERIFY(profile.save(settings));
        QCOMPARE(RemoteAccessProfile::load(settings).selectedAddress(), profile.tailnet);
        profile.tailnet = QStringLiteral("http://100.88.1.2:8391");
        QVERIFY(!profile.save(settings));
        profile.allowHttp = true;
        QVERIFY(profile.save(settings));
        QCOMPARE(RemoteAccessProfile::load(settings).selectedAddress(), profile.tailnet);
    }
    void dialogRejectsHttpUntilExplicitlyEnabledAndReopensSavedChoice()
    {
        RemoteAccessDialog dialog;
        dialog.findChild<QLineEdit *>(QStringLiteral("umbrelTailnetAddress"))->setText(QStringLiteral("http://100.88.1.2:8391"));
        dialog.findChild<QComboBox *>(QStringLiteral("umbrelConnectionMode"))->setCurrentIndex(1);
        auto *save = dialog.findChild<QDialogButtonBox *>()->button(QDialogButtonBox::Save);
        save->click();
        QVERIFY(dialog.result() != QDialog::Accepted);
        dialog.findChild<QCheckBox *>(QStringLiteral("umbrelAllowHttp"))->setChecked(true);
        save->click();
        QCOMPARE(dialog.result(), int(QDialog::Accepted));
        RemoteAccessDialog reopened;
        QCOMPARE(reopened.selectedAddress(), QStringLiteral("http://100.88.1.2:8391"));
    }
    void renderDialog()
    {
        const auto capture = qEnvironmentVariable("UMBREL_REMOTE_CAPTURE");
        if (capture.isEmpty()) {
            return;
        }
        RemoteAccessDialog dialog;
        dialog.findChild<QLineEdit *>(QStringLiteral("umbrelTailnetAddress"))->setText(QStringLiteral("https://umbrel.tail123.ts.net:8390"));
        dialog.findChild<QComboBox *>(QStringLiteral("umbrelConnectionMode"))->setCurrentIndex(1);
        dialog.show();
        QCoreApplication::processEvents();
        QVERIFY(dialog.grab().save(capture));
    }
    void tailscaleStatus()
    {
        QCOMPARE(RemoteAccessProfile::tailscaleState(R"({"BackendState":"Running"})", true), QStringLiteral("Running"));
        QCOMPARE(RemoteAccessProfile::tailscaleState(R"({"BackendState":"NeedsLogin"})", true), QStringLiteral("NeedsLogin"));
        QCOMPARE(RemoteAccessProfile::tailscaleState(R"({"BackendState":"Stopped"})", true), QStringLiteral("Stopped"));
        QVERIFY(RemoteAccessProfile::tailscaleState("invalid", true).isEmpty());
        QVERIFY(RemoteAccessProfile::tailscaleState(R"({"BackendState":"Running"})", false).isEmpty());
        QVERIFY(RemoteAccessProfile::tailscaleState(R"({"BackendState":"future"})", true).isEmpty());
    }
};
QTEST_MAIN(TestRemoteAccess)
#include "testremoteaccess.moc"
