/**
 * PesaGuard Status Site — Home page logic.
 *
 * DATA HONESTY CONTRACT
 * ---------------------
 * The overview renders exactly what the JSON payloads contain. When a payload
 * is unverified (`verified !== true`) or a value is missing, the page says so
 * instead of guessing. It never invents a status, latency, or uptime figure,
 * and it never stamps a "last updated" time that did not come from the source.
 *
 * Sources:
 *   api/status.json   (runtime endpoint, preferred)
 *   data/status.json  (static fallback)
 *   data/uptime.json, data/incidents.json, data/maintenance.json
 */
(function () {
  "use strict";

  var UI = window.StatusUI;
  var REFRESH_INTERVAL = 30000; /* 30 seconds */
  var NOT_AVAILABLE = "Not available";
  var NOT_REPORTED = "Not yet reported";
  var refreshTimer = null;

  function isVerified(payload) {
    return !!(payload && payload.verified === true);
  }

  /* --- Overall status ----------------------------------------------------- */

  function renderOverall(data) {
    var overall = (data && data.overall) || { status: "unknown", label: "Status unavailable" };
    var tone = UI.statusTone(overall.status);

    var indicator = document.getElementById("status-indicator");
    if (indicator) {
      /* Use setAttribute for class: SVG elements expose className as a
       * read-only SVGAnimatedString, and this block may touch both HTML and
       * SVG children. */
      indicator.setAttribute("class", "status-indicator " + tone);
      var icon = indicator.querySelector(".status-icon");
      var text = indicator.querySelector(".status-indicator-text");
      if (icon) icon.setAttribute("class", "status-icon " + tone);
      if (text) text.textContent = overall.label;
    }

    var subtext = document.querySelector(".status-indicator-subtext");
    if (subtext) subtext.textContent = overall.description || "";

    /* Hero heading mirrors the overall label. */
    var heroHeading = document.getElementById("hero-status-heading");
    if (heroHeading) heroHeading.textContent = overall.label;

    /* Timestamps are only shown when the source actually supplied one. */
    var stamp = (data && data.lastUpdated) || null;
    var display = stamp ? UI.formatDate(stamp) : NOT_REPORTED;
    document.querySelectorAll(".js-last-updated").forEach(function (el) {
      el.textContent = display;
    });

    /* Header chrome status dot follows the real state, not a hardcoded value. */
    var headerDot = document.querySelector(".status-header .status-dot");
    if (headerDot) headerDot.setAttribute("class", "status-dot " + tone);
    var headerText = document.querySelector(".status-header .js-header-status");
    if (headerText) headerText.textContent = overall.label;

    /* Unverified banner: explains, in the page, why states read "unknown". */
    var notice = document.getElementById("unverified-notice");
    if (notice) {
      if (isVerified(data)) {
        notice.style.display = "none";
      } else {
        notice.style.display = "block";
        var noteText = notice.querySelector(".js-unverified-note");
        if (noteText) {
          noteText.textContent = (data && data.note) ||
            "No monitoring source is connected. States shown as unknown have not been measured.";
        }
      }
    }
  }

  /* --- Service cards ------------------------------------------------------ */

  function renderServices(data) {
    var container = document.getElementById("service-list");
    if (!container) return;

    var services = (data && data.services) || [];
    if (services.length === 0) {
      container.innerHTML =
        '<p class="text-muted" style="padding:8px 0;">No service definitions are configured.</p>';
      return;
    }

    var html = "";
    services.forEach(function (svc) {
      var tone = UI.statusTone(svc.status);
      html += '<div class="service-status-card" data-service="' + UI.escapeHTML(svc.id) + '">';
      html += '<div class="service-name">';
      html += '<span class="status-dot ' + tone + '" aria-hidden="true"></span>';
      html += "<span>" + UI.escapeHTML(svc.name) + "</span>";
      html += "</div>";
      html += '<div class="service-meta">';
      html += '<span class="status-pill" data-tone="' + tone + '"><i></i>' +
        UI.escapeHTML(UI.statusLabel(svc.status)) + "</span>";
      html += '<span style="display:block;margin-top:4px">' +
        (svc.latency ? UI.escapeHTML(svc.latency) + " latency" : "latency not measured") +
        "</span>";
      html += "</div></div>";
    });

    container.innerHTML = html;
  }

  /* --- Uptime summary (from data/uptime.json) ----------------------------- */

  function renderUptimeSummary(uptime) {
    var container = document.getElementById("uptime-summary");
    if (!container) return;

    var ranges = ["24h", "7d", "30d", "90d"];
    var labels = { "24h": "24-hour", "7d": "7-day", "30d": "30-day", "90d": "90-day" };
    var periods = (uptime && uptime.periods) || {};

    var html = "";
    ranges.forEach(function (range) {
      var value = periods[range] || null;
      html += '<div class="uptime-card">';
      html += '<div class="uptime-value">' +
        (value ? UI.escapeHTML(value) : NOT_AVAILABLE) + "</div>";
      html += '<div class="uptime-label">' + labels[range] + " uptime</div>";
      html += "</div>";
    });
    container.innerHTML = html;
  }

  /* --- Active incident banner --------------------------------------------- */

  function renderIncidentBanner(data) {
    var banner = document.getElementById("incident-banner");
    if (!banner) return;

    var incidents = (data && data.activeIncidents) || [];
    if (incidents.length === 0) {
      banner.style.display = "none";
      return;
    }

    banner.style.display = "block";
    var html = "";
    incidents.forEach(function (incident) {
      html += '<div class="status-incident-banner">';
      html += "<h2>" + UI.escapeHTML(incident.title || "Active incident") + "</h2>";
      html += "<p>" + UI.escapeHTML(incident.description || "") + " ";
      html += '<a href="incidents.html">View details</a></p></div>';
    });
    banner.innerHTML = html;
  }

  /* --- Recent incidents (from data/incidents.json) ------------------------ */

  function renderRecentIncidents(payload) {
    var container = document.getElementById("recent-incidents");
    if (!container) return;

    var incidents = (payload && payload.incidents) || [];
    if (incidents.length === 0) {
      container.innerHTML =
        '<p class="text-muted" style="padding:8px 0;">No incidents have been recorded. ' +
        '<a href="incidents.html">Incident history</a></p>';
      return;
    }

    var html = "";
    incidents.slice(0, 3).forEach(function (inc) {
      var tone = UI.incidentStatusTone(inc.status);
      html += '<div class="incident-card" data-severity="' + UI.escapeHTML(inc.severity || "medium") + '">';
      html += '<div class="incident-card-header">';
      html += '<span class="status-pill" data-tone="' + tone + '"><i></i>' +
        UI.escapeHTML(UI.incidentStatusLabel(inc.status)) + "</span>";
      html += '<time class="incident-card-meta" datetime="' + UI.escapeHTML(inc.created || "") + '">' +
        (inc.created ? UI.formatDate(inc.created) : NOT_REPORTED) + "</time>";
      html += "</div>";
      html += '<h3 class="incident-card-title"><a href="incidents.html#incident-' +
        UI.escapeHTML(inc.id) + '">' + UI.escapeHTML(inc.title || "") + "</a></h3>";
      html += '<div class="incident-card-footer">Duration: ' +
        UI.escapeHTML(inc.duration || NOT_AVAILABLE) + "</div>";
      html += "</div>";
    });
    container.innerHTML = html;
  }

  /* --- Scheduled maintenance (from data/maintenance.json) ----------------- */

  function renderScheduledMaintenance(payload) {
    var container = document.getElementById("scheduled-maintenance");
    if (!container) return;

    var windows = (payload && payload.maintenance) || [];
    var upcoming = windows.filter(function (m) {
      return m.status === "scheduled" || m.status === "in-progress";
    });

    if (upcoming.length === 0) {
      container.innerHTML =
        '<p class="text-muted" style="padding:8px 0;">No maintenance is scheduled. ' +
        '<a href="maintenance.html">Maintenance history</a></p>';
      return;
    }

    var html = "";
    upcoming.slice(0, 3).forEach(function (m) {
      html += '<div class="maintenance-card">';
      html += '<div class="maintenance-card-header">';
      html += '<span class="status-pill" data-tone="maintenance"><i></i>' +
        UI.escapeHTML(m.status === "in-progress" ? "In progress" : "Scheduled") + "</span>";
      html += '<time class="maintenance-card-meta" datetime="' + UI.escapeHTML(m.scheduledStart || "") + '">' +
        (m.scheduledStart ? UI.formatDate(m.scheduledStart) : NOT_REPORTED) + "</time>";
      html += "</div>";
      html += '<h3 class="maintenance-card-title">' + UI.escapeHTML(m.title || "") + "</h3>";
      html += "</div>";
    });
    container.innerHTML = html;
  }

  /* --- Data loading -------------------------------------------------------
   * Note: no client-side caching. A status page must not show a remembered
   * state as though it were current; every render comes from a fresh fetch.
   * ----------------------------------------------------------------------- */

  function loadData() {
    UI.fetchJSON("api/status.json", null).then(function (apiData) {
      if (apiData) {
        applyStatus(apiData);
        return;
      }
      UI.fetchJSON("data/status.json", null).then(function (staticData) {
        if (!staticData) {
          var list = document.getElementById("service-list");
          UI.showError(list, "Failed to load status. The last known state could not be confirmed.");
          renderOverall(null);
          return;
        }
        applyStatus(staticData);
      });
    });
  }

  function applyStatus(data) {
    renderOverall(data);
    renderServices(data);
    renderIncidentBanner(data);

    UI.fetchJSON("data/uptime.json", null).then(renderUptimeSummary);
    UI.fetchJSON("data/incidents.json", null).then(renderRecentIncidents);
    UI.fetchJSON("data/maintenance.json", null).then(renderScheduledMaintenance);
  }

  /* --- Auto-refresh ------------------------------------------------------- */

  function startAutoRefresh() {
    if (refreshTimer) clearInterval(refreshTimer);
    refreshTimer = setInterval(function () {
      loadData();
      var dot = document.querySelector(".auto-refresh-dot");
      if (dot) dot.classList.add("is-refreshing");
      setTimeout(function () {
        if (dot) dot.classList.remove("is-refreshing");
      }, 600);
    }, REFRESH_INTERVAL);
  }

  /* --- Init --------------------------------------------------------------- */

  function init() {
    var list = document.getElementById("service-list");
    if (list) UI.renderSkeleton(list, 6, "service");

    loadData();
    startAutoRefresh();

    document.addEventListener("visibilitychange", function () {
      if (!document.hidden) loadData();
    });
  }

  document.addEventListener("status:components-loaded", init);

  /* Fallback when component loading is unavailable (e.g. JS-free host). */
  document.addEventListener("DOMContentLoaded", function () {
    setTimeout(function () {
      if (window.StatusUI && !refreshTimer) init();
    }, 1200);
  });
})();

