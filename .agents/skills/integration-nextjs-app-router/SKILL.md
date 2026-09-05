---
name: integration-nextjs-app-router
description: Integrate or maintain PostHog analytics in a Next.js App Router application, including client instrumentation, server-side events, feature flags, and authenticated user identity. Do not use for generic analytics work or Pages Router-only implementations.
---

# PostHog in Next.js App Router

Implement PostHog as a small, privacy-conscious part of the existing Next.js application. Preserve the project's current routing, authentication, environment-variable, and deployment conventions. Do not add a proxy, session replay, feature flags, or new analytics dependencies unless the requested change requires them.

## Before changing code

1. Inspect the existing PostHog setup, event calls, authentication flow, environment variables, and Content Security Policy.
2. Read [the Next.js integration reference](references/next-js.md) for client initialization, server-side use, and framework-specific constraints.
3. For any work involving login, logout, person properties, or client-to-server attribution, also read [the user-identification reference](references/identify-users.md).
4. Check the installed package versions and their local documentation before using framework or SDK APIs that may have changed.

## Implementation rules

- Initialize browser analytics in the repository's established App Router client-instrumentation location. Keep the initialization client-side.
- Use a stable authenticated user ID as PostHog's `distinct_id`. Do not use email as the primary ID when a canonical ID exists, and never use a shared placeholder.
- Identify the user once their authenticated identity is available, then reset PostHog on logout.
- Use the same canonical ID for client and server events. If forwarding tracing headers to a separate backend, configure only the backend hostname and never treat those headers as authorization credentials.
- Keep server-only event capture and flag evaluation on the server. Flush or shut down short-lived server clients after use, as described in the reference.
- Capture only product-analytics data needed for the stated purpose. Do not send property documents, extracted document text, addresses, credentials, access tokens, or other sensitive personal data to PostHog.
- Follow consent and privacy requirements already present in the application. Do not enable recording or identify anonymous visitors without an explicit product and legal basis.
- Keep event names and properties consistent with existing analytics conventions. Use structured, bounded properties rather than free-form text.

## Verification

Before finishing, verify that the relevant client and server code type-checks, authentication and logout do not merge users, and no secret or sensitive document content is included in analytics payloads. Report any analytics behavior that cannot be verified locally.

## References

- [Next.js integration](references/next-js.md): client SDK setup, App Router server SDK usage, feature flags, CSP, proxying, and tracing headers.
- [Identify users](references/identify-users.md): `distinct_id` selection, identification timing, logout reset, person properties, and cross-platform identity.
