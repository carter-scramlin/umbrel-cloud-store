<?php
// SPDX-License-Identifier: AGPL-3.0-or-later
namespace OCA\UmbrelDrive\Controller;
use OCP\AppFramework\Controller;
use OCP\AppFramework\Http\TemplateResponse;
use OCP\AppFramework\Http\Attribute\NoAdminRequired;
use OCP\AppFramework\Http\Attribute\NoCSRFRequired;
use OCP\IRequest;
use OCP\IURLGenerator;
class PageController extends Controller {
 public function __construct(string $appName, IRequest $request, private IURLGenerator $urls) {
  parent::__construct($appName, $request);
 }
 #[NoAdminRequired]
 #[NoCSRFRequired]
 public function index(): TemplateResponse {
  return new TemplateResponse('umbreldrive', 'index', [
   'server' => $this->urls->getAbsoluteURL('/'),
   'files' => $this->urls->linkToRoute('files.view.index'),
   'security' => $this->urls->linkToRoute('settings.PersonalSettings.index', ['section' => 'security']),
   'logo' => $this->urls->imagePath('umbreldrive', 'logo.svg'),
  ]);
 }
}
