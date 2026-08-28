"use client";

import { useState } from "react";
import {
  AlertTriangle, ArrowRight, Building2, Check, ChevronRight, CircleHelp,
  FileCheck2, FileText, FolderOpen, Gauge, Home, Leaf, Menu, Search,
  ShieldAlert, Upload, WalletCards, Wrench,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  Sheet, SheetContent, SheetDescription, SheetFooter, SheetHeader, SheetTitle,
} from "@/components/ui/sheet";

type Detail = {
  kind: "risk" | "missing" | "document";
  title: string;
  subtitle: string;
  severity?: "Critique" | "À vérifier" | "Validé";
  source?: string;
  excerpt?: string;
};

const risks: Detail[] = [
  { kind: "risk", title: "DPE classé F", subtitle: "Performance énergétique faible", severity: "Critique", source: "DPE.pdf · page 2", excerpt: "Consommation conventionnelle : 382 kWhEP/m²/an. Classe énergétique F." },
  { kind: "risk", title: "Fonds travaux insuffisant", subtitle: "Montant inférieur au seuil recommandé", severity: "Critique", source: "PV_AG_2025.pdf · page 8", excerpt: "Le fonds travaux disponible s’élève à 18 420 € pour la copropriété." },
  { kind: "risk", title: "Ravalement à chiffrer", subtitle: "Travaux évoqués sans budget voté", severity: "À vérifier", source: "PV_AG_2025.pdf · page 11", excerpt: "L’assemblée décide de solliciter trois devis avant le prochain exercice." },
];

const missing: Detail[] = [
  { kind: "missing", title: "État daté", subtitle: "À demander au syndic" },
  { kind: "missing", title: "Plan pluriannuel de travaux", subtitle: "À demander au vendeur" },
  { kind: "missing", title: "Carnet d’entretien", subtitle: "Recommandé avant compromis" },
];

const documents: Detail[] = [
  { kind: "document", title: "DPE.pdf", subtitle: "Analysé · 2 alertes", severity: "Critique" },
  { kind: "document", title: "PV_AG_2025.pdf", subtitle: "Analysé · 3 alertes", severity: "À vérifier" },
  { kind: "document", title: "Règlement_copropriété.pdf", subtitle: "Analysé · aucun risque", severity: "Validé" },
  { kind: "document", title: "Appels_fonds_2024.pdf", subtitle: "Analysé · aucun risque", severity: "Validé" },
];

const categories = [
  { label: "Copropriété", value: "2 alertes", icon: Building2, tone: "amber" },
  { label: "Énergie", value: "1 critique", icon: Leaf, tone: "red" },
  { label: "Finances", value: "À vérifier", icon: WalletCards, tone: "amber" },
  { label: "Travaux", value: "1 critique", icon: Wrench, tone: "red" },
];

