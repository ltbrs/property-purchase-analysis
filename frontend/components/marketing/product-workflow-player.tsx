export function ProductWorkflowPlayer() {
  return (
    <video
      className="workflow-player"
      aria-label="Animation du parcours Acquora : dépôt des documents, analyse, puis rapport sourcé."
      controls
      loop
      muted
      playsInline
      poster="/images/product-workflow-poster.png"
      preload="none"
    >
      <source src="/videos/product-workflow.mp4" type="video/mp4" />
      Votre navigateur ne permet pas de lire cette animation.
    </video>
  );
}
