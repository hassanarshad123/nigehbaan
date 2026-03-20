# Design System

## Nigehbaan — Dark Intelligence Theme

**Version:** 1.0
**Date:** March 19, 2026

The Nigehbaan visual language is built around a dark intelligence theme: serious, authoritative, and respectful. The platform presents sensitive data about child trafficking — the design must convey gravity without sensationalism, provide clarity without overwhelming, and remain functional on low-end devices over poor network connections.

---

## 1. Color Palette

### Base Colors (Dark Theme)

| Token | Hex | Usage |
|-------|-----|-------|
| `--bg-primary` | `#0F172A` | Page background, map container background |
| `--bg-surface` | `#1E293B` | Cards, panels, popups, sidebar |
| `--bg-surface-hover` | `#263548` | Card hover state, interactive surface elements |
| `--border-default` | `#334155` | Card borders, dividers, input borders |
| `--border-focus` | `#475569` | Input focus state, active tab indicator |
| `--text-primary` | `#F8FAFC` | Headings, primary text, important labels |
| `--text-secondary` | `#94A3B8` | Body text, descriptions, secondary labels |
| `--text-muted` | `#64748B` | Placeholder text, disabled states, timestamps |

### Accent Colors (Data & Status)

| Token | Hex | Usage |
|-------|-----|-------|
| `--alert-red` | `#EF4444` | Critical hotspots, high-risk indicators, border crossings |
| `--alert-red-bg` | `#EF444420` | Red background tint for alert cards |
| `--amber` | `#F59E0B` | Warning indicators, moderate risk, public report pins |
| `--amber-bg` | `#F59E0B20` | Amber background tint |
| `--cyan` | `#06B6D4` | Data points, informational indicators, missing children markers |
| `--cyan-bg` | `#06B6D420` | Cyan background tint |
| `--emerald` | `#10B981` | Positive trends, high conviction rates, resolved status |
| `--emerald-bg` | `#10B98120` | Emerald background tint |
| `--kiln-orange` | `#F97316` | Brick kiln markers, bonded labor indicators |
| `--route-magenta` | `#EC4899` | Trafficking route lines, cross-border flow indicators |

### Heat Map Gradient

For incident density heat maps, use a gradient from low to high intensity:

```
Low density:   #06B6D4 (cyan, 30% opacity)
Medium:        #F59E0B (amber, 50% opacity)
High:          #EF4444 (red, 70% opacity)
Critical:      #DC2626 (dark red, 90% opacity)
```

### Choropleth Scales

**Vulnerability Score (0-100):**
```
0-20:    #10B981 (emerald)
21-40:   #84CC16 (lime)
41-60:   #F59E0B (amber)
61-80:   #F97316 (orange)
81-100:  #EF4444 (red)
```

**Poverty Index:**
```
Low poverty:     #7C3AED20 (light purple)
High poverty:    #7C3AED (full purple)
```

**Conviction Rate:**
```
Low conviction:  #EF4444 (red — impunity is bad)
High conviction: #10B981 (green — enforcement is good)
```

---

## 2. Typography

### Font Families

| Language | Font | Weight Range | Fallback |
|----------|------|-------------|----------|
| English | Inter | 400, 500, 600, 700 | system-ui, -apple-system, sans-serif |
| Urdu (RTL) | Noto Nastaliq Urdu | 400, 700 | "Jameel Noori Nastaleeq", serif |
| Monospace | JetBrains Mono | 400, 500 | "Fira Code", monospace |

### Type Scale

| Token | Size | Weight | Line Height | Usage |
|-------|------|--------|-------------|-------|
| `--text-display` | 48px / 3rem | 700 | 1.1 | Landing page hero headline |
| `--text-h1` | 32px / 2rem | 700 | 1.2 | Page titles |
| `--text-h2` | 24px / 1.5rem | 600 | 1.3 | Section headings |
| `--text-h3` | 20px / 1.25rem | 600 | 1.4 | Card titles, panel headings |
| `--text-h4` | 16px / 1rem | 600 | 1.4 | Sub-section headings |
| `--text-body` | 16px / 1rem | 400 | 1.6 | Body text, descriptions |
| `--text-body-sm` | 14px / 0.875rem | 400 | 1.5 | Secondary text, table cells |
| `--text-caption` | 12px / 0.75rem | 400 | 1.4 | Timestamps, metadata, chart labels |
| `--text-counter` | 40px / 2.5rem | 700 | 1.0 | Animated stat counters |