export default function HomePage() {
  const [detail, setDetail] = useState<Detail | null>(null);
  const [mobileNav, setMobileNav] = useState(false);

  return (
    <main className="min-h-screen bg-[#f5f6f2] text-[#14241f]">
      <div className="mx-auto flex min-h-screen max-w-[1600px]">
        <aside className={`${mobileNav ? "flex" : "hidden"} fixed inset-y-0 left-0 z-40 w-64 flex-col bg-[#102a25] px-4 py-5 text-white md:static md:flex`}>
          <div className="flex items-center gap-3 px-2">
            <div className="grid size-9 place-items-center rounded-xl bg-[#d8ff72] text-[#102a25]"><Home className="size-4" /></div>
            <span className="font-semibold tracking-tight">Clairimmo</span>
          </div>
          <nav className="mt-10 space-y-1" aria-label="Navigation principale">
            <NavItem icon={Gauge} label="Vue d’ensemble" active />
            <NavItem icon={FolderOpen} label="Documents" />
            <NavItem icon={ShieldAlert} label="Alertes" count="3" />
          </nav>
          <div className="mt-auto rounded-2xl border border-white/10 bg-white/5 p-4">
            <div className="mb-3 flex items-center justify-between text-xs text-white/70"><span>Dossier complété</span><span>62%</span></div>
            <Progress value={62} className="bg-white/10 [&_[data-slot=progress-indicator]]:bg-[#d8ff72]" />
            <button className="mt-4 flex w-full items-center justify-between text-left text-sm font-medium">3 pièces manquantes <ArrowRight className="size-4" /></button>
          </div>
        </aside>

        {mobileNav && <button aria-label="Fermer le menu" className="fixed inset-0 z-30 bg-black/30 md:hidden" onClick={() => setMobileNav(false)} />}

        <section className="min-w-0 flex-1">
          <header className="flex h-18 items-center gap-3 border-b border-[#dfe4dd] bg-white/80 px-5 backdrop-blur md:px-8">
            <button className="md:hidden" aria-label="Ouvrir le menu" onClick={() => setMobileNav(true)}><Menu className="size-5" /></button>
            <div className="min-w-0">
              <p className="text-xs font-medium text-[#6a7b74]">DOSSIER D’ACHAT</p>
              <h1 className="truncate text-sm font-semibold sm:text-base">Appartement · Paris 12e</h1>
            </div>
            <div className="ml-auto hidden items-center gap-2 rounded-xl border bg-white px-3 py-2 text-sm text-[#6a7b74] sm:flex"><Search className="size-4" /> Rechercher</div>
            <Button className="rounded-xl bg-[#173f35] text-white hover:bg-[#102a25]"><Upload className="size-4" /><span className="hidden sm:inline">Ajouter</span></Button>
          </header>

          <div className="p-5 md:p-8 lg:p-10">
            <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
              <div>
                <p className="mb-2 text-sm text-[#6a7b74]">Analyse mise à jour il y a 4 min</p>
                <h2 className="text-3xl font-semibold tracking-[-0.04em] md:text-4xl">Ce qui mérite votre attention.</h2>
              </div>
              <div className="flex items-center gap-2 rounded-full border border-[#cfd8d2] bg-white px-4 py-2 text-sm font-medium"><span className="size-2 rounded-full bg-[#ee6955]" /> 3 risques importants</div>
            </div>

            <div className="grid gap-4 xl:grid-cols-[1.35fr_.65fr]">
              <section className="rounded-[24px] border border-[#dfe4dd] bg-white p-5 md:p-6">
                <div className="mb-5 flex items-center justify-between">
                  <div><p className="text-xs font-semibold uppercase tracking-[.12em] text-[#789087]">Prioritaire</p><h3 className="mt-1 text-xl font-semibold">Alertes</h3></div>
                  <Button variant="ghost" size="sm" className="text-[#315e52]">Tout voir <ArrowRight className="size-4" /></Button>
                </div>
                <div className="divide-y divide-[#e7ebe7]">
                  {risks.map((item, index) => <CompactRow key={item.title} item={item} index={index} onClick={() => setDetail(item)} />)}
                </div>
              </section>

              <section className="rounded-[24px] bg-[#173f35] p-6 text-white">
                <div className="flex items-start justify-between"><div><p className="text-xs font-semibold uppercase tracking-[.12em] text-white/55">Dossier</p><p className="mt-2 text-4xl font-semibold">62%</p></div><FileCheck2 className="size-6 text-[#d8ff72]" /></div>
                <Progress value={62} className="mt-7 bg-white/10 [&_[data-slot=progress-indicator]]:bg-[#d8ff72]" />
                <div className="mt-6 grid grid-cols-3 gap-3 border-t border-white/10 pt-5 text-sm"><Stat value="16" label="reçus" /><Stat value="3" label="manquants" /><Stat value="2" label="en cours" /></div>
              </section>
            </div>

            <section className="mt-4 grid grid-cols-2 gap-3 lg:grid-cols-4">
              {categories.map(({ label, value, icon: Icon, tone }) => (
                <button key={label} className="group flex items-center gap-3 rounded-2xl border border-[#dfe4dd] bg-white p-4 text-left transition hover:-translate-y-0.5 hover:border-[#9eb4aa] hover:shadow-sm">
                  <span className={`grid size-10 shrink-0 place-items-center rounded-xl ${tone === "red" ? "bg-[#fff0ed] text-[#c9513f]" : "bg-[#fff7df] text-[#a46d0c]"}`}><Icon className="size-5" /></span>
                  <span className="min-w-0"><span className="block truncate text-sm font-semibold">{label}</span><span className="text-xs text-[#6a7b74]">{value}</span></span>
                  <ChevronRight className="ml-auto size-4 text-[#9aaba4] transition group-hover:translate-x-0.5" />
                </button>
              ))}
            </section>

            <div className="mt-4 grid gap-4 xl:grid-cols-[.65fr_1.35fr]">
              <section className="rounded-[24px] border border-[#dfe4dd] bg-[#fff9e9] p-5 md:p-6">
                <div className="mb-4 flex items-center justify-between"><div><p className="text-xs font-semibold uppercase tracking-[.12em] text-[#9c7728]">Avant compromis</p><h3 className="mt-1 text-lg font-semibold">Documents manquants</h3></div><Badge className="bg-[#f7d978] text-[#5d4715]">3</Badge></div>
                <div className="space-y-2">
                  {missing.map(item => <button key={item.title} onClick={() => setDetail(item)} className="flex w-full items-center gap-3 rounded-xl bg-white/70 p-3 text-left transition hover:bg-white"><span className="size-2 rounded-full bg-[#e2a727]" /><span className="min-w-0"><span className="block truncate text-sm font-semibold">{item.title}</span><span className="block truncate text-xs text-[#81724f]">{item.subtitle}</span></span><ChevronRight className="ml-auto size-4" /></button>)}
                </div>
              </section>

              <section className="rounded-[24px] border border-[#dfe4dd] bg-white p-5 md:p-6">
                <div className="mb-4 flex items-center justify-between"><div><p className="text-xs font-semibold uppercase tracking-[.12em] text-[#789087]">Bibliothèque</p><h3 className="mt-1 text-lg font-semibold">Documents analysés</h3></div><Button variant="outline" size="sm" className="rounded-xl">Ouvrir</Button></div>
                <div className="grid gap-2 sm:grid-cols-2">
                  {documents.map(item => <button key={item.title} onClick={() => setDetail(item)} className="flex items-center gap-3 rounded-xl border border-[#e7ebe7] p-3 text-left transition hover:border-[#9eb4aa] hover:bg-[#f7f9f6]"><span className="grid size-9 shrink-0 place-items-center rounded-lg bg-[#eef2ef]"><FileText className="size-4" /></span><span className="min-w-0"><span className="block truncate text-sm font-semibold">{item.title}</span><span className="block truncate text-xs text-[#6a7b74]">{item.subtitle}</span></span><ChevronRight className="ml-auto size-4 text-[#9aaba4]" /></button>)}
                </div>
              </section>
            </div>
          </div>
        </section>
      </div>

      <Sheet open={!!detail} onOpenChange={(open) => !open && setDetail(null)}>
        <SheetContent className="w-full border-[#dfe4dd] sm:max-w-[520px]">
          {detail && <>
            <SheetHeader className="border-b border-[#e7ebe7] p-6 pr-12">
              <div className="mb-3 flex items-center gap-2">
                {detail.severity && <StatusBadge severity={detail.severity} />}
                <span className="text-xs font-medium uppercase tracking-[.1em] text-[#789087]">{detail.kind === "risk" ? "Alerte détectée" : detail.kind === "missing" ? "Document requis" : "Document"}</span>
              </div>
              <SheetTitle className="text-2xl tracking-tight">{detail.title}</SheetTitle>
              <SheetDescription>{detail.subtitle}</SheetDescription>
            </SheetHeader>
            <div className="flex-1 space-y-6 overflow-y-auto p-6">
              {detail.kind === "risk" && <>
                <InfoBlock icon={CircleHelp} title="Pourquoi c’est important">Ce point peut modifier le coût réel de l’achat ou vos obligations après la signature.</InfoBlock>
                <div><p className="mb-2 text-xs font-semibold uppercase tracking-[.1em] text-[#789087]">Source</p><button className="flex w-full items-center gap-3 rounded-2xl border border-[#dfe4dd] p-4 text-left hover:bg-[#f7f9f6]"><FileText className="size-5 text-[#315e52]" /><span><span className="block text-sm font-semibold">{detail.source}</span><span className="text-xs text-[#6a7b74]">Ouvrir dans le document</span></span><ChevronRight className="ml-auto size-4" /></button></div>
                <div><p className="mb-2 text-xs font-semibold uppercase tracking-[.1em] text-[#789087]">Extrait détecté</p><blockquote className="rounded-2xl border-l-4 border-[#e9a597] bg-[#fff4f1] p-4 text-sm leading-6 text-[#57332d]">“{detail.excerpt}”</blockquote></div>
              </>}
              {detail.kind === "missing" && <>
                <InfoBlock icon={AlertTriangle} title="Pourquoi le demander">Il complète les vérifications nécessaires avant de vous engager définitivement.</InfoBlock>
                <div className="rounded-2xl bg-[#f2f5f2] p-4"><p className="text-xs text-[#6a7b74]">Responsable suggéré</p><p className="mt-1 font-semibold">{detail.subtitle.replace("À demander au ", "")}</p></div>
              </>}
              {detail.kind === "document" && <>
                <InfoBlock icon={FileCheck2} title="Analyse terminée">Le document a été lu et les points utiles ont été reliés aux pages sources.</InfoBlock>
                <div className="grid grid-cols-2 gap-3"><MiniMetric label="Pages" value="24" /><MiniMetric label="Confiance" value="94%" /></div>
              </>}
            </div>
            <SheetFooter className="border-t border-[#e7ebe7] p-6">
              <Button className="h-11 rounded-xl bg-[#173f35] text-white hover:bg-[#102a25]">{detail.kind === "risk" ? "Voir la source" : detail.kind === "missing" ? "Préparer la demande" : "Ouvrir le document"}<ArrowRight className="size-4" /></Button>
            </SheetFooter>
          </>}
        </SheetContent>
      </Sheet>
    </main>
  );
}

