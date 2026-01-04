#!/usr/bin/env python3
"""
SCSS/CSS Architecture Training Data Generator
Generates training examples for SCSS, CSS, styling architecture, and design systems.
"""

import json
import random
from pathlib import Path
from typing import List, Dict

DATA_DIR = Path(__file__).parent.parent / "data"

SYSTEM_PROMPT = """You are AJ, an expert AI assistant for frontend development.
You help with SCSS, CSS, styling architecture, design systems, and responsive design."""

# =============================================================================
# SCSS/CSS CONCEPTS
# =============================================================================

BASIC_CONCEPTS = [
    {
        "question": "What is SCSS and how is it different from CSS?",
        "answer": "SCSS (Sassy CSS) is a CSS preprocessor that extends CSS with programming features. Key differences: 1) Variables: $primary-color vs CSS custom properties (--primary), 2) Nesting: selectors can be nested for cleaner code, 3) Mixins: reusable blocks of styles, 4) Functions: color manipulation, math operations, 5) Partials: modular file organization with @use/@import, 6) Inheritance: @extend for sharing styles. SCSS compiles to standard CSS. Modern CSS has many features (custom properties, calc(), nesting) but SCSS still offers better organization for large projects."
    },
    {
        "question": "How do SCSS variables work?",
        "answer": "SCSS variables use $ prefix: $primary-color: #3498db; Usage: .btn { background: $primary-color; }. Variables can hold: colors, numbers, strings, lists, maps. Scope: global by default, local within selectors. Default values: $color: blue !default; (won't override if already set). Maps for grouped values: $colors: (primary: #3498db, secondary: #2ecc71); Access with map-get($colors, primary). CSS custom properties (--var) are different: runtime, inherited, can be changed by JS."
    },
    {
        "question": "How does SCSS nesting work?",
        "answer": "Nesting places child selectors inside parents. Example: .nav { ul { list-style: none; } li { display: inline; } a { color: blue; &:hover { color: red; } } }. The & references parent selector - essential for pseudo-classes, BEM. Compiles to: .nav ul, .nav li, .nav a, .nav a:hover. Avoid deep nesting (max 3-4 levels) - creates specificity issues and long selectors. Nesting is for organization, not to match HTML structure literally."
    },
    {
        "question": "What are SCSS mixins and when should I use them?",
        "answer": "Mixins are reusable style blocks. Define: @mixin flex-center { display: flex; justify-content: center; align-items: center; }. Use: @include flex-center;. Parameters: @mixin button($bg, $color: white) { background: $bg; color: $color; }. Use for: vendor prefixes, complex repeated patterns, responsive breakpoints. Don't use for: single properties (use variables), semantic styles (use @extend). Mixins duplicate CSS output - @extend creates comma-separated selectors."
    },
    {
        "question": "What is @extend in SCSS and when to use it?",
        "answer": "@extend shares styles between selectors. %placeholder defines extendable style: %button-base { padding: 10px; border: none; }. Usage: .btn-primary { @extend %button-base; background: blue; }. Compiles to comma-separated selectors - efficient output. Use % placeholders to avoid outputting base class. Pitfalls: can create unexpected selector combinations when extending across nested rules. Prefer mixins for: parameterized styles, avoiding selector explosion. @extend best for: true semantic relationships."
    },
    {
        "question": "How do I organize SCSS files in a project?",
        "answer": "Common patterns - 7-1 Pattern: abstracts/ (variables, mixins), base/ (reset, typography), components/, layout/, pages/, themes/, vendors/, main.scss. ITCSS (Inverted Triangle): settings, tools, generic, elements, objects, components, utilities. Simple: variables.scss, mixins.scss, base.scss, components/. Use @use (modern) or @import. @use namespaces: @use 'variables' as v; then v.$color. Partials start with _: _variables.scss (not compiled separately). Index files: @forward members."
    },
    {
        "question": "What are SCSS functions and how do I use them?",
        "answer": "SCSS has built-in functions and custom functions. Color: lighten($color, 20%), darken(), saturate(), mix($c1, $c2, 50%), rgba($color, 0.5). Math: percentage(0.5), round(), ceil(), floor(). String: quote(), unquote(), str-length(). List: length(), nth($list, 1), append(). Map: map-get(), map-merge(), map-keys(). Custom: @function double($n) { @return $n * 2; }. Use functions for: calculations, color manipulation. Unlike mixins, functions return values, don't output CSS."
    },
    {
        "question": "What is BEM methodology for CSS?",
        "answer": "BEM: Block-Element-Modifier naming convention. Block: standalone component (.card). Element: part of block (.card__title, .card__image). Modifier: variation (.card--featured, .card__title--large). SCSS with BEM: .card { &__title { } &__image { } &--featured { } }. Benefits: clear relationships, flat specificity, self-documenting. Rules: elements belong to blocks only, modifiers modify blocks or elements, no element of element (__title__icon - bad). Combine with component organization."
    },
    {
        "question": "How do CSS custom properties differ from SCSS variables?",
        "answer": "CSS custom properties (--var): runtime, inherited through DOM, changeable via JS, scoped to selectors. SCSS variables ($var): compile-time, static output, not in final CSS. Custom properties: :root { --color: blue; } .box { color: var(--color); }. Can scope: .dark-theme { --color: white; }. JS access: getComputedStyle(el).getPropertyValue('--color'). Fallback: var(--color, blue). Use CSS custom properties for: theming, runtime changes. Use SCSS for: calculations, loops, complex compile-time logic."
    },
    {
        "question": "How do I implement dark mode with SCSS/CSS?",
        "answer": "Approaches: 1) CSS custom properties (recommended): :root { --bg: white; --text: black; } .dark { --bg: #1a1a1a; --text: white; }. 2) Media query: @media (prefers-color-scheme: dark) { }. 3) SCSS maps with mixins. Implementation: toggle class on body or :root. Store preference in localStorage. Respect system preference with matchMedia('(prefers-color-scheme: dark)'). SCSS can generate: @each $theme, $colors in $themes { .#{$theme} { ... } }. Transition: transition: background-color 0.3s;"
    },
]

