# Frontend Design System Summary

## Overview
The frontend uses a **minimal, modern, clean design system** built on **shadcn/ui** components with **Tailwind CSS** styling, following a flat UI philosophy with neutral colors and consistent spacing.

---

## Core Technologies

### UI Component Library
- **shadcn/ui** (default style)
- **React Server Components** (RSC) enabled
- **TypeScript** for type safety

### Styling
- **Tailwind CSS** for utility-first styling
- **CSS Variables** for theming (HSL color format)
- **Base color**: Slate

### Typography
- **Font**: Inter (from `next/font/google`)
- Applied globally via `layout.tsx`

---

## Color System

### Light Mode (Default)
Uses CSS variables with HSL values:

- **Background**: `--background: 0 0% 100%` (white)
- **Foreground**: `--foreground: 222.2 47.4% 11.2%` (dark slate)
- **Card**: `--card: 0 0% 100%` (white)
- **Primary**: `--primary: 222.2 47.4% 11.2%` (dark slate)
- **Secondary**: `--secondary: 210 40% 96.1%` (light gray)
- **Muted**: `--muted: 210 40% 96.1%` (light gray)
- **Muted Foreground**: `--muted-foreground: 215.4 16.3% 46.9%` (medium gray)
- **Destructive**: `--destructive: 0 84.2% 60.2%` (red)
- **Border**: `--border: 214.3 31.8% 91.4%` (light gray)
- **Ring**: `--ring: 222.2 47.4% 11.2%` (dark slate)

### Dark Mode
Dark mode variables are defined but not actively used. Follows the same structure with inverted values.

### Usage Pattern
- **Semantic tokens only**: Use `text-foreground`, `text-muted-foreground`, `bg-card`, `border-border`, etc.
- **No hardcoded colors**: Avoid `text-gray-800`, `bg-white`, etc.
- **Opacity modifiers**: Use `/50`, `/10` for subtle effects (e.g., `border-destructive/50`, `bg-destructive/10`)

---

## Typography

### Font Weights
- **All text**: `font-normal` (400 weight)
- **No bold or medium**: Reduced from `font-medium` to maintain minimal aesthetic

### Font Sizes
- **Headings**: `text-lg` (18px)
- **Body text**: `text-sm` (14px)
- **Small text**: `text-xs` (12px)

### Text Colors
- **Primary text**: `text-foreground`
- **Secondary/muted text**: `text-muted-foreground`
- **Destructive text**: `text-destructive-foreground`

---

## Spacing System

### Container & Layout
- **Container**: `container mx-auto` (centered, responsive)
- **Max width**: `max-w-7xl` (1280px)
- **Padding**: `px-4` (horizontal), `py-12` (vertical sections)
- **Section spacing**: `mb-8` (between major sections)

### Component Spacing
- **Gaps**: `gap-2` (small gaps between elements)
- **Padding**: `px-2 py-0.5` (minimal labels), `p-0` (tables), `pt-6` (card content)
- **Margins**: `mb-4`, `mb-8` (vertical spacing)

---

## Component Patterns

### Buttons
- **Variants**: `default`, `outline`, `ghost`
- **Sizes**: `sm`, `icon`
- **Small buttons**: `h-8 px-2 text-xs` (refresh buttons)
- **Icons**: `h-3 w-3` (small icons in buttons)

### Cards
- **Usage**: Wrap content sections (tables, error messages)
- **Padding**: `p-0` for tables, `pt-6` for content
- **Borders**: Use semantic border colors (`border-destructive/50` for errors)

### Tables
- **Structure**: shadcn/ui `Table`, `TableHeader`, `TableBody`, `TableRow`, `TableCell`, `TableHead`
- **Alignment**: `text-right` for numeric columns
- **Padding**: `py-1` for compact rows
- **Headers**: `text-foreground` for all headers

### Labels/Badges
- **Minimal labels**: 
  ```tsx
  <span className="inline-flex items-center px-2 py-0.5 text-xs font-normal text-foreground border border-border rounded-md bg-card">
  ```
- **Used for**: Status indicators, numeric values, tags
- **Styling**: Single-pixel border, rounded corners (`rounded-md`), white/transparent background

### Separators
- **Component**: shadcn/ui `Separator`
- **Spacing**: `my-12` (between major sections)

