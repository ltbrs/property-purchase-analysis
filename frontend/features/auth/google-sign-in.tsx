"use client";

import Script from "next/script";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { createClient } from "@/lib/supabase/client";

type CredentialResponse = Readonly<{
  credential?: string;
}>;

type GoogleIdentity = Readonly<{
  initialize: (options: {
    callback: (response: CredentialResponse) => void;
    client_id: string;
    context: "signin";
    itp_support: boolean;
    nonce: string;
    ux_mode: "popup";
  }) => void;
  renderButton: (
    parent: HTMLElement,
    options: {
      locale: "fr";
      logo_alignment: "left";
      shape: "rectangular";
      size: "large";
      text: "continue_with";
      theme: "outline";
      type: "standard";
      width: number;
    },
  ) => void;
}>;

declare global {
  interface Window {
    google?: {
      accounts: {
        id: GoogleIdentity;
      };
    };
  }
}

type GoogleSignInProps = Readonly<{
  callbackUrl: string;
  clientId?: string;
}>;

async function createNonce() {
  const randomBytes = crypto.getRandomValues(new Uint8Array(32));
  const nonce = btoa(String.fromCharCode(...randomBytes));
  const digest = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(nonce),
  );
  const hashedNonce = Array.from(new Uint8Array(digest), (byte) =>
    byte.toString(16).padStart(2, "0"),
  ).join("");

  return { hashedNonce, nonce };
}

export function GoogleSignIn({ callbackUrl, clientId }: GoogleSignInProps) {
  const router = useRouter();
  const buttonContainer = useRef<HTMLDivElement>(null);
  const [scriptReady, setScriptReady] = useState(false);
  const [buttonReady, setButtonReady] = useState(false);
  const [error, setError] = useState<string>();

  useEffect(() => {
    const googleIdentity = window.google?.accounts.id;
    const container = buttonContainer.current;
    if (!scriptReady || !clientId || !googleIdentity || !container) return;
    const configuredClientId = clientId;
    const identity = googleIdentity;
    const target = container;

    let cancelled = false;

    async function initialize() {
      try {
        const { hashedNonce, nonce } = await createNonce();
        if (cancelled) return;

        identity.initialize({
          client_id: configuredClientId,
          context: "signin",
          ux_mode: "popup",
          nonce: hashedNonce,
          itp_support: true,
          callback: async ({ credential }) => {
            if (!credential) {
              setError("Google n’a pas transmis d’identifiant. Réessayez.");
              return;
            }

            setError(undefined);
            const supabase = createClient();
            const { error: signInError } = await supabase.auth.signInWithIdToken({
              provider: "google",
              token: credential,
              nonce,
            });

            if (signInError) {
              setError("La connexion Google n’a pas abouti. Réessayez.");
              return;
            }

            router.replace(callbackUrl);
            router.refresh();
          },
        });

        target.replaceChildren();
        identity.renderButton(target, {
          type: "standard",
          theme: "outline",
          size: "large",
          text: "continue_with",
          shape: "rectangular",
          logo_alignment: "left",
          locale: "fr",
          width: Math.min(Math.floor(target.clientWidth), 400),
        });
        setButtonReady(true);
      } catch {
        if (!cancelled) {
          setError("La connexion Google est temporairement indisponible.");
        }
      }
    }

    void initialize();
    return () => {
      cancelled = true;
    };
  }, [callbackUrl, clientId, router, scriptReady]);

  return (
    <div className="google-sign-in-block">
      <Script
        onError={() => setError("La connexion Google est temporairement indisponible.")}
        onReady={() => setScriptReady(true)}
        src="https://accounts.google.com/gsi/client?hl=fr"
        strategy="afterInteractive"
      />
      {!buttonReady ? (
        <button className="google-sign-in-loading" disabled type="button">
          Continuer avec Google
        </button>
      ) : null}
      <div
        aria-busy={!buttonReady}
        className={`google-sign-in-container${buttonReady ? " is-ready" : ""}`}
        ref={buttonContainer}
      />
      {!clientId ? (
        <p className="auth-error" role="alert">
          La connexion Google n’est pas configurée.
        </p>
      ) : null}
      {error ? (
        <p className="auth-error" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}
