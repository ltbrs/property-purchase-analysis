export const marketingRoutes = {
  home: "/",
  howItWorks: "/comment-ca-marche",
  pricing: "/tarifs",
  blog: "/blog",
  blogCoproperty: "/blog/copropriete",
  contact: "/nous-contacter",
  privacy: "/confidentialite",
  terms: "/conditions-generales",
} as const;

export const productRoutes = {
  home: "/app",
  demo: "/app/demo",
  demoAnalysis: "/app/demo/analyse",
  demoDocuments: "/app/demo/documents",
  cases: "/app/dossiers",
  caseOverview: "/app/dossiers/vue-ensemble",
  documents: "/app/dossiers/documents",
  analysis: "/app/analyse",
  account: "/app/compte",
  admin: "/app/administration",
  signIn: "/connexion",
  forgotPassword: "/mot-de-passe-oublie",
  updatePassword: "/reinitialiser-mot-de-passe",
} as const;
