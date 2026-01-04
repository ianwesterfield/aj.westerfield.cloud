#!/usr/bin/env python3
"""
Generate web development fundamentals training data for AJ fine-tuning.
Covers HTML, CSS, JavaScript, accessibility, and web APIs.
"""

import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"

SYSTEM_PROMPT = "You are AJ, an AI coding assistant. You are helping with web development and frontend technologies."

# =============================================================================
# HTML CONCEPTS
# =============================================================================

HTML_CONCEPTS = [
    {
        "question": "What is semantic HTML and why does it matter?",
        "answer": "Semantic HTML uses tags that describe meaning, not just appearance. Examples: header, nav, main, article, section, aside, footer, figure, figcaption. Benefits: accessibility (screen readers understand structure), SEO (search engines parse content better), maintainability (clear document structure). Avoid: div soup (divs everywhere), presentational tags (b vs strong, i vs em). Header for introductory content, nav for navigation, main for primary content, article for self-contained content."
    },
    {
        "question": "What are data attributes in HTML?",
        "answer": "Data attributes: custom attributes with data- prefix. <div data-user-id=\"123\" data-role=\"admin\">. Access in JavaScript: element.dataset.userId (camelCase conversion). Use for: storing data for JS, configuration, UI state. CSS can select: [data-active=\"true\"]. Don't use for: styling-only purposes (use classes), sensitive data (visible in source). Alternative to: hidden inputs, complex class names for state. Part of HTML5 spec, valid HTML."
    },
    {
        "question": "How do I optimize images for the web?",
        "answer": "Formats: JPEG (photos), PNG (transparency, graphics), WebP (modern, smaller), AVIF (newest, smallest). Responsive images: srcset for different sizes, sizes attribute for breakpoints. <img srcset=\"small.jpg 300w, large.jpg 1200w\" sizes=\"(max-width: 600px) 300px, 1200px\">. picture element for art direction. Lazy loading: loading=\"lazy\". Compression: optimize quality vs size. Modern: use WebP with fallbacks, CDN with automatic format conversion."
    },
    {
        "question": "What is the picture element used for?",
        "answer": "Picture element provides multiple image sources for art direction. Browser picks first matching source. <picture><source media=\"(min-width: 800px)\" srcset=\"large.jpg\"><source media=\"(min-width: 400px)\" srcset=\"medium.jpg\"><img src=\"small.jpg\"></picture>. Use for: different crops at breakpoints, format fallbacks (WebP with JPEG fallback), dark mode images. Different from srcset: picture for different images, srcset for same image different sizes. Always include img as fallback."
    },
    {
        "question": "What is the difference between defer and async for scripts?",
        "answer": "Regular script: blocks HTML parsing, executes immediately. async: downloads parallel, executes when ready (order not guaranteed), blocks rendering during execution. defer: downloads parallel, executes after HTML parsed, maintains order. Use defer for: scripts that need DOM, scripts with dependencies. Use async for: independent scripts (analytics, ads). Both only work with external scripts (src). Modern alternative: type=\"module\" (always deferred)."
    },
    {
        "question": "How do forms work in HTML5?",
        "answer": "Form elements: input types (text, email, password, number, date, file, etc.), select, textarea, button. New types: email (validates format), number (arrows, min/max), date (date picker), range (slider). Attributes: required, pattern (regex), min/max, minlength/maxlength, placeholder. Form validation: built-in browser validation, :valid/:invalid CSS. action: where to submit, method: GET/POST. Prevent default: event.preventDefault(). FormData API for JavaScript handling."
    },
    {
        "question": "What are web components?",
        "answer": "Web components: native custom elements with encapsulation. Three specs: Custom Elements (define new tags), Shadow DOM (encapsulated DOM/CSS), HTML Templates (reusable markup). Define: class extends HTMLElement, customElements.define('my-element', MyElement). Shadow DOM: this.attachShadow({mode: 'open'}). Slots: allow content projection. Lifecycle: connectedCallback, disconnectedCallback, attributeChangedCallback. Benefits: framework-agnostic, native encapsulation. Limitations: SSR challenges, limited browser APIs in shadow DOM."
    },
]

