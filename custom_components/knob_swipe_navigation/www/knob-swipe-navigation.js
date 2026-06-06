const KNOB_SWIPE_NAV_VERSION = "0.1.1";
const WS_CONFIG_TYPE = "knob_swipe_navigation/config";
const OVERLAY_ID = "knob-swipe-navigation-overlay";
const STYLE_ID = "knob-swipe-navigation-style";
const DEFAULT_OVERLAY_TIMEOUT = 2800;
const SWIPE_ANIMATION_MS = 220;
const SWIPE_DELAY_MS = 32;

const viewSelectors = [
  "home-assistant",
  "$",
  "home-assistant-main",
  "$",
  "partial-panel-resolver",
  "ha-panel-lovelace",
  "$",
  "hui-root",
];

const viewContainerSelectors = viewSelectors.concat("$", '[id="view"]');
const appModernSelectors = viewSelectors.concat("$", "ha-app-layout");
const appLegacySelectors = viewSelectors.concat("$", "div");

const state = {
  config: null,
  configLoaded: false,
  lastEventAt: 0,
  unsubscribe: null,
};

function deepQuery(selectors) {
  let node = document;
  for (const selector of selectors) {
    if (!node) return null;
    node = selector === "$" ? node.shadowRoot : node.querySelector(selector);
  }
  return node;
}

function getHomeAssistantElement() {
  return document.querySelector("home-assistant");
}

function getHass() {
  return getHomeAssistantElement()?.hass || null;
}

function getConnection(hass) {
  return hass?.connection || window.hassConnection?.conn || null;
}

function waitForHass() {
  return new Promise((resolve) => {
    const existing = getHass();
    if (existing && getConnection(existing)) {
      resolve(existing);
      return;
    }

    let attempts = 0;
    const timer = window.setInterval(() => {
      const hass = getHass();
      attempts += 1;
      if (hass && getConnection(hass)) {
        window.clearInterval(timer);
        resolve(hass);
      } else if (attempts > 120) {
        window.clearInterval(timer);
      }
    }, 500);
  });
}

async function callWS(hass, message) {
  if (typeof hass.callWS === "function") {
    return hass.callWS(message);
  }
  const connection = getConnection(hass);
  if (connection?.sendMessagePromise) {
    return connection.sendMessagePromise(message);
  }
  throw new Error("Home Assistant WebSocket connection is unavailable.");
}

async function loadBackendConfig(hass) {
  try {
    state.config = await callWS(hass, { type: WS_CONFIG_TYPE });
    state.configLoaded = true;
  } catch (err) {
    state.config = null;
    state.configLoaded = false;
  }
}

function lovelaceRoot() {
  return deepQuery(viewSelectors);
}

function lovelaceConfig() {
  const root = lovelaceRoot();
  return (
    root?.lovelace?.config ||
    root?._lovelace?.config ||
    root?.config ||
    null
  );
}

function dashboardPath() {
  const parts = location.pathname.split("/").filter(Boolean);
  return parts[0] || "lovelace";
}

function normalizeBool(value, defaultValue) {
  if (value === undefined || value === null) return defaultValue;
  if (value === "true") return true;
  if (value === "false") return false;
  return Boolean(value);
}

function normalizeNumber(value, defaultValue, min, max) {
  const parsed = Number.parseInt(value, 10);
  if (!Number.isFinite(parsed)) return defaultValue;
  return Math.max(min, Math.min(max, parsed));
}

function dashboardKnobConfig() {
  const config = lovelaceConfig();
  const swipeNav = config?.swipe_nav || {};
  const knob = swipeNav.knob || config?.knob_swipe_navigation || null;
  if (!knob || knob.enable !== true) return null;

  return {
    wrap: normalizeBool(swipeNav.wrap, true),
    overlay: normalizeBool(knob.overlay, true),
    overlayTimeout: normalizeNumber(
      knob.overlay_timeout,
      DEFAULT_OVERLAY_TIMEOUT,
      500,
      10000,
    ),
    cooldownMs: normalizeNumber(knob.cooldown_ms, 0, 0, 10000),
    requireFully: normalizeBool(knob.require_fully, false),
    requireQueryParam:
      typeof knob.require_query_param === "string"
        ? knob.require_query_param.trim()
        : "",
    suppressIfEntityOn:
      typeof knob.suppress_if_entity_on === "string"
        ? knob.suppress_if_entity_on.trim()
        : "",
  };
}

