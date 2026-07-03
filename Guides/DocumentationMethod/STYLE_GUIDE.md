# Style guide – Markdown conventions

This file documents available visual conventions for the Nordic NeTEx Profile guides,
powered by the Entur-branded docsify theme.

---

## Callouts (flexible-alerts plugin)

```markdown
> [!TIP]
> A helpful tip. Rendered with navy left border.

> [!NOTE]
> Informational note. Rendered with blue left border.

> [!WARNING]
> Something to watch out for. Rendered with amber left border.

> [!IMPORTANT]
> Critical information. Rendered with coral left border.
```

---

## Transport mode badges

Use inline HTML for transport mode context:

```html
<span class="badge train">Train</span>
<span class="badge bus">Bus</span>
<span class="badge metro">Metro</span>
<span class="badge tram">Tram</span>
<span class="badge ferry">Ferry</span>
<span class="badge plane">Air</span>
```

**Result:** <span class="badge train">Train</span> <span class="badge bus">Bus</span> <span class="badge metro">Metro</span> <span class="badge tram">Tram</span> <span class="badge ferry">Ferry</span> <span class="badge plane">Air</span>

---

## Status badges

```html
<span class="badge status-required">Required</span>
<span class="badge status-optional">Optional</span>
<span class="badge status-new">New in v3</span>
<span class="badge status-changed">Changed</span>
```

**Result:** <span class="badge status-required">Required</span> <span class="badge status-optional">Optional</span> <span class="badge status-new">New in v3</span> <span class="badge status-changed">Changed</span>

---

## Profile level markers

Show whether an element is from the minimal (MIN) or Nordic (NP) profile level:

```html
<span class="profile-level min">MIN</span>
<span class="profile-level np">NP</span>
```

**Result:** <span class="profile-level min">MIN</span> <span class="profile-level np">NP</span>

---

## Example usage in a guide

```markdown
## ServiceJourney <span class="badge train">Train</span> <span class="badge bus">Bus</span>

| Element | Type | Card. | Level |
|---------|------|-------|-------|
| `Name` | `MultilingualString` | 0:1 | <span class="profile-level np">NP</span> |
| `DepartureTime` | `xsd:time` | 1:1 | <span class="profile-level min">MIN</span> |

> [!TIP]
> When modelling a `ServiceJourney`, always include `passingTimes` –
> the profile requires at least departure time for the first stop.
```

---

## Text conventions (Entur style)

- **Sentence case** everywhere (headings, buttons, labels)
- **24-hour time:** 07:42, 14:15
- **En-dash** for ranges/pairs: Oslo S – Bergen, 07:42 – 14:15
- **Middle dot** as list separator: 3 changes · 6 h 32 min
- No emoji in production UI (emoji in guides for scannability is acceptable)

---

## Colors reference

| Token | Hex | Usage |
|-------|-----|-------|
| Navy | `#181C56` | Primary text, headings, links |
| Coral | `#FF5959` | Accent only (active states, highlights) |
| Train | `#181C56` | Rail mode |
| Bus | `#6A1B9A` | Bus mode |
| Metro | `#E65100` | Metro mode |
| Tram | `#2E7D32` | Tram mode |
| Ferry | `#0277BD` | Water mode |
| Plane | `#8B1A1A` | Air mode |
