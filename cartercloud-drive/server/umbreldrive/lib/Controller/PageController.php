<?php
// SPDX-License-Identifier: AGPL-3.0-or-later
namespace OCA\UmbrelDrive\Controller;
use OCP\AppFramework\Controller;
use OCP\AppFramework\Http\TemplateResponse;
use OCP\AppFramework\Http\JSONResponse;
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
   'connections' => $this->urls->linkToRoute('umbreldrive.page.connections'),
   'remoteSettings' => $this->urls->linkToRoute('umbreldrive.page.saveRemote'),
   'osSettings' => $this->osOrigin() . '/?dialog=app-settings&app=cartercloud-drive&view=storage',
   'osFiles' => $this->osOrigin() . '/files',
   'full' => rtrim($this->urls->linkToRoute('files.view.index'), '/'),
   'setup' => $this->urls->linkToRoute('umbreldrive.page.index'),
   'security' => $this->urls->linkToRoute('settings.PersonalSettings.index', ['section' => 'security']),
   'osHome' => $this->osOrigin(),
   'uploadRoot' => $this->urls->getAbsoluteURL('/remote.php/dav/uploads/'),
   'davRoot' => $this->urls->getAbsoluteURL('/remote.php/dav/files/'),
   'ocs' => $this->urls->getAbsoluteURL('/ocs/v2.php/apps/files_sharing/api/v1/shares'),
   'fileLink' => $this->urls->getAbsoluteURL('/f/'),
   'logo' => $this->urls->imagePath('umbreldrive', 'logo.svg'),
   'css' => $this->urls->linkTo('umbreldrive', 'css/fast.css') . '?v=' . substr(hash_file('sha256', __DIR__ . '/../../css/fast.css'), 0, 12),
   'js' => $this->urls->linkTo('umbreldrive', 'js/fast.js') . '?v=' . substr(hash_file('sha256', __DIR__ . '/../../js/fast.js'), 0, 12),
  ], TemplateResponse::RENDER_AS_BLANK);
 }
 private function osOrigin(): string {
  $origin = parse_url($this->urls->getAbsoluteURL('/'));
  $host = $origin['host'];
  if (str_contains($host, ':') && !str_starts_with($host, '[')) { $host = '[' . $host . ']'; }
  return ($origin['scheme'] ?? 'https') . '://' . $host;
 }
 #[NoAdminRequired]
 #[NoCSRFRequired]
 public function connections(): JSONResponse {
  $owner = $this->session->getUser()?->getUID() === 'umbrel';
  $libraries = [];
  if ($owner) {
   foreach (['files', 'photos'] as $prefix) {
    $status = $this->config->getAppValue('umbreldrive', $prefix . '_status', 'disconnected');
    $libraries[$prefix] = in_array($status, ['connected', 'read-only', 'name-conflict', 'owner-missing'], true) ? $status : 'disconnected';
   }
  }
  $response = new JSONResponse(['owner' => $owner, 'libraries' => $libraries,
   'remoteAddress' => $owner ? $this->config->getAppValue('umbreldrive', 'remote_address', '') : '']);
  $response->addHeader('Cache-Control', 'no-store');
  return $response;
 }
 #[NoAdminRequired]
 public function saveRemote(string $address): JSONResponse {
  if ($this->session->getUser()?->getUID() !== 'umbrel') { return new JSONResponse(['error' => 'Owner account required'], 403); }
  $address = trim($address);
  $parts = parse_url($address);
  $host = strtolower(trim($parts['host'] ?? '', '[]'));
  $scheme = strtolower($parts['scheme'] ?? '');
  $packed = @inet_pton($host);
  $tailnet = (filter_var($host, FILTER_VALIDATE_DOMAIN, FILTER_FLAG_HOSTNAME) && str_ends_with($host, '.ts.net'))
   || ($packed !== false && strlen($packed) === 4 && ord($packed[0]) === 100 && (ord($packed[1]) & 192) === 64)
   || ($packed !== false && strlen($packed) === 16 && bin2hex(substr($packed, 0, 6)) === 'fd7a115ca1e0');
  if ($address !== '' && (!$parts || !$tailnet || !in_array($scheme, ['http', 'https'], true)
   || isset($parts['user']) || isset($parts['pass']) || isset($parts['query']) || isset($parts['fragment'])
   || !in_array($parts['path'] ?? '', ['', '/'], true) || ($parts['port'] ?? 1) < 1)) {
   return new JSONResponse(['error' => 'Use an HTTP or HTTPS Tailscale IP or full .ts.net address, with the Drive port and no path or credentials.'], 400);
  }
  $hostPart = str_contains($host, ':') ? '[' . $host . ']' : $host;
  $normalized = $address === '' ? '' : $scheme . '://' . $hostPart . (isset($parts['port']) ? ':' . $parts['port'] : '');
  try {
   $domains = $this->config->getSystemValue('trusted_domains', []);
   $previous = $this->config->getAppValue('umbreldrive', 'remote_managed_host', '');
   if ($previous !== '' && $previous !== $hostPart) { $domains = array_values(array_filter($domains, fn($domain) => $domain !== $previous)); }
   $managed = $previous === $hostPart;
   if ($hostPart !== '' && !in_array($hostPart, $domains, true)) { $domains[] = $hostPart; $managed = true; }
   $this->config->setSystemValue('trusted_domains', $domains);
   $this->config->setAppValue('umbreldrive', 'remote_managed_host', $managed ? $hostPart : '');
   $this->config->setAppValue('umbreldrive', 'remote_address', $normalized);
  } catch (\Throwable $error) { return new JSONResponse(['error' => 'Could not save the remote address. Check server configuration permissions.'], 500); }
  $response = new JSONResponse(['address' => $normalized]);
  $response->addHeader('Cache-Control', 'no-store');
  return $response;
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
   'osTailscale' => $os . '/app-store/tailscale',
   'httpServer' => 'http://' . $origin['host'] . ':8391/',
   'bridgeFiles' => $this->urls->linkToRoute('umbreldrive.page.files', ['dir' => '/Umbrel Files']),
  ]);
 }
}
