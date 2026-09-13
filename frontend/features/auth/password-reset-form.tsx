"use client";

import { useActionState } from "react";

import {
  requestPasswordReset,
  updatePassword,
} from "@/features/auth/actions";

type PasswordResetFormProps = Readonly<{
  mode: "request" | "update";
}>;

export function PasswordResetForm({ mode }: PasswordResetFormProps) {
  const action = mode === "request" ? requestPasswordReset : updatePassword;
  const [state, formAction, pending] = useActionState(action, {});

  return (
    <form action={formAction} className="auth-fields">
      {mode === "request" ? (
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
      ) : (
        <>
          <label>
            <span>Nouveau mot de passe</span>
            <input
              autoComplete="new-password"
              minLength={12}
              name="password"
              required
              type="password"
            />
          </label>
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
        </>
      )}

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
          : mode === "request"
            ? "Envoyer le lien"
            : "Enregistrer le mot de passe"}
      </button>
    </form>
  );
}
