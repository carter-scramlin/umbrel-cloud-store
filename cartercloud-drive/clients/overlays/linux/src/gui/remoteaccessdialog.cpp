/*
 * SPDX-FileCopyrightText: 2026 Carter Cloud
 * SPDX-License-Identifier: GPL-2.0-or-later
 */
#include "remoteaccessdialog.h"
#include "remoteaccessprofile.h"
#include <QCheckBox>
#include <QComboBox>
#include <QDesktopServices>
#include <QDialogButtonBox>
#include <QFormLayout>
#include <QLabel>
#include <QLineEdit>
#include <QProcess>
#include <QPushButton>
#include <QTimer>
#include <QUrl>
#include <QVBoxLayout>

namespace OCC {
RemoteAccessDialog::RemoteAccessDialog(QWidget *parent) : QDialog(parent)
{
    setWindowTitle(tr("Remote access"));
    setMinimumWidth(520);
    auto *layout = new QVBoxLayout(this);
    layout->setContentsMargins(24, 24, 24, 24);
    layout->setSpacing(12);
    auto note = [layout](const QString &text) {
        auto *label = new QLabel(text);
        label->setWordWrap(true);
        layout->addWidget(label);
        return label;
    };
    auto *title = note(tr("Remote access"));
    auto titleFont = title->font();
    titleFont.setPointSize(titleFont.pointSize() + 6);
    titleFont.setBold(true);
    title->setFont(titleFont);
    note(tr("Connect this computer and your Umbrel to the same Tailscale network. Enter your Umbrel's full MagicDNS name or Tailscale IP and Drive port. Tailscale must be connected on both devices."));
    QSettings settings;
    const auto profile = RemoteAccessProfile::load(settings);
    auto *form = new QFormLayout;
    _local = new QLineEdit(profile.local, this);
    _local->setObjectName(QStringLiteral("umbrelLocalAddress"));
    _tailnet = new QLineEdit(profile.tailnet, this);
    _tailnet->setObjectName(QStringLiteral("umbrelTailnetAddress"));
    _tailnet->setPlaceholderText(QStringLiteral("https://umbrel.tail123.ts.net:8390"));
    _mode = new QComboBox(this);
    _mode->setObjectName(QStringLiteral("umbrelConnectionMode"));
    _mode->addItems({tr("Local address"), tr("Tailscale address")});
    _mode->setCurrentIndex(profile.remote ? 1 : 0);
    form->addRow(tr("Local address"), _local);
    form->addRow(tr("Tailscale address"), _tailnet);
    form->addRow(tr("Use for new sign-ins"), _mode);
    layout->addLayout(form);
    _http = new QCheckBox(tr("Allow HTTP addresses"), this);
    _http->setObjectName(QStringLiteral("umbrelAllowHttp"));
    _http->setChecked(profile.allowHttp);
    layout->addWidget(_http);
    note(tr("HTTP has no TLS encryption. Use it only over a trusted connection, such as Tailscale. HTTPS stays the default and certificate verification stays enabled."));
    note(tr("These settings apply to new sign-ins. Existing sync accounts keep their address. Sign in with the Tailscale address for sync at home and away. Never configure two accounts to sync the same local folder."));
    auto *install = new QPushButton(tr("Set up Tailscale"), this);
    layout->addWidget(install);
    connect(install, &QPushButton::clicked, this, [] { QDesktopServices::openUrl(QUrl(QStringLiteral("https://tailscale.com/download/linux"))); });
    auto *check = new QPushButton(tr("Check Tailscale on this computer"), this);
    layout->addWidget(check);
    auto *status = note(tr("Tailscale connection has not been checked."));
    connect(check, &QPushButton::clicked, this, [this, check, status] {
        check->setEnabled(false);
        auto *process = new QProcess(this);
        auto *timer = new QTimer(process);
        timer->setSingleShot(true);
        connect(timer, &QTimer::timeout, process, &QProcess::kill);
        connect(process, &QProcess::errorOccurred, this, [check, status, process](QProcess::ProcessError error) {
            if (error == QProcess::FailedToStart) {
                status->setText(tr("Tailscale CLI is unavailable. Install Tailscale, then connect it to your network."));
                check->setEnabled(true);
                process->deleteLater();
            }
        });
        connect(process, qOverload<int, QProcess::ExitStatus>(&QProcess::finished), this, [check, status, process](int code, QProcess::ExitStatus exit) {
            const auto state = RemoteAccessProfile::tailscaleState(process->readAllStandardOutput(), code == 0 && exit == QProcess::NormalExit);
            status->setText(state == QStringLiteral("Running") ? tr("Tailscale is connected on this computer. Your Umbrel must also be connected and permitted by your tailnet policy.")
                : state == QStringLiteral("NeedsLogin") ? tr("Tailscale needs sign-in. Open Tailscale to connect.")
                : state == QStringLiteral("Stopped") ? tr("Tailscale is disconnected. Connect it before using the remote address.")
                : tr("Could not read Tailscale status. Check the Tailscale app or service."));
            check->setEnabled(true);
            process->deleteLater();
        });
        process->start(QStringLiteral("tailscale"), {QStringLiteral("status"), QStringLiteral("--json")});
        timer->start(5000);
    });
    _error = note(QString());
    _error->setObjectName(QStringLiteral("umbrelRemoteError"));
    auto *buttons = new QDialogButtonBox(QDialogButtonBox::Save | QDialogButtonBox::Cancel, this);
    layout->addWidget(buttons);
    connect(buttons, &QDialogButtonBox::rejected, this, &QDialog::reject);
    connect(buttons, &QDialogButtonBox::accepted, this, [this] {
        RemoteAccessProfile updated;
        updated.local = _local->text();
        updated.tailnet = _tailnet->text();
        updated.remote = _mode->currentIndex() == 1;
        updated.allowHttp = _http->isChecked();
        QSettings settings;
        if (!updated.save(settings)) {
            _error->setText(tr("Enter a valid HTTP or HTTPS address without passwords, query strings or fragments. Enable HTTP explicitly to use it. Check that settings can be saved."));
            return;
        }
        accept();
    });
}

QString RemoteAccessDialog::selectedAddress() const
{
    return RemoteAccessProfile::normalizedAddress(_mode->currentIndex() == 1 ? _tailnet->text() : _local->text(), _http->isChecked());
}
}
