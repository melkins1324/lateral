// Second Brain browser clipper (readable source).
// It sends the page title, URL, selected text and browser name to the
// "Share to Second Brain" shortcut through the shortcuts:// URL scheme.
// No Notion token ever touches the web page.
// The one-line version for your bookmarks bar is in bookmarklet.txt.
(() => {
  const ua = navigator.userAgent;
  const app = /Edg\//.test(ua) ? "Edge"
    : /OPR\//.test(ua) ? "Opera"
    : /Firefox\//.test(ua) ? "Firefox"
    : /Chrome\//.test(ua) ? (navigator.brave ? "Brave" : "Chrome")
    : /Safari\//.test(ua) ? "Safari" : "Browser";
  const payload = {
    title: document.title,
    url: location.href,
    selection: String(window.getSelection() || ""),
    app,
  };
  location.href = "shortcuts://run-shortcut?name=" + encodeURIComponent("Share to Second Brain") +
    "&input=text&text=" + encodeURIComponent("SBCLIP1\n" + JSON.stringify(payload));
})();