# =============================================================================
# CSS CONCEPTS
# =============================================================================

CSS_CONCEPTS = [
    {
        "question": "How does CSS specificity work?",
        "answer": "Specificity determines which CSS rules apply. Calculation: inline styles (1000), IDs (100), classes/attributes/pseudo-classes (10), elements/pseudo-elements (1). !important overrides specificity (avoid). Same specificity: later rule wins. Universal selector (*) and combinators don't add specificity. Example: #header .nav a (100+10+1=111) beats .nav a (10+1=11). Debugging: DevTools shows specificity. Best practice: keep specificity low with class-based styling."
    },
    {
        "question": "What is the CSS box model?",
        "answer": "Box model: content → padding → border → margin. Content: actual content area. Padding: space inside border. Border: visible line around padding. Margin: space outside border. box-sizing: content-box (default, width = content only), border-box (width includes padding + border, usually preferred). Margin collapse: vertical margins combine. Negative margins: pull elements. Reset: * { box-sizing: border-box } is common."
    },
    {
        "question": "What is CSS Grid and when should I use it?",
        "answer": "CSS Grid: two-dimensional layout system. Define rows and columns on container. display: grid; grid-template-columns: 1fr 2fr 1fr. fr = fractional unit. gap for spacing. Place items: grid-column, grid-row, or grid-area. Named areas: grid-template-areas. Auto-fit/auto-fill with minmax() for responsive. Use Grid for: page layouts, card grids, complex two-dimensional layouts. Use Flexbox for: one-dimensional layouts, component internals. They complement each other."
    },
    {
        "question": "What is CSS Flexbox and how do I use it?",
        "answer": "Flexbox: one-dimensional layout. Container: display: flex. Direction: flex-direction (row, column). Alignment: justify-content (main axis), align-items (cross axis). Item sizing: flex-grow, flex-shrink, flex-basis, shorthand: flex: 1. Order: change visual order without changing HTML. Wrap: flex-wrap for multiple lines. Common patterns: centering (justify-content + align-items center), space-between navigation, equal-width columns (flex: 1)."
    },
    {
        "question": "What are CSS custom properties (variables)?",
        "answer": "CSS variables: define with --, access with var(). :root { --primary: #007bff } .btn { background: var(--primary) }. Cascade: inherit, can override at any level. Fallback: var(--color, #000). Dynamic: can change with JavaScript (element.style.setProperty). Scope: cascade through DOM. Use for: theming, consistent values, dynamic styles. Different from preprocessor variables: live in browser, can be changed, work with calc(), cascade. Great for dark mode: change root variables."
    },
    {
        "question": "How do CSS media queries work?",
        "answer": "Media queries: apply styles conditionally. Syntax: @media (min-width: 768px) { }. Types: width, height, orientation, prefers-color-scheme, prefers-reduced-motion. Combine: and, or (comma), not. Mobile-first: start with mobile styles, add min-width queries for larger. Desktop-first: max-width queries. Common breakpoints: 480px (mobile), 768px (tablet), 1024px (desktop). Container queries: @container for component-based responsive."
    },
    {
        "question": "What are CSS transitions and animations?",
        "answer": "Transitions: smooth property changes. transition: property duration timing-function delay. Example: transition: opacity 0.3s ease. Only between states (hover, class change). Animations: keyframe-based, can loop. @keyframes name { from { } to { } }. animation: name duration timing iteration. Can animate multiple properties, pause, reverse. Performance: animate transform and opacity (GPU accelerated). will-change hints to browser. Avoid: layout-triggering properties (width, height). Use for: UI feedback, loading states, attention."
    },
    {
        "question": "What are CSS pseudo-classes vs pseudo-elements?",
        "answer": "Pseudo-classes: state-based selectors, single colon. :hover (mouse over), :focus (keyboard focus), :first-child, :nth-child(), :not(), :checked, :disabled, :valid/:invalid. Pseudo-elements: create elements, double colon. ::before, ::after (content: required), ::first-letter, ::first-line, ::placeholder, ::selection. Before/after: decorative elements, icons, clearfix. Both: powerful for styling without extra HTML. Accessibility: don't put important content in ::before/::after."
    },
    {
        "question": "What are CSS container queries?",
        "answer": "Container queries: style based on parent container size, not viewport. Define container: container-type: inline-size. Query: @container (min-width: 400px) { }. Named containers: container-name for specific targeting. Use for: reusable components that adapt to their container. Example: card component works in sidebar (narrow) and main content (wide). Better than media queries for components. Browser support: modern browsers (2023+). Polyfills available for older browsers."
    },
]

