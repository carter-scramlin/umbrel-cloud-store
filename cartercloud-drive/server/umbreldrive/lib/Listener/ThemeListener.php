<?php
// SPDX-License-Identifier: AGPL-3.0-or-later
namespace OCA\UmbrelDrive\Listener;
use OCP\EventDispatcher\Event;
use OCP\EventDispatcher\IEventListener;
use OCP\AppFramework\Http\Events\BeforeTemplateRenderedEvent;
use OCP\Util;
use OCP\IRequest;
class ThemeListener implements IEventListener {
 public function __construct(private IRequest $request) {}
 public function handle(Event $event): void {
  if ($event instanceof BeforeTemplateRenderedEvent) {
   Util::addStyle('umbreldrive', 'drive');
   if ($this->request->getParam('drivePerf') === '1') {
    Util::addScript('umbreldrive', 'performance-probe');
   }
  }
 }
}
