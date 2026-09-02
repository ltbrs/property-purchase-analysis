import type { CSSProperties, ReactNode } from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
} from "remotion";

import { Icon, type IconName } from "@/components/icons";

export const PRODUCT_WORKFLOW_DURATION = 270;
export const PRODUCT_WORKFLOW_FPS = 30;
export const PRODUCT_WORKFLOW_WIDTH = 1200;
export const PRODUCT_WORKFLOW_HEIGHT = 675;

const colors = {
  canvas: "#eef2eb",
  ink: "#14251f",
  muted: "#66776f",
  surface: "#ffffff",
  line: "#dfe5df",
  green: "#173f35",
  greenDark: "#102a25",
  greenLight: "#e7f0eb",
  lime: "#d8ff72",
  red: "#bd4b3b",
  redSoft: "#fff0ed",
  amber: "#9b690f",
  amberSoft: "#fff7df",
};

const shellStyle: CSSProperties = {
  backgroundColor: colors.surface,
  border: `1px solid ${colors.line}`,
  borderRadius: 28,
  boxShadow: "0 28px 70px rgba(16, 42, 37, 0.12)",
};

function appear(frame: number, start: number) {
  return spring({
    frame: frame - start,
    fps: PRODUCT_WORKFLOW_FPS,
    config: { damping: 18, stiffness: 120, mass: 0.8 },
  });
}

function sceneOpacity(frame: number, start: number, end: number) {
  return interpolate(
    frame,
    [start, start + 12, end - 12, end],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
  );
}

function IconTile({ name, tone = "green" }: { name: IconName; tone?: "green" | "lime" | "red" | "amber" }) {
  const palettes = {
    green: { background: colors.greenLight, color: colors.green },
    lime: { background: colors.lime, color: colors.greenDark },
    red: { background: colors.redSoft, color: colors.red },
    amber: { background: colors.amberSoft, color: colors.amber },
  };

  return (
    <div
      style={{
        ...palettes[tone],
        alignItems: "center",
        borderRadius: 14,
        display: "flex",
        flexShrink: 0,
        height: 48,
        justifyContent: "center",
        width: 48,
      }}
    >
      <Icon name={name} style={{ height: 22, width: 22 }} />
    </div>
  );
}

function WorkflowHeader({ active }: { active: number }) {
  const steps = ["Documents", "Analyse", "Rapport"];

  return (
    <div style={{ alignItems: "center", display: "flex", height: 82, padding: "0 38px" }}>
      <div style={{ alignItems: "center", display: "flex", gap: 12 }}>
        <div
          style={{
            alignItems: "center",
            background: colors.lime,
            borderRadius: 12,
            color: colors.greenDark,
            display: "flex",
            fontSize: 22,
            fontWeight: 900,
            height: 38,
            justifyContent: "center",
            width: 38,
          }}
        >
          A
        </div>
        <span style={{ color: colors.greenDark, fontSize: 24, fontWeight: 800, letterSpacing: -0.6 }}>acquora</span>
      </div>
      <div style={{ display: "flex", gap: 10, marginLeft: "auto" }}>
        {steps.map((step, index) => (
          <div
            key={step}
            style={{
              background: index === active ? colors.green : colors.canvas,
              borderRadius: 999,
              color: index === active ? "white" : colors.muted,
              fontSize: 14,
              fontWeight: 700,
              padding: "8px 15px",
            }}
          >
            {index + 1}. {step}
          </div>
        ))}
      </div>
    </div>
  );
}

function VideoScene({ children, style }: { children: ReactNode; style?: CSSProperties }) {
  return (
    <AbsoluteFill style={{ padding: "86px 70px 64px", ...style }}>
      <div style={{ ...shellStyle, height: "100%", overflow: "hidden", position: "relative" }}>{children}</div>
    </AbsoluteFill>
  );
}