function viewPath(view, index) {
  const path = typeof view.path === "string" ? view.path.trim() : "";
  return path || String(index);
}

function viewTitle(view, index) {
  const title = typeof view.title === "string" ? view.title.trim() : "";
  return title || `Tab ${index + 1}`;
}

function viewIcon(view) {
  const icon = typeof view.icon === "string" ? view.icon.trim() : "";
  return icon || "mdi:view-dashboard-outline";
}

function shouldIncludeView(view) {
  if (!view) return false;
  if (view.subview === true) return false;
  if (view.visible === false) return false;
  return true;
}

function dashboardTabs() {
  const config = lovelaceConfig();
  const views = Array.isArray(config?.views) ? config.views : [];
  const base = dashboardPath();
  return views
    .map((view, index) => ({
      name: viewTitle(view, index),
      icon: viewIcon(view),
      view: viewPath(view, index),
      originalIndex: index,
      path: `/${base}/${viewPath(view, index)}${location.search || ""}`,
      visible: shouldIncludeView(view),
    }))
    .filter((tab) => tab.visible);
}

function currentIndex(tabs) {
  if (!tabs.length) return -1;
  const parts = location.pathname.split("/").filter(Boolean);
  const currentView = parts[1] || tabs[0].view;
  const index = tabs.findIndex(
    (tab) => tab.view === currentView || tab.path.split("?")[0] === location.pathname,
  );
  return index >= 0 ? index : 0;
}

function targetIndex(current, tabs, goNext, settings) {
  const next = current + (goNext ? 1 : -1);
  if (next >= 0 && next < tabs.length) return next;
  if (settings.wrap === false) return -1;
  return (next + tabs.length) % tabs.length;
}

