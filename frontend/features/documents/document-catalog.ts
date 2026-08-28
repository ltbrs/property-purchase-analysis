export type PropertyType = "unknown" | "apartment_coproperty" | "house";

export type DocumentType =
  | "dpe"
  | "ag_minutes"
  | "diagnostics"
  | "copro_financials"
  | "charges"
  | "works_call"
  | "property_tax"
  | "copro_rules"
  | "maintenance_log"
  | "risk_statement"
  | "unknown";

export type ExpectedDocument = {
  key: string;
  label: string;
  description: string;
  acceptedTypes: DocumentType[];
  priority: "essential" | "useful";
};

export const propertyTypeLabels: Record<PropertyType, string> = {
  unknown: "Type de logement à préciser",
  apartment_coproperty: "Appartement en copropriété",
  house: "Maison individuelle",
};

export const documentTypeLabels: Record<DocumentType, string> = {
  dpe: "DPE",
  ag_minutes: "Procès-verbal d’AG",
  diagnostics: "Diagnostics techniques",
  copro_financials: "Comptes de copropriété",
  charges: "Charges de copropriété",
  works_call: "Appel de fonds travaux",
  property_tax: "Taxe foncière",
  copro_rules: "Règlement de copropriété",
  maintenance_log: "Carnet d’entretien",
  risk_statement: "État des risques",
  unknown: "Type non identifié",
};

const commonDocuments: ExpectedDocument[] = [
  {
    key: "dpe",
    label: "Diagnostic de performance énergétique",
    description: "Classe énergie, consommation et validité du diagnostic.",
    acceptedTypes: ["dpe"],
    priority: "essential",
  },
  {
    key: "diagnostics",
    label: "Dossier de diagnostics techniques",
    description: "Amiante, plomb, gaz, électricité et autres diagnostics applicables.",
    acceptedTypes: ["diagnostics"],
    priority: "essential",
  },
  {
    key: "risk_statement",
    label: "État des risques",
    description: "Risques naturels, miniers, technologiques et pollution des sols.",
    acceptedTypes: ["risk_statement"],
    priority: "useful",
  },
  {
    key: "property_tax",
    label: "Dernier avis de taxe foncière",
    description: "Repère utile pour estimer les charges annuelles du bien.",
    acceptedTypes: ["property_tax"],
    priority: "useful",
  },
];

const copropertyDocuments: ExpectedDocument[] = [
  {
    key: "ag_minutes",
    label: "Procès-verbaux d’AG récents",
    description: "Décisions, travaux votés et sujets suivis par la copropriété.",
    acceptedTypes: ["ag_minutes"],
    priority: "essential",
  },
  {
    key: "copro_financials",
    label: "Charges et comptes de copropriété",
    description: "Charges courantes, appels de fonds et situation financière.",
    acceptedTypes: ["copro_financials", "charges", "works_call"],
    priority: "essential",
  },
  {
    key: "copro_rules",
    label: "Règlement de copropriété",
    description: "Règles de l’immeuble et informations relatives au lot.",
    acceptedTypes: ["copro_rules"],
    priority: "useful",
  },
  {
    key: "maintenance_log",
    label: "Carnet d’entretien de l’immeuble",
    description: "Entretien réalisé et contrats concernant les équipements communs.",
    acceptedTypes: ["maintenance_log"],
    priority: "useful",
  },
];

export function expectedDocumentsFor(propertyType: PropertyType) {
  return propertyType === "apartment_coproperty"
    ? [...commonDocuments, ...copropertyDocuments]
    : commonDocuments;
}
