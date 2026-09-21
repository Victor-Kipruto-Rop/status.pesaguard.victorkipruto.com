/**
 * Accessibility tests — validates HTML pages for a11y best practices.
 */
module.exports = function (ctx) {
  var test = ctx.test;
  var assert = ctx.assert;
  var fs = ctx.fs;
  var path = ctx.path;
  var BASE = ctx.BASE;

  var pages = ["index.html", "incidents.html", "maintenance.html", "uptime.html", "404.html"];

  pages.forEach(function (page) {
    var html = fs.readFileSync(path.join(BASE, page), "utf8");

    test(page + ": has lang attribute", function () {
      assert(/<html[^>]+lang=["']en["']/.test(html), "missing lang='en'");
    });

    test(page + ": has viewport meta", function () {
      assert(/name=["']viewport["']/.test(html), "missing viewport");
    });

    test(page + ": has skip-to-content link", function () {
      assert(/visually-hidden.*Skip to content|href="#main"/.test(html), "missing skip link");
    });

    test(page + ": has main landmark", function () {
      assert(/<main[^>]*id="main"/.test(html), "missing <main id=\"main\">");
    });

    test(page + ": has header landmark", function () {
      assert(/<header[^>]*id="site-header"/.test(html), "missing header placeholder");
    });

    test(page + ": has footer landmark", function () {
      assert(/<footer[^>]*id="site-footer"/.test(html), "missing footer placeholder");
    });

    test(page + ": has favicon", function () {
      assert(/favicon\.svg/.test(html), "missing favicon");
    });

    test(page + ": includes reduced-motion support", function () {
      assert(/animations\.css|prefers-reduced-motion/.test(html), "missing reduced-motion support");
    });
  });

  /* --- Dark mode check --- */
  test("dark theme support in CSS", function () {
    var cssFiles = ["variables.css", "layout.css", "components.css", "animations.css"];
    var allCSS = "";
    cssFiles.forEach(function (f) {
      try { allCSS += fs.readFileSync(path.join(BASE, "css", f), "utf8"); } catch (e) { /* ignore */ }
    });
    assert(/prefers-color-scheme:\s*dark/.test(allCSS), "missing dark-theme support");
  });

  /* --- Page-specific checks --- */
  test("index.html: has status indicator", function () {
    var html = fs.readFileSync(path.join(BASE, "index.html"), "utf8");
    assert(/status-indicator/.test(html), "missing status indicator");
  });

  test("index.html: has auto-refresh indicator", function () {
    var html = fs.readFileSync(path.join(BASE, "index.html"), "utf8");
    assert(/auto-refresh/.test(html), "missing auto-refresh");
  });

  test("index.html: has subscription form with aria-label", function () {
    var html = fs.readFileSync(path.join(BASE, "index.html"), "utf8");
    assert(/type=["']email["']/.test(html), "missing email input");
    assert(/aria-label/.test(html), "missing aria-label on subscription");
  });

  test("incidents.html: has filter controls", function () {
    var html = fs.readFileSync(path.join(BASE, "incidents.html"), "utf8");
    assert(/filter-year/.test(html), "missing year filter");
    assert(/filter-service/.test(html), "missing service filter");
    assert(/filter-status/.test(html), "missing status filter");
  });

  test("incidents.html: has back-to-status link", function () {
    var html = fs.readFileSync(path.join(BASE, "incidents.html"), "utf8");
    assert(/Back to status/.test(html), "missing back-to-status link");
  });

  test("maintenance.html: has maintenance sections", function () {
    var html = fs.readFileSync(path.join(BASE, "maintenance.html"), "utf8");
    assert(/active-maintenance/.test(html), "missing active section");
    assert(/upcoming-maintenance/.test(html), "missing upcoming section");
    assert(/maintenance-history/.test(html), "missing history section");
  });

  test("uptime.html: has range selector buttons", function () {
    var html = fs.readFileSync(path.join(BASE, "uptime.html"), "utf8");
    assert(/data-range="24h"/.test(html), "missing 24h range");
    assert(/data-range="7d"/.test(html), "missing 7d range");
    assert(/data-range="30d"/.test(html), "missing 30d range");
    assert(/data-range="90d"/.test(html), "missing 90d range");
  });

  test("uptime.html: has service selector", function () {
    var html = fs.readFileSync(path.join(BASE, "uptime.html"), "utf8");
    assert(/service-selector/.test(html), "missing service selector");
  });

  test("404.html: has error heading", function () {
    var html = fs.readFileSync(path.join(BASE, "404.html"), "utf8");
    assert(/Page not found/i.test(html), "missing error heading");
  });

  test("404.html: links back to homepage", function () {
    var html = fs.readFileSync(path.join(BASE, "404.html"), "utf8");
        assert(/href="index\.html"/.test(html), "missing link back to index");
  });

  /* --- SEO checks --- */
  test("every page has canonical URL", function () {
    pages.forEach(function (page) {
      var html = fs.readFileSync(path.join(BASE, page), "utf8");
      assert(/<link rel="canonical"/.test(html), page + " missing canonical");
    });
  });

  test("every page has title tag", function () {
    pages.forEach(function (page) {
      var html = fs.readFileSync(path.join(BASE, page), "utf8");
      assert(/<title>[^<]+<\/title>/.test(html), page + " missing title");
    });
  });

  test("every page has description meta", function () {
    pages.forEach(function (page) {
      var html = fs.readFileSync(path.join(BASE, page), "utf8");
      assert(/name="description"/.test(html), page + " missing description");
    });
  });

  test("every page has Open Graph metadata", function () {
    pages.forEach(function (page) {
      var html = fs.readFileSync(path.join(BASE, page), "utf8");
      assert(/property="og:title"/.test(html), page + " missing og:title");
      assert(/property="og:description"/.test(html), page + " missing og:description");
    });
  });

  /* --- Component checks --- */
  test("header.html has all navigation links", function () {
    var html = fs.readFileSync(path.join(BASE, "components", "header.html"), "utf8");
    assert(/href="index\.html"/.test(html), "header missing Home link");
    assert(/href="incidents\.html"/.test(html), "header missing Incidents link");
    assert(/href="maintenance\.html"/.test(html), "header missing Maintenance link");
    assert(/href="uptime\.html"/.test(html), "header missing Uptime link");
  });

  test("header.html has mobile nav toggle with ARIA", function () {
    var html = fs.readFileSync(path.join(BASE, "components", "header.html"), "utf8");
    assert(/status-nav-toggle/.test(html), "header missing nav toggle");
    assert(/aria-expanded/.test(html), "nav toggle missing aria-expanded");
    assert(/aria-label/.test(html), "header missing aria-label");
  });

  test("footer.html has product and support links", function () {
    var html = fs.readFileSync(path.join(BASE, "components", "footer.html"), "utf8");
    assert(/pesaguard\.victorkipruto\.com/.test(html), "footer missing product link");
    assert(/Documentation/.test(html), "footer missing documentation link");
    assert(/Privacy Policy/.test(html), "footer missing privacy link");
    assert(/Terms of Service/.test(html), "footer missing terms link");
  });

  /* --- Honesty contract ---------------------------------------------------
   * These guard against a healthy-looking default state being shipped before
   * any monitoring source exists. They are the most important tests here.
   * ---------------------------------------------------------------------- */

  test("no page hardcodes a healthy overall status", function () {
    pages.forEach(function (page) {
      var html = fs.readFileSync(path.join(BASE, page), "utf8");
      assert(!/All Systems Operational/i.test(html),
        page + " hardcodes a healthy status; state must come from data");
      assert(!/All PesaGuard services are operating normally/i.test(html),
        page + " hardcodes a healthy status description");
    });
  });

  test("no component hardcodes a healthy status dot", function () {
    ["header.html", "footer.html", "status-overview.html"].forEach(function (name) {
      var html = fs.readFileSync(path.join(BASE, "components", name), "utf8");
      assert(!/status-dot operational/.test(html),
        name + " hardcodes an operational dot");
      assert(!/status-(dot|pill)[^>]*data-tone="operational"/.test(html),
        name + " hardcodes an operational pill");
    });
  });

  test("no page ships a fabricated timestamp", function () {
    pages.forEach(function (page) {
      var html = fs.readFileSync(path.join(BASE, page), "utf8");
      assert(!/2026-09-22T14:30/.test(html),
        page + " contains a fabricated example timestamp");
    });
  });

  test("index.html subscription form is disabled and declared unavailable", function () {
    var html = fs.readFileSync(path.join(BASE, "index.html"), "utf8");
    assert(/id="subscription-form"/.test(html), "missing subscription form");
    assert(/disabled/.test(html), "subscription controls must be disabled");
    assert(/not available yet/i.test(html),
      "subscription section must state that it is unavailable");
    assert(!/Check your email to confirm/i.test(html),
      "must not claim an email was sent");
  });

  test("index.html exposes an unverified notice element", function () {
    var html = fs.readFileSync(path.join(BASE, "index.html"), "utf8");
    assert(/id="unverified-notice"/.test(html),
      "index.html must expose the unverified notice");
  });

  test("no page references the removed js-last-updated-display hook", function () {
    pages.forEach(function (page) {
      var html = fs.readFileSync(path.join(BASE, page), "utf8");
      assert(!/js-last-updated-display/.test(html),
        page + " references a hook no script populates");
    });
  });
};