function ensureStyle() {
  const existing = document.getElementById(STYLE_ID);
  if (existing && existing.dataset.version === KNOB_SWIPE_NAV_VERSION) return;
  if (existing) existing.remove();

  const style = document.createElement("style");
  style.id = STYLE_ID;
  style.dataset.version = KNOB_SWIPE_NAV_VERSION;
  style.textContent = `
    #${OVERLAY_ID} {
      all: initial !important;
      position: fixed !important;
      left: 50% !important;
      bottom: calc(32px + env(safe-area-inset-bottom, 0px)) !important;
      transform: translateX(-50%) translateY(12px) scale(0.98) !important;
      z-index: 2147483647 !important;
      opacity: 0 !important;
      filter: blur(2px) !important;
      pointer-events: none !important;
      transition: opacity 120ms ease, transform 160ms cubic-bezier(0.2, 0.9, 0.2, 1), filter 160ms ease !important;
      color: white !important;
      font-family: Roboto, Arial, sans-serif !important;
      contain: layout style paint !important;
      isolation: isolate !important;
    }
    #${OVERLAY_ID}.is-visible {
      opacity: 1 !important;
      filter: blur(0) !important;
      transform: translateX(-50%) translateY(0) scale(1) !important;
    }
    #${OVERLAY_ID}.is-hidden {
      opacity: 0 !important;
      filter: blur(2px) !important;
      transform: translateX(-50%) translateY(12px) scale(0.98) !important;
    }
    #${OVERLAY_ID} .knob-tab-panel {
      width: min(92vw, max(360px, calc(var(--knob-tab-count, 5) * 128px))) !important;
      display: grid !important;
      grid-template-columns: repeat(var(--knob-tab-count, 5), minmax(0, 1fr)) !important;
      align-items: center !important;
      gap: 12px !important;
      padding: 12px 14px !important;
      border: 1px solid rgba(255, 255, 255, 0.2) !important;
      border-radius: 18px !important;
      background: rgba(8, 12, 22, 0.82) !important;
      box-shadow: 0 18px 48px rgba(0, 0, 0, 0.42) !important;
      backdrop-filter: blur(18px) saturate(135%) !important;
      -webkit-backdrop-filter: blur(18px) saturate(135%) !important;
      transform-origin: bottom center !important;
      will-change: transform, opacity !important;
    }
    #${OVERLAY_ID} .knob-tab {
      width: 100% !important;
      min-width: 0 !important;
      min-height: 76px !important;
      box-sizing: border-box !important;
      display: flex !important;
      flex-direction: column !important;
      align-items: center !important;
      justify-content: center !important;
      gap: 6px !important;
      border: 1px solid rgba(255, 255, 255, 0.08) !important;
      border-radius: 14px !important;
      color: rgba(255, 255, 255, 0.62) !important;
      background: rgba(255, 255, 255, 0.06) !important;
      transition: color 120ms ease, border-color 120ms ease, background 120ms ease, box-shadow 120ms ease !important;
      will-change: transform, opacity !important;
    }
    #${OVERLAY_ID} .knob-tab ha-icon {
      width: 28px !important;
      height: 28px !important;
      color: currentColor !important;
    }
    #${OVERLAY_ID} .knob-label {
      width: 100% !important;
      max-width: 100% !important;
      overflow: hidden !important;
      text-align: center !important;
      text-overflow: ellipsis !important;
      white-space: nowrap !important;
      font-size: 12px !important;
      line-height: 1 !important;
      font-weight: 650 !important;
      letter-spacing: 0 !important;
    }
    #${OVERLAY_ID} .knob-tab.is-active {
      color: white !important;
      border-color: rgba(141, 213, 255, 0.72) !important;
      background: linear-gradient(180deg, rgba(74, 173, 228, 0.42), rgba(51, 100, 198, 0.34)) !important;
      box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.2), 0 0 24px rgba(67, 167, 255, 0.3) !important;
    }
    #${OVERLAY_ID}.is-entering .knob-tab-panel {
      animation: knobSwipeOverlayPanelIn 190ms cubic-bezier(0.18, 0.9, 0.2, 1.18) both !important;
    }
    #${OVERLAY_ID}.is-exiting .knob-tab-panel {
      animation: knobSwipeOverlayPanelOut 130ms ease-in both !important;
    }
    #${OVERLAY_ID}.is-entering .knob-tab {
      animation: knobSwipeOverlayItemIn 190ms cubic-bezier(0.18, 0.9, 0.2, 1.12) both !important;
    }
    #${OVERLAY_ID}.is-entering .knob-tab:nth-child(2) {
      animation-delay: 14ms !important;
    }
    #${OVERLAY_ID}.is-entering .knob-tab:nth-child(3) {
      animation-delay: 28ms !important;
    }
    #${OVERLAY_ID}.is-entering .knob-tab:nth-child(4) {
      animation-delay: 42ms !important;
    }
    #${OVERLAY_ID}.is-entering .knob-tab:nth-child(5) {
      animation-delay: 56ms !important;
    }
    @keyframes knobSwipeOverlayPanelIn {
      0% { opacity: 0.35; transform: translateY(10px) scale(0.965); }
      68% { opacity: 1; transform: translateY(-2px) scale(1.012); }
      100% { opacity: 1; transform: translateY(0) scale(1); }
    }
    @keyframes knobSwipeOverlayPanelOut {
      0% { opacity: 1; transform: translateY(0) scale(1); }
      100% { opacity: 0; transform: translateY(8px) scale(0.97); }
    }
    @keyframes knobSwipeOverlayItemIn {
      0% { opacity: 0; filter: blur(2px); transform: translateY(7px) scale(0.92); }
      100% { opacity: 1; filter: blur(0); transform: translateY(0) scale(1); }
    }
    @media (prefers-reduced-motion: reduce) {
      #${OVERLAY_ID},
      #${OVERLAY_ID} .knob-tab,
      #${OVERLAY_ID} .knob-tab-panel {
        animation: none !important;
        transition: opacity 80ms ease !important;
        filter: none !important;
      }
    }
  `;
  document.head.appendChild(style);
}

function ensureOverlay() {
  let overlay = document.getElementById(OVERLAY_ID);
  if (overlay) return overlay;
  overlay = document.createElement("div");
  overlay.id = OVERLAY_ID;
  document.body.appendChild(overlay);
  return overlay;
}

