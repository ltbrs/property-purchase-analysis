// Keep a selected PDF on this device across authentication redirects.
// Each handoff has its own identifier so separate tabs cannot mix documents.
const DATABASE_NAME = "acquora-pending-documents";
const STORE_NAME = "documents";
const RETENTION_MS = 60 * 60 * 1000;
export const MAX_DOCUMENT_SIZE = 25 * 1024 * 1024;

type PendingDocument = { id: string; file: File; expiresAt: number };

export function pdfValidationError(file: File): string | null {
  if (file.type !== "application/pdf" && !(file.type === "" && /\.pdf$/i.test(file.name))) {
    return "Choisissez un fichier PDF.";
  }
  if (file.size === 0) return "Ce fichier est vide. Choisissez un autre PDF.";
  if (file.size > MAX_DOCUMENT_SIZE) return "Ce fichier dépasse la limite de 25 Mo.";
  return null;
}

function openDatabase(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DATABASE_NAME, 1);
    request.onupgradeneeded = () => request.result.createObjectStore(STORE_NAME, { keyPath: "id" });
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(new Error("Impossible de conserver le PDF sur cet appareil. Réessayez ou commencez depuis l’app."));
  });
}

async function transaction<T>(
  mode: IDBTransactionMode,
  operation: (store: IDBObjectStore) => IDBRequest<T>,
): Promise<T> {
  const database = await openDatabase();
  return new Promise((resolve, reject) => {
    const tx = database.transaction(STORE_NAME, mode);
    const request = operation(tx.objectStore(STORE_NAME));
    tx.oncomplete = () => { database.close(); resolve(request.result); };
    tx.onabort = tx.onerror = () => {
      database.close();
      reject(new Error("Le PDF n’a pas pu être conservé sur cet appareil. Réessayez."));
    };
  });
}

async function removeExpiredDocuments() {
  const database = await openDatabase();
  await new Promise<void>((resolve, reject) => {
    const tx = database.transaction(STORE_NAME, "readwrite");
    const cursor = tx.objectStore(STORE_NAME).openCursor();
    cursor.onsuccess = () => {
      const entry = cursor.result;
      if (!entry) return;
      if ((entry.value as PendingDocument).expiresAt <= Date.now()) entry.delete();
      entry.continue();
    };
    tx.oncomplete = () => { database.close(); resolve(); };
    tx.onabort = tx.onerror = () => { database.close(); reject(tx.error); };
  });
}

export async function savePendingDocument(file: File): Promise<string> {
  const error = pdfValidationError(file);
  if (error) throw new Error(error);
  const header = await file.slice(0, 5).text();
  if (header !== "%PDF-") throw new Error("Ce fichier ne semble pas être un PDF valide.");
  await removeExpiredDocuments();
  const id = crypto.randomUUID();
  const pdf = file.type ? file : new File([file], file.name, { type: "application/pdf", lastModified: file.lastModified });
  await transaction("readwrite", (store) => store.put({ id, file: pdf, expiresAt: Date.now() + RETENTION_MS } satisfies PendingDocument));
  return id;
}

export async function getPendingDocument(id: string): Promise<File | null> {
  await removeExpiredDocuments();
  const entry = await transaction<PendingDocument | undefined>("readonly", (store) => store.get(id));
  return entry?.file ?? null;
}

export async function discardPendingDocument(id: string): Promise<void> {
  await transaction("readwrite", (store) => store.delete(id));
}
