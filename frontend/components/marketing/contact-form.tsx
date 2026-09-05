"use client";

import posthog from "posthog-js";
import { FormEvent, useRef, useState } from "react";

import { isPostHogConfigured } from "@/instrumentation-client";

type SubmissionState = "idle" | "pending" | "success" | "error";

export function ContactForm() {
  const formRef = useRef<HTMLFormElement>(null);
  const [submissionState, setSubmissionState] = useState<SubmissionState>("idle");
  const [feedback, setFeedback] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmissionState("pending");
    setFeedback("");

    const formData = new FormData(event.currentTarget);
    const payload = {
      name: formData.get("name"),
      email: formData.get("email"),
      subject: formData.get("subject"),
      message: formData.get("message"),
      privacy_consent: formData.get("privacy_consent") === "on",
      website: formData.get("website"),
    };

    try {
      const response = await fetch("/api/contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        setSubmissionState("error");
        setFeedback(
          response.status === 429
            ? "Trop de tentatives ont été envoyées. Réessayez un peu plus tard."
            : "Votre message n’a pas pu être envoyé. Vérifiez les champs puis réessayez.",
        );
        return;
      }

      formRef.current?.reset();
      if (isPostHogConfigured) {
        posthog.capture("contact_form_submitted", {
          subject: String(formData.get("subject") ?? "unknown"),
        });
      }
      setSubmissionState("success");
      setFeedback("Merci, votre message a bien été enregistré.");
    } catch {
      setSubmissionState("error");
      setFeedback("Le service est momentanément indisponible. Réessayez plus tard.");
    }
  }

  const pending = submissionState === "pending";

  return (
    <form ref={formRef} className="contact-form" onSubmit={handleSubmit}>
      <div className="contact-form-row">
        <label className="contact-field">
          <span>Nom</span>
          <input
            name="name"
            type="text"
            autoComplete="name"
            minLength={2}
            maxLength={100}
            required
          />
        </label>
        <label className="contact-field">
          <span>Adresse e-mail</span>
          <input
            name="email"
            type="email"
            autoComplete="email"
            maxLength={254}
            required
          />
        </label>
      </div>

      <label className="contact-field">
        <span>Objet de votre demande</span>
        <select name="subject" defaultValue="" required>
          <option value="" disabled>Sélectionnez un sujet</option>
          <option value="product">Question sur Acquora</option>
          <option value="analysis">Analyse ou documents immobiliers</option>
          <option value="pricing">Tarifs</option>
          <option value="privacy">Confidentialité et données</option>
          <option value="technical">Problème technique</option>
          <option value="partnership">Partenariat</option>
          <option value="other">Autre demande</option>
        </select>
      </label>

      <label className="contact-field">
        <span>Message</span>
        <textarea
          name="message"
          minLength={20}
          maxLength={4000}
          rows={8}
          placeholder="Expliquez-nous comment nous pouvons vous aider."
          required
        />
        <small>20 à 4 000 caractères. N’incluez aucune pièce jointe ni donnée sensible.</small>
      </label>

      <label className="contact-honeypot" aria-hidden="true">
        <span>Site internet</span>
        <input name="website" type="text" tabIndex={-1} autoComplete="off" />
      </label>

      <label className="contact-consent">
        <input name="privacy_consent" type="checkbox" required />
        <span>
          J’accepte que mes informations soient utilisées pour traiter cette
          demande et me répondre.
        </span>
      </label>

      <div className="contact-submit-row">
        <button type="submit" disabled={pending}>
          {pending ? "Envoi en cours…" : "Envoyer mon message"}
        </button>
        <p
          className={`contact-feedback contact-feedback--${submissionState}`}
          aria-live="polite"
          role={submissionState === "error" ? "alert" : "status"}
        >
          {feedback}
        </p>
      </div>
    </form>
  );
}
