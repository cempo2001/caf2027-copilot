import { execFileSync } from "node:child_process";
import { existsSync } from "node:fs";
import path from "node:path";

/**
 * Pomoćne funkcije koje pričaju direktno sa backend-om:
 * - nova test institucija po testu (backend/scripts/seed_e2e.py)
 * - brzo popunjavanje podkriterijuma preko API-ja (UI se testira na 1.1,
 *   ostalih 27 nema smisla "klikati" u svakom prolazu)
 */
const BACKEND_DIR = process.env.E2E_BACKEND_DIR ?? path.resolve(process.cwd(), "..", "backend");
const API_URL = (process.env.E2E_API_URL ?? "http://localhost:8765").replace(/\/+$/, "");

export interface SeededInstitution {
  institution_id: string;
  sponsor: string;
  lead: string;
  password: string;
}

function pythonExecutable(): string {
  if (process.env.E2E_PYTHON) return process.env.E2E_PYTHON;
  const venvPython =
    process.platform === "win32"
      ? path.join(BACKEND_DIR, ".venv", "Scripts", "python.exe")
      : path.join(BACKEND_DIR, ".venv", "bin", "python");
  return existsSync(venvPython) ? venvPython : "python";
}

export function seedInstitution(): SeededInstitution {
  const output = execFileSync(pythonExecutable(), ["scripts/seed_e2e.py"], {
    cwd: BACKEND_DIR,
    encoding: "utf-8",
  });
  const lastLine = output.trim().split(/\r?\n/).pop() ?? "";
  return JSON.parse(lastLine) as SeededInstitution;
}

async function api<T>(
  method: string,
  pathName: string,
  token?: string,
  body?: unknown
): Promise<{ status: number; body: T }> {
  const response = await fetch(`${API_URL}/api/v1${pathName}`, {
    method,
    headers: {
      Accept: "application/json",
      ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  return { status: response.status, body: (await response.json()) as T };
}

export async function apiLogin(email: string, password: string, lang: string): Promise<string> {
  const { status, body } = await api<{ access_token: string }>("POST", "/auth/login", undefined, {
    email,
    password,
    lang,
  });
  if (status !== 200) throw new Error(`API login nije uspio (${status}) za ${email}`);
  return body.access_token;
}

export async function fillRemainingSubcriteria(
  token: string,
  sarId: string,
  skipCodes: string[]
): Promise<void> {
  const { body } = await api<{ subcriteria_scores: { subcriteria_code: string }[] }>(
    "GET",
    `/self-assessments/${sarId}`,
    token
  );
  for (const { subcriteria_code: code } of body.subcriteria_scores) {
    if (skipCodes.includes(code)) continue;
    const result = await api("PATCH", `/self-assessments/${sarId}/subcriteria/${code}`, token, {
      evidence_text: "E2E dokaz: plan je definisan, sproveden, praćen kroz izvještaje i unaprijeđen.",
      weaknesses_text: "E2E slabost: nedovoljno sistematsko mjerenje.",
      score: 3,
    });
    if (result.status !== 200) throw new Error(`PATCH ${code} vratio ${result.status}`);
  }
}

export async function patchSubcriteria(
  token: string,
  sarId: string,
  code: string,
  score: number
): Promise<{ status: number; error?: string }> {
  const { status, body } = await api<{ error?: string }>(
    "PATCH",
    `/self-assessments/${sarId}/subcriteria/${code}`,
    token,
    { score }
  );
  return { status, error: body.error };
}