function renderOverlay(tabs, activeIndex, ttl) {
  if (!tabs.length) return;
  ensureStyle();
  const overlay = ensureOverlay();
  const wasVisible =
    overlay.classList.contains("is-visible") &&
    !overlay.classList.contains("is-hidden");
  overlay.textContent = "";
  overlay.style.setProperty("--knob-tab-count", String(tabs.length));

  const panel = document.createElement("div");
  panel.className = "knob-tab-panel";
  for (const [index, tab] of tabs.entries()) {
    const item = document.createElement("div");
    item.className = `knob-tab${index === activeIndex ? " is-active" : ""}`;

    const icon = document.createElement("ha-icon");
    icon.setAttribute("icon", tab.icon);
    icon.setAttribute("aria-hidden", "true");
    item.appendChild(icon);

    const label = document.createElement("div");
    label.className = "knob-label";
    label.textContent = tab.name;
    item.appendChild(label);

    panel.appendChild(item);
  }
  overlay.appendChild(panel);

  overlay.classList.remove("is-hidden", "is-exiting");
  window.clearTimeout(window.__knobSwipeOverlayEnterTimer);
  window.clearTimeout(window.__knobSwipeOverlayExitTimer);
  if (wasVisible) {
    overlay.classList.add("is-visible");
  } else {
    overlay.classList.remove("is-visible", "is-entering");
    overlay.offsetWidth;
    window.requestAnimationFrame(() => {
      overlay.classList.add("is-visible", "is-entering");
      window.__knobSwipeOverlayEnterTimer = window.setTimeout(() => {
        overlay.classList.remove("is-entering");
      }, 280);
    });
  }

  window.clearTimeout(window.__knobSwipeOverlayTimer);
  window.__knobSwipeOverlayTimer = window.setTimeout(() => {
    overlay.classList.remove("is-entering");
    overlay.classList.add("is-exiting");
    overlay.classList.remove("is-visible");
    overlay.classList.add("is-hidden");
    window.__knobSwipeOverlayExitTimer = window.setTimeout(() => {
      overlay.classList.remove("is-exiting");
    }, 180);
  }, ttl);
}

function navigate(target) {
  const url = new URL(target, location.origin);
  const next = url.pathname + url.search + url.hash;
  if (location.pathname + location.search + location.hash !== next) {
    history.pushState(null, "", next);
    window.dispatchEvent(new CustomEvent("location-changed"));
  }
}

function dispatchSwipe(goNext) {
  const app = deepQuery(appModernSelectors) || deepQuery(appLegacySelectors);
  if (!app || typeof Touch !== "function" || typeof TouchEvent !== "function") {
    return false;
  }
  const width = Math.max(window.innerWidth || 0, screen.width || 0, 800);
  const height = Math.max(window.innerHeight || 0, screen.height || 0, 600);
  const startX = Math.round(width * (goNext ? 0.78 : 0.22));
  const endX = Math.round(width * (goNext ? 0.22 : 0.78));
  const y = Math.round(height * 0.5);
  const id = Date.now() % 100000;
  const touch = (x) =>
    new Touch({
      identifier: id,
      target: app,
      clientX: x,
      clientY: y,
      screenX: x,
      screenY: y,
      pageX: x,
      pageY: y,
    });
  const start = touch(startX);
  const end = touch(endX);
  app.dispatchEvent(
    new TouchEvent("touchstart", {
      bubbles: true,
      cancelable: true,
      composed: true,
      touches: [start],
      targetTouches: [start],
      changedTouches: [start],
    }),
  );
    app.dispatchEvent(
      new TouchEvent("touchmove", {
        bubbles: true,
        cancelable: true,
        composed: true,
        touches: [end],
        targetTouches: [end],
        changedTouches: [end],
      }),
    );
  app.dispatchEvent(
    new TouchEvent("touchend", {
      bubbles: true,
      cancelable: true,
      composed: true,
      touches: [],
      targetTouches: [],
      changedTouches: [end],
    }),
  );
  return true;
}

function animate(target, goNext) {
  const view = deepQuery(viewContainerSelectors);
  if (!view) {
    navigate(target);
    return;
  }
  const app = deepQuery(appModernSelectors) || deepQuery(appLegacySelectors);
  const width = Math.max(window.innerWidth || 0, screen.width || 0, 800);
  const distance = Math.round(width * 0.5);
  const out = goNext ? -distance : distance;
  const incoming = goNext ? distance : -distance;
  if (app) app.style.overflow = "hidden";
  view.style.transition = `transform ${SWIPE_ANIMATION_MS}ms ease-in, opacity ${SWIPE_ANIMATION_MS}ms ease-in`;
  view.style.opacity = "0";
  view.style.transform = `translate(${out}px,0)`;
  window.setTimeout(() => {
    view.style.transition = "";
    view.style.transform = `translate(${incoming}px,0)`;
    navigate(target);
  }, SWIPE_ANIMATION_MS + 10);
  window.setTimeout(() => {
    const active = deepQuery(viewContainerSelectors) || view;
    active.style.transition = `transform ${SWIPE_ANIMATION_MS}ms ease-out, opacity ${SWIPE_ANIMATION_MS}ms ease-out`;
    active.style.opacity = "1";
    active.style.transform = "";
  }, SWIPE_ANIMATION_MS + 50);
  window.setTimeout(() => {
    const active = deepQuery(viewContainerSelectors) || view;
    active.style.transition = "";
    active.style.transform = "";
    active.style.opacity = "";
    if (app) app.style.overflow = "";
  }, SWIPE_ANIMATION_MS * 2 + 160);
}

