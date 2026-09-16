import "@testing-library/jest-dom/vitest";

// jsdom does not implement scrollIntoView; components that auto-scroll a
// chat log call it in a useEffect, so provide a harmless no-op for tests.
if (typeof Element !== "undefined" && !Element.prototype.scrollIntoView) {
  Element.prototype.scrollIntoView = () => {};
}