function NavItem({ icon: Icon, label, active, count }: { icon: typeof Home; label: string; active?: boolean; count?: string }) {
  return <button className={`flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition ${active ? "bg-white text-[#102a25]" : "text-white/65 hover:bg-white/10 hover:text-white"}`}><Icon className="size-4" /><span>{label}</span>{count && <span className="ml-auto rounded-full bg-[#ef6c59] px-2 py-0.5 text-[10px] font-bold text-white">{count}</span>}</button>;
}

function CompactRow({ item, index, onClick }: { item: Detail; index: number; onClick: () => void }) {
  return <button onClick={onClick} className="group flex w-full items-center gap-4 py-4 text-left first:pt-1 last:pb-1"><span className={`grid size-10 shrink-0 place-items-center rounded-xl ${index < 2 ? "bg-[#fff0ed] text-[#c9513f]" : "bg-[#fff7df] text-[#a46d0c]"}`}><AlertTriangle className="size-4" /></span><span className="min-w-0"><span className="block truncate text-sm font-semibold sm:text-base">{item.title}</span><span className="block truncate text-xs text-[#6a7b74] sm:text-sm">{item.subtitle}</span></span><ChevronRight className="ml-auto size-5 text-[#9aaba4] transition group-hover:translate-x-1" /></button>;
}