function UploadScene({ frame }: { frame: number }) {
  const documents = [
    { name: "DPE.pdf", pages: "18 pages", delay: 18 },
    { name: "PV_AG_2025.pdf", pages: "24 pages", delay: 28 },
    { name: "Charges_2024.pdf", pages: "6 pages", delay: 38 },
  ];
  const dropProgress = appear(frame, 8);

  return (
    <VideoScene
      style={{
        opacity: interpolate(frame, [0, 80, 92], [1, 1, 0], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
        }),
      }}
    >
      <WorkflowHeader active={0} />
      <div style={{ display: "grid", gridTemplateColumns: "0.9fr 1.1fr", height: "calc(100% - 82px)", padding: "24px 38px 38px" }}>
        <div style={{ alignSelf: "center", padding: "0 32px 0 8px" }}>
          <span style={{ color: colors.green, fontSize: 16, fontWeight: 800, letterSpacing: 1.2, textTransform: "uppercase" }}>Votre dossier d’achat</span>
          <h2 style={{ color: colors.ink, fontSize: 46, letterSpacing: -2, lineHeight: 1.04, margin: "16px 0" }}>Tous vos documents,<br />au même endroit.</h2>
          <p style={{ color: colors.muted, fontSize: 19, lineHeight: 1.5, margin: 0 }}>Déposez les PDF transmis par le vendeur, l’agence ou le syndic.</p>
        </div>
        <div
          style={{
            alignSelf: "center",
            background: colors.canvas,
            borderRadius: 24,
            height: 350,
            opacity: dropProgress,
            padding: 26,
            transform: `translateY(${interpolate(dropProgress, [0, 1], [32, 0])}px)`,
          }}
        >
          <div style={{ alignItems: "center", display: "flex", gap: 14, marginBottom: 18 }}>
            <IconTile name="upload" tone="lime" />
            <div>
              <div style={{ color: colors.ink, fontSize: 18, fontWeight: 800 }}>Documents ajoutés</div>
              <div style={{ color: colors.muted, fontSize: 14 }}>PDF · données conservées en privé</div>
            </div>
          </div>
          <div style={{ display: "grid", gap: 10 }}>
            {documents.map((document) => {
              const progress = appear(frame, document.delay);
              return (
                <div
                  key={document.name}
                  style={{
                    alignItems: "center",
                    background: colors.surface,
                    border: `1px solid ${colors.line}`,
                    borderRadius: 16,
                    display: "flex",
                    gap: 14,
                    opacity: progress,
                    padding: "13px 16px",
                    transform: `translateY(${interpolate(progress, [0, 1], [20, 0])}px)`,
                  }}
                >
                  <Icon name="document" style={{ color: colors.green, height: 22, width: 22 }} />
                  <span style={{ color: colors.ink, fontSize: 15, fontWeight: 750 }}>{document.name}</span>
                  <span style={{ color: colors.muted, fontSize: 13, marginLeft: "auto" }}>{document.pages}</span>
                  <div style={{ alignItems: "center", background: colors.greenLight, borderRadius: 999, color: colors.green, display: "flex", height: 26, justifyContent: "center", width: 26 }}>
                    <Icon name="check" style={{ height: 15, width: 15 }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </VideoScene>
  );
}

function AnalysisScene({ frame }: { frame: number }) {
  const localFrame = frame - 72;
  const progress = interpolate(localFrame, [10, 72], [8, 100], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const facts = [
    { label: "Énergie", value: "DPE F", icon: "leaf" as const, tone: "red" as const },
    { label: "Copropriété", value: "3 PV lus", icon: "building" as const, tone: "green" as const },
    { label: "Travaux", value: "2 évoqués", icon: "wrench" as const, tone: "amber" as const },
  ];

  return (
    <VideoScene style={{ opacity: sceneOpacity(frame, 72, 182) }}>
      <WorkflowHeader active={1} />
      <div style={{ height: "calc(100% - 82px)", padding: "26px 38px 38px" }}>
        <div style={{ alignItems: "flex-end", display: "flex", justifyContent: "space-between", marginBottom: 24 }}>
          <div>
            <span style={{ color: colors.green, fontSize: 15, fontWeight: 800, letterSpacing: 1, textTransform: "uppercase" }}>Analyse en cours</span>
            <h2 style={{ color: colors.ink, fontSize: 38, letterSpacing: -1.5, margin: "8px 0 0" }}>Les faits sont structurés et recoupés.</h2>
          </div>
          <span style={{ color: colors.green, fontSize: 30, fontWeight: 850 }}>{Math.round(progress)}%</span>
        </div>
        <div style={{ background: colors.canvas, borderRadius: 999, height: 12, overflow: "hidden" }}>
          <div style={{ background: colors.green, borderRadius: 999, height: "100%", width: `${progress}%` }} />
        </div>
        <div style={{ display: "grid", gap: 14, gridTemplateColumns: "repeat(3, 1fr)", marginTop: 26 }}>
          {facts.map((fact, index) => {
            const itemProgress = appear(localFrame, 20 + index * 11);
            return (
              <div
                key={fact.label}
                style={{
                  background: colors.canvas,
                  borderRadius: 20,
                  opacity: itemProgress,
                  padding: 20,
                  transform: `translateY(${interpolate(itemProgress, [0, 1], [24, 0])}px)`,
                }}
              >
                <IconTile name={fact.icon} tone={fact.tone} />
                <div style={{ color: colors.muted, fontSize: 14, marginTop: 20 }}>{fact.label}</div>
                <div style={{ color: colors.ink, fontSize: 22, fontWeight: 800, marginTop: 3 }}>{fact.value}</div>
              </div>
            );
          })}
        </div>
      </div>
    </VideoScene>
  );
}

function ReportScene({ frame }: { frame: number }) {
  const localFrame = frame - 160;
  const panelProgress = appear(localFrame, 5);
  const alerts = [
    { title: "DPE classé F", source: "DPE.pdf · page 2", tone: "red" as const },
    { title: "Ravalement à chiffrer", source: "PV_AG_2025.pdf · page 11", tone: "amber" as const },
  ];

  return (
    <VideoScene style={{ opacity: sceneOpacity(frame, 160, 270) }}>
      <WorkflowHeader active={2} />
      <div style={{ display: "grid", gap: 22, gridTemplateColumns: "1.35fr 0.65fr", height: "calc(100% - 82px)", padding: "24px 38px 38px" }}>
        <div
          style={{
            background: colors.canvas,
            borderRadius: 22,
            opacity: panelProgress,
            padding: 22,
            transform: `translateY(${interpolate(panelProgress, [0, 1], [26, 0])}px)`,
          }}
        >
          <div style={{ alignItems: "center", display: "flex", marginBottom: 15 }}>
            <div>
              <div style={{ color: colors.green, fontSize: 13, fontWeight: 800, letterSpacing: 1, textTransform: "uppercase" }}>À regarder en priorité</div>
              <div style={{ color: colors.ink, fontSize: 27, fontWeight: 850, letterSpacing: -0.8, marginTop: 5 }}>2 points importants</div>
            </div>
            <div style={{ alignItems: "center", background: colors.redSoft, borderRadius: 999, color: colors.red, display: "flex", fontSize: 13, fontWeight: 800, gap: 7, marginLeft: "auto", padding: "9px 13px" }}>
              <Icon name="alert" style={{ height: 16, width: 16 }} />
              À vérifier
            </div>
          </div>
          <div style={{ display: "grid", gap: 10 }}>
            {alerts.map((alert, index) => {
              const itemProgress = appear(localFrame, 16 + index * 12);
              return (
                <div key={alert.title} style={{ alignItems: "center", background: colors.surface, border: `1px solid ${colors.line}`, borderRadius: 16, display: "flex", gap: 13, opacity: itemProgress, padding: "14px 16px" }}>
                  <IconTile name="alert" tone={alert.tone} />
                  <div>
                    <div style={{ color: colors.ink, fontSize: 16, fontWeight: 800 }}>{alert.title}</div>
                    <div style={{ color: colors.muted, fontSize: 13, marginTop: 3 }}>{alert.source}</div>
                  </div>
                  <Icon name="chevron" style={{ color: colors.muted, height: 18, marginLeft: "auto", width: 18 }} />
                </div>
              );
            })}
          </div>
        </div>
        <div style={{ display: "grid", gap: 14, gridTemplateRows: "1fr 1fr" }}>
          <div style={{ background: colors.green, borderRadius: 22, color: "white", padding: 22 }}>
            <Icon name="eye" style={{ color: colors.lime, height: 24, width: 24 }} />
            <div style={{ fontSize: 23, fontWeight: 850, marginTop: 17 }}>Chaque constat<br />garde sa source.</div>
            <div style={{ color: "rgba(255,255,255,.6)", fontSize: 13, marginTop: 10 }}>Document, page et extrait utile</div>
          </div>
          <div style={{ alignItems: "center", background: colors.greenLight, borderRadius: 22, display: "flex", gap: 14, padding: 22 }}>
            <IconTile name="check" tone="lime" />
            <div>
              <div style={{ color: colors.ink, fontSize: 18, fontWeight: 850 }}>Rapport prêt</div>
              <div style={{ color: colors.muted, fontSize: 13, marginTop: 4 }}>Décidez avec les faits en main.</div>
            </div>
          </div>
        </div>
      </div>
    </VideoScene>
  );
}

export function ProductWorkflowVideo() {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ background: colors.greenDark, fontFamily: "Arial, Helvetica, sans-serif" }}>
      <div
        style={{
          background: "radial-gradient(circle at 15% 25%, rgba(216,255,114,.18), transparent 32%)",
          inset: 0,
          position: "absolute",
        }}
      />
      <UploadScene frame={frame} />
      <AnalysisScene frame={frame} />
      <ReportScene frame={frame} />
      <div style={{ bottom: 28, color: "rgba(255,255,255,.52)", fontSize: 14, left: 0, letterSpacing: 0.4, position: "absolute", right: 0, textAlign: "center" }}>
        De vos documents à une décision éclairée
      </div>
    </AbsoluteFill>
  );
}
