# Plan: Auth, Email Verification, Paywall y Tenant Subdomain Flow

Fecha: 2026-03-23
Estado: en progreso

---

## Decisiones confirmadas

| # | Decisión |
|---|----------|
| 1 | Un usuario = un tenant principal (sin selector de workspace en login) |
| 2 | Paywall: implementar lógica + unit tests ahora; activar cuando Stripe esté configurado |
| 3 | El usuario elige su propio subdomain slug en el registro |
| 4 | Mailhog para email local (SMTP en puerto 1025, UI en 8025) |

---

## Fase 1 — Mailhog + Email Verification Mandatoria

### 1A. Instalar y configurar Mailhog

**Homebrew (dev local):**
```bash
brew install mailhog
mailhog  # → UI en http://localhost:8025
```

**Docker Compose (docker-compose.yml)** — agregar servicio:
```yaml
mailhog:
  image: mailhog/mailhog:latest
  ports:
    - "1025:1025"   # SMTP
    - "8025:8025"   # Web UI
```

**`backend/config/settings/development.py`** — reemplazar console backend:
```python
# Email via Mailhog (SMTP local)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "localhost"
EMAIL_PORT = 1025
EMAIL_USE_TLS = False
EMAIL_USE_SSL = False
```

### 1B. Backend: activar verificación mandatoria

**`backend/config/settings/base.py`**
```python
ACCOUNT_EMAIL_VERIFICATION = "mandatory"  # era "optional"
```

### 1C. Backend: LoginView verifica email antes de emitir tokens

**`backend/apps/authentication/views.py`** — en `LoginView.post()`, después de `authenticate()`:
```python
from allauth.account.models import EmailAddress

if not EmailAddress.objects.filter(user=user, verified=True).exists():
    return Response(
        {"code": "email_not_verified", "detail": "Please verify your email address."},
        status=status.HTTP_403_FORBIDDEN,
    )
```

Nota: Google OAuth no pasa por LoginView → allauth marca email verified automáticamente → sin fricción.

### 1D. Backend: endpoint resend verification

**`backend/apps/authentication/views.py`** — nuevo `ResendVerificationView`:
```
POST /api/v1/auth/resend-verification/
Body: { "email": "user@example.com" }
Throttle: ResendVerificationThrottle (1 request / 5 min por IP)
Returns: 200 siempre (no revelar si el email existe)
```

Lógica:
```python
from allauth.account.models import EmailAddress
from allauth.account.utils import send_email_confirmation

ea = EmailAddress.objects.filter(email=email, verified=False).first()
if ea:
    send_email_confirmation(request, ea.user, signup=False)
return Response({"detail": "If that email exists and is unverified, a new link was sent."})
```

**`backend/apps/authentication/throttles.py`** — crear:
```python
class ResendVerificationThrottle(AnonRateThrottle):
    rate = "1/5min"
    scope = "resend_verification"
```

Registrar en `settings/base.py` REST_FRAMEWORK throttle rates:
```python
"resend_verification": "1/5min",
```

**`backend/apps/authentication/urls.py`** — agregar:
```python
path("resend-verification/", ResendVerificationView.as_view(), name="resend-verification"),
```

### 1E. Frontend: EmailVerificationGate

**`frontend/src/components/auth/email-verification-gate.tsx`** — crear:
- Mensaje: "Check your inbox for {email}"
- Botón "Resend email" con cooldown de 5 minutos
  - Persistir `lastResendAt` en `localStorage` con key `resend_verification_ts`
  - Mostrar cuenta regresiva: "Resend in 4:32"
  - Al hacer click: `POST /api/v1/auth/resend-verification/` con el email
- Link "Use a different account" → vuelve al login limpiando el estado

**`frontend/src/components/auth/login-form.tsx`** — manejar 403:
```typescript
// En el catch del login:
if (err.code === "email_not_verified") {
  setVerificationEmail(email);  // mostrar EmailVerificationGate en lugar del form
  return;
}
```

El gate se renderiza dentro de la misma página de login (no ruta separada).

### 1F. Tests

**`backend/apps/authentication/tests/test_email_verification.py`** — crear:
- `test_login_unverified_returns_403`
- `test_login_verified_returns_tokens`
- `test_resend_verification_returns_200_always`
- `test_resend_verification_throttle`

---

## Fase 2 — Registro: Slug Elegido por el Usuario

### 2A. Backend: validar slug disponible

**`backend/apps/authentication/views.py`** — nuevo `CheckSlugView`:
```
GET /api/v1/auth/check-slug/?slug=acme
Returns: {"available": true} o {"available": false, "suggestion": "acme-1"}
```