### Urdu Typography Notes

- Urdu text uses Noto Nastaliq Urdu with `direction: rtl` and `text-align: right`
- Line height for Nastaliq script should be at least 2.0 due to vertical character extensions
- District names displayed in both English and Urdu: "Lahore (لاہور)"
- Navigation labels in Urdu use 16px minimum for readability of Nastaliq script

---

## 3. Map Styling

### Base Map

- **Style:** `mapbox://styles/mapbox/dark-v11`
- **Background:** Dark blue-gray that blends with `--bg-primary`
- **Labels:** Muted white for country/province names, hidden at district level (our boundary layer replaces them)

### Custom Map Layers

| Layer | Geometry | Visual Style |
|-------|----------|-------------|
| District Boundaries | Polygon (stroke) | 1px `#334155` stroke, no fill, 2px on hover |
| Incident Heat Map | Point aggregated to heatmap | Cyan -> Amber -> Red gradient, radius 20-40px |
| Brick Kilns | Point (circle) | `#F97316` fill, 4-8px radius proportional to `population_1km`, 60% opacity |
| Border Crossings | Point (triangle icon) | `#EF4444` triangle, 12px, pulsing animation for high-vulnerability |
| Trafficking Routes | LineString | `#EC4899` dashed line, 2-4px width proportional to evidence confidence |
| Missing Children | Point (circle) | `#06B6D4` circle, 6px, pulsing animation (CSS keyframe) |
| Poverty Choropleth | Polygon (fill) | Purple gradient, 20-60% opacity |
| School Dropout Choropleth | Polygon (fill) | Orange gradient, 20-60% opacity |
| Flood Extent | Polygon (fill) | `#3B82F6` blue, 20% opacity |
| Public Reports | Point (pin icon) | `#F59E0B` pin marker, 10px |
| Conviction Rate Choropleth | Polygon (fill) | Green (high) to Red (low), 30% opacity |

---

## 4. Component Specifications

### Cards

```
Background:     var(--bg-surface) (#1E293B)
Border:         1px solid var(--border-default) (#334155)
Border Radius:  8px (var(--radius-md))
Padding:        16px (var(--space-4))
Shadow:         none (flat design on dark backgrounds)
Hover:          background shifts to var(--bg-surface-hover)
                border-color shifts to var(--border-focus)
                subtle glow: box-shadow: 0 0 20px rgba(6, 182, 212, 0.08)
Transition:     all 200ms ease-in-out
```

### Sidebar Panel (Map Layer Controls)

```
Background:     rgba(30, 41, 59, 0.95)  (semi-transparent surface)
Backdrop Filter: blur(12px)
Width:          320px (desktop), full-width bottom sheet (mobile)
Border Right:   1px solid var(--border-default)
Padding:        16px
```

### District Popup (Map Click)

```
Background:     var(--bg-surface)
Border:         1px solid var(--border-default)
Border Radius:  8px
Max Width:      280px
Padding:        12px
Shadow:         0 4px 24px rgba(0, 0, 0, 0.4)
Arrow:          8px CSS triangle pointing to clicked location
Content:        District name (h3), P-code (caption), population (body),
                incident count with trend arrow, vulnerability score badge,
                "View Full Profile" link (cyan underline)
```

### Stat Counter

```
Font:           var(--text-counter) (40px, weight 700)
Color:          var(--text-primary)
Animation:      Count up from 0 to target value over 1.5 seconds
                Uses requestAnimationFrame for smooth 60fps animation
                Easing: ease-out (fast start, gentle finish)
Suffix:         "+" appended for approximate values
Label:          Below counter in var(--text-caption), var(--text-secondary)
```

