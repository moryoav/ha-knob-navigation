/** Exercise the shipped frontend through input events, timers, and navigation. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const source = fs.readFileSync(path.join(__dirname,
  "../../custom_components/knob_swipe_navigation/www/knob-swipe-navigation.js"), "utf8");

/** Model event registration so lifecycle leaks and listener options are visible. */
class EventTargetStub {
  listeners = new Map();

  /** Register an event listener using the browser's callback/capture identity. */
  addEventListener(type, callback, options = {}) {
    const capture = typeof options === "boolean" ? options : !!options.capture;
    const entries = this.listeners.get(type) || [];
    if (!entries.some((item) => item.callback === callback && item.capture === capture)) {
      entries.push({ callback, capture, passive: !!options.passive });
    }
    this.listeners.set(type, entries);
  }

  /** Remove the listener with the matching callback and capture flag. */
  removeEventListener(type, callback, options = {}) {
    const capture = typeof options === "boolean" ? options : !!options.capture;
    this.listeners.set(type, (this.listeners.get(type) || [])
      .filter((item) => item.callback !== callback || item.capture !== capture));
  }

  /** Deliver an event without emulating any integration-specific behavior. */
  dispatchEvent(event) {
    for (const { callback } of [...(this.listeners.get(event.type) || [])]) {
      callback(event);
    }
  }
}

/** Create an isolated browser with a deterministic clock and a minimal HA host. */
async function createBrowser(overrides = {}, extraEntries = [], animated = false) {
  let now = 1_000_000;
  let nextTimer = 0;
  let rotationCallback;
  let unsubscribed = 0;
  const timers = new Map();
  const results = [];
  const navigations = [];
  const window = new EventTargetStub();
  const document = new EventTargetStub();
  const location = new URL("https://ha.example/dashboard-home/car?kiosk");
  const entry = {
    entry_id: "entrance", device_id: "knob-1", dashboard_path: "dashboard-home",
    navigation_enabled: true, overlay_enabled: false, cooldown_ms: 0,
    idle_return_enabled: true, idle_return_timeout_seconds: 60,
    ...overrides,
  };
  const config = { entries: [entry, ...extraEntries] };
  const hass = {
    states: {},
    connection: {
      subscribeMessage: async (callback) => {
        rotationCallback = callback;
        return () => { unsubscribed += 1; };
      },
    },
    callWS: async (message) => {
      if (message.type.endsWith("/config")) return config;
      results.push(message);
      return {};
    },
  };
  const view = { style: {} };
  const root = { lovelace: { config: { views: [
    { path: "default_view", title: "Home" }, { path: "car", title: "Car" },
    { path: "routines", title: "Routines" },
  ] } }, shadowRoot: {
    querySelector: (selector) => animated && selector === '[id="view"]' ? view : null,
  } };
  const chain = { querySelector: (selector) => selector === "hui-root" ? root : chain };
  chain.shadowRoot = chain;
  const host = { hass, shadowRoot: chain };
  document.querySelector = (selector) => selector === "home-assistant" ? host : null;
  document.hidden = false;
  window.setTimeout = (callback, delay) => {
    const id = ++nextTimer;
    timers.set(id, { callback, at: now + delay, interval: 0 });
    return id;
  };
  window.setInterval = (callback, delay) => {
    const id = window.setTimeout(callback, delay);
    timers.get(id).interval = delay;
    return id;
  };
  window.clearTimeout = window.clearInterval = (id) => timers.delete(id);
  const context = vm.createContext({
    window, document, location, URL, URLSearchParams, console, screen: { width: 1280, height: 900 },
    Date: class extends Date { static now() { return now; } },
    CustomEvent: class { constructor(type) { this.type = type; this.isTrusted = false; } },
    history: {
      pushState: (_state, _title, target) => {
        location.href = new URL(target, location).href;
        navigations.push(location.pathname);
      },
    },
  });
  vm.runInContext(source, context);
  await new Promise(setImmediate);

  return {
    window, document, location, hass, entry, results, navigations, timers,
    /** Advance all browser timers, including promise work scheduled by callbacks. */
    async advance(milliseconds) {
      const end = now + milliseconds;
      for (;;) {
        const next = [...timers.entries()].filter(([, timer]) => timer.at <= end)
          .sort((a, b) => a[1].at - b[1].at || a[0] - b[0])[0];
        if (!next) break;
        const [id, timer] = next;
        now = timer.at;
        if (timer.interval) timer.at += timer.interval;
        else timers.delete(id);
        timer.callback();
        await new Promise(setImmediate);
      }
      now = end;
    },
    /** Dispatch input with trusted events as the default for human interaction. */
    input(type, details = {}) {
      const event = { type, isTrusted: true, pointerId: 1, touches: [], ...details };
      window.dispatchEvent(event);
      return event;
    },
    /** Deliver a real backend rotation subscription payload to the module. */
    async rotate(direction = "next") {
      await rotationCallback({ entry_id: "entrance", direction });
    },
    /** Re-execute the module as a browser would when a new version loads. */
    async reload() {
      const upgrade = source.replace(/^const KNOB_SWIPE_NAV_VERSION = "[^"]+";/m,
        'const KNOB_SWIPE_NAV_VERSION = "test-upgrade";');
      vm.runInContext(upgrade, vm.createContext({ ...context }));
      await new Promise(setImmediate);
    },
    /** Return the number of subscriptions that have been cleaned up. */
    unsubscribeCount() { return unsubscribed; },
  };
}

