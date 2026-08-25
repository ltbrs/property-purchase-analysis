import Link from "next/link";

export default function HomePage() {
  return (
    <section className="page-intro">
      <p className="eyebrow">Aide à la décision immobilière</p>
      <h1>Comprenez les documents avant d’acheter.</h1>
      <p>
        Une analyse structurée pour faire ressortir les risques, coûts futurs,
        incohérences et informations manquantes d’un bien immobilier.
      </p>
      <div className="actions">
        <Link className="button" href="/upload">
          Ajouter des documents
        </Link>
        <Link className="button button-secondary" href="/analysis">
          Voir l’analyse
        </Link>
      </div>
    </section>
  );
}

