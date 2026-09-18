"use server";

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { getAuthOrigin, safeRedirectPath } from "@/lib/auth/redirects";
import { marketingRoutes, productRoutes } from "@/lib/routes";
import { createClient } from "@/lib/supabase/server";

export type AuthActionState = Readonly<{
  error?: string;
  success?: string;
}>;

const INVALID_CREDENTIALS =
  "Connexion impossible. Vérifiez vos informations et réessayez.";

function rawFieldValue(formData: FormData, name: string) {
  const value = formData.get(name);
  return typeof value === "string" ? value : "";
}

function fieldValue(formData: FormData, name: string) {
  return rawFieldValue(formData, name).trim();
}

function credentials(formData: FormData) {
  return {
    email: fieldValue(formData, "email").toLowerCase(),
    password: rawFieldValue(formData, "password"),
  };
}

function callbackPath(formData: FormData) {
  return safeRedirectPath(fieldValue(formData, "callbackUrl"));
}

export async function signInWithPassword(
  _state: AuthActionState,
  formData: FormData,
): Promise<AuthActionState> {
  const { email, password } = credentials(formData);
  if (!email || !password) return { error: INVALID_CREDENTIALS };

  const supabase = await createClient();
  const { error } = await supabase.auth.signInWithPassword({ email, password });
  if (error) return { error: INVALID_CREDENTIALS };

  revalidatePath("/", "layout");
  redirect(callbackPath(formData));
}

export async function signUpWithPassword(
  _state: AuthActionState,
  formData: FormData,
): Promise<AuthActionState> {
  const { email, password } = credentials(formData);
  const passwordConfirmation = rawFieldValue(formData, "passwordConfirmation");
  const name = fieldValue(formData, "name");
  if (!email || !email.includes("@")) {
    return { error: "Saisissez une adresse e-mail valide." };
  }
  if (password.length < 12) {
    return { error: "Le mot de passe doit contenir au moins 12 caractères." };
  }
  if (password !== passwordConfirmation) {
    return { error: "Les deux mots de passe ne correspondent pas." };
  }

  const supabase = await createClient();
  const callbackUrl = callbackPath(formData);
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      data: name ? { full_name: name.slice(0, 200) } : undefined,
      emailRedirectTo: `${getAuthOrigin()}/auth/callback?next=${encodeURIComponent(callbackUrl)}`,
    },
  });
  if (error) {
    return {
      error: "Création du compte impossible. Vérifiez les informations saisies.",
    };
  }
  if (data.session) {
    revalidatePath("/", "layout");
    redirect(callbackUrl);
  }

  return {
    success:
      "Consultez votre boîte e-mail pour confirmer votre adresse avant de vous connecter.",
  };
}

export async function requestPasswordReset(
  _state: AuthActionState,
  formData: FormData,
): Promise<AuthActionState> {
  const email = fieldValue(formData, "email").toLowerCase();
  if (!email || !email.includes("@")) {
    return { error: "Saisissez une adresse e-mail valide." };
  }

  const supabase = await createClient();
  await supabase.auth.resetPasswordForEmail(email, {
    redirectTo: `${getAuthOrigin()}/auth/callback?next=${encodeURIComponent(productRoutes.updatePassword)}`,
  });

  return {
    success:
      "Si un compte correspond à cette adresse, un lien de réinitialisation vient d’être envoyé.",
  };
}

export async function updatePassword(
  _state: AuthActionState,
  formData: FormData,
): Promise<AuthActionState> {
  const password = rawFieldValue(formData, "password");
  const confirmation = rawFieldValue(formData, "passwordConfirmation");
  if (password.length < 12) {
    return { error: "Le mot de passe doit contenir au moins 12 caractères." };
  }
  if (password !== confirmation) {
    return { error: "Les deux mots de passe ne correspondent pas." };
  }

  const supabase = await createClient();
  const { data: claimsData, error: claimsError } = await supabase.auth.getClaims();
  if (claimsError || !claimsData?.claims?.sub) {
    return { error: "Ce lien a expiré. Demandez un nouveau lien." };
  }
  const { error } = await supabase.auth.updateUser({ password });
  if (error) return { error: "Le mot de passe n’a pas pu être modifié." };

  revalidatePath("/", "layout");
  redirect(`${productRoutes.account}?password=updated`);
}

export async function signOutCurrentSession() {
  const supabase = await createClient();
  await supabase.auth.signOut({ scope: "local" });
  revalidatePath("/", "layout");
  redirect(marketingRoutes.home);
}