function Stat({ value, label }: { value: string; label: string }) { return <div><p className="text-xl font-semibold">{value}</p><p className="text-xs text-white/55">{label}</p></div>; }

function StatusBadge({ severity }: { severity: NonNullable<Detail["severity"]> }) {
  const styles = severity === "Critique" ? "bg-[#fff0ed] text-[#b84030]" : severity === "Validé" ? "bg-[#e9f7e9] text-[#28713d]" : "bg-[#fff7df] text-[#8b5e0b]";
  return <Badge className={`${styles} border-0`}>{severity === "Validé" && <Check className="size-3" />}{severity}</Badge>;
}

function InfoBlock({ icon: Icon, title, children }: { icon: typeof Home; title: string; children: React.ReactNode }) { return <div className="rounded-2xl bg-[#eef5f1] p-4"><div className="flex items-center gap-2 font-semibold"><Icon className="size-4 text-[#315e52]" />{title}</div><p className="mt-2 text-sm leading-6 text-[#52655e]">{children}</p></div>; }

function MiniMetric({ label, value }: { label: string; value: string }) { return <div className="rounded-2xl border border-[#dfe4dd] p-4"><p className="text-xs text-[#6a7b74]">{label}</p><p className="mt-1 text-xl font-semibold">{value}</p></div>; }