---

## Visual Style Principles

### Flat UI
- **No shadows**: Except shadcn default component shadows
- **No gradients**: Solid colors only
- **No fancy borders**: Simple 1px borders

### Neutral Palette
- **Primary colors**: Gray/slate scale
- **Accent**: Minimal use of primary color
- **Destructive**: Red for errors only

### Border Radius
- **Consistent**: `rounded-md` (0.5rem / 8px) everywhere
- **No pill shapes**: Avoid `rounded-full`

### Icons
- **Library**: `lucide-react`
- **Sizes**: `h-3 w-3` (small), `h-4 w-4` (default), `h-6 w-6` (larger)
- **Common icons**: `RefreshCw`, `Loader2`, `Info`, `X`

---

## Layout Patterns

### Page Structure
```tsx
<div className="container mx-auto py-12 px-4 max-w-7xl">
  {/* Error messages */}
  {/* Section header with title and action button */}
  {/* Content (Card with Table) */}
  <Separator className="my-12" />
  {/* Next section */}
</div>
```

### Section Headers
```tsx
<div className="mb-8 flex justify-between items-center">
  <h2 className="text-lg font-normal text-foreground">Section Title</h2>
  <Button variant="outline" size="sm" className="h-8 px-2 text-xs">
    Action
  </Button>
</div>
```

### Table Structure
- Wrapped in `Card` with `CardContent className="p-0"`
- Header row with `TableHead` elements
- Optional totals/averages row below header
- Data rows with `TableCell` elements
- Empty state with appropriate `colSpan`

---

## Interactive States

### Loading States
- **Spinner**: `Loader2` icon with `animate-spin`
- **Button disabled**: `disabled` prop on Button component
- **Table visibility**: Hidden during initial load, visible during refresh

### Error States
- **Error card**: `border-destructive/50 bg-destructive/10`
- **Error text**: `text-destructive-foreground`
- **Retry button**: `border-destructive/50 text-destructive hover:bg-destructive/10`

### Hover States
- **Buttons**: Default shadcn hover states
- **List items**: `hover:bg-muted` for interactive lists

---

## Design Philosophy

### Minimalism
- **Clean**: Remove unnecessary visual noise
- **Calm**: Neutral colors, plenty of whitespace
- **Flat**: No shadows, gradients, or heavy chrome
- **Consistent**: Same patterns throughout

### Accessibility
- **Semantic HTML**: Proper use of headings, tables, buttons
- **Color contrast**: shadcn defaults ensure WCAG compliance
- **Interactive elements**: Clear hover and focus states

### Responsiveness
- **Container**: Responsive container with max-width
- **Padding**: Responsive horizontal padding (`px-4`)
- **Tables**: Horizontal scroll on small screens (default table behavior)

---

## Key Rules

1. **Always use semantic color tokens** (`text-foreground`, `bg-card`, etc.)
2. **Never use hardcoded colors** (`text-gray-800`, `bg-white`, etc.)
3. **Font weight**: Always `font-normal` (never `font-medium` or `font-bold`)
4. **Border radius**: Always `rounded-md` (never `rounded-full` or custom values)
5. **Spacing**: Use consistent scale (4, 6, 8, 12, 16)
6. **Icons**: Use `lucide-react` only
7. **Components**: Use shadcn/ui components when available
8. **Labels**: Use minimal label pattern for status indicators and numbers

---

## Example Patterns

### Minimal Label
```tsx
<span className="inline-flex items-center px-2 py-0.5 text-xs font-normal text-foreground border border-border rounded-md bg-card">
  {value}
</span>
```

### Section Header
```tsx
<div className="mb-8 flex justify-between items-center">
  <h2 className="text-lg font-normal text-foreground">Title</h2>
  <Button variant="outline" size="sm" className="h-8 px-2 text-xs">
    <RefreshCw className="h-3 w-3" />
    Refresh
  </Button>
</div>
```

### Error Display
```tsx
<Card className="mb-8 border-destructive/50 bg-destructive/10">
  <CardContent className="pt-6">
    <p className="text-sm text-destructive-foreground mb-4">Error: {error}</p>
    <Button variant="outline" size="sm" className="border-destructive/50 text-destructive hover:bg-destructive/10">
      Retry
    </Button>
  </CardContent>
</Card>
```

