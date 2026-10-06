"use client";

import { useEffect, useEffectEvent, useRef } from "react";

export function useDocumentDialog(onClose: () => void) {
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const closeOnEscape = useEffectEvent((event: KeyboardEvent) => {
    if (event.key === "Escape") onClose();
  });

  // Parent polling can change onClose without reopening or refocusing the dialog.
  useEffect(() => {
    const previousActiveElement = document.activeElement;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    closeButtonRef.current?.focus();
    window.addEventListener("keydown", closeOnEscape);

    return () => {
      window.removeEventListener("keydown", closeOnEscape);
      document.body.style.overflow = previousOverflow;
      if (previousActiveElement instanceof HTMLElement) previousActiveElement.focus();
    };
  }, []);

  return closeButtonRef;
}
