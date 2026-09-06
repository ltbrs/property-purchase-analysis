import posthog, { type Properties } from "posthog-js";

const projectToken = process.env.NEXT_PUBLIC_POSTHOG_PROJECT_TOKEN;
const host = process.env.NEXT_PUBLIC_POSTHOG_HOST;
const isConfigured = Boolean(projectToken && host);

type ProductAnalyticsUser = Readonly<{
  id: string;
  authProvider?: string;
}>;

export function initializeProductAnalytics() {
  if (!projectToken || !host) {
    if (process.env.NODE_ENV === "development") {
      const missingVariable = projectToken
        ? "NEXT_PUBLIC_POSTHOG_HOST"
        : "NEXT_PUBLIC_POSTHOG_PROJECT_TOKEN";

      console.error(
        `[product-analytics] ${missingVariable} is missing, so PostHog is disabled.`,
      );
    }
    return;
  }

  try {
    posthog.init(projectToken, {
      api_host: host,
      defaults: "2026-05-30",
      capture_pageview: "history_change",
      capture_pageleave: true,
      save_campaign_params: true,
      save_referrer: true,
      person_profiles: "identified_only",
      autocapture: false,
      capture_exceptions: false,
      disable_session_recording: true,
      debug: process.env.NODE_ENV === "development",
    });
  } catch (error) {
    console.error("[product-analytics] PostHog initialization failed.", error);
  }
}

export function captureProductEvent(event: string, properties?: Properties) {
  if (!isConfigured) return;
  posthog.capture(event, properties);
}

export function identifyProductUser(user: ProductAnalyticsUser) {
  if (!isConfigured) return;
  posthog.identify(user.id, {
    ...(user.authProvider ? { auth_provider: user.authProvider } : {}),
  });
}

export function resetProductAnalytics() {
  if (!isConfigured) return;
  posthog.reset();
}
