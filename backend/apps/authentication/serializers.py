"""
Authentication serializers.
"""

import logging

from better_profanity import profanity
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

User = get_user_model()
logger = logging.getLogger(__name__)

RESERVED_SLUGS = frozenset(
    {
        # Existing
        "www",
        "api",
        "app",
        "admin",
        "mail",
        "static",
        "media",
        "dev",
        "staging",
        "prod",
        "help",
        "support",
        "blog",
        "status",
        "dashboard",
        "billing",
        "auth",
        "invite",
        # Infrastructure / DNS
        "ns",
        "ns1",
        "ns2",
        "ns3",
        "ns4",
        "mx",
        "smtp",
        "imap",
        "pop",
        "pop3",
        "ftp",
        "sftp",
        "ssh",
        "vpn",
        "dns",
        "cdn",
        "ssl",
        "tls",
        "proxy",
        "gateway",
        "relay",
        "node",
        "server",
        "host",
        "hosting",
        # Web / app services
        "login",
        "signin",
        "signup",
        "register",
        "logout",
        "logoff",
        "account",
        "accounts",
        "profile",
        "settings",
        "preferences",
        "console",
        "portal",
        "panel",
        "cp",
        "webmail",
        "email",
        "calendar",
        "password",
        "reset",
        # Company / brand sensitive
        "official",
        "secure",
        "security",
        "trust",
        "verify",
        "verification",
        "confirm",
        "confirmation",
        "noreply",
        "no-reply",
        "info",
        "contact",
        "sales",
        "legal",
        "compliance",
        "abuse",
        "postmaster",
        "hostmaster",
        "webmaster",
        "team",
        "company",
        "corporate",
        # Payments / billing
        "pay",
        "payment",
        "payments",
        "checkout",
        "invoice",
        "invoices",
        "subscription",
        "subscriptions",
        "stripe",
        # DevOps / monitoring / environments
        "ci",
        "cd",
        "test",
        "testing",
        "debug",
        "production",
        "demo",
        "sandbox",
        "preview",
        "internal",
        "monitoring",
        "metrics",
        "grafana",
        "sentry",
        "logs",
        "logging",
        "health",
        "ping",
        "uptime",
        # Docs / marketing
        "docs",
        "documentation",
        "wiki",
        "kb",
        "faq",
        "news",
        "updates",
        "changelog",
        "roadmap",
        "marketing",
        "promo",
        "landing",
        "home",
        # API / protocols
        "graphql",
        "grpc",
        "ws",
        "wss",
        "webhooks",
        "oauth",
        "sso",
        "saml",
        "auth0",
        "v1",
        "v2",
        "v3",
        "v4",
        # Generic / reserved names
        "root",
        "null",
        "undefined",
        "localhost",
        "local",
        "default",
        "system",
        "tmp",
        "temp",
        "new",
        # Phishing / impersonation risk
        "customer-support",
        "helpdesk",
        "help-desk",
        "customer-service",
        "customerservice",
        "tech-support",
        "techsupport",
        "account-security",
        "accountsecurity",
        "account-verify",
        "account-verification",
        "password-reset",
        "passwordreset",
        "billing-support",
        "billing-help",
        "payment-verify",
        "payment-verification",
        "invoice-payment",
        "invoice-verify",
        "signin-secure",
        "secure-login",
        "securelogin",
        "login-verify",
        "verify-account",
        "update-billing",
        "update-payment",
        "suspended",
        "suspension",
        "restricted",
        "alert",
        "alerts",
        "warning",
        "warnings",
        "notice",
        "notices",
        "urgent",
        "critical",
        "important",
        # Trust & safety / legal risk
        "fraud",
        "chargeback",
        "dispute",
        "disputes",
        "dmca",
        "copyright",
        "trademark",
        "privacy",
        "terms",
        "tos",
        "gdpr",
        "ccpa",
        "report",
        "reports",
        "reporting",
        "takedown",
        "law",
        "lawyer",
        "attorney",
        "lawsuit",
        "police",
        "law-enforcement",
        # Infrastructure squatting / confusion
        "assets",
        "asset",
        "files",
        "file",
        "uploads",
        "upload",
        "images",
        "img",
        "js",
        "css",
        "backup",
        "backups",
        "db",
        "database",
        "cache",
        "queue",
        "worker",
        "workers",
        "cron",
        "jobs",
        "job",
        "tasks",
        "task",
        "storage",
        "store",
        "bucket",
        "buckets",
        "config",
        "configs",
        "env",
        "envs",
        "secrets",
        "deploy",
        "deployment",
        "deployments",
        "release",
        "releases",
        "build",
        "builds",
        "pipeline",
        "pipelines",
        # Third-party service names (impersonation)
        "github",
        "gitlab",
        "bitbucket",
        "slack",
        "discord",
        "teams",
        "zoom",
        "google",
        "microsoft",
        "apple",
        "amazon",
        "aws",
        "twilio",
        "sendgrid",
        "mailchimp",
        "mailgun",
        "resend",
        "cloudflare",
        "fastly",
        "akamai",
        "heroku",
        "vercel",
        "netlify",
        "render",
        "datadog",
        "newrelic",
        "pagerduty",
        "opsgenie",
        "jira",
        "confluence",
        "notion",
        "linear",
        "asana",
        "intercom",
        "zendesk",
        "freshdesk",
        "hubspot",
        "salesforce",
        "marketo",
        "twitch",
        "youtube",
        "twitter",
        "facebook",
        "instagram",
        "linkedin",
        # Business / org squatting
        "enterprise",
        "business",
        "startup",
        "agency",
        "partner",
        "partners",
        "partnership",
        "reseller",
        "resellers",
        "affiliate",
        "affiliates",
        "referral",
        "referrals",
        "investor",
        "investors",
        "press",
        "media",
        "careers",
        "jobs",
        "hiring",
        "hr",
        "about",
        "about-us",
        "aboutus",
        "pricing",
        "plans",
        "upgrade",
        "onboarding",
        "welcome",
        "getting-started",
        "feedback",
        "survey",
        "surveys",
        "forum",
        "forums",
        "community",
        "communities",
        # Admin / ops confusion
        "superadmin",
        "super-admin",
        "sysadmin",
        "sys-admin",
        "root-admin",
        "god",
        "owner",
        "ops",
        "operations",
        "devops",
        "infra",
        "infrastructure",
        "platform",
        "engineering",
        "product",
        "design",
        "ceo",
        "cto",
        "cfo",
        "coo",
        # AI / ML
        "ai",
        "ml",
        "llm",
        "nlp",
        "gpt",
        "chatgpt",
        "openai",
        "anthropic",
        "claude",
        "gemini",
        "copilot",
        "mistral",
        "llama",
        "deepseek",
        "perplexity",
        "cohere",
        "huggingface",
        "replicate",
        "together",
        "chat",
        "chatbot",
        "bot",
        "assistant",
        "agent",
        "agents",
        "autopilot",
        "automate",
        "automation",
        "neural",
        "model",
        "models",
        "inference",
        "training",
        "embedding",
        "embeddings",
        "vector",
        "vectors",
        "rag",
        "fine-tune",
        "finetune",
        "prompt",
        "prompts",
        "ai-assistant",
        "ai-agent",
        "ai-chat",
        "ai-support",
        # Payment processors
        "paypal",
        "venmo",
        "braintree",
        "adyen",
        "klarna",
        "affirm",
        "afterpay",
        "wise",
        "transferwise",
        # Cloud providers
        "azure",
        "gcp",
        "digitalocean",
        "linode",
        "hetzner",
        "vultr",
        "ovh",
        # Dev tools / registries
        "docker",
        "kubernetes",
        "k8s",
        "terraform",
        "jenkins",
        "circleci",
        "travisci",
        "npm",
        "pypi",
        # Social / comms platforms
        "telegram",
        "whatsapp",
        "signal",
        "reddit",
        "tiktok",
        "snapchat",
        "pinterest",
        "medium",
        # Financial / crypto
        "bank",
        "crypto",
        "bitcoin",
        "ethereum",
        "wallet",
        "exchange",
        "finance",
        "financial",
        "invest",
        "investing",
        # Government / authority
        "gov",
        "government",
        "irs",
        "sec",
        "fbi",
        "fda",
        # Misc / squatting
        "example",
        "sample",
        "placeholder",
        "live-chat",
        "livechat",
        "chat-support",
    }
)


