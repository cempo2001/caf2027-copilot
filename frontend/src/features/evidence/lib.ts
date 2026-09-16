import type { EvidenceUploadResponse } from "@/types/api";

export interface UploadEvidenceState {
  status: "idle" | "success" | "error";
  errorKey: string | null;
  /** HTTP status kad je status "error" — 404 znači "ruta ne postoji" (backend je nema još), ne pouzdaj se u `errorKey` za to (FastAPI-jev default 404 nema `{error,message}` envelope). */
  httpStatus?: number;
  result?: EvidenceUploadResponse;
}

export const INITIAL_UPLOAD_STATE: UploadEvidenceState = {
  status: "idle",
  errorKey: null,
};

/** 25 MB — razuman klijentski limit dok backend (6.1) ne objavi svoj (kontrakt ga ne navodi). */
export const MAX_EVIDENCE_FILE_BYTES = 25 * 1024 * 1024;