ADVANCED_CONCEPTS = [
    {
        "question": "How do I create a responsive design system with SCSS?",
        "answer": "Core components: 1) Breakpoint mixin: $breakpoints: (sm: 576px, md: 768px, lg: 992px); @mixin respond($bp) { @media (min-width: map-get($breakpoints, $bp)) { @content; } }. 2) Spacing scale: $spacing: (0: 0, 1: 0.25rem, 2: 0.5rem, 4: 1rem); 3) Typography scale: modular scale or custom. 4) Color tokens: semantic naming (--color-primary, --color-surface). Usage: .container { padding: spacing(4); @include respond(md) { padding: spacing(6); } }. Generate utility classes: @each $key, $val in $spacing { .p-#{$key} { padding: $val; } }"
    },
    {
        "question": "What is CSS-in-JS and when should I use SCSS instead?",
        "answer": "CSS-in-JS (styled-components, Emotion): styles in JavaScript, component scoping, dynamic styling. SCSS benefits: better tooling, faster build, CSS caching, no runtime cost, familiar syntax, works with any framework. CSS-in-JS benefits: true component isolation, props-based styling, co-location. Use SCSS for: traditional projects, performance-critical apps, teams with CSS expertise, large design systems. Use CSS-in-JS for: highly dynamic styling, component libraries, React-heavy teams. Consider: CSS Modules as middle ground."
    },
    {
        "question": "How do I implement CSS Grid layouts with SCSS helpers?",
        "answer": "Grid mixin: @mixin grid($cols, $gap: 1rem) { display: grid; grid-template-columns: repeat($cols, 1fr); gap: $gap; }. Auto-fit: @mixin auto-grid($min: 250px) { display: grid; grid-template-columns: repeat(auto-fit, minmax($min, 1fr)); gap: 1rem; }. Grid areas helper: @mixin grid-area($name) { grid-area: $name; }. Responsive: .grid { @include grid(1); @include respond(md) { @include grid(3); } }. Named areas for complex layouts: grid-template-areas: 'header header' 'sidebar main'."
    },
    {
        "question": "How do I create reusable animation mixins?",
        "answer": "@mixin keyframes($name) { @keyframes #{$name} { @content; } }. @mixin animate($name, $duration: 0.3s, $timing: ease) { animation: $name $duration $timing; }. Usage: @include keyframes(fadeIn) { from { opacity: 0; } to { opacity: 1; } }. .element { @include animate(fadeIn, 0.5s); }. Transition mixin: @mixin transition($props...) { transition-property: $props; transition-duration: 0.3s; transition-timing-function: ease; }. Consider prefers-reduced-motion: @media (prefers-reduced-motion: reduce) { animation: none; }."
    },
    {
        "question": "How do I structure SCSS for a component library?",
        "answer": "Structure: /tokens (colors, spacing, typography), /mixins (utilities), /components (one file per component), /themes. Each component: // _button.scss with .btn, .btn--primary, etc. Entry point: @forward all components. Theming: CSS custom properties for runtime, SCSS maps for generation. Documentation: style guide showing all variants. Distribution: ship CSS or SCSS source. Versioning: semantic versioning with changelog. Consider: tree-shaking unused components, design tokens in JSON for multi-platform."
    },
    {
        "question": "What are CSS logical properties and how do they help?",
        "answer": "Logical properties adapt to writing direction (LTR/RTL). Physical: margin-left, padding-top. Logical: margin-inline-start, padding-block-start. Mapping: inline = horizontal, block = vertical; start/end = contextual. Examples: margin-inline: auto (horizontal centering), padding-block: 1rem (top/bottom), inset-inline-start: 0 (left in LTR). Benefits: automatic RTL support. SCSS helper: @mixin padding-inline($val) { padding-inline-start: $val; padding-inline-end: $val; }. Browser support is good for modern browsers."
    },
    {
        "question": "How do I implement CSS Container Queries?",
        "answer": "Container queries style based on container size, not viewport. Setup: .card-container { container-type: inline-size; container-name: card; }. Query: @container card (min-width: 400px) { .card { flex-direction: row; } }. SCSS wrapper: @mixin container-query($name, $min) { @container #{$name} (min-width: $min) { @content; } }. Use cases: reusable components adapting to available space, widget sizing, dashboard layouts. Different from media queries: responds to parent container. cqw/cqh units reference container dimensions."
    },
    {
        "question": "How do I create a fluid typography system?",
        "answer": "Fluid typography scales smoothly between breakpoints. CSS clamp: font-size: clamp(1rem, 2.5vw, 2rem);. SCSS function: @function fluid($min, $max, $min-vw: 320px, $max-vw: 1200px) { @return clamp(#{$min}, calc(#{$min} + #{strip-unit($max - $min)} * ((100vw - #{$min-vw}) / #{strip-unit($max-vw - $min-vw)})), #{$max}); }. Usage: h1 { font-size: fluid(1.5rem, 3rem); }. Modular scale: $ratio: 1.25; h2 font-size = h3 * ratio. Consider line-height scaling too. Test across all viewport sizes."
    },
    {
        "question": "What is CSS Cascade Layers and how do they work?",
        "answer": "@layer controls cascade order independent of specificity. Define order: @layer reset, base, components, utilities;. Assign styles: @layer components { .btn { } }. Later layers win over earlier. Unlayered styles beat all layers. Use cases: reset < framework < custom, managing third-party CSS conflicts. SCSS integration: group @layer declarations. @layer can be nested. Import with layers: @import url('lib.css') layer(framework);. Benefits: predictable cascade, easier overrides, cleaner architecture. Specificity still matters within a layer."
    },
    {
        "question": "How do I create utility-first styles with SCSS?",
        "answer": "Generate utilities programmatically: $utilities: (p: padding, m: margin, d: display); $spacing: (0: 0, 1: 0.25rem, 2: 0.5rem); @each $prop-key, $prop in $utilities { @each $size-key, $size in $spacing { .#{$prop-key}-#{$size-key} { #{$prop}: $size; } } }. Display: @each $val in (flex, grid, block, none) { .d-#{$val} { display: $val; } }. Responsive: @each $bp, $width in $breakpoints { @media (min-width: $width) { .#{$bp}\\:d-flex { display: flex; } } }. Escape special chars with \\\\. Combine with component styles."
    },
    {
        "question": "How do I handle CSS specificity issues in large projects?",
        "answer": "Strategies: 1) BEM keeps specificity flat (.block__element--modifier). 2) Utility-first: single-class utilities. 3) CSS Layers: @layer for explicit ordering. 4) CSS Modules: auto-scoped classes. SCSS pitfalls: deep nesting increases specificity. Rules: avoid IDs for styling, avoid !important (except utilities), don't over-nest. Measuring: count (IDs, classes, elements). When overriding: match or exceed specificity, or use cascade position. Tooling: stylelint can warn on high specificity. Reset specificity: :where(.class) has 0 specificity."
    },
    {
        "question": "What are CSS Houdini APIs and custom properties worklets?",
        "answer": "Houdini extends CSS with JavaScript. Typed custom properties: CSS.registerProperty({ name: '--angle', syntax: '<angle>', initialValue: '0deg', inherits: false }); enables animations on custom properties. Paint API: custom background painting. Layout API: custom layout algorithms. Animation Worklet: 60fps animations off main thread. Browser support varies - Chrome leads. Use cases: complex effects impossible in pure CSS, design tools, animation libraries. Fallback needed for unsupported browsers. Mostly experimental - use progressively."
    },
    {
        "question": "How do I optimize SCSS compilation and CSS output?",
        "answer": "SCSS optimization: 1) Use @use/@forward over @import (caches). 2) Avoid @import in partials (causes duplication). 3) Use index files: @forward 'variables'. CSS output: 1) PurgeCSS/UnCSS removes unused styles. 2) cssnano minifies. 3) PostCSS autoprefixer adds vendor prefixes. 4) Combine similar selectors. Build: Sass CLI or bundler (webpack, Vite). Source maps for debugging. Critical CSS: extract above-fold styles for inline. Consider CSS containment for rendering performance. Monitor bundle size with tools."
    },
    {
        "question": "How do I implement a token-based design system?",
        "answer": "Design tokens: primitive values abstracted for theming. Tiers: 1) Primitive: $blue-500: #3498db. 2) Semantic: $color-primary: $blue-500. 3) Component: $button-bg: $color-primary. Token file: JSON or SCSS maps. Multi-platform: Style Dictionary transforms tokens for web (CSS), iOS (Swift), Android (XML). SCSS generation: @each $name, $value in $colors { --color-#{$name}: #{$value}; }. Versioning: token changes are breaking changes. Documentation: generated reference from tokens. Theming: swap semantic token values per theme."
    },
    # === ADDITIONAL SCSS CONCEPTS ===
    {
        "question": "How do I handle CSS vendor prefixes in SCSS?",
        "answer": "Options: 1) Autoprefixer (PostCSS) - recommended, auto-adds prefixes based on browserlist. 2) SCSS mixin: @mixin prefix($property, $value, $prefixes: webkit moz ms) { @each $p in $prefixes { -#{$p}-#{$property}: $value; } #{$property}: $value; }. 3) Compass/Bourbon libraries (dated). Best practice: don't manually prefix - use Autoprefixer in build. Configure .browserslistrc for target browsers. Removes outdated prefixes too. Check caniuse.com for prefix requirements."
    },
    {
        "question": "What is CSS @scope and how does it work?",
        "answer": "@scope creates a style scope with boundaries. Syntax: @scope (.card) to (.card-content) { img { border-radius: 10px; } }. Styles only apply within .card but stop at .card-content. Benefits: component isolation without Shadow DOM, proximity-based styling. SCSS can generate scoped patterns: @mixin scoped($root, $limit: null) { @at-root { @scope (#{$root}) #{if($limit, 'to (#{$limit})', '')} { @content; } } }. Still emerging - check browser support."
    },
    {
        "question": "How do I create a CSS reset with SCSS?",
        "answer": "Modern reset approach: // _reset.scss *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; } html { -webkit-text-size-adjust: 100%; } body { line-height: 1.5; -webkit-font-smoothing: antialiased; } img, picture, video, canvas, svg { display: block; max-width: 100%; } input, button, textarea, select { font: inherit; } p, h1, h2, h3, h4, h5, h6 { overflow-wrap: break-word; }. Consider normalize.css or modern-normalize as base. Reset opinions vary - customize for project."
    },
    {
        "question": "How do I implement aspect-ratio with fallbacks in SCSS?",
        "answer": "Modern CSS: .video { aspect-ratio: 16/9; }. Fallback mixin: @mixin aspect-ratio($width, $height) { aspect-ratio: #{$width}/#{$height}; @supports not (aspect-ratio: 1) { &::before { content: ''; display: block; padding-top: calc(#{$height} / #{$width} * 100%); } > * { position: absolute; top: 0; left: 0; width: 100%; height: 100%; } position: relative; } }. The padding-top trick uses % which is relative to width. aspect-ratio is well-supported now."
    },
    {
        "question": "How do I create a CSS grid system with SCSS?",
        "answer": "12-column grid: $columns: 12; $gutter: 1.5rem; .row { display: flex; flex-wrap: wrap; margin: 0 calc(-#{$gutter} / 2); } @for $i from 1 through $columns { .col-#{$i} { flex: 0 0 calc(#{$i} / #{$columns} * 100%); padding: 0 calc(#{$gutter} / 2); } } Responsive: @each $bp, $width in $breakpoints { @media (min-width: $width) { @for $i from 1 through 12 { .col-#{$bp}-#{$i} { flex: 0 0 calc(#{$i} / 12 * 100%); } } } }. Or use CSS Grid: simpler, more powerful."
    },
    {
        "question": "How do I use SCSS with Tailwind CSS?",
        "answer": "Tailwind has its own utility generation, but can coexist with SCSS. Setup: configure postcss.config.js with both sass-loader and tailwindcss. Use SCSS for: complex components, mixins, functions. Use Tailwind for: utilities, rapid prototyping. @apply in SCSS doesn't work - use in CSS/PostCSS files. Alternative: use @layer to organize. Or use Tailwind's config to extend with custom values matching your SCSS tokens. Some teams prefer one or the other - mixing adds complexity."
    },
    {
        "question": "How do I create hover/focus states systematically in SCSS?",
        "answer": "Interactive mixin: @mixin interactive($prop, $base, $hover, $active: null) { #{$prop}: $base; &:hover, &:focus-visible { #{$prop}: $hover; } @if $active { &:active { #{$prop}: $active; } } }. Usage: .btn { @include interactive(background, $blue-500, $blue-600, $blue-700); }. Focus-visible over focus: shows focus ring only for keyboard nav. Add transition: transition: background-color 0.2s ease. Consider :focus-within for parent elements. Accessibility: ensure sufficient contrast on all states."
    },
    {
        "question": "How do I debug SCSS compilation issues?",
        "answer": "Debugging tools: 1) @debug $variable - prints to console during compile. 2) @warn 'message' - shows warning. 3) @error 'message' - stops compilation. 4) Source maps - enable in compiler for browser DevTools mapping. Common issues: missing semicolons, undefined variables (check @use order), nesting errors, wrong map syntax. VSCode: SCSS IntelliSense extension. CLI: sass --watch with error output. Check: imported file exists, correct path, proper @use namespace. @use strict mode catches more issues."
    },
]