# =============================================================================
# JAVASCRIPT CONCEPTS
# =============================================================================

JS_CONCEPTS = [
    {
        "question": "What is the difference between let, const, and var?",
        "answer": "var: function-scoped, hoisted, can redeclare, avoid using. let: block-scoped, hoisted but not initialized (TDZ), can reassign. const: block-scoped, must initialize, cannot reassign (but object contents can change). Best practice: default to const, use let when reassignment needed, never var. const object = {} can still add properties; const arr = [] can push. For true immutability: Object.freeze() or immutable libraries."
    },
    {
        "question": "What is the event loop in JavaScript?",
        "answer": "Event loop: enables async JavaScript in single-threaded environment. Call stack: executes sync code. Task queue (macrotasks): setTimeout, setInterval, I/O. Microtask queue: Promises, queueMicrotask. Order: run stack → empty microtask queue → one macrotask → repeat. Promise callbacks run before setTimeout(0). Blocking call stack freezes UI. requestAnimationFrame before repaint. Understanding helps debug async timing issues."
    },
    {
        "question": "What are closures in JavaScript?",
        "answer": "Closure: function that remembers outer scope even after outer function returns. Created every time function created. Example: function outer() { let x = 1; return function inner() { return x; } }. inner() still accesses x. Use for: data privacy (module pattern), callbacks with context, partial application, memoization. Gotcha: closures in loops capture same variable - use let or IIFE. Memory: closures keep references alive."
    },
    {
        "question": "How does 'this' work in JavaScript?",
        "answer": "this: determined by how function is called. Object method: this = object. Standalone function: this = undefined (strict) or global. Event handler: this = element. Arrow function: inherits this from enclosing scope (lexical). Explicit binding: call(thisArg), apply(thisArg), bind(thisArg) returns new function. class methods: this = instance but loses binding when passed as callback (use arrow or bind). Common bug: losing this context in callbacks."
    },
    {
        "question": "What are Promises and async/await?",
        "answer": "Promise: represents eventual completion/failure of async operation. States: pending, fulfilled, rejected. Create: new Promise((resolve, reject) => {}). Consume: .then(onFulfilled).catch(onRejected).finally(). async/await: syntactic sugar for Promises. async function returns Promise. await pauses until Promise settles. Error handling: try/catch with await. Parallel: Promise.all([]), Promise.allSettled(). Race: Promise.race(). Always handle rejections."
    },
    {
        "question": "What is destructuring in JavaScript?",
        "answer": "Destructuring: extract values from arrays/objects. Array: const [a, b] = [1, 2]. Skip: [a, , c]. Rest: [first, ...rest]. Object: const {name, age} = person. Rename: const {name: personName} = person. Default: const {x = 10} = {}. Nested: const {user: {name}} = data. Function params: function({name, age}) {}. Use for: extracting properties, function parameters, swapping variables [a, b] = [b, a]."
    },
    {
        "question": "What are JavaScript modules?",
        "answer": "ES Modules: import/export syntax. export: named (export const x) or default (export default func). import: import {x} from './file' or import func from './file'. Dynamic import: await import('./module.js'). Benefits: encapsulation, tree-shaking, clear dependencies. Browser: <script type=\"module\">. Node.js: .mjs extension or type: module in package.json. CommonJS: require/module.exports (Node.js legacy). Modules are strict mode by default."
    },
    {
        "question": "What is the spread operator and rest parameters?",
        "answer": "Spread (...): expands iterable. Array: [...arr1, ...arr2] merges. Object: {...obj, newProp: value} copies and extends. Function call: func(...args). Rest (...): collects remaining. Function: function(first, ...rest) { }. Destructuring: const [head, ...tail] = array. Spread copies are shallow. Common uses: array copy, object merge, function arguments from array. Rest for variadic functions. Both use same ... syntax, context determines meaning."
    },
]