class RegisterSerializer(serializers.Serializer):
    """User registration — creates user + tenant, or joins via invite_token."""

    # Workspace fields — required only when not using an invite_token
    company_name = serializers.CharField(
        max_length=200, min_length=2, required=False, allow_blank=True
    )
    slug = serializers.RegexField(
        r"^[a-z0-9][a-z0-9-]{1,48}[a-z0-9]$",
        required=False,
        allow_blank=True,
        error_messages={
            "invalid": (
                "Slug must be 3–50 characters: lowercase letters, numbers, and hyphens only. "
                "Cannot start or end with a hyphen."
            )
        },
    )
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
    )
    first_name = serializers.CharField(max_length=150, required=False, default="")
    last_name = serializers.CharField(max_length=150, required=False, default="")
    invite_token = serializers.CharField(required=False, write_only=True)

    def validate_email(self, value: str) -> str:
        normalized = value.strip().lower()
        if User.objects.filter(email__iexact=normalized).exists():
            raise serializers.ValidationError(
                _("A user with that email already exists.")
            )
        return normalized

    def validate_password(self, value: str) -> str:
        validate_password(value)
        return value

    def validate_slug(self, value: str) -> str:
        from apps.tenants.models import Tenant

        if value in RESERVED_SLUGS:
            raise serializers.ValidationError(_("That workspace URL is reserved."))
        if profanity.contains_profanity(value):
            raise serializers.ValidationError(_("That workspace URL is not allowed."))
        if Tenant.objects.filter(slug=value).exists():
            raise serializers.ValidationError(_("That workspace URL is already taken."))
        return value

    def validate(self, attrs: dict) -> dict:
        invite_token = attrs.get("invite_token")
        if invite_token:
            from apps.teams.models import Invitation

            try:
                invitation = Invitation.objects.select_related("tenant").get(
                    token=invite_token
                )
            except (Invitation.DoesNotExist, ValueError):
                raise serializers.ValidationError(
                    {"invite_token": _("Invalid invitation token.")}
                )
            if not invitation.is_valid:
                raise serializers.ValidationError(
                    {
                        "invite_token": _(
                            "This invitation has expired or already been used."
                        )
                    }
                )
            attrs["_invitation"] = invitation
        else:
            if not attrs.get("company_name"):
                raise serializers.ValidationError(
                    {"company_name": _("This field is required.")}
                )
            if not attrs.get("slug"):
                raise serializers.ValidationError(
                    {"slug": _("This field is required.")}
                )
        return attrs

    def create(self, validated_data: dict) -> tuple:
        from apps.tenants.models import Tenant, TenantMembership

        email = validated_data["email"]
        password = validated_data["password"]
        first_name = validated_data.get("first_name", "").strip()
        last_name = validated_data.get("last_name", "").strip()
        invitation = validated_data.pop("_invitation", None)

        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )

        if invitation:
            # Join existing tenant via invitation
            TenantMembership.objects.get_or_create(
                user=user,
                tenant=invitation.tenant,
                defaults={"role": invitation.role},
            )
            invitation.accepted = True
            from django.utils import timezone

            invitation.accepted_at = timezone.now()
            invitation.save(update_fields=["accepted", "accepted_at"])
            tenant = invitation.tenant
        else:
            # Create new tenant
            company_name = validated_data["company_name"].strip()
            slug = validated_data["slug"]
            tenant = Tenant.objects.create(name=company_name, slug=slug, owner=user)
            TenantMembership.objects.create(
                user=user,
                tenant=tenant,
                role=TenantMembership.Role.ADMIN,
            )

        # Invited users have already verified their email by clicking the link
        from allauth.account.models import EmailAddress

        request = self.context.get("request")
        if invitation:
            EmailAddress.objects.create(
                user=user, email=email, primary=True, verified=True
            )
        else:
            ea = EmailAddress.objects.create(
                user=user, email=email, primary=True, verified=False
            )
            ea.send_confirmation(request, signup=True)

        logger.info("New user registered: %s (tenant: %s)", email, tenant.slug)
        return user, tenant


class LoginSerializer(serializers.Serializer):
    """Authenticate with email + password."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    def validate(self, attrs: dict) -> dict:
        email = attrs.get("email", "").strip().lower()
        password = attrs.get("password", "")

        user = authenticate(
            request=self.context.get("request"),
            username=email,
            password=password,
        )

        if not user:
            raise serializers.ValidationError(
                _("Unable to log in with provided credentials."),
                code="authorization",
            )

        if not user.is_active:
            raise serializers.ValidationError(
                _("User account is disabled."),
                code="authorization",
            )

        attrs["user"] = user
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    """Request a password-reset email."""

    email = serializers.EmailField()

    def validate_email(self, value: str) -> str:
        return value.strip().lower()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Confirm a password reset with token + new password."""

    token = serializers.CharField()
    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={"input_type": "password"},
    )

    def validate_new_password(self, value: str) -> str:
        validate_password(value)
        return value