Validación del slug:
- Regex: `^[a-z0-9][a-z0-9-]{1,48}[a-z0-9]$` (3-50 chars, solo lowercase + guiones, no empieza/termina en guión)
- Reservados: `www`, `api`, `app`, `admin`, `mail`, `static`, `media`, `dev`, `staging`, `prod`
- Si no disponible: sugerir `{slug}-1`, `{slug}-2`, etc.

### 2B. Backend: RegisterSerializer acepta slug + company_name

**`backend/apps/authentication/serializers.py`** — modificar:
```python
company_name = serializers.CharField(max_length=200, required=True, min_length=2)
slug = serializers.RegexField(
    r'^[a-z0-9][a-z0-9-]{1,48}[a-z0-9]$',
    required=True,
    error_messages={"invalid": "Slug must be 3-50 chars, lowercase letters, numbers, hyphens only."}
)

def validate_slug(self, value):
    RESERVED = {"www", "api", "app", "admin", "mail", "static", "media", "dev", "staging", "prod"}
    if value in RESERVED:
        raise serializers.ValidationError("That slug is reserved.")
    if Tenant.objects.filter(slug=value).exists():
        raise serializers.ValidationError("That slug is already taken.")
    return value
```

En `save()`: usar `company_name` para `tenant.name` y `slug` para `tenant.slug` directamente.

### 2C. Backend: RegisterView retorna tenant_slug

**`backend/apps/authentication/views.py`** — modificar response de RegisterView:
```python
{
    "access": access,
    "tenant_slug": tenant.slug,   # NUEVO
    "user": { "id", "email", "first_name", "last_name" }
}
```

### 2D. Backend: LoginView retorna tenant_slug

**`backend/apps/authentication/views.py`** — modificar response de LoginView:
```python
membership = TenantMembership.objects.select_related("tenant").filter(user=user).first()
tenant_slug = membership.tenant.slug if membership else None

# Agregar al response:
"tenant_slug": tenant_slug,
```

### 2E. Backend: /users/me/ incluye tenant_slug

**`backend/apps/users/serializers.py`** — en `UserSerializer`:
```python
tenant_slug = serializers.SerializerMethodField()

def get_tenant_slug(self, obj):
    membership = obj.tenantmembership_set.select_related("tenant").first()
    return membership.tenant.slug if membership else None
```

### 2F. Frontend: RegisterForm con slug + company_name

**`frontend/src/components/auth/register-form.tsx`** — agregar:
- Campo "Workspace name" (company_name) — primer campo
- Campo "Workspace URL" con preview en tiempo real:
  - Input: `[slug]`
  - Preview: `{slug}.tudominio.com`
  - Auto-sugerencia: mientras escribe company_name, auto-popula slug (slugify)
  - Check de disponibilidad en tiempo real con debounce 500ms → `GET /api/v1/auth/check-slug/`
  - Indicador visual: ✓ disponible / ✗ no disponible / sugerencia automática
- Validación client-side: regex + reservados

### 2G. Tests

**`backend/apps/authentication/tests/test_registration.py`** — crear/expandir:
- `test_register_creates_tenant_with_chosen_slug`
- `test_register_duplicate_slug_returns_400`
- `test_register_reserved_slug_returns_400`
- `test_check_slug_available`
- `test_check_slug_taken_returns_suggestion`
- `test_register_response_includes_tenant_slug`
- `test_login_response_includes_tenant_slug`

---

## Fase 3 — Redirect al Subdominio del Tenant

### 3A. Frontend: utilidad tenant.ts

**`frontend/src/lib/tenant.ts`** — crear:
```typescript
export function getTenantUrl(slug: string, path = "/dashboard"): string {
  const { protocol, port } = window.location;
  const baseDomain = process.env.NEXT_PUBLIC_BASE_DOMAIN || "localhost";
  const portSuffix = port && port !== "80" && port !== "443" ? `:${port}` : "";
  return `${protocol}//${slug}.${baseDomain}${portSuffix}${path}`;
}

export function getCurrentTenantSlug(): string | null {
  if (typeof window === "undefined") return null;
  const baseDomain = process.env.NEXT_PUBLIC_BASE_DOMAIN || "localhost";
  const host = window.location.hostname;
  if (host === baseDomain || host === "localhost" || !host.includes(".")) return null;
  return host.split(".")[0] || null;
}
```

**`frontend/.env` + `frontend/.env.example`** — agregar:
```
NEXT_PUBLIC_BASE_DOMAIN=localhost
```

### 3B. Post-registro: redirect a subdominio

**`frontend/src/components/auth/register-form.tsx`**:
```typescript
const { user, access, tenant_slug } = await register(formData);
setAuth(user, access, tenant_slug);
toast.success(`Welcome, ${user.first_name}!`);
window.location.href = getTenantUrl(tenant_slug, "/dashboard");
```

### 3C. Post-login: redirect si no está en el subdominio correcto

**`frontend/src/components/auth/login-form.tsx`**:
```typescript
const { user, access, tenant_slug } = await login(email, password);
setAuth(user, access, tenant_slug);
toast.success(`Welcome back, ${user.first_name}!`);