# =============================================================================
# CODE EXAMPLES
# =============================================================================

CODE_EXAMPLES = [
    {
        "instruction": "Create a responsive flexbox navigation with SCSS",
        "language": "scss",
        "code": '''// _variables.scss
$breakpoints: (
  sm: 576px,
  md: 768px,
  lg: 992px
);

$nav-height: 60px;
$nav-bg: #1a1a2e;
$nav-link-color: #eee;
$nav-link-hover: #00d9ff;

// _mixins.scss
@mixin respond($bp) {
  @media (min-width: map-get($breakpoints, $bp)) {
    @content;
  }
}

// _nav.scss
.nav {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  padding: 0 1rem;
  background: $nav-bg;
  min-height: $nav-height;

  &__logo {
    font-size: 1.5rem;
    font-weight: bold;
    color: $nav-link-hover;
    text-decoration: none;
  }

  &__toggle {
    display: block;
    background: none;
    border: none;
    color: $nav-link-color;
    font-size: 1.5rem;
    cursor: pointer;

    @include respond(md) {
      display: none;
    }
  }

  &__menu {
    display: none;
    flex-basis: 100%;
    list-style: none;
    padding: 1rem 0;
    margin: 0;

    &--open {
      display: block;
    }

    @include respond(md) {
      display: flex;
      flex-basis: auto;
      padding: 0;
      gap: 1rem;
    }
  }

  &__link {
    display: block;
    padding: 0.5rem 0;
    color: $nav-link-color;
    text-decoration: none;
    transition: color 0.2s ease;

    &:hover,
    &--active {
      color: $nav-link-hover;
    }
  }
}''',
        "explanation": "Responsive navigation using BEM, flexbox, and mobile-first approach"
    },
    {
        "instruction": "Create a theme system with CSS custom properties and SCSS",
        "language": "scss",
        "code": '''// _themes.scss
$themes: (
  light: (
    bg-primary: #ffffff,
    bg-secondary: #f5f5f5,
    text-primary: #1a1a1a,
    text-secondary: #666666,
    accent: #3498db,
    border: #e0e0e0,
  ),
  dark: (
    bg-primary: #1a1a1a,
    bg-secondary: #2d2d2d,
    text-primary: #f5f5f5,
    text-secondary: #a0a0a0,
    accent: #00d9ff,
    border: #404040,
  ),
);

// Generate CSS custom properties for each theme
:root {
  @each $key, $value in map-get($themes, light) {
    --#{$key}: #{$value};
  }
}

[data-theme="dark"] {
  @each $key, $value in map-get($themes, dark) {
    --#{$key}: #{$value};
  }
}

// Respect system preference
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    @each $key, $value in map-get($themes, dark) {
      --#{$key}: #{$value};
    }
  }
}

// Usage in components
.card {
  background: var(--bg-secondary);
  color: var(--text-primary);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 1.5rem;
  
  &__title {
    color: var(--accent);
    margin-bottom: 0.5rem;
  }
  
  &__text {
    color: var(--text-secondary);
  }
}

// Theme toggle transition
* {
  transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease;
}''',
        "explanation": "Theme system supporting light/dark mode with system preference detection"
    },
    {
        "instruction": "Create fluid typography scale with SCSS",
        "language": "scss",
        "code": '''// _functions.scss
@function strip-unit($value) {
  @return $value / ($value * 0 + 1);
}

@function fluid($min-size, $max-size, $min-vw: 320px, $max-vw: 1200px) {
  $min-size-rem: $min-size;
  $max-size-rem: $max-size;
  
  @return clamp(
    #{$min-size-rem},
    calc(#{$min-size-rem} + #{strip-unit($max-size-rem - $min-size-rem)} * ((100vw - #{$min-vw}) / #{strip-unit($max-vw - $min-vw)})),
    #{$max-size-rem}
  );
}

// _typography.scss
$type-scale: (
  xs:    (min: 0.75rem,  max: 0.875rem),
  sm:    (min: 0.875rem, max: 1rem),
  base:  (min: 1rem,     max: 1.125rem),
  lg:    (min: 1.125rem, max: 1.25rem),
  xl:    (min: 1.25rem,  max: 1.5rem),
  2xl:   (min: 1.5rem,   max: 2rem),
  3xl:   (min: 2rem,     max: 2.5rem),
  4xl:   (min: 2.5rem,   max: 3.5rem),
);

@mixin text($size) {
  $values: map-get($type-scale, $size);
  font-size: fluid(map-get($values, min), map-get($values, max));
}

// Generate utility classes
@each $name, $values in $type-scale {
  .text-#{$name} {
    font-size: fluid(map-get($values, min), map-get($values, max));
  }
}

// Usage
h1 { @include text(4xl); line-height: 1.1; }
h2 { @include text(3xl); line-height: 1.2; }
h3 { @include text(2xl); line-height: 1.3; }
h4 { @include text(xl);  line-height: 1.4; }
p  { @include text(base); line-height: 1.6; }
small { @include text(sm); }''',
        "explanation": "Fluid typography that scales smoothly between viewport sizes"
    },
    {
        "instruction": "Create a button component system with SCSS variants",
        "language": "scss",
        "code": '''// _button.scss
$btn-colors: (
  primary: (bg: #3498db, text: #fff, hover: #2980b9),
  secondary: (bg: #6c757d, text: #fff, hover: #545b62),
  success: (bg: #2ecc71, text: #fff, hover: #27ae60),
  danger: (bg: #e74c3c, text: #fff, hover: #c0392b),
  outline: (bg: transparent, text: #3498db, hover: rgba(#3498db, 0.1)),
);

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.625rem 1.25rem;
  font-size: 1rem;
  font-weight: 500;
  border-radius: 0.375rem;
  border: 2px solid transparent;
  cursor: pointer;
  transition: all 0.2s ease;
  
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  
  @each $name, $colors in $btn-colors {
    &--#{$name} {
      background: map-get($colors, bg);
      color: map-get($colors, text);
      
      @if $name == outline {
        border-color: map-get($colors, text);
      }
      
      &:hover:not(:disabled) {
        background: map-get($colors, hover);
      }
    }
  }
  
  // Size modifiers
  &--sm { padding: 0.375rem 0.75rem; font-size: 0.875rem; }
  &--lg { padding: 0.875rem 1.75rem; font-size: 1.125rem; }
  
  // Full width
  &--block { width: 100%; }
}''',
        "explanation": "Scalable button system using SCSS maps for variants and modifiers"
    },
    {
        "instruction": "Create a CSS Grid layout system with SCSS",
        "language": "scss",
        "code": '''// _grid.scss
$grid-columns: 12;
$grid-gutter: 1.5rem;
$container-max: 1200px;

.container {
  width: 100%;
  max-width: $container-max;
  margin: 0 auto;
  padding: 0 1rem;
}

.grid {
  display: grid;
  gap: $grid-gutter;
  
  // Column utilities
  @for $i from 1 through $grid-columns {
    &--cols-#{$i} {
      grid-template-columns: repeat($i, 1fr);
    }
  }
  
  // Auto-fit responsive grid
  &--auto {
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  }
}

// Column span utilities
@for $i from 1 through $grid-columns {
  .col-#{$i} {
    grid-column: span $i;
  }
}

// Responsive columns
@each $bp, $width in (sm: 576px, md: 768px, lg: 992px) {
  @media (min-width: $width) {
    @for $i from 1 through $grid-columns {
      .col-#{$bp}-#{$i} {
        grid-column: span $i;
      }
    }
  }
}''',
        "explanation": "Modern CSS Grid system with responsive column spans"
    },
    {
        "instruction": "Create a card component with SCSS mixins",
        "language": "scss",
        "code": '''// _card.scss
@mixin card-base {
  background: var(--bg-card, #fff);
  border-radius: 0.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  transition: box-shadow 0.2s ease, transform 0.2s ease;
}

@mixin card-interactive {
  cursor: pointer;
  &:hover {
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    transform: translateY(-2px);
  }
}

.card {
  @include card-base;
  
  &--interactive {
    @include card-interactive;
  }
  
  &__image {
    width: 100%;
    aspect-ratio: 16/9;
    object-fit: cover;
  }
  
  &__content {
    padding: 1.25rem;
  }
  
  &__title {
    font-size: 1.25rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
  }
  
  &__text {
    color: var(--text-secondary, #666);
    line-height: 1.6;
  }
  
  &__footer {
    padding: 1rem 1.25rem;
    border-top: 1px solid var(--border, #eee);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
}''',
        "explanation": "Reusable card component with BEM naming and CSS custom properties"
    },
    {
        "instruction": "Create spacing and margin utilities with SCSS",
        "language": "scss",
        "code": '''// _spacing.scss
$spacer: 1rem;
$spacers: (
  0: 0,
  1: $spacer * 0.25,
  2: $spacer * 0.5,
  3: $spacer,
  4: $spacer * 1.5,
  5: $spacer * 2,
  6: $spacer * 3,
  auto: auto,
);

$sides: (
  t: top,
  r: right,
  b: bottom,
  l: left,
  x: (left, right),
  y: (top, bottom),
);

// Generate margin and padding utilities
@each $prop-short, $prop in (m: margin, p: padding) {
  // All sides
  @each $size, $value in $spacers {
    .#{$prop-short}-#{$size} {
      #{$prop}: $value;
    }
  }
  
  // Individual sides
  @each $side-short, $side in $sides {
    @each $size, $value in $spacers {
      .#{$prop-short}#{$side-short}-#{$size} {
        @if type-of($side) == list {
          @each $s in $side {
            #{$prop}-#{$s}: $value;
          }
        } @else {
          #{$prop}-#{$side}: $value;
        }
      }
    }
  }
}''',
        "explanation": "Generate comprehensive spacing utility classes programmatically"
    },
    {
        "instruction": "Create a modal/dialog component with SCSS",
        "language": "scss",
        "code": '''// _modal.scss
.modal {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.3s, visibility 0.3s;
  z-index: 1000;
  
  &--open {
    opacity: 1;
    visibility: visible;
  }
  
  &__backdrop {
    position: absolute;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(4px);
  }
  
  &__dialog {
    position: relative;
    background: var(--bg-modal, #fff);
    border-radius: 0.75rem;
    max-width: 500px;
    width: 100%;
    max-height: 90vh;
    overflow: auto;
    transform: scale(0.95);
    transition: transform 0.3s;
    
    .modal--open & {
      transform: scale(1);
    }
  }
  
  &__header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1.25rem;
    border-bottom: 1px solid var(--border, #eee);
  }
  
  &__title {
    font-size: 1.25rem;
    font-weight: 600;
  }
  
  &__close {
    background: none;
    border: none;
    font-size: 1.5rem;
    cursor: pointer;
    opacity: 0.5;
    &:hover { opacity: 1; }
  }
  
  &__body { padding: 1.25rem; }
  
  &__footer {
    display: flex;
    gap: 0.75rem;
    justify-content: flex-end;
    padding: 1rem 1.25rem;
    border-top: 1px solid var(--border, #eee);
  }
}''',
        "explanation": "Accessible modal component with backdrop blur and smooth animations"
    },
    {
        "instruction": "Create form input styles with SCSS",
        "language": "scss",
        "code": '''// _forms.scss
$input-border: #ddd;
$input-focus: #3498db;
$input-error: #e74c3c;

@mixin input-base {
  width: 100%;
  padding: 0.75rem 1rem;
  font-size: 1rem;
  border: 1px solid $input-border;
  border-radius: 0.375rem;
  background: var(--bg-input, #fff);
  transition: border-color 0.2s, box-shadow 0.2s;
  
  &:focus {
    outline: none;
    border-color: $input-focus;
    box-shadow: 0 0 0 3px rgba($input-focus, 0.1);
  }
  
  &::placeholder {
    color: #999;
  }
  
  &:disabled {
    background: #f5f5f5;
    cursor: not-allowed;
  }
}

.form-group {
  margin-bottom: 1.25rem;
}

.form-label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.form-input {
  @include input-base;
  
  &--error {
    border-color: $input-error;
    &:focus {
      box-shadow: 0 0 0 3px rgba($input-error, 0.1);
    }
  }
}

.form-select {
  @include input-base;
  appearance: none;
  background-image: url("data:image/svg+xml,%3csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 16 16\'%3e%3cpath fill=\'none\' stroke=\'%23333\' stroke-linecap=\'round\' stroke-linejoin=\'round\' stroke-width=\'2\' d=\'M2 5l6 6 6-6\'/%3e%3c/svg%3e");
  background-repeat: no-repeat;
  background-position: right 0.75rem center;
  background-size: 1rem;
  padding-right: 2.5rem;
}

.form-error {
  color: $input-error;
  font-size: 0.875rem;
  margin-top: 0.25rem;
}''',
        "explanation": "Complete form styling with focus states, error handling, and custom select"
    },
]

