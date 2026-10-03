/**
 * Unit tests for lib/events.ts — cross-component custom events.
 */
import {
  BADGE_CHECK_EVENT,
  PROGRESS_UPDATE_EVENT,
  triggerBadgeCheck,
  onBadgeCheck,
  triggerProgressUpdate,
  onProgressUpdate,
} from '@/lib/events';

describe('event name constants', () => {
  it('exposes stable event names', () => {
    expect(BADGE_CHECK_EVENT).toBe('badge:check');
    expect(PROGRESS_UPDATE_EVENT).toBe('progress:update');
  });
});

describe('badge check events', () => {
  it('invokes a registered listener when triggered', () => {
    const cb = jest.fn();
    const cleanup = onBadgeCheck(cb);
    triggerBadgeCheck();
    expect(cb).toHaveBeenCalledTimes(1);
    cleanup();
  });

  it('stops invoking the listener after cleanup', () => {
    const cb = jest.fn();
    const cleanup = onBadgeCheck(cb);
    cleanup();
    triggerBadgeCheck();
    expect(cb).not.toHaveBeenCalled();
  });

  it('supports multiple independent listeners', () => {
    const a = jest.fn();
    const b = jest.fn();
    const ca = onBadgeCheck(a);
    const cb = onBadgeCheck(b);
    triggerBadgeCheck();
    expect(a).toHaveBeenCalledTimes(1);
    expect(b).toHaveBeenCalledTimes(1);
    ca();
    cb();
  });
});

describe('progress update events', () => {
  it('invokes a registered listener when triggered', () => {
    const cb = jest.fn();
    const cleanup = onProgressUpdate(cb);
    triggerProgressUpdate();
    expect(cb).toHaveBeenCalledTimes(1);
    cleanup();
  });

  it('stops invoking the listener after cleanup', () => {
    const cb = jest.fn();
    const cleanup = onProgressUpdate(cb);
    cleanup();
    triggerProgressUpdate();
    expect(cb).not.toHaveBeenCalled();
  });

  it('badge and progress channels are independent', () => {
    const badgeCb = jest.fn();
    const progressCb = jest.fn();
    const c1 = onBadgeCheck(badgeCb);
    const c2 = onProgressUpdate(progressCb);
    triggerProgressUpdate();
    expect(progressCb).toHaveBeenCalledTimes(1);
    expect(badgeCb).not.toHaveBeenCalled();
    c1();
    c2();
  });
});
