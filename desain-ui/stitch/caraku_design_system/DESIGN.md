---
name: Caraku Design System
colors:
  surface: '#fcf9f8'
  surface-dim: '#dcd9d9'
  surface-bright: '#fcf9f8'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f6f3f2'
  surface-container: '#f0edec'
  surface-container-high: '#ebe7e7'
  surface-container-highest: '#e5e2e1'
  on-surface: '#1c1b1b'
  on-surface-variant: '#3d4949'
  inverse-surface: '#313030'
  inverse-on-surface: '#f3f0ef'
  outline: '#6d7a79'
  outline-variant: '#bcc9c8'
  surface-tint: '#006a6a'
  primary: '#006a6a'
  on-primary: '#ffffff'
  primary-container: '#0fa3a3'
  on-primary-container: '#003131'
  inverse-primary: '#60d8d8'
  secondary: '#ae3026'
  on-secondary: '#ffffff'
  secondary-container: '#fc6959'
  on-secondary-container: '#690003'
  tertiary: '#815600'
  on-tertiary: '#ffffff'
  tertiary-container: '#c68600'
  on-tertiary-container: '#3e2700'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#7ff5f4'
  primary-fixed-dim: '#60d8d8'
  on-primary-fixed: '#002020'
  on-primary-fixed-variant: '#004f50'
  secondary-fixed: '#ffdad5'
  secondary-fixed-dim: '#ffb4aa'
  on-secondary-fixed: '#410001'
  on-secondary-fixed-variant: '#8c1712'
  tertiary-fixed: '#ffddb1'
  tertiary-fixed-dim: '#ffba4b'
  on-tertiary-fixed: '#291800'
  on-tertiary-fixed-variant: '#624000'
  background: '#fcf9f8'
  on-background: '#1c1b1b'
  surface-variant: '#e5e2e1'
typography:
  display:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '800'
    lineHeight: 40px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '700'
    lineHeight: 32px
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 20px
    fontWeight: '700'
    lineHeight: 28px
  body-lg:
    fontFamily: Be Vietnam Pro
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Be Vietnam Pro
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  label-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.01em
  print:
    fontFamily: Helvetica Neue
    fontSize: 14px
    lineHeight: '1.5'
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  xs: 4px
  sm: 8px
  md: 12px
  lg: 16px
  xl: 24px
  xxl: 32px
  max_width: 46rem
  touch_target: 44px
---

## Brand & Style
The design system for Caraku is built on a foundation of **Warmth, Encouragement, and Clarity**. Aimed at elementary school students, the UI balances educational rigor with a "lucu" (cute) aesthetic to reduce math anxiety. 

The style combines **Soft Minimalism** with **Tactile Elements**. It uses generous whitespace and a warm cream base to create a friendly atmosphere, while high-contrast borders and vibrant action colors ensure the interface remains accessible and easy to navigate for younger users. The presence of a mascot-driven identity (the Owl) should be woven into success states and empty screens to provide emotional support.

## Colors
This design system utilizes a high-contrast, playful palette designed for clarity and emotional feedback. 

- **Primary Action (Teal):** Used for positive progression, "Strong" mastery status, and primary navigation elements.
- **CTA/Error (Coral):** Used for critical actions (New/Save) and indicating "Wrong" status. 
- **Challenge (Amber):** Used for management roles and "Weak" mastery areas to draw attention without the alarm of red.
- **Background Strategy:** Use the Warm Cream (`#FFF8EE`) for the global background to reduce eye strain. Use pure White (`#FFFFFF`) for interactive cards and input areas to make them "pop" from the page.

## Typography
The typography is designed for high legibility and a friendly tone. **Plus Jakarta Sans** is used for headings to provide a modern, rounded, and welcoming feel. **Be Vietnam Pro** is used for body text to ensure comfortable reading during math practice.

- **Scale:** Maintain a 16px base for all body content to accommodate younger readers.
- **Print:** When exporting worksheets, switch to the Print token (Helvetica Neue) to ensure standardized layout and ink efficiency.
- **Weights:** Use Bold (700+) sparingly for headings and emphasized instructions.

## Layout & Spacing
The design system follows a **Mobile-First, Single-Column** philosophy. Content is contained within a 46rem (approx. 736px) max-width to ensure line lengths remain readable and math equations don't stretch excessively.

- **Rhythm:** Use a 4px base unit. Gaps between related items should be `sm` (8px), while sections should be separated by `xl` (24px) or `xxl` (32px).
- **Touch Areas:** Every interactive element (buttons, checkboxes, inputs) must maintain a minimum height/width of `44px` to accommodate developing motor skills.
- **Responsiveness:** Tables and complex data must wrap and stack vertically once the viewport narrows below the `max_width`.

## Elevation & Depth
In this design system, depth is communicated through **Tonal Layering and Physicality** rather than heavy shadows. 

- **Level 0 (Base):** The Warm Cream background.
- **Level 1 (Interactive):** White cards with a subtle 1px border using `border_strong` at 10% opacity. 
- **Level 2 (Focus/Active):** When an element is interacted with, increase the border weight to 2px and use the full `border_strong` color or the `primary` color.
- **Mascot Integration:** The Owl mascot should appear "on top" of the Level 1 cards, occasionally breaking the bounding box to add a sense of playfulness.

## Shapes
Shapes are intentionally soft to evoke a friendly, safe learning environment.

- **Cards:** Use `12px` (radius_card) for all main content containers and math problem sets.
- **Inputs & Buttons:** Use `10px` (radius_md) to give them a distinct, clickable appearance.
- **Diagnosis Pills:** Always use `999px` (radius_pill) to differentiate status indicators from functional buttons.

## Components

### Buttons & CTAs
- **Primary:** Solid Teal (`#0FA3A3`) with white text. Rounded `10px`.
- **Secondary (Coral):** Specifically for "New" or "Save" actions. Use `#FF6B5B`.
- **States:** On press, buttons should "shrink" slightly (scale 0.98) to provide tactile feedback.

### Diagnosis Pills
Small, high-contrast labels used to identify math misconceptions. They use the specific background and text pairings defined in the Colors section (e.g., Konsep, Hitung, Estimasi).

### Input Fields
Large, white boxes with a clear `16px` text size. On focus, the border should thicken to `2px` using the Teal primary color. 

### Cards
All math problems should be housed in a white card with `12px` rounded corners. Use a `16px` or `24px` padding to give the equations "room to breathe."

### Navbar
- **Sticky:** Top-aligned.
- **Structure:** Logo (Owl Icon + "Caraku" Teal Wordmark) on the far left. A single prominent Coral action button on the far right for the "primary next step."

### Tables
Keep borders minimal. On mobile, transition from a horizontal grid to a "Stacked Card" view where each row becomes its own 12px rounded card.