# =============================================================================
# ERROR/TROUBLESHOOTING SCENARIOS
# =============================================================================

ERROR_SCENARIOS = [
    {
        "instruction": "SCSS variables not working in calc()",
        "error_type": "syntax_issue",
        "response": {
            "status": "fixable",
            "cause": "SCSS variables need interpolation inside calc()",
            "wrong": "calc($spacing * 2)",
            "correct": "calc(#{$spacing} * 2)",
            "explanation": "SCSS variables in calc() need #{} interpolation. Alternative: use SCSS math directly outside calc() when possible: $spacing * 2. CSS custom properties work directly in calc(): calc(var(--spacing) * 2)."
        }
    },
    {
        "instruction": "Styles are duplicated in compiled CSS",
        "error_type": "optimization",
        "response": {
            "status": "architecture_issue",
            "common_causes": [
                "Using @import instead of @use (imports entire file each time)",
                "Importing partials multiple times in different files",
                "Mixins used where @extend would be better"
            ],
            "solutions": [
                "Use @use with namespaces: @use 'variables' as v;",
                "Create index files with @forward",
                "Use @extend with % placeholders for shared styles",
                "Review import tree for duplicates"
            ]
        }
    },
    {
        "instruction": "CSS specificity wars - styles not applying",
        "error_type": "specificity",
        "response": {
            "status": "architecture_issue",
            "diagnosis": [
                "Check selector specificity (IDs > Classes > Elements)",
                "Check order in stylesheet (later wins if equal specificity)",
                "Look for !important declarations",
                "Check for inline styles in HTML"
            ],
            "solutions": [
                "Flatten specificity with BEM naming",
                "Use CSS Layers: @layer base, components, utilities;",
                "Use :where() for zero-specificity selectors",
                "Avoid IDs for styling, avoid !important",
                "DevTools shows applied/overridden styles"
            ]
        }
    },
    {
        "instruction": "@extend not working across files",
        "error_type": "import_issue",
        "response": {
            "status": "fixable",
            "cause": "@extend can only extend selectors in the same compilation context",
            "solutions": [
                "Ensure extended class is imported before extending file",
                "Use @use to load the file containing the extended class",
                "Consider using a mixin instead - works across files reliably",
                "Use % placeholder selectors in a shared partial"
            ],
            "best_practice": "Prefer mixins for reuse across files, @extend for true inheritance within same file/context"
        }
    },
    {
        "instruction": "SCSS @use not loading styles from partial",
        "error_type": "import_issue",
        "response": {
            "status": "fixable",
            "cause": "@use only loads variables, mixins, and functions - not raw CSS",
            "diagnosis": [
                "Check if partial has actual CSS output or just definitions",
                "Verify the path is correct (omit leading _ and .scss)",
                "@use 'folder/file' not @use 'folder/_file.scss'"
            ],
            "solutions": [
                "Use @forward in index files to re-export",
                "Access variables with namespace: vars.$color",
                "For CSS output, import in main.scss not components"
            ]
        }
    },
    {
        "instruction": "Media queries not working inside SCSS nesting",
        "error_type": "syntax_issue",
        "response": {
            "status": "works_but_unexpected",
            "explanation": "SCSS bubbles media queries to top level in compiled CSS",
            "example_input": ".card { @media (min-width: 768px) { width: 50%; } }",
            "example_output": "@media (min-width: 768px) { .card { width: 50%; } }",
            "tip": "This is expected behavior - nesting is for convenience, output is valid CSS. Use breakpoint mixins for consistency: @include respond(md) { }."
        }
    },
    {
        "instruction": "SCSS map-get returning null",
        "error_type": "runtime_issue",
        "response": {
            "status": "fixable",
            "causes": [
                "Key doesn't exist in map",
                "Key is string but accessing with unquoted value",
                "Typo in key name"
            ],
            "debugging": [
                "@debug $map to see contents",
                "@debug map-keys($map) to see available keys",
                "Check if key is 'red' (string) vs red (color)"
            ],
            "safe_access": "Use map-has-key($map, $key) before map-get, or provide default: map.get($map, $key, $default)"
        }
    },
    {
        "instruction": "Flexbox gap not working in Safari",
        "error_type": "browser_compatibility",
        "response": {
            "status": "fixable",
            "cause": "Safari 14.0 and earlier don't support gap in flexbox (only grid)",
            "solutions": [
                "Use margin-based approach: > * + * { margin-left: 1rem; }",
                "Negative margin on container: margin: -0.5rem; with padding on children",
                "@supports (gap: 1rem) { } for progressive enhancement"
            ],
            "current_status": "Safari 14.1+ (2021) supports flex gap. Check your target browsers."
        }
    },
    {
        "instruction": "CSS animations stuttering or janky",
        "error_type": "performance",
        "response": {
            "status": "fixable",
            "causes": [
                "Animating layout properties (width, height, top, left)",
                "Triggering layout/paint on each frame",
                "Too many simultaneous animations"
            ],
            "solutions": [
                "Use transform and opacity only (GPU accelerated)",
                "Add will-change: transform (sparingly)",
                "Reduce animation complexity",
                "Use requestAnimationFrame for JS animations"
            ],
            "example": "Instead of animating 'left', use transform: translateX()"
        }
    },
]