if (tenant_slug && getCurrentTenantSlug() !== tenant_slug) {
  window.location.href = getTenantUrl(tenant_slug, callbackUrl || "/dashboard");
} else {
  router.push(callbackUrl || "/dashboard");
}
```

### 3D. Auth store: guardar tenantSlug + cookie

**`frontend/src/stores/auth-store.ts`** — modificar:
```typescript
interface AuthState {
  tenantSlug: string | null;  // NUEVO
}

setAuth: (user, accessToken, tenantSlug?) => {
  // Cookie para el middleware de Next.js:
  document.cookie = `tenant_slug=${tenantSlug ?? ""}; path=/; SameSite=Strict; max-age=604800`;
  set({ user, accessToken, isAuthenticated: true, tenantSlug: tenantSlug ?? null });
  // cookie auth_session ya existente se mantiene
}

logout: () => {
  document.cookie = "tenant_slug=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT";
  // ...resto del logout
}
```

En `initialize()`: al obtener el perfil de `/users/me/`, guardar `tenantSlug`:
```typescript
const profile = await getProfile();   // ya incluye tenant_slug (Fase 2E)
set({ user: profile, tenantSlug: profile.tenant_slug ?? null });
document.cookie = `tenant_slug=${profile.tenant_slug ?? ""}; path=/; SameSite=Strict; max-age=604800`;
```

### 3E. Tests

**`frontend/src/lib/__tests__/tenant.test.ts`** — crear:
- `getTenantUrl` construye URL correcta en localhost
- `getTenantUrl` construye URL correcta en producción
- `getCurrentTenantSlug` retorna null en root domain
- `getCurrentTenantSlug` extrae slug de subdominio

---

## Fase 4 — Middleware Frontend: Bloquear Root Domain

### 4A. middleware.ts — redirigir a subdominio si usuario autenticado en root domain

**`frontend/src/middleware.ts`** — agregar al inicio:
```typescript
const baseDomain = process.env.NEXT_PUBLIC_BASE_DOMAIN || "localhost";
const hostname = request.headers.get("host") || "";
// Detectar root domain (con o sin puerto)
const rootHostnames = [baseDomain, `${baseDomain}:3000`, "localhost", "localhost:3000"];
const isRootDomain = rootHostnames.some(h => hostname === h);

const isAuthenticated = request.cookies.has("auth_session");
const tenantSlug = request.cookies.get("tenant_slug")?.value;

// Usuario autenticado en root domain intentando acceder a ruta protegida
if (isAuthenticated && isRootDomain && isProtectedPath && tenantSlug) {
  const port = hostname.includes(":") ? `:${hostname.split(":")[1]}` : "";
  const redirectUrl = `${request.nextUrl.protocol}//${tenantSlug}.${baseDomain}${port}${request.nextUrl.pathname}`;
  return NextResponse.redirect(redirectUrl);
}
```

Si no hay `tenant_slug` cookie pero hay `auth_session` → dejar pasar (evitar redirect loop en edge cases).

---

## Fase 5 — Paywall Middleware (Opcional, activar con Stripe)

### 5A. Feature flag REQUIRE_SUBSCRIPTION

**`backend/config/settings/base.py`**:
```python
FEATURE_FLAGS = {
    ...
    "REQUIRE_SUBSCRIPTION": config("FEATURE_REQUIRE_SUBSCRIPTION", cast=bool, default=False),
}
```

**`backend/apps/core/features.py`**:
```python
@classmethod
def require_subscription(cls) -> bool:
    return cls.get_feature("REQUIRE_SUBSCRIPTION")
```

### 5B. Backend: SubscriptionPaywallMiddleware

**`backend/apps/subscriptions/middleware.py`** — crear:
```python
PAYWALL_EXEMPT_PREFIXES = (
    "/health",
    "/tacomate",         # admin URL (dinámico pero cubrimos el default)
    "/api/v1/auth/",
    "/api/v1/features/",
    "/api/v1/subscriptions/",  # para poder comprar
    "/api/docs/",
    "/api/schema/",",
)

class SubscriptionPaywallMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not FeatureFlags.require_subscription():
            return self.get_response(request)

        # Solo aplicar en requests autenticados a tenants con tenant context
        if not hasattr(request, "tenant") or request.tenant is None:
            return self.get_response(request)

        path = request.path
        if any(path.startswith(p) for p in PAYWALL_EXEMPT_PREFIXES):
            return self.get_response(request)

        if not request.path.startswith("/api/"):
            return self.get_response(request)

        # Verificar autenticación (JWT)
        # Solo bloquear requests autenticados (anon pasa, JWT inválido lo maneja auth)
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return self.get_response(request)

        # Verificar suscripción activa del tenant
        from apps.subscriptions.models import Subscription
        has_active = Subscription.objects.filter(
            tenant=request.tenant,
            status__in=["active", "trialing", "cancelling"]
        ).exists()

        if not has_active:
            return JsonResponse(
                {"code": "subscription_required", "detail": "An active subscription is required."},
                status=402
            )

        return self.get_response(request)
```

Registrar en **`MIDDLEWARE`** de `base.py`, después de `TenantMiddleware`:
```python
"apps.subscriptions.middleware.SubscriptionPaywallMiddleware",
```

### 5C. Frontend: 402 handler en API client

**`frontend/src/lib/api.ts`** — en el handler de errores HTTP:
```typescript
if (response.status === 402) {
  // Disparar evento global para que el protected layout muestre el gate
  window.dispatchEvent(new CustomEvent("subscription_required"));
  throw new ApiError("subscription_required", "An active subscription is required.", 402);
}
```

**`frontend/src/app/(protected)/layout.tsx`** — escuchar el evento:
```typescript
useEffect(() => {
  const handler = () => setSubscriptionRequired(true);
  window.addEventListener("subscription_required", handler);
  return () => window.removeEventListener("subscription_required", handler);
}, []);

if (subscriptionRequired) return <SubscriptionRequiredGate />;
```

**`frontend/src/components/billing/subscription-required-gate.tsx`** — crear:
- Mensaje: "You need an active subscription to use {APP_NAME}"
- Botón "View plans" → `/pricing`
- Botón "Manage billing" → abre customer portal

### 5D. Tests

**`backend/apps/subscriptions/tests/test_paywall_middleware.py`** — crear:
- `test_paywall_disabled_passes_all_requests`
- `test_paywall_no_tenant_passes`
- `test_paywall_exempt_paths_pass` (auth, features, subscriptions)
- `test_paywall_no_subscription_returns_402`
- `test_paywall_active_subscription_passes`
- `test_paywall_trialing_subscription_passes`
- `test_paywall_cancelled_subscription_returns_402`

---

## Archivos nuevos

| Archivo | Propósito |
|---------|-----------|
| `frontend/src/lib/tenant.ts` | Utilidades subdominio |
| `frontend/src/components/auth/email-verification-gate.tsx` | Gate "verifica tu email" |
| `backend/apps/authentication/throttles.py` | Throttle resend verification |
| `backend/apps/subscriptions/middleware.py` | Paywall middleware |
| `backend/apps/authentication/tests/test_email_verification.py` | Tests Fase 1 |
| `backend/apps/authentication/tests/test_registration.py` | Tests Fase 2 |
| `frontend/src/lib/__tests__/tenant.test.ts` | Tests Fase 3 |
| `backend/apps/subscriptions/tests/test_paywall_middleware.py` | Tests Fase 5 |

## Archivos modificados

| Archivo | Cambio |
|---------|--------|
| `docker-compose.yml` | Agregar servicio mailhog |
| `backend/config/settings/base.py` | email_verification=mandatory, REQUIRE_SUBSCRIPTION flag |
| `backend/config/settings/development.py` | EMAIL_BACKEND smtp → mailhog |
| `backend/apps/authentication/views.py` | LoginView: check verified + tenant_slug. RegisterView: tenant_slug. ResendVerificationView. CheckSlugView |
| `backend/apps/authentication/serializers.py` | RegisterSerializer: company_name + slug |
| `backend/apps/authentication/urls.py` | resend-verification, check-slug |
| `backend/apps/users/serializers.py` | UserSerializer: tenant_slug |
| `frontend/src/components/auth/login-form.tsx` | Manejar 403, redirect subdominio |
| `frontend/src/components/auth/register-form.tsx` | company_name, slug, redirect subdominio |
| `frontend/src/lib/auth.ts` | register() + login() retornan tenant_slug |
| `frontend/src/stores/auth-store.ts` | tenantSlug state + cookie |
| `frontend/src/middleware.ts` | Redirect root domain → subdominio |
| `frontend/.env` + `.env.example` | NEXT_PUBLIC_BASE_DOMAIN |

---

## Orden de implementación

```
Fase 1 (Mailhog + email verification)
    ↓
Fase 2 (slug en registro)           ← puede correr en paralelo con Fase 1
    ↓
Fase 3 (redirect subdominio)        ← depende de Fase 2
    ↓
Fase 4 (middleware root domain)     ← depende de Fase 3
    ↓
Fase 5 (paywall)                    ← independiente, activar con Stripe
```