# =============================================================================
# WEB ACCESSIBILITY
# =============================================================================

ACCESSIBILITY = [
    {
        "question": "What is web accessibility and WCAG?",
        "answer": "Accessibility (a11y): making web usable by people with disabilities. WCAG: Web Content Accessibility Guidelines. Levels: A (minimum), AA (standard, often legally required), AAA (highest). Four principles (POUR): Perceivable (text alternatives, captions), Operable (keyboard navigation, enough time), Understandable (readable, predictable), Robust (compatible with assistive tech). Common issues: missing alt text, poor contrast, no keyboard support, no form labels."
    },
    {
        "question": "How do I make images accessible?",
        "answer": "Alt text: describe image content/purpose. Decorative images: alt=\"\" (empty). Informative images: describe content. Functional images (buttons): describe action. Complex images: longer description nearby or aria-describedby. Charts: provide data table alternative. CSS background images: don't use for meaningful content. SVG: title element, role=\"img\", aria-labelledby. Screen readers announce alt text. Test: does page make sense without images?"
    },
    {
        "question": "How do I ensure proper keyboard accessibility?",
        "answer": "All interactive elements must be keyboard accessible. Tab order: logical flow, tabindex=\"0\" for custom elements, avoid positive tabindex. Focus indicators: visible :focus styles (never outline: none without alternative). ARIA: roles for custom widgets (role=\"button\"), aria-expanded, aria-pressed. Enter/Space: activate buttons. Arrow keys: navigate within components. Escape: close modals. Skip links: bypass navigation. Test: use site with keyboard only."
    },
    {
        "question": "What is ARIA and when should I use it?",
        "answer": "ARIA: Accessible Rich Internet Applications. Attributes that provide semantics to assistive tech. First rule: don't use ARIA if native HTML works (use button, not div with role=\"button\"). Roles: define element type. States: aria-expanded, aria-checked, aria-disabled. Properties: aria-label, aria-describedby, aria-labelledby. Live regions: aria-live for dynamic content. Landmarks: main, navigation, complementary. Misusing ARIA is worse than not using it."
    },
    {
        "question": "How do I create accessible forms?",
        "answer": "Labels: every input needs associated label (for attribute or wrap input). Placeholder is not a label. Error messages: associated with input (aria-describedby), clear description. Required fields: indicate visually and programmatically (required attribute, aria-required). Error handling: focus first error, announce errors to screen readers. Grouping: fieldset/legend for related inputs. Autocomplete: appropriate autocomplete values. Color alone: don't indicate errors only by color."
    },
    {
        "question": "What is color contrast and why does it matter?",
        "answer": "Color contrast: difference between text and background. WCAG requirements: 4.5:1 for normal text, 3:1 for large text (18pt+ or 14pt+ bold). AA level: minimum. AAA: 7:1 and 4.5:1. Tools: WebAIM contrast checker, Chrome DevTools. Don't rely on color alone: add icons, text, patterns. Consider: colorblindness (8% of men), low vision, bright light conditions. CSS: use sufficient contrast in light and dark modes."
    },
]

# =============================================================================
# WEB APIs
# =============================================================================

