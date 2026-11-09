<?php
// SPDX-License-Identifier: AGPL-3.0-or-later
namespace OCA\UmbrelDrive\Controller;
use OCP\AppFramework\Controller;
use OCP\AppFramework\Http\TemplateResponse;
use OCP\AppFramework\Http\Attribute\NoAdminRequired;
use OCP\AppFramework\Http\Attribute\NoCSRFRequired;
use OCP\IRequest;
use OCP\IURLGenerator;
use OCP\IConfig;
use OCP\IUserSession;
class PageController extends Controller {
 public function __construct(string $appName, IRequest $request, private IURLGenerator $urls, private IConfig $config, private IUserSession $session) {
  parent::__construct($appName, $request);
 }
 #[NoAdminRequired]
 #[NoCSRFRequired]
 public function index(): TemplateResponse {
  $origin = parse_url($this->urls->getAbsoluteURL('/'));
  $os = ($origin['scheme'] ?? 'https') . '://' . $origin['host'];
  return new TemplateResponse('umbreldrive', 'index', [
   'server' => $this->urls->getAbsoluteURL('/'),
   'umbrelHost' => $origin['host'],
   'files' => $this->urls->linkToRoute('files.view.index'),
   'security' => $this->urls->linkToRoute('settings.PersonalSettings.index', ['section' => 'security']),
   'logo' => $this->urls->imagePath('umbreldrive', 'logo.svg'),
   'owner' => $this->session->getUser()?->getUID() === 'umbrel',
   'bridgeStatus' => $this->config->getAppValue('umbreldrive', 'files_status', 'disconnected'),
   'osSettings' => $os . '/?dialog=app-settings&app=cartercloud-drive&view=storage',
   'osFiles' => $os . '/files',
   'bridgeFiles' => $this->urls->linkToRoute('files.view.index', ['dir' => '/Umbrel Files']),
  ]);
 }
}
