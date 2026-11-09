<?php
// SPDX-License-Identifier: AGPL-3.0-or-later
namespace OCA\UmbrelDrive\Listener;
use OCP\EventDispatcher\Event;
use OCP\EventDispatcher\IEventListener;
use OCP\AppFramework\Http\Events\BeforeTemplateRenderedEvent;
use OCP\Util;
class ThemeListener implements IEventListener {
 public function handle(Event $event): void {
  if ($event instanceof BeforeTemplateRenderedEvent) {
   Util::addStyle('umbreldrive', 'drive');
  }
 }
}