WEB_APIS = [
    {
        "question": "What is the Fetch API?",
        "answer": "Fetch: modern API for network requests. Returns Promise. Basic: fetch(url).then(r => r.json()). Options: fetch(url, {method: 'POST', headers: {...}, body: JSON.stringify(data)}). Response methods: .json(), .text(), .blob(). Error handling: fetch doesn't reject on HTTP errors, check response.ok. AbortController for cancellation. Credentials: include for cookies cross-origin. Replaces XMLHttpRequest. Async/await: const data = await fetch(url).then(r => r.json())."
    },
    {
        "question": "What is localStorage vs sessionStorage?",
        "answer": "Both: Web Storage API, key-value, string only. localStorage: persists until cleared, ~5MB, shared across tabs. sessionStorage: cleared when tab closes, separate per tab. API: setItem(key, value), getItem(key), removeItem(key), clear(). JSON storage: JSON.stringify to save, JSON.parse to retrieve. Sync: blocks main thread (use sparingly). Security: don't store sensitive data, XSS can access. Alternative: IndexedDB for large/structured data."
    },
    {
        "question": "What is the Intersection Observer API?",
        "answer": "Intersection Observer: efficient visibility detection. Use for: lazy loading images, infinite scroll, animations on scroll. Create: new IntersectionObserver(callback, options). options: root (viewport if null), rootMargin, threshold (0-1 or array). callback receives entries with isIntersecting, intersectionRatio. observe(element) to watch. More performant than scroll events. Disconnect when done. Example: load image when 50% visible (threshold: 0.5)."
    },
    {
        "question": "What is the ResizeObserver API?",
        "answer": "ResizeObserver: watch element size changes. Better than window resize for component-level responsiveness. Create: new ResizeObserver(callback). callback receives entries with contentRect (width, height). observe(element) to watch. Use for: responsive components without media queries, canvas sizing, dynamic layouts. Avoids layout thrashing. Works on any element, not just window. Modern browsers support. Polyfill available."
    },
    {
        "question": "How do Service Workers work?",
        "answer": "Service Worker: script running in background, separate from page. Use for: offline support, push notifications, background sync. Lifecycle: register, install (cache assets), activate (clean old caches), fetch (intercept requests). Cache API: cache.put(), cache.match(). Strategies: cache-first, network-first, stale-while-revalidate. Must be HTTPS (except localhost). Scope: controls pages under its directory. Update: browser checks for changes, new worker waits until old closes. Workbox library simplifies."
    },
    # === ADDITIONAL WEB APIs ===
    {
        "question": "What is the Clipboard API?",
        "answer": "Clipboard API: read/write clipboard data. Write: navigator.clipboard.writeText(text). Read: navigator.clipboard.readText(). Requires user permission (triggered by user action). Async (returns Promises). Rich content: read()/write() for images, HTML. Security: HTTPS only, permission-based. Fallback: document.execCommand('copy') deprecated but has broader support. Use for: copy buttons, paste functionality. Check permission: navigator.permissions.query({name: 'clipboard-read'})."
    },
    {
        "question": "What is the History API?",
        "answer": "History API: manipulate browser history without page reload. pushState(state, title, url): add entry. replaceState(): modify current entry. popstate event: when user navigates (back/forward). history.back(), forward(), go(). Use for: SPA routing, updating URL without reload. state: arbitrary data stored with history entry. Security: same-origin URLs only. React Router, Vue Router use this internally. Base for client-side routing in modern SPAs."
    },
    {
        "question": "What is the Geolocation API?",
        "answer": "Geolocation API: get user's location with permission. navigator.geolocation.getCurrentPosition(success, error). Continuous: watchPosition() returns ID for clearWatch(). Options: enableHighAccuracy, timeout, maximumAge. Response: coords.latitude, longitude, accuracy, altitude. Requires HTTPS. Privacy: always ask permission, handle denial gracefully. Error codes: PERMISSION_DENIED, POSITION_UNAVAILABLE, TIMEOUT. Use for: maps, local search, location-based features."
    },
    {
        "question": "What is the Web Notifications API?",
        "answer": "Notifications API: show system notifications. Request permission: Notification.requestPermission(). Check: Notification.permission. Create: new Notification(title, {body, icon, tag}). Events: onclick, onclose, onerror. Requires user permission and HTTPS. tag: prevents duplicate notifications. Service Worker: for persistent notifications when page closed. Push + Notifications: receive notifications via push API, display with Notifications. Always provide in-app alternative."
    },
    {
        "question": "What is the Web Audio API?",
        "answer": "Web Audio API: advanced audio processing and synthesis. AudioContext: create audio graph. Source nodes: oscillator, audio buffer, media element. Processing: gain, filter, analyzer, convolver. Destination: speakers. Connect nodes: source.connect(gain).connect(context.destination). Use for: games, music apps, audio visualization, effects. Analyzer for visualizations: getByteFrequencyData(). More powerful than HTML5 audio element. Suspended by default until user interaction."
    },
    {
        "question": "What is the Canvas API?",
        "answer": "Canvas API: 2D drawing in browser. <canvas> element + getContext('2d'). Drawing: fillRect, strokeRect, arc, beginPath, lineTo, bezierCurveTo. Style: fillStyle, strokeStyle, lineWidth. Text: fillText, strokeText. Images: drawImage. Transformations: translate, rotate, scale, save/restore. Animation: requestAnimationFrame loop. Pixel manipulation: getImageData, putImageData. WebGL: getContext('webgl') for 3D. Use for: charts, games, image editing, data visualization."
    },
    {
        "question": "What is the Performance API?",
        "answer": "Performance API: measure performance metrics. performance.now(): high-resolution timestamp. User Timing: performance.mark('start'), measure('name', 'start', 'end'). Navigation Timing: page load metrics. Resource Timing: individual resource load times. PerformanceObserver: watch for entries. Core Web Vitals: LCP, FID, CLS. Use for: measuring feature timing, identifying bottlenecks, real user monitoring. Send metrics to analytics. Built-in browser profiling."
    },
    {
        "question": "What is the MutationObserver API?",
        "answer": "MutationObserver: watch for DOM changes. Create: new MutationObserver(callback). observe(target, config): childList, attributes, characterData, subtree. callback receives MutationRecord list: type, addedNodes, removedNodes, attributeName. Use for: reacting to dynamic content, third-party script detection, accessibility tools. More performant than polling. disconnect() when done. Alternative to deprecated Mutation Events. Clean up to prevent memory leaks."
    },
    {
        "question": "What is the Drag and Drop API?",
        "answer": "Drag and Drop API: native drag and drop functionality. Make draggable: draggable=\"true\". Events: dragstart, drag, dragend (on dragged element); dragenter, dragover, dragleave, drop (on target). dataTransfer: store data during drag. dataTransfer.setData('text/plain', data), getData(). preventDefault on dragover and drop. Use for: file uploads, sortable lists, kanban boards. Native but can be complex - libraries like SortableJS simplify."
    },
    {
        "question": "What is the Web Crypto API?",
        "answer": "Web Crypto API: cryptographic operations in browser. Available via crypto.subtle. Operations: encrypt, decrypt, sign, verify, digest (hash), deriveBits, deriveKey. Generate keys: generateKey(), importKey(). Algorithms: AES-GCM (encryption), RSA-OAEP, ECDSA (signatures), SHA-256 (hashing). Returns ArrayBuffer, use TextEncoder/Decoder. Requires HTTPS. Use for: client-side encryption, secure tokens, integrity verification. Not for password hashing (use bcrypt server-side)."
    },
    {
        "question": "What is the Broadcast Channel API?",
        "answer": "Broadcast Channel API: communicate between browsing contexts (tabs, iframes). Create: new BroadcastChannel('channel-name'). Send: channel.postMessage(data). Receive: channel.onmessage = (e) => e.data. Same origin only. Use for: logout across tabs, theme sync, real-time state sharing. Close when done: channel.close(). Alternative to localStorage events for cross-tab communication. Simple pub/sub for same-origin pages."
    },
    {
        "question": "What is the Web Share API?",
        "answer": "Web Share API: native share dialog on mobile. Check support: navigator.share. Share: navigator.share({title, text, url}). Returns Promise. Files: navigator.canShare({files}) then share with files array. Mobile only (primarily). Requires user gesture (click handler). Fallback: copy to clipboard, social share buttons. Use for: sharing content to native apps. Progressive enhancement - check before using."
    },
    {
        "question": "What are Web Workers?",
        "answer": "Web Workers: run JavaScript in background thread. Create: new Worker('worker.js'). Communicate: postMessage(data), onmessage event. No DOM access in worker. Use for: heavy computation, data processing, parsing. Types: Dedicated Worker (one owner), Shared Worker (multiple pages), Service Worker (offline/push). Import scripts: importScripts(). Transferable objects for efficient large data transfer. Keep UI responsive during intensive tasks."
    },
    {
        "question": "What is the File API?",
        "answer": "File API: access files from user input. Input: <input type=\"file\"> fires change event with e.target.files (FileList). File properties: name, size, type, lastModified. Read content: FileReader with readAsText, readAsDataURL, readAsArrayBuffer. Events: load, error, progress. Drag and drop: e.dataTransfer.files. URL.createObjectURL for preview. Multiple: multiple attribute. Accept: accept=\"image/*\". Validation: check type, size before upload."
    },
    {
        "question": "What is the Screen Wake Lock API?",
        "answer": "Screen Wake Lock API: prevent device screen from dimming or locking. Request: const lock = await navigator.wakeLock.request('screen'). Release: lock.release(). Document visibility: lock auto-releases when hidden, re-acquire on visibilitychange. Use for: video players, presentations, maps navigation, cooking recipes. Check support: 'wakeLock' in navigator. Battery conscious - only when needed. Mobile primarily but desktop Chrome supports."
    },
]

