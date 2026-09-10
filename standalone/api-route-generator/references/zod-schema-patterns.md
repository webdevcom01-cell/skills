# Zod Schema Patterns Reference

All Zod validation patterns used in `src/lib/validations.ts`.

## File Location

All schemas go in `src/lib/validations.ts`. Follow the section comment pattern:

```typescript
// ─── EntityName ─────────────────────────────────────────
```

## Basic Patterns

### Required String

```typescript
name: z.string().min(1, "Name is required").max(100)
```

### Optional String

```typescript
description: z.string().max(500).optional()
```

### Long Text

```typescript
systemPrompt: z.string().max(5000).optional()
```

### String with Default

```typescript
model: z.string().default("gpt-4o-mini")
```

### Email

```typescript
email: z.string().email("Invalid email address")
```

### URL

```typescript
url: z.string().url("Must be a valid URL")
```

### Hex Color

```typescript
primaryColor: z.string().regex(/^#[0-9a-fA-F]{6}$/, "Invalid hex color").default("#3b82f6")
```

### Fixed-Length Code

```typescript
token: z.string().length(6, "Code must be 6 digits").regex(/^\d{6}$/, "Code must be numeric")
```

## Number Patterns

### Number with Range and Default

```typescript
temperature: z.number().min(0).max(2).default(0.7)
```

### Coerced Number (from query string)

```typescript
page: z.coerce.number().min(1).default(1)
limit: z.coerce.number().min(1).max(100).default(50)
```

### Integer Range

```typescript
topK: z.number().min(1).max(20).default(5)
```

## Enum Patterns

### Simple Enum

```typescript
role: z.enum(["ADMIN", "EDITOR", "VIEWER"])
```

### Enum with Default

```typescript
position: z.enum(["bottom-right", "bottom-left"]).default("bottom-right")
```

### Literal (for discriminated union)

```typescript
provider: z.literal("saml")
```

## Boolean Patterns

### Boolean with Default

```typescript
isActive: z.boolean().default(false)
```

### Optional Boolean

```typescript
removeBranding: z.boolean().default(false)
```

## Object Patterns

### Nested Object

```typescript
content: z.object({
  nodes: z.array(z.record(z.string(), z.unknown())).max(500, "Too many nodes"),
  edges: z.array(z.record(z.string(), z.unknown())).max(1000, "Too many connections"),
  variables: z.array(z.record(z.string(), z.unknown())).optional(),
})
```

### JSON Catch-All (for config fields)

```typescript
config: z.record(z.string(), z.unknown()).optional().default({})
```

### Nullable Optional

```typescript
customLogo: z.string().nullable().optional()
```

## Array Patterns

### Array of Objects with Min/Max

```typescript
variants: z.array(z.object({
  name: z.string().min(1),
  flowId: z.string().min(1),
  isControl: z.boolean().default(false),
})).min(2, "At least 2 variants are required").max(4)
```

### Record (dynamic keys)

```typescript
trafficSplit: z.record(z.string(), z.number().min(0).max(100))
```

## Discriminated Union

```typescript
export const ssoConfigSchema = z.discriminatedUnion("provider", [
  z.object({
    provider: z.literal("saml"),
    entityId: z.string().min(1, "IdP Entity ID is required"),
    ssoUrl: z.string().url("Must be a valid SSO URL"),
    certificate: z.string().min(1, "X.509 Certificate is required"),
    issuer: z.string().min(1, "Issuer is required"),
    enabled: z.boolean().default(false),
  }),
  z.object({
    provider: z.literal("oidc"),
    clientId: z.string().min(1, "Client ID is required"),
    discoveryUrl: z.string().url("Must be a valid discovery URL"),
    clientSecret: z.string().min(1, "Client Secret is required"),
    issuer: z.string().max(500).optional(),
    enabled: z.boolean().default(false),
  }),
]);
```

## Refinements

### Cross-field Validation

```typescript
export const registerSchema = z
  .object({
    password: z.string().min(8, "Password must be at least 8 characters"),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });
```

## Create/Update Pattern

The standard pattern for CRUD schemas:

```typescript
// ─── Entity ─────────────────────────────────────────────

export const createEntitySchema = z.object({
  name: z.string().min(1, "Name is required").max(100),
  description: z.string().max(500).optional(),
  type: z.enum(["TYPE_A", "TYPE_B"]),
  config: z.record(z.string(), z.unknown()).optional().default({}),
});

export const updateEntitySchema = createEntitySchema.partial();
```

## Type Exports

Always add type exports at the bottom of the file:

```typescript
// ─── Types ──────────────────────────────────────────────

export type CreateEntityInput = z.infer<typeof createEntitySchema>;
export type UpdateEntityInput = z.infer<typeof updateEntitySchema>;
```

## DateTime Patterns

```typescript
expiresAt: z.string().datetime().optional()
from: z.string().optional()  // ISO date string
to: z.string().optional()
```