test("idle dashboard returns at the configured deadline", async () => {
  const browser = await createBrowser();
  await browser.advance(59_999);
  assert.equal(browser.location.pathname, "/dashboard-home/car");
  await browser.advance(1);
  assert.equal(browser.location.pathname, "/dashboard-home/default_view");
  assert.equal(browser.results[0].result, "returned_idle");
  assert.equal(browser.results[0].reason, "idle_timeout");
});

for (const type of ["click", "pointermove", "wheel", "keydown", "keyup", "input"]) {
  test(`${type} restarts the full inactivity delay`, async () => {
    const browser = await createBrowser();
    await browser.advance(55_000);
    browser.input(type);
    await browser.advance(59_999);
    assert.equal(browser.navigations.length, 0);
    await browser.advance(1);
    assert.equal(browser.location.pathname, "/dashboard-home/default_view");
  });
}

test("held mouse drag pauses return until release", async () => {
  const browser = await createBrowser();
  await browser.advance(55_000);
  browser.input("pointerdown");
  await browser.advance(120_000);
  assert.equal(browser.navigations.length, 0);
  browser.input("pointermove");
  browser.input("pointerup");
  await browser.advance(59_999);
  assert.equal(browser.navigations.length, 0);
  await browser.advance(1);
  assert.equal(browser.navigations.length, 1);
});

test("touch scrolling stays active after the browser cancels pointer events", async () => {
  const browser = await createBrowser();
  browser.input("pointerdown");
  browser.input("touchstart", { touches: [{ identifier: 1 }] });
  browser.input("pointercancel");
  browser.input("touchmove", { touches: [{ identifier: 1 }] });
  await browser.advance(120_000);
  assert.equal(browser.navigations.length, 0);
  browser.input("touchend");
  await browser.advance(59_999);
  assert.equal(browser.navigations.length, 0);
  await browser.advance(1);
  assert.equal(browser.navigations.length, 1);
});

test("all fingers must be released before the idle countdown starts", async () => {
  const browser = await createBrowser();
  browser.input("pointerdown", { pointerId: 1 });
  browser.input("pointerdown", { pointerId: 2 });
  browser.input("pointerup", { pointerId: 1 });
  await browser.advance(120_000);
  assert.equal(browser.navigations.length, 0);
  browser.input("pointerup", { pointerId: 2 });
  await browser.advance(60_000);
  assert.equal(browser.navigations.length, 1);
});

