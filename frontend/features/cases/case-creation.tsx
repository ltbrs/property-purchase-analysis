"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";

import { Icon } from "@/components/icons";
import type { PropertyType } from "@/features/documents/document-catalog";
import { productRoutes } from "@/lib/routes";
import {
  API_URL,
  type AnalysisCase,
  getOrCreateUserId,
  readApiError,
  saveWorkspace,
} from "@/lib/workspace";

type CaseCreationProps = {
  onCreated?: (analysisCase: AnalysisCase) => void;
};

const propertyTypes: {
  value: Exclude<PropertyType, "unknown">;
  label: string;
  description: string;
  icon: "building" | "home";
}[] = [
  {
    value: "apartment_coproperty",
    label: "Appartement en copropriété",
    description: "Le logement dépend d’une copropriété.",
    icon: "building",
  },
  {
    value: "house",
    label: "Maison individuelle",
    description: "Le bien ne dépend pas d’une copropriété.",
    icon: "home",
  },
];

function optionalValue(formData: FormData, name: string) {
  const value = String(formData.get(name) ?? "").trim();
  return value === "" ? null : value;
}

export function CaseCreation({ onCreated }: CaseCreationProps) {
  const router = useRouter();
  const [propertyType, setPropertyType] = useState<Exclude<PropertyType, "unknown"> | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!propertyType || isSubmitting) return;

    setIsSubmitting(true);
    setError(null);
    const formData = new FormData(event.currentTarget);

    try {
      const response = await fetch(`${API_URL}/analysis-cases`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-User-Id": getOrCreateUserId(),
        },
        body: JSON.stringify({
          title: String(formData.get("title") ?? "").trim(),
          property_type: propertyType,
          price_eur: optionalValue(formData, "price_eur"),
          surface_m2: optionalValue(formData, "surface_m2"),
          lot_count: optionalValue(formData, "lot_count"),
        }),
      });
      if (!response.ok) throw new Error(await readApiError(response));

      const analysisCase = (await response.json()) as AnalysisCase;
      saveWorkspace(analysisCase.id);
      onCreated?.(analysisCase);
      router.push(productRoutes.caseOverview);
    } catch (creationError) {
      setError(
        creationError instanceof Error
          ? creationError.message
          : "Impossible de créer le dossier.",
      );
      setIsSubmitting(false);
    }
  }

  return (
    <section className="case-creation" aria-labelledby="case-creation-title">
      <div className="case-creation-intro">
        <p className="eyebrow">Nouveau dossier</p>
        <h1 id="case-creation-title">Commençons par le bien</h1>
        <p>
          Ces quelques informations permettent d’adapter les documents attendus et de
          contextualiser l’analyse.
        </p>
        <div className="creation-trust-note">
          <Icon name="shield" />
          <span>Vous pourrez ensuite ajouter les documents du bien en stockage privé.</span>
        </div>
      </div>

      <form className="case-creation-form" onSubmit={(event) => void submit(event)}>
        <div className="form-section-heading">
          <span>1</span>
          <div>
            <strong>Identification du bien</strong>
            <small>Seul le nom et le type sont obligatoires.</small>
          </div>
        </div>

        <label className="form-field form-field-wide">
          <span>Adresse ou nom du bien <i>Obligatoire</i></span>
          <input
            type="text"
            name="title"
            required
            minLength={1}
            maxLength={200}
            autoComplete="street-address"
            placeholder="Ex. 24 rue des Lilas, Nantes"
          />
          <small>Utilisez l’adresse complète ou le nom de votre choix.</small>
        </label>

        <fieldset className="creation-property-type">
          <legend>Type de bien <i>Obligatoire</i></legend>
          <div className="property-type-options">
            {propertyTypes.map((choice) => (
              <label
                key={choice.value}
                className={`property-type-option${propertyType === choice.value ? " is-selected" : ""}`}
              >
                <input
                  type="radio"
                  name="property_type"
                  value={choice.value}
                  checked={propertyType === choice.value}
                  required
                  onChange={() => setPropertyType(choice.value)}
                />
                <span className="property-type-icon"><Icon name={choice.icon} /></span>
                <span>
                  <strong>{choice.label}</strong>
                  <small>{choice.description}</small>
                </span>
                <span className="radio-indicator" aria-hidden="true" />
              </label>
            ))}
          </div>
        </fieldset>

        <div className="form-section-heading form-details-heading">
          <span>2</span>
          <div>
            <strong>Informations complémentaires</strong>
            <small>Facultatives, elles enrichiront la synthèse du dossier.</small>
          </div>
        </div>

        <div className="optional-fields">
          <label className="form-field">
            <span>Prix affiché ou envisagé</span>
            <span className="input-with-unit">
              <input
                type="number"
                name="price_eur"
                min="0.01"
                step="0.01"
                inputMode="decimal"
                placeholder="425000"
              />
              <b>€</b>
            </span>
          </label>
          <label className="form-field">
            <span>Surface</span>
            <span className="input-with-unit">
              <input
                type="number"
                name="surface_m2"
                min="0.01"
                step="0.01"
                inputMode="decimal"
                placeholder="67.4"
              />
              <b>m²</b>
            </span>
          </label>
          <label className="form-field">
            <span>Nombre de lots</span>
            <input
              type="number"
              name="lot_count"
              min="1"
              step="1"
              inputMode="numeric"
              placeholder="3"
            />
          </label>
        </div>

        {error ? <p className="creation-error" role="alert">{error}</p> : null}

        <div className="creation-actions">
          <span>Les champs facultatifs pourront rester vides.</span>
          <button type="submit" disabled={!propertyType || isSubmitting}>
            {isSubmitting ? "Création…" : "Créer le dossier"}
            {!isSubmitting ? <Icon name="arrow" /> : null}
          </button>
        </div>
      </form>
    </section>
  );
}
