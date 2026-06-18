# EcoMentor AI — Accessibility Standards

## Target Level

**WCAG 2.1 AA** — all new code must meet or exceed this level. AAA is encouraged where practical (sufficient contrast, extended audio descriptions).

---

## 1. WCAG Principles (POUR)

| Principle | Requirement | How We Enforce |
|---|---|---|
| **Perceivable** | Content must be presentable to at least one sense. | Alt text on all images; captions for video; colour not used as sole differentiator. |
| **Operable** | UI components must work with multiple input methods. | Full keyboard support; no mouse-dependent interactions; generous target sizes. |
| **Understandable** | Content and navigation must be clear. | Visible labels, error suggestions, predictable layout, plain language. |
| **Robust** | Content must work across assistive tech. | Semantic HTML, valid ARIA, tested with NVDA and VoiceOver. |

---

## 2. Keyboard Navigation

All interactive elements must be reachable and operable **without a mouse**.

### Focus Management

```
Tab order follows visual / logical DOM order.
  ✓ tabindex="-1"  for off-screen / programmatic focus
  ✓ tabindex="0"   for custom interactive elements
  ✗ tabindex > 0   (never use positive tabindex)
```

### Required Behaviours

| Component | Key | Behaviour |
|---|---|---|
| Button / Link | `Enter` or `Space` | Activate |
| Custom checkbox | `Space` | Toggle state |
| Radio group | `↑` / `↓` or `←` / `→` | Move selection |
| Modal / Dialog | `Escape` | Close |
| Select / Combobox | `Enter` or `Space` | Open options |
| Slider | `←` / `→`, `↑` / `↓` | Increment / decrement |
| Tab panel | `Tab` into panel, `←` / `→` switch tabs | Focus stays inside |
| Data table row action | `Enter` | Trigger action |
| Dismissible alert | `Escape` | Dismiss |

### Focus Indicators

- Visible focus ring **always** required — never `outline: none` without a custom replacement.
- Minimum 2 px solid outline with 3:1 contrast against the adjacent background.
- Use `:focus-visible` for mouse-vs-keyboard differentiation.

```css
:focus-visible {
  outline: 2px solid #1a73e8;
  outline-offset: 2px;
}
```

### Skip Links

Every page must have a skip-to-main-content link as the first focusable element:

```html
<a class="skip-link" href="#main-content">Skip to main content</a>
```

---

## 3. Labels

Every form control, button, and interactive widget must have an **accessible name**.

### One Of (Pick One Per Control)

| Method | Example | When To Use |
|---|---|---|
| `<label>` element | `<label for="email">Email</label>` | Visible text label exists |
| `aria-label` | `<button aria-label="Close modal">×</button>` | Icon-only buttons |
| `aria-labelledby` | `<input aria-labelledby="zip-label">` | Label text is elsewhere in DOM |
| `title` (last resort) | `<input title="Search">` | No better option |

### Form Error Labels

- Each invalid field must have `aria-describedby` pointing to an error message element.
- Error messages must be visible **and** programmatically associated.

```html
<label for="email">Email</label>
<input
  id="email"
  type="email"
  aria-describedby="email-error"
  aria-invalid="true"
/>
<p id="email-error" role="alert">Enter a valid email address.</p>
```

---

## 4. ARIA Attributes

Use native HTML semantics first. ARIA is a supplement, not a replacement.

### Allowed ARIA Roles

| Role | Allowed On | Notes |
|---|---|---|
| `banner` | `<header>` (page-level) | One per page |
| `navigation` | `<nav>` | One per `<nav>` |
| `main` | `<main>` | One per page |
| `contentinfo` | `<footer>` (page-level) | One per page |
| `complementary` | `<aside>` | |
| `form` | `<form>` | Only if no native `<form>` |
| `button` | `<div>`, `<span>` | Must add `tabindex="0"` + keyboard handler |
| `dialog` | Modal container | Manage focus trapping |
| `alert` | Dynamic messages | Live region, no focus needed |
| `progressbar` | Loading indicators | Include `aria-valuenow` / `aria-valuemin` / `aria-valuemax` |
| `tablist`, `tab`, `tabpanel` | Tab interface | Manage `aria-selected`, `aria-controls`, `aria-labelledby` |
| `listbox`, `option` | Custom dropdown | Arrow key navigation |
| `switch` | Toggle control | `aria-checked` not `aria-selected` |

### Forbidden ARIA

| Pattern | Reason |
|---|---|
| `role="menu"` for nav links | Users expect OS-style menus; use `navigation` instead |
| `role="alert"` on static text | Only for dynamically-updated content |
| `aria-hidden="true"` on focusable elements | Screen reader can still focus, creating ghost targets |
| WAI-ARIA tree / grid patterns | Overly complex; prefer simpler patterns |

