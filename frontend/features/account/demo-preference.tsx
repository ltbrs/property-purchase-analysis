"use client";

import { useEffect, useState } from "react";

import { captureProductEvent } from "@/lib/analytics/product-analytics";
import {
  fetchAnalysisCases,
  fetchUserPreferences,
  getWorkspace,
  resetWorkspace,
  updateUserPreferences,
  WORKSPACE_CHANGE_EVENT,
} from "@/lib/workspace";

export function DemoPreference() {
  const [isVisible, setIsVisible] = useState(true);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    void fetchUserPreferences()
      .then((preferences) => {
        if (!cancelled) setIsVisible(preferences.show_demo_case);
      })
      .catch((loadError: unknown) => {
        if (!cancelled) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Impossible de charger cette préférence.",
          );
        }
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function changeVisibility(showDemoCase: boolean) {
    if (isSaving) return;
    setIsSaving(true);
    setError(null);
    try {
      const activeCaseId = getWorkspace()?.caseId ?? null;
      const casesBeforeUpdate = showDemoCase ? [] : await fetchAnalysisCases();
      const activeCase = casesBeforeUpdate.find(({ id }) => id === activeCaseId);
      const preferences = await updateUserPreferences({ show_demo_case: showDemoCase });
      setIsVisible(preferences.show_demo_case);
      if (!showDemoCase && activeCase?.case_kind === "demo") {
        resetWorkspace(activeCase.id);
      } else {
        window.dispatchEvent(new Event(WORKSPACE_CHANGE_EVENT));
      }
      captureProductEvent("demo_case_visibility_changed", {
        visible: preferences.show_demo_case,
      });
    } catch (updateError) {
      setError(
        updateError instanceof Error
          ? updateError.message
          : "Impossible d’enregistrer cette préférence.",
      );
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <section className="account-preference-card" aria-labelledby="demo-preference-title">
      <div>
        <strong id="demo-preference-title">Afficher le dossier de démonstration</strong>
        <span>
          Un exemple fictif en lecture seule pour découvrir un rapport Acquora complet.
        </span>
      </div>
      <label className="preference-switch">
        <input
          type="checkbox"
          checked={isVisible}
          disabled={isLoading || isSaving}
          onChange={(event) => void changeVisibility(event.currentTarget.checked)}
        />
        <span aria-hidden="true" />
        <small>{isSaving ? "Enregistrement…" : isVisible ? "Affiché" : "Masqué"}</small>
      </label>
      {error ? <p className="preference-error" role="alert">{error}</p> : null}
    </section>
  );
}