# =============================================================================
# GENERATOR FUNCTIONS
# =============================================================================

def generate_concept_examples() -> List[Dict]:
    examples = []
    for concept in BASIC_CONCEPTS + ADVANCED_CONCEPTS:
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": concept["question"],
            "response": concept["answer"]
        })
    return examples

def generate_code_examples() -> List[Dict]:
    examples = []
    for ex in CODE_EXAMPLES:
        response = json.dumps({
            "action": "provide_code",
            "language": ex["language"],
            "code": ex["code"],
            "explanation": ex["explanation"]
        }, indent=2)
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": ex["instruction"],
            "response": response
        })
    return examples

def generate_error_examples() -> List[Dict]:
    examples = []
    for scenario in ERROR_SCENARIOS:
        response = scenario["response"].copy()
        response["error_type"] = scenario["error_type"]
        examples.append({
            "system": SYSTEM_PROMPT,
            "instruction": scenario["instruction"],
            "response": json.dumps(response, indent=2)
        })
    return examples

def main():
    DATA_DIR.mkdir(exist_ok=True)
    
    all_examples = []
    
    concept_examples = generate_concept_examples()
    all_examples.extend(concept_examples)
    
    code_examples = generate_code_examples()
    all_examples.extend(code_examples)
    
    error_examples = generate_error_examples()
    all_examples.extend(error_examples)
    
    random.shuffle(all_examples)
    
    output_file = DATA_DIR / "scss_css.jsonl"
    with open(output_file, "w", encoding="utf-8") as f:
        for example in all_examples:
            f.write(json.dumps(example, ensure_ascii=False) + "\n")
    
    print(f"  [OK] Saved {len(all_examples)} examples to {output_file}")

if __name__ == "__main__":
    main()