### Live Regions

For auto-updating content (e.g. live carbon footprint calculation):

```html
<div aria-live="polite" aria-atomic="true" id="footprint-result">
  Waiting for input…
</div>
```

| Polite | Assertive | Use case |
|---|---|---|
| `aria-live="polite"` | `aria-live="assertive"` | Polite for most updates; assertive only for critical errors / warnings |

---

## 5. Mobile Responsiveness

### Breakpoints

| Name | Min width | Target |
|---|---|---|
| **Mobile** | 0 | Single column, stacked navigation |
| **Tablet** | 640 px | Two-column layouts, visible nav |
| **Desktop** | 1024 px | Full layout, sidebar |

### Touch Targets

- Minimum tap target: **44 × 44 px** (WCAG 2.5.5).
- No actionable element within 4 px of another (collapse margin/padding).
- Interactive elements must not overlap or shift on interaction.

### Zoom & Scaling

- Never disable `user-scalable=no` on `<meta name="viewport">`.
- Use `rem` / `em` for font sizes — never `px` for type.
- Content must not overflow or require horizontal scrolling at 320 px width.

### Orientation

- Layout must work in both portrait and landscape without loss of functionality.
- Do not lock orientation.

### Touch Gestures

- All swipe / pinch / drag gestures must have a **non-gesture alternative** (buttons, links).
- No critical action depends on hover (hover does not exist on touch devices).

---

## 6. Developer Checklist

Use this checklist per feature / component before marking a PR ready for review.

### HTML / Semantic Structure

- [ ] Page uses landmark elements (`<header>`, `<nav>`, `<main>`, `<footer>`) correctly and uniquely
- [ ] Heading hierarchy is logical (`h1` → `h2` → `h3`, no skips)
- [ ] Lists use `<ul>` / `<ol>` / `<dl>` — not `<div>` with bullets
- [ ] Form controls use `<form>`, `<fieldset>`, `<legend>` where appropriate
- [ ] Tables use `<th>` with `scope` for data tables; layout tables use `role="presentation"`
- [ ] No empty links or buttons
- [ ] `lang` attribute set on `<html>`

### Keyboard

- [ ] All interactive elements are reachable by `Tab`
- [ ] Tab order matches visual order
- [ ] No keyboard traps (focus cannot get stuck)
- [ ] Custom interactive elements handle `Enter`, `Space`, arrows, and `Escape`
- [ ] Skip link present and functional
- [ ] Visible focus indicator on all interactive elements

### Labels & Names

- [ ] Every `<input>`, `<select>`, `<textarea>` has a `<label>` or `aria-label`
- [ ] Icon-only buttons have `aria-label`
- [ ] Error messages are associated via `aria-describedby`
- [ ] Invalid fields have `aria-invalid="true"`

### ARIA

- [ ] ARIA roles, states, and properties used correctly (validate with browser a11y tree)
- [ ] No redundant ARIA (e.g. `role="button"` on a `<button>`)
- [ ] `aria-hidden` not used on focusable elements
- [ ] Dynamic content uses `aria-live` (polite for most, assertive for critical)
- [ ] Modals / dialogs trap focus when open and restore it on close

### Colour & Contrast

- [ ] Text has **4.5:1** contrast ratio (3:1 for large text ≥ 18 px / 14 px bold)
- [ ] Colour is never the only differentiator (use icons, text, patterns)
- [ ] Focus indicators have **3:1** contrast against adjacent background

### Mobile

- [ ] Tap targets ≥ **44 × 44 px**
- [ ] No adjacent tap targets within 4 px of each other
- [ ] Page works at **320 px** width without horizontal scroll
- [ ] Touch gestures have non-gesture alternatives
- [ ] `user-scalable=no` is **not** set on viewport meta
- [ ] Font sizes use `rem` / `em`
- [ ] Works in both portrait and landscape

### Testing

- [ ] Navigated entire feature using only **Tab + Enter**
- [ ] Tested with **NVDA** (Windows) or **VoiceOver** (macOS)
- [ ] Tested on **mobile** (Chrome DevTools device mode + physical device if possible)
- [ ] No axe-core / Lighthouse accessibility violations
- [ ] Form errors announced by screen reader on submission

---

## 7. CI Enforcement

- Lighthouse CI in GitHub Actions blocks PRs with an accessibility score below 90.
- `axe-core` runs on every PR for the affected pages — failures fail the build.
- Manual a11y review required before every production release.

---

## 8. Resources

- [WCAG 2.1 Quick Reference](https://www.w3.org/WAI/WCAG21/quickref/)
- [ARIA Authoring Practices Guide](https://www.w3.org/WAI/ARIA/apg/)
- [axe-core Docs](https://www.deque.com/axe/)
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
