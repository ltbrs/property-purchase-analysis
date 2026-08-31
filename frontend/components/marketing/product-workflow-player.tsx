"use client";

import { Player } from "@remotion/player";
import { useEffect, useState } from "react";

import {
  PRODUCT_WORKFLOW_DURATION,
  PRODUCT_WORKFLOW_FPS,
  PRODUCT_WORKFLOW_HEIGHT,
  PRODUCT_WORKFLOW_WIDTH,
  ProductWorkflowVideo,
} from "./product-workflow-video";

export function ProductWorkflowPlayer() {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    const updatePreference = () => setPrefersReducedMotion(mediaQuery.matches);

    updatePreference();
    mediaQuery.addEventListener("change", updatePreference);
    return () => mediaQuery.removeEventListener("change", updatePreference);
  }, []);

  return (
    <div
      className="workflow-player"
      role="group"
      aria-label="Animation du parcours Acquora : dépôt des documents, analyse, puis rapport sourcé."
    >
      <Player
        component={ProductWorkflowVideo}
        durationInFrames={PRODUCT_WORKFLOW_DURATION}
        compositionWidth={PRODUCT_WORKFLOW_WIDTH}
        compositionHeight={PRODUCT_WORKFLOW_HEIGHT}
        fps={PRODUCT_WORKFLOW_FPS}
        autoPlay={!prefersReducedMotion}
        loop
        controls
        initiallyMuted
        showVolumeControls={false}
        style={{ aspectRatio: "16 / 9", width: "100%" }}
      />
    </div>
  );
}
