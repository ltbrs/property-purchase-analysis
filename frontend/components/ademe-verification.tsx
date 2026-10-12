import { AdemeMark } from "@/components/ademe-mark";
import { Icon } from "@/components/icons";

export type AdemeVerificationStatus =
  | "not_attempted"
  | "verified"
  | "verified_with_inconsistencies"
  | "not_found"
  | "unavailable";

export const ademeVerificationCopy = {
  verified: {
    label: "Vérifié",
    description: "Le numéro DPE a été retrouvé dans le registre public de l’ADEME et les données comparables sont cohérentes.",
  },
  verified_with_inconsistencies: {
    label: "Écarts détectés",
    description: "Le numéro DPE a été retrouvé dans le registre public de l’ADEME, avec des écarts sur certaines données. Le document et sa version sont à vérifier.",
  },
  not_found: {
    label: "Non vérifié",
    description: "Le numéro DPE extrait n’a pas été retrouvé dans le registre public de l’ADEME. Demandez au vendeur ou au diagnostiqueur de confirmer le numéro et l’enregistrement du DPE.",
  },
  unavailable: {
    label: "Non vérifié",
    description: "L’API ADEME était indisponible pendant l’analyse. L’enregistrement du DPE reste à vérifier auprès de l’ADEME.",
  },
  not_attempted: {
    label: "Non vérifié",
    description: "Aucun numéro DPE exploitable n’a été détecté dans le document. Demandez un numéro lisible pour vérifier son enregistrement auprès de l’ADEME.",
  },
} satisfies Record<AdemeVerificationStatus, { label: string; description: string }>;

export function AdemeVerification({ status }: { status: AdemeVerificationStatus }) {
  const copy = ademeVerificationCopy[status];
  const isVerified = status === "verified";

  return (
    <span
      className={`ademe-verification${
        isVerified
          ? ""
          : status === "verified_with_inconsistencies"
            ? " has-inconsistencies"
            : " needs-verification"
      }`}
      title={copy.description}
      aria-label={`ADEME : ${copy.label}. ${copy.description}`}
    >
      <AdemeMark />
      <span aria-hidden="true"><Icon name={isVerified ? "check" : "info"} /></span>
      {copy.label}
    </span>
  );
}