for (const end of ["pointercancel", "touchcancel", "blur", "pagehide", "hidden"]) {
  test(`${end} releases held input so idle return can recover`, async () => {
    const browser = await createBrowser();
    const touch = end === "touchcancel";
    browser.input(touch ? "touchstart" : "pointerdown", { touches: [{ identifier: 1 }] });
    await browser.advance(120_000);
    assert.equal(browser.navigations.length, 0);
    if (end === "hidden") {
      browser.document.hidden = true;
      browser.document.dispatchEvent({ type: "visibilitychange" });
    } else browser.input(end);
    await browser.advance(60_000);
    assert.equal(browser.navigations.length, 1);
  });
}

test("programmatic tab changes and synthetic input do not postpone idle return", async () => {
  const browser = await createBrowser();
  await browser.advance(55_000);
  for (const type of ["pointerdown", "touchstart", "click", "wheel", "input"]) {
    browser.input(type, { isTrusted: false, touches: [{ identifier: 1 }] });
  }
  browser.location.pathname = "/dashboard-home/routines";
  browser.input("location-changed", { isTrusted: false });
  browser.hass.states["sensor.temperature"] = { state: "23" };
  await browser.advance(5_000);
  assert.equal(browser.location.pathname, "/dashboard-home/default_view");
});

test("manual tab change receives a full delay from its click", async () => {
  const browser = await createBrowser();
  await browser.advance(59_000);
  browser.input("pointerdown");
  browser.input("pointerup");
  browser.input("click");
  browser.location.pathname = "/dashboard-home/routines";
  browser.input("location-changed", { isTrusted: false });
  await browser.advance(59_999);
  assert.equal(browser.navigations.length, 0);
  await browser.advance(1);
  assert.equal(browser.location.pathname, "/dashboard-home/default_view");
});

test("knob rotation still navigates and resets the full delay", async () => {
  const browser = await createBrowser();
  await browser.advance(55_000);
  await browser.rotate();
  await browser.advance(32);
  assert.equal(browser.location.pathname, "/dashboard-home/routines");
  await browser.advance(59_967);
  assert.equal(browser.navigations.length, 1);
  await browser.advance(1);
  assert.equal(browser.location.pathname, "/dashboard-home/default_view");
});

test("another browser's activity does not postpone this browser's return", async () => {
  const tablet = await createBrowser();
  const phone = await createBrowser();
  await tablet.advance(55_000);
  await phone.advance(55_000);
  phone.input("click");
  await tablet.advance(5_000);
  await phone.advance(5_000);
  assert.equal(tablet.navigations.length, 1);
  assert.equal(phone.navigations.length, 0);
});

test("closely spaced activity still gets a full inactivity delay", async () => {
  const browser = await createBrowser();
  await browser.advance(100);
  browser.input("click");
  await browser.advance(59_999);
  assert.equal(browser.navigations.length, 0);
  await browser.advance(1);
  assert.equal(browser.navigations.length, 1);
});

test("manual tab selection cancels verification of an earlier idle return", async () => {
  const browser = await createBrowser();
  await browser.advance(60_000);
  assert.equal(browser.location.pathname, "/dashboard-home/default_view");
  browser.input("click");
  browser.location.pathname = "/dashboard-home/routines";
  browser.input("location-changed", { isTrusted: false });
  await browser.advance(700);
  assert.equal(browser.location.pathname, "/dashboard-home/routines");
  await browser.advance(59_299);
  assert.equal(browser.location.pathname, "/dashboard-home/routines");
  await browser.advance(1);
  assert.equal(browser.location.pathname, "/dashboard-home/default_view");
});

test("interaction during an idle animation cancels its pending navigation", async () => {
  const browser = await createBrowser({}, [], true);
  await browser.advance(60_000);
  browser.input("click");
  await browser.advance(59_999);
  assert.equal(browser.navigations.length, 0);
  await browser.advance(231);
  assert.equal(browser.location.pathname, "/dashboard-home/default_view");
  assert.equal(browser.navigations.length, 1);
});

