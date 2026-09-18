"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { Icon } from "@/components/icons";
import { captureProductEvent } from "@/lib/analytics/product-analytics";
import { marketingRoutes } from "@/lib/routes";
import { API_URL, readApiError } from "@/lib/workspace";

type OfferCode = "single_analysis" | "search_pack";

export type BillingSummary = {
  available_analyses: number;
  next_credit_expiration: string | null;
  can_create_free_preview: boolean;
};

const offers: Array<{
  code: OfferCode;
  name: string;
  price: string;
  detail: string;
}> = [
  {
    code: "single_analysis",
    name: "Analyse complète",
    price: "19 €",
    detail: "1 bien",
  },
  {
    code: "search_pack",
    name: "Pack Recherche",
    price: "39 €",
    detail: "3 biens, valables 12 mois",
  },
];

type BillingPanelProps = Readonly<{
  compact?: boolean;
  paymentStatus?: string;
  onSummaryChange?: (summary: BillingSummary) => void;
}>;

export async function fetchBillingSummary() {
  const response = await fetch(`${API_URL}/billing/summary`, { cache: "no-store" });
  if (!response.ok) throw new Error(await readApiError(response));
  return (await response.json()) as BillingSummary;
}

export function BillingPanel({
  compact = false,
  paymentStatus,
  onSummaryChange,
}: BillingPanelProps) {
  const [summary, setSummary] = useState<BillingSummary | null>(null);
  const [loadingOffer, setLoadingOffer] = useState<OfferCode | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    let timeout: ReturnType<typeof setTimeout> | undefined;
    let attempts = paymentStatus === "succes" ? 5 : 1;

    async function loadSummary() {
      try {
        const loaded = await fetchBillingSummary();
        if (cancelled) return;
        setSummary(loaded);
        onSummaryChange?.(loaded);
        if (paymentStatus === "succes" && attempts > 1) {
          attempts -= 1;
          timeout = setTimeout(() => void loadSummary(), 1_000);
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Impossible de charger vos analyses disponibles.",
          );
        }
      }
    }

    void loadSummary();
    return () => {
      cancelled = true;
      if (timeout) clearTimeout(timeout);
    };
  }, [onSummaryChange, paymentStatus]);

  async function startCheckout(offerCode: OfferCode) {
    setLoadingOffer(offerCode);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/billing/checkout-sessions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ offer_code: offerCode }),
      });
      if (!response.ok) throw new Error(await readApiError(response));
      const checkout = (await response.json()) as { checkout_url: string };
      captureProductEvent("checkout_started", { offer_code: offerCode });
      window.location.assign(checkout.checkout_url);
    } catch (checkoutError) {
      setError(
        checkoutError instanceof Error
          ? checkoutError.message
          : "Le paiement n’a pas pu être préparé.",
      );
      setLoadingOffer(null);
    }
  }

  return (
    <section className={`billing-panel${compact ? " is-compact" : ""}`} aria-labelledby="billing-title">
      <div className="billing-panel-heading">
        <div>
          <p className="section-kicker">Analyses</p>
          <h2 id="billing-title">Vos analyses disponibles</h2>
        </div>
        <strong>{summary?.available_analyses ?? "…"}</strong>
      </div>

      {paymentStatus === "succes" ? (
        <p className="billing-notice is-success" role="status">
          <Icon name="check" /> Paiement confirmé. Le crédit apparaît dès validation du webhook Stripe.
        </p>
      ) : paymentStatus === "annule" ? (
        <p className="billing-notice"><Icon name="info" /> Paiement annulé, rien n’a été débité.</p>
      ) : null}

      <div className="billing-offers">
        {offers.map((offer) => (
          <article key={offer.code}>
            <div>
              <strong>{offer.name}</strong>
              <span>{offer.detail}</span>
            </div>
            <b>{offer.price}</b>
            <button
              type="button"
              disabled={loadingOffer !== null}
              onClick={() => void startCheckout(offer.code)}
            >
              {loadingOffer === offer.code ? "Redirection…" : "Choisir"}
            </button>
          </article>
        ))}
      </div>
      <p className="billing-footnote">
        Paiement unique et sécurisé par Stripe, sans abonnement. En choisissant une
        offre, vous acceptez les <Link href={marketingRoutes.terms}>conditions générales</Link>
        {" "}et reconnaissez avoir consulté la <Link href={marketingRoutes.privacy}>politique de confidentialité</Link>.
      </p>
      {error ? <p className="billing-error" role="alert">{error}</p> : null}
    </section>
  );
}
