"use client";

import Link from "next/link";
import { useActionState, useState } from "react";

import {
  signInWithGoogle,
  signInWithPassword,
  signUpWithPassword,
} from "@/features/auth/actions";
import { productRoutes } from "@/lib/routes";

type AuthFormProps = Readonly<{
  callbackUrl: string;
  routeError?: string;
}>;

function GoogleLogo() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24">
      <path fill="#4285F4" d="M21.6 12.2c0-.7-.1-1.5-.2-2.2H12v4h5.4a4.7 4.7 0 0 1-2 3v2.7h3.4c2-1.9 2.8-4.5 2.8-7.5Z" />
      <path fill="#34A853" d="M12 22c2.7 0 5-.9 6.8-2.3L15.4 17c-.9.6-2.1 1-3.4 1-2.6 0-4.8-1.8-5.6-4.1H3v2.7A10.3 10.3 0 0 0 12 22Z" />
      <path fill="#FBBC05" d="M6.4 13.9A6 6 0 0 1 6.1 12c0-.7.1-1.3.3-1.9V7.4H3A10 10 0 0 0 2 12c0 1.7.4 3.2 1 4.6l3.4-2.7Z" />
      <path fill="#EA4335" d="M12 6c1.5 0 2.8.5 3.8 1.5l3-2.9A10 10 0 0 0 3 7.4l3.4 2.7A6 6 0 0 1 12 6Z" />
    </svg>
  );
}

export function AuthForm({ callbackUrl, routeError }: AuthFormProps) {
  const [mode, setMode] = useState<"sign-in" | "sign-up">("sign-in");
  const [signInState, signInAction, signInPending] = useActionState(
    signInWithPassword,
    {},
  );
  const [signUpState, signUpAction, signUpPending] = useActionState(
    signUpWithPassword,
    {},
  );
  const state = mode === "sign-in" ? signInState : signUpState;
  const pending = mode === "sign-in" ? signInPending : signUpPending;

  return (
    <div className="auth-options">
      {routeError ? (
        <p className="auth-error" role="alert">
          {routeError === "confirmation"
            ? "Le lien de confirmation est invalide ou a expiré."
            : "La connexion n’a pas abouti. Vous pouvez réessayer."}
        </p>
      ) : null}

      <form action={signInWithGoogle}>
        <input name="callbackUrl" type="hidden" value={callbackUrl} />
        <button className="google-sign-in" type="submit">
          <GoogleLogo />
          <span>Continuer avec Google</span>
        </button>
      </form>

      <div className="auth-divider" aria-hidden="true">
        <span>ou</span>
      </div>

      <div className="auth-tabs" role="tablist" aria-label="Mode de connexion">
        <button
          aria-selected={mode === "sign-in"}
          className={mode === "sign-in" ? "is-active" : undefined}
          onClick={() => setMode("sign-in")}
          role="tab"
          type="button"
        >
          Se connecter
        </button>
        <button
          aria-selected={mode === "sign-up"}
          className={mode === "sign-up" ? "is-active" : undefined}
          onClick={() => setMode("sign-up")}
          role="tab"
          type="button"
        >
          Créer un compte
        </button>
      </div>

      <form
        action={mode === "sign-in" ? signInAction : signUpAction}
        className="auth-fields"
      >
        <input name="callbackUrl" type="hidden" value={callbackUrl} />
        {mode === "sign-up" ? (
          <label>
            <span>Nom</span>
            <input
              autoComplete="name"
              maxLength={200}
              name="name"
              placeholder="Votre nom"
              type="text"
            />
          </label>
        ) : null}
        <label>
          <span>Adresse e-mail</span>
          <input
            autoComplete="email"
            inputMode="email"
            name="email"
            placeholder="vous@exemple.fr"
            required
            type="email"
          />
        </label>
        <label>
          <span>Mot de passe</span>
          <input
            autoComplete={mode === "sign-in" ? "current-password" : "new-password"}
            minLength={mode === "sign-up" ? 12 : undefined}
            name="password"
            required
            type="password"
          />
        </label>
        {mode === "sign-up" ? (
          <label>
            <span>Confirmer le mot de passe</span>
            <input
              autoComplete="new-password"
              minLength={12}
              name="passwordConfirmation"
              required
              type="password"
            />
          </label>
        ) : null}

        {state.error ? (
          <p className="auth-error" role="alert">
            {state.error}
          </p>
        ) : null}
        {state.success ? (
          <p className="auth-success" role="status">
            {state.success}
          </p>
        ) : null}

        <button className="auth-submit" disabled={pending} type="submit">
          {pending
            ? "Veuillez patienter…"
            : mode === "sign-in"
              ? "Se connecter"
              : "Créer mon compte"}
        </button>
      </form>

      {mode === "sign-in" ? (
        <Link className="auth-secondary-link" href={productRoutes.forgotPassword}>
          Mot de passe oublié ?
        </Link>
      ) : (
        <p className="auth-password-hint">12 caractères minimum.</p>
      )}
    </div>
  );
}
