/*
 * SPDX-FileCopyrightText: 2026 Carter Cloud
 * SPDX-License-Identifier: GPL-2.0-or-later
 */
#pragma once
#include <QDialog>
class QLineEdit;
class QCheckBox;
class QComboBox;
class QLabel;
namespace OCC {
class RemoteAccessDialog : public QDialog
{
public:
    explicit RemoteAccessDialog(QWidget *parent = nullptr);
    [[nodiscard]] QString selectedAddress() const;
private:
    QLineEdit *_local;
    QLineEdit *_tailnet;
    QComboBox *_mode;
    QCheckBox *_http;
    QLabel *_error;
};
}