### Form Inputs (Dark Theme)

```
Background:     var(--bg-primary) (#0F172A)
Border:         1px solid var(--border-default) (#334155)
Border Radius:  6px (var(--radius-sm))
Padding:        10px 12px
Color:          var(--text-primary)
Placeholder:    var(--text-muted)
Focus:          border-color: var(--cyan) (#06B6D4)
                box-shadow: 0 0 0 2px rgba(6, 182, 212, 0.2)
                outline: none
Error:          border-color: var(--alert-red) (#EF4444)
Disabled:       opacity: 0.5, cursor: not-allowed
```

### Buttons

**Primary:**
```
Background:     var(--cyan) (#06B6D4)
Color:          #0F172A (dark text on cyan)
Border Radius:  6px
Padding:        10px 20px
Font Weight:    600
Hover:          brightness(1.1)
Active:         brightness(0.9)
Disabled:       opacity: 0.5
```

**Secondary:**
```
Background:     transparent
Border:         1px solid var(--border-default)
Color:          var(--text-primary)
Hover:          background: var(--bg-surface-hover)
```

**Danger:**
```
Background:     var(--alert-red) (#EF4444)
Color:          white
Hover:          brightness(1.1)
```

### Badges / Tags

```
Background:     accent color at 20% opacity (e.g., #EF444420)
Color:          accent color at full (e.g., #EF4444)
Border Radius:  9999px (pill shape)
Padding:        2px 10px
Font Size:      var(--text-caption) (12px)
Font Weight:    500
```

### Data Tables

```
Header BG:      var(--bg-primary)
Header Color:   var(--text-secondary)
Header Weight:  600
Row BG:         var(--bg-surface)
Row Hover:      var(--bg-surface-hover)
Border:         1px solid var(--border-default) between rows
Cell Padding:   10px 16px
Font Size:      var(--text-body-sm) (14px)
```

---

## 5. Animations

### Pulsing Markers (Missing Children, Critical Alerts)

```css
@keyframes pulse-marker {
  0% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.8);
    opacity: 0.4;
  }
  100% {
    transform: scale(2.4);
    opacity: 0;
  }
}

.marker-pulse {
  animation: pulse-marker 2s ease-out infinite;
}
```

The pulse uses a secondary semi-transparent ring that expands outward from the marker center. The marker itself remains static — only the ring animates.

### Counter Animation

```typescript
function animateCounter(element: HTMLElement, target: number, duration: number = 1500): void {
  const start = 0;
  const startTime = performance.now();

  function update(currentTime: number): void {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);

    // Ease-out cubic: fast start, gentle finish
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = Math.floor(start + (target - start) * eased);

    element.textContent = current.toLocaleString();

    if (progress < 1) {
      requestAnimationFrame(update);
    }
  }

  requestAnimationFrame(update);
}
```

Counters trigger when they enter the viewport (Intersection Observer). They animate once and hold the final value.

### Route Animation (Trafficking Routes)

Using Deck.gl's PathLayer with `getDashArray` and animated `dashOffset`:

```typescript
const routeLayer = new PathLayer({
  data: routes,
  getPath: (d) => d.coordinates,
  getColor: [236, 72, 153],        // --route-magenta
  getWidth: 3,
  getDashArray: [8, 4],
  dashJustified: true,
  // Animate dash offset for flowing effect
  transitions: {
    getDashArray: { duration: 1000, type: 'interpolation' }
  }
});
```

### Page Transitions

- Content sections fade in with `opacity: 0 -> 1` over 300ms when entering viewport
- Cards use a subtle slide-up: `transform: translateY(8px) -> translateY(0)` over 300ms
- No aggressive animations — the data is serious, the interface should be calm

---

## 6. Spacing Scale

Based on a 4px grid system:

