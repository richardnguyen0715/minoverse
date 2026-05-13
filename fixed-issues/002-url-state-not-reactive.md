# Issue 002 — URL Search Param Not Reactive: Filter Ignores Sidebar Navigation

**Category:** Frontend / Next.js  
**Fixed in:** `35b5fd0`  
**Files changed:** `apps/web/src/app/resources/page.tsx`, `apps/web/src/app/notes/page.tsx`

---

## Symptom

Clicking a sidebar link like "Daily Notes" changes the URL to `/resources?type=daily_note`, but:

- The filter tab bar still shows the previous selection (or "All")
- The resource list does not re-fetch with the new type
- The content appears frozen until a full page reload

---

## Root Cause

The page used `useState` seeded from `useSearchParams()`:

```typescript
// ❌ BROKEN
const searchParams = useSearchParams()
const initialType = searchParams.get('type') as ResourceType | null

// useState only uses the initial value — ignores all future URL changes
const [selectedType, setSelectedType] = useState<ResourceType | null>(initialType)

useEffect(() => {
  listResources(selectedType ? { resource_type: selectedType } : undefined)
    .then(setResources)
}, [selectedType])  // depends on state, not URL
```

`useState(initialType)` is evaluated **once** at mount. When Next.js's client-side router updates the URL (soft navigation), the component does **not** remount — it just re-renders. `useSearchParams()` returns the new params but `selectedType` state is already frozen.

---

## Fix

Remove the local state entirely. Derive `selectedType` directly from `useSearchParams()` on every render. Handle tab clicks via `router.push()` to update the URL, which automatically causes `useSearchParams()` to return the new value:

```typescript
// ✅ FIXED
const searchParams = useSearchParams()
const router = useRouter()
const selectedType = searchParams.get('type') as ResourceType | null  // reactive

useEffect(() => {
  listResources(selectedType ? { resource_type: selectedType } : undefined)
    .then(setResources)
}, [selectedType])  // re-runs whenever URL changes

const setType = useCallback((type: ResourceType | null) => {
  const params = new URLSearchParams(searchParams.toString())
  if (type) params.set('type', type)
  else params.delete('type')
  router.push(`/resources?${params.toString()}`)
}, [router, searchParams])
```

---

## Prevention Checklist

- [ ] **Never** use `useState(searchParams.get('x'))` as a source of truth for URL-driven state. The URL is the source of truth; read it directly.
- [ ] Tab/filter components driven by URL should: read via `useSearchParams()` and write via `router.push()`.
- [ ] Wrap pages that use `useSearchParams()` in `<Suspense>` (Next.js requirement for static export compatibility).
- [ ] The rule of thumb: if a filter/tab is reflected in the URL, the URL controls it — not local state.
