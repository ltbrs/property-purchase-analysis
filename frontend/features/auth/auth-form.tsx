"use client";

import Link from "next/link";
import { useActionState, useState } from "react";

import {
  signInWithPassword,
  signUpWithPassword,
} from "@/features/auth/actions";
import { GoogleSignIn } from "@/features/auth/google-sign-in";
import { productRoutes } from "@/lib/routes";

type AuthFormProps = Readonly<{
  callbackUrl: string;
  googleClientId?: string;
  routeError?: string;
}>;

export function AuthForm({ callbackUrl, googleClientId, routeError }: AuthFormProps) {
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

      <GoogleSignIn callbackUrl={callbackUrl} clientId={googleClientId} />

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