def main():
    """Generate web fundamentals training examples."""
    all_examples = []
    
    # HTML Concepts
    for item in HTML_CONCEPTS:
        all_examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": item["question"],
            "response": item["answer"],
            "metadata": {
                "domain": "web_fundamentals",
                "subdomain": "html",
                "response_type": "concepts"
            }
        })
    
    # CSS Concepts
    for item in CSS_CONCEPTS:
        all_examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": item["question"],
            "response": item["answer"],
            "metadata": {
                "domain": "web_fundamentals",
                "subdomain": "css",
                "response_type": "concepts"
            }
        })
    
    # JavaScript Concepts
    for item in JS_CONCEPTS:
        all_examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": item["question"],
            "response": item["answer"],
            "metadata": {
                "domain": "web_fundamentals",
                "subdomain": "javascript",
                "response_type": "concepts"
            }
        })
    
    # Accessibility
    for item in ACCESSIBILITY:
        all_examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": item["question"],
            "response": item["answer"],
            "metadata": {
                "domain": "web_fundamentals",
                "subdomain": "accessibility",
                "response_type": "concepts"
            }
        })
    
    # Web APIs
    for item in WEB_APIS:
        all_examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": item["question"],
            "response": item["answer"],
            "metadata": {
                "domain": "web_fundamentals",
                "subdomain": "web_apis",
                "response_type": "concepts"
            }
        })
    
    # Save to file
    output_file = DATA_DIR / "web_fundamentals.jsonl"
    with open(output_file, "w", encoding="utf-8") as f:
        for example in all_examples:
            f.write(json.dumps(example, ensure_ascii=False) + "\n")
    
    print(f"  [OK] Saved {len(all_examples)} examples to {output_file}")

if __name__ == "__main__":
    main()
