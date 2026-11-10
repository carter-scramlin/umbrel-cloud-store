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
 public function files(): TemplateResponse {
  return new TemplateResponse('umbreldrive', 'files', [
   'uid' => $this->session->getUser()->getUID(),
   'displayName' => $this->session->getUser()->getDisplayName(),
   'owner' => $this->session->getUser()->getUID() === 'umbrel',
   'bridgeConnected' => in_array($this->config->getAppValue('umbreldrive', 'files_status', ''), ['connected', 'read-only'], true),
   'photosConnected' => $this->config->getAppValue('umbreldrive', 'photos_status', '') === 'read-only',
   'full' => rtrim($this->urls->linkToRoute('files.view.index'), '/'),
   'setup' => $this->urls->linkToRoute('umbreldrive.page.index'),
   'security' => $this->urls->linkToRoute('settings.PersonalSettings.index', ['section' => 'security']),
   'osHome' => (parse_url($this->urls->getAbsoluteURL('/'), PHP_URL_SCHEME) ?: 'https') . '://' . parse_url($this->urls->getAbsoluteURL('/'), PHP_URL_HOST),
   'uploadRoot' => $this->urls->getAbsoluteURL('/remote.php/dav/uploads/'),
   'davRoot' => $this->urls->getAbsoluteURL('/remote.php/dav/files/'),
   'ocs' => $this->urls->getAbsoluteURL('/ocs/v2.php/apps/files_sharing/api/v1/shares'),
   'fileLink' => $this->urls->getAbsoluteURL('/f/'),
   'logo' => $this->urls->imagePath('umbreldrive', 'logo.svg'),
   'css' => $this->urls->linkTo('umbreldrive', 'css/fast.css') . '?v=' . substr(hash_file('sha256', __DIR__ . '/../../css/fast.css'), 0, 12),
   'js' => $this->urls->linkTo('umbreldrive', 'js/fast.js') . '?v=' . substr(hash_file('sha256', __DIR__ . '/../../js/fast.js'), 0, 12),
  ], TemplateResponse::RENDER_AS_BLANK);
 }
 #[NoAdminRequired]
 #[NoCSRFRequired]
 public function index(): TemplateResponse {
  $origin = parse_url($this->urls->getAbsoluteURL('/'));
  $os = ($origin['scheme'] ?? 'https') . '://' . $origin['host'];
  return new TemplateResponse('umbreldrive', 'index', [
   'server' => $this->urls->getAbsoluteURL('/'),
   'umbrelHost' => $origin['host'],
   'files' => $this->urls->linkToRoute('umbreldrive.page.files'),
   'security' => $this->urls->linkToRoute('settings.PersonalSettings.index', ['section' => 'security']),
   'logo' => $this->urls->imagePath('umbreldrive', 'logo.svg'),
   'owner' => $this->session->getUser()?->getUID() === 'umbrel',
   'photosStatus' => $this->config->getAppValue('umbreldrive', 'photos_status', 'disconnected'),
   'photosFiles' => $this->urls->linkToRoute('umbreldrive.page.files', ['dir' => '/Umbrel Photos']),
   'bridgeStatus' => $this->config->getAppValue('umbreldrive', 'files_status', 'disconnected'),
   'osSettings' => $os . '/?dialog=app-settings&app=cartercloud-drive&view=storage',
   'osFiles' => $os . '/files',
   'bridgeFiles' => $this->urls->linkToRoute('umbreldrive.page.files', ['dir' => '/Umbrel Files']),
  ]);
 }
}
