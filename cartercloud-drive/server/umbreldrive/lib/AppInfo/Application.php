<?php
// SPDX-License-Identifier: AGPL-3.0-or-later
namespace OCA\UmbrelDrive\AppInfo;
use OCP\AppFramework\App;
use OCP\AppFramework\Bootstrap\IBootstrap;
use OCP\AppFramework\Bootstrap\IBootContext;
use OCP\AppFramework\Bootstrap\IRegistrationContext;
use OCP\AppFramework\Http\Events\BeforeTemplateRenderedEvent;
use OCA\UmbrelDrive\Listener\ThemeListener;
class Application extends App implements IBootstrap {
 public function __construct(array $params = []) { parent::__construct('umbreldrive', $params); }
 public function register(IRegistrationContext $context): void {
  $context->registerEventListener(BeforeTemplateRenderedEvent::class, ThemeListener::class);
 }
 public function boot(IBootContext $context): void {}
}