test("disabling idle return cancels an already pending animation", async () => {
  const browser = await createBrowser({}, [], true);
  await browser.advance(60_000);
  browser.entry.idle_return_enabled = false;
  await browser.advance(60_000);
  assert.equal(browser.navigations.length, 0);
});

for (const [type, details] of [
  ["pointerout", { relatedTarget: null, pointerType: "mouse" }],
  ["pointermove", { buttons: 0, pointerType: "mouse" }],
]) {
  test(`${type} recovers a mouse released outside the viewport`, async () => {
    const browser = await createBrowser();
    browser.input("pointerdown");
    await browser.advance(120_000);
    assert.equal(browser.navigations.length, 0);
    browser.input(type, details);
    await browser.advance(59_999);
    assert.equal(browser.navigations.length, 0);
    await browser.advance(1);
    assert.equal(browser.navigations.length, 1);
  });
}

test("moving between dashboard elements does not release a held pointer", async () => {
  const browser = await createBrowser();
  browser.input("pointerdown");
  browser.input("pointerout", { relatedTarget: {}, pointerType: "mouse" });
  await browser.advance(120_000);
  assert.equal(browser.navigations.length, 0);
  browser.input("pointerup");
  await browser.advance(60_000);
  assert.equal(browser.navigations.length, 1);
});

test("activity resets entries when the required query parameter matches", async () => {
  const browser = await createBrowser({ require_query_param: "kiosk" });
  await browser.advance(55_000);
  browser.input("click");
  await browser.advance(59_999);
  assert.equal(browser.navigations.length, 0);
  await browser.advance(1);
  assert.equal(browser.navigations.length, 1);
});

for (const overrides of [
  { navigation_enabled: false }, { idle_return_enabled: false },
  { dashboard_path: "dashboard-kitchen" }, { require_query_param: "tablet" },
]) {
  test(`disabled or unmatched entry stays inactive: ${JSON.stringify(overrides)}`, async () => {
    const browser = await createBrowser(overrides);
    browser.input("click");
    await browser.advance(120_000);
    assert.equal(browser.navigations.length, 0);
    assert.equal(browser.results.length, 0);
  });
}

test("input on another dashboard does not postpone this entry's deadline", async () => {
  const browser = await createBrowser({}, [{
    entry_id: "kitchen", device_id: "knob-2", dashboard_path: "dashboard-kitchen",
    navigation_enabled: true, idle_return_enabled: true, idle_return_timeout_seconds: 60,
    overlay_enabled: false,
  }]);
  await browser.advance(55_000);
  browser.location.pathname = "/dashboard-kitchen/car";
  browser.input("click");
  browser.location.pathname = "/dashboard-home/car";
  await browser.advance(5_000);
  assert.equal(browser.navigations.length, 1);
  assert.equal(browser.results[0].entry_id, "entrance");
});

test("input listeners use passive capture and are removed on destroy", async () => {
  const browser = await createBrowser();
  const [listener] = browser.window.listeners.get("pointerdown");
  assert.equal(listener.capture, true);
  assert.equal(listener.passive, true);
  browser.input("pointerdown");
  browser.window.knobSwipeNavigation.destroy();
  assert.equal(browser.timers.size, 0);
  assert.equal(browser.unsubscribeCount(), 1);
  assert.ok([...browser.window.listeners.values()].every((items) => items.length === 0));
  assert.ok([...browser.document.listeners.values()].every((items) => items.length === 0));
});

test("reload cleans the old instance and registers input listeners once", async () => {
  const browser = await createBrowser();
  browser.input("pointerdown");
  await browser.reload();
  assert.equal(browser.window.listeners.get("pointerdown").length, 1);
  assert.equal(browser.document.listeners.get("visibilitychange").length, 1);
  await browser.advance(60_000);
  assert.equal(browser.navigations.length, 1);
});