| Token | Value | Usage |
|-------|-------|-------|
| `--space-0` | 0px | Reset |
| `--space-1` | 4px | Tight spacing (badge padding, icon margins) |
| `--space-2` | 8px | Compact spacing (between related items) |
| `--space-3` | 12px | Standard gap (form field spacing) |
| `--space-4` | 16px | Card padding, section gap |
| `--space-5` | 20px | Comfortable spacing |
| `--space-6` | 24px | Section padding |
| `--space-8` | 32px | Large section gap |
| `--space-10` | 40px | Page section dividers |
| `--space-12` | 48px | Major section breaks |
| `--space-16` | 64px | Page top/bottom padding |

---

## 7. Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `--radius-sm` | 6px | Buttons, inputs, small cards |
| `--radius-md` | 8px | Cards, panels, popups |
| `--radius-lg` | 12px | Modal dialogs, large panels |
| `--radius-xl` | 16px | Hero sections, feature cards |
| `--radius-full` | 9999px | Badges, pills, avatar circles |

---

## 8. Responsive Breakpoints

| Breakpoint | Width | Layout Behavior |
|-----------|-------|-----------------|
| `mobile` | < 640px | Single column, bottom sheet for map controls, stacked dashboard charts, full-width forms |
| `tablet` | 640px - 1024px | Two-column dashboard, collapsible sidebar on map |
| `desktop` | 1024px - 1440px | Full sidebar on map, three-column dashboard grid |
| `wide` | > 1440px | Max content width 1440px, centered |

### Map-Specific Responsive Behavior

- **Desktop:** Full-screen map with 320px sidebar panel on left, popup cards appear next to clicked features
- **Tablet:** Map fills screen, sidebar collapses to icon strip, expands on tap
- **Mobile:** Map fills screen, layer controls move to bottom sheet (swipe up to reveal), popups appear as bottom cards

### Dashboard Responsive Behavior

- **Desktop:** 3-column grid for chart cards, filter bar at top
- **Tablet:** 2-column grid
- **Mobile:** Single column, stacked charts, filter drawer (slide in from right)

---

## 9. Accessibility

### Contrast Ratios

All text meets WCAG 2.1 AA minimum contrast ratios:

| Text | Background | Ratio | Pass |
|------|-----------|-------|------|
| `#F8FAFC` (primary) | `#0F172A` (bg) | 15.4:1 | AAA |
| `#F8FAFC` (primary) | `#1E293B` (surface) | 11.5:1 | AAA |
| `#94A3B8` (secondary) | `#0F172A` (bg) | 5.6:1 | AA |
| `#94A3B8` (secondary) | `#1E293B` (surface) | 4.2:1 | AA (large text) |
| `#0F172A` (dark) | `#06B6D4` (cyan button) | 7.8:1 | AAA |

### Chart Accessibility

- All charts include `aria-label` describing the data being visualized
- Recharts renders SVG with accessible group labels
- Color is never the sole indicator — patterns/shapes supplement color coding
- Data tables provided as alternative to charts for screen reader users

### Interactive Elements

- All interactive elements have visible focus rings (`box-shadow` outline in cyan)
- Tab order follows logical reading order
- Map interactions have keyboard alternatives (arrow keys for pan, +/- for zoom)
- Skip-to-content link at top of every page

---

## 10. Iconography

Use Lucide React icons (included with shadcn/ui) for all UI icons:

| Icon | Usage |
|------|-------|
| `MapPin` | Location markers, district selection |
| `AlertTriangle` | Warning indicators, high-risk badges |
| `Shield` | Security, protection, verified status |
| `Search` | Search bar, filter inputs |
| `Filter` | Filter controls, layer toggles |
| `Download` | Export buttons |
| `FileText` | Reports, court judgments |
| `Phone` | Helpline numbers |
| `Eye` / `EyeOff` | Layer visibility toggle |
| `ChevronRight` | Navigation, expansion |
| `BarChart3` | Dashboard, statistics |
| `Globe` | Map view, geographic data |

Icons are rendered at 16px (small), 20px (default), or 24px (large) with `currentColor` stroke for theme consistency.

---

*This design system is the visual specification for all Nigehbaan interfaces. For component implementation, refer to the frontend codebase. For architecture details, see [ARCHITECTURE.md](ARCHITECTURE.md).*