function verify(target, expectedIndex, tabs, settings, delay, goNext) {
  window.setTimeout(() => {
    const actual = currentIndex(tabs);
    if (actual === expectedIndex) {
      if (settings.overlay) renderOverlay(tabs, actual, settings.overlayTimeout);
      return;
    }
    if (location.pathname !== new URL(target, location.origin).pathname) {
      animate(target, goNext);
      window.setTimeout(() => {
        const finalIndex = currentIndex(tabs);
        if (settings.overlay) {
          renderOverlay(
            tabs,
            finalIndex >= 0 ? finalIndex : expectedIndex,
            settings.overlayTimeout,
          );
        }
      }, SWIPE_ANIMATION_MS * 2 + 260);
      return;
    }
    if (settings.overlay) {
      renderOverlay(tabs, actual >= 0 ? actual : expectedIndex, settings.overlayTimeout);
    }
  }, delay);
}

function rotateValue(eventData) {
  const params = eventData?.params || {};
  if (Object.prototype.hasOwnProperty.call(params, "rotate_type")) {
    return Number(params.rotate_type);
  }
  const args = Array.isArray(eventData?.args) ? eventData.args : [];
  if (args.length) return Number(args[0]);
  return Number.NaN;
}

function handleRotate(direction) {
  const settings = dashboardKnobConfig();
  if (!settings) return;
  if (settings.requireFully && !window.fully) return;
  if (
    settings.requireQueryParam &&
    !new URLSearchParams(location.search).has(settings.requireQueryParam)
  ) {
    return;
  }
  const hass = getHass();
  if (
    settings.suppressIfEntityOn &&
    hass?.states?.[settings.suppressIfEntityOn]?.state === "on"
  ) {
    return;
  }

  const now = Date.now();
  if (settings.cooldownMs > 0 && now - state.lastEventAt < settings.cooldownMs) {
    return;
  }
  state.lastEventAt = now;

  const tabs = dashboardTabs();
  if (tabs.length < 2) return;

  const current = currentIndex(tabs);
  if (current < 0) return;

  const goNext = direction === "next";
  const next = targetIndex(current, tabs, goNext, settings);
  if (next < 0) return;

  const target = tabs[next].path;
  if (settings.overlay) {
    renderOverlay(tabs, next, settings.overlayTimeout);
  }

  window.setTimeout(() => {
    const usedSynthetic = dispatchSwipe(goNext);
    if (!usedSynthetic) {
      animate(target, goNext);
      verify(target, next, tabs, settings, SWIPE_ANIMATION_MS * 2 + 260, goNext);
      return;
    }
    verify(target, next, tabs, settings, SWIPE_ANIMATION_MS + 260, goNext);
  }, SWIPE_DELAY_MS);
}

function handleZhaEvent(event) {
  if (!state.configLoaded || !state.config) return;
  const data = event?.data || {};
  if (data.device_id !== state.config.device_id) return;
  if (data.command !== "rotate_type") return;

  const value = rotateValue(data);
  const direction = state.config.rotate?.[String(value)];
  if (direction !== "next" && direction !== "previous") return;
  handleRotate(direction);
}

async function init() {
  if (window.__knobSwipeNavigationInitialized) return;
  window.__knobSwipeNavigationInitialized = true;

  const hass = await waitForHass();
  if (!hass) return;
  await loadBackendConfig(hass);

  const connection = getConnection(hass);
  if (!connection?.subscribeEvents) return;
  state.unsubscribe = await connection.subscribeEvents(handleZhaEvent, "zha_event");
}

window.knobSwipeNavigation = {
  version: KNOB_SWIPE_NAV_VERSION,
  reloadConfig: async () => {
    const hass = getHass();
    if (hass) await loadBackendConfig(hass);
  },
  showOverlay: () => {
    const settings = dashboardKnobConfig() || {
      overlay: true,
      overlayTimeout: DEFAULT_OVERLAY_TIMEOUT,
    };
    const tabs = dashboardTabs();
    renderOverlay(tabs, currentIndex(tabs), settings.overlayTimeout);
  },
};

init();
