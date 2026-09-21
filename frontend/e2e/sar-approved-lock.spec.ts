import { expect, test, type Page } from "@playwright/test";
import {
  apiLogin,
  fillRemainingSubcriteria,
  patchSubcriteria,
  seedInstitution,
  type SeededInstitution,
} from "./support/backend";
import { msg, msgPattern, type Lang } from "./support/i18n";

/**
 * "Izlaz Faze 1" (CLAUDE.md Sekcija 4): jedna institucija kompletno sprovodi
 * SAR od unosa do Approved Lock-a — kroz pravi UI, na OBA jezika (6.3).
 *
 * Tok: CAFLead kreira SAR -> Wizard 1.1 (unos, AI predlog, dokaz, sledeći
 * korak ostaje na istom jeziku) -> ostalih 27 preko API-ja -> CIP stavka ->
 * Sponsor vidi radar i odobrava -> sve je zaključano (UI i API).
 */

const EVIDENCE =
  "Rukovodstvo je donijelo strateški plan sa jasno definisanim ciljevima i prioritetima. " +
  "Plan je sproveden kroz obuke zaposlenih i redovne sastanke, a sprovođenje se prati kroz " +
  "kvartalne izvještaje i ankete. Na osnovu analize procesi su unaprijeđeni.";
const WEAKNESSES = "Povratne informacije zaposlenih se ne prikupljaju sistematski.";
const PDF = Buffer.from("%PDF-1.4\n% E2E dokaz\n1 0 obj << >> endobj\ntrailer << >>\n%%EOF\n");
const AV_DISABLED = process.env.E2E_AV_DISABLED === "1";

async function login(page: Page, lang: Lang, email: string, password: string): Promise<void> {
  await page.goto(`/${lang}/login`);
  await page.getByLabel(msg(lang, "Login", "emailLabel"), { exact: true }).fill(email);
  await page.getByLabel(msg(lang, "Login", "passwordLabel"), { exact: true }).fill(password);
  await page.getByLabel(msg(lang, "Login", "languageLabel"), { exact: true }).selectOption(lang);
  await page.getByRole("button", { name: msg(lang, "Login", "submit"), exact: true }).click();
  // Duži timeout SAMO ovdje: prva prijava u CI-ju pogađa "cold start"
  // kompilaciju Next.js Server Action-a u dev modu (next dev kompajlira na
  // prvi poziv, ne unaprijed) — na GitHub-ovom 2-jezgarnom runneru to zna
  // trajati duže od podrazumijevanog expect timeout-a (15s). Sve naredne
  // provjere u testu koriste podrazumijevani timeout jer je ruta/akcija
  // do tada već kompajlirana.
  await expect(page).toHaveURL(new RegExp(`/${lang}/dashboard$`), { timeout: 45_000 });
  await expect(page.locator("html")).toHaveAttribute("lang", lang);
}

async function logout(page: Page, lang: Lang): Promise<void> {
  await page.getByRole("button", { name: msg(lang, "Nav", "logout"), exact: true }).click();
  await expect(page).toHaveURL(new RegExp(`/${lang}/login$`));
}

async function saveWizardStep(page: Page, lang: Lang, code: string): Promise<void> {
  const saved = page.waitForResponse(
    (r) => r.request().method() === "POST" && r.url().includes(`/wizard/${code}`)
  );
  await page.getByRole("button", { name: msg(lang, "Wizard", "save"), exact: true }).click();
  expect((await saved).ok()).toBe(true);
  await expect(page.getByText(msg(lang, "Wizard", "saved"), { exact: true })).toBeVisible();
}

for (const lang of ["me", "en"] as const) {
  test(`SAR od unosa do Approved Lock-a [${lang}]`, async ({ page }) => {
    const seed: SeededInstitution = seedInstitution();

    // ---------------------------------------------------------------- //
    // 1. CAFLead kreira SAR
    // ---------------------------------------------------------------- //
    await login(page, lang, seed.lead, seed.password);
    await page.getByRole("button", { name: msg(lang, "Sar", "createSar"), exact: true }).click();
    await page.waitForURL(new RegExp(`/${lang}/sar/[0-9a-f-]{36}$`));
    const sarId = page.url().split("/").pop() as string;
    await expect(
      page.getByText(msg(lang, "Sar", "progressLabel", { done: 0, total: 28 }))
    ).toBeVisible();

    // ---------------------------------------------------------------- //
    // 2. Wizard 1.1 — unos, AI predlog (human-in-the-loop), dokaz
    // ---------------------------------------------------------------- //
    await page.goto(`/${lang}/wizard/1.1`);
    await expect(page.getByRole("heading", { level: 1 })).not.toBeEmpty();

    const aiButton = page.getByRole("button", { name: msg(lang, "Wizard", "aiConsensusButton") });
    await aiButton.click();
    await expect(page.getByText(msg(lang, "Errors", "consensus_needs_evidence"))).toBeVisible();

    await page.getByLabel(msg(lang, "Wizard", "evidenceLabel"), { exact: true }).fill(EVIDENCE);
    await page.getByLabel(msg(lang, "Wizard", "weaknessesLabel"), { exact: true }).fill(WEAKNESSES);
    const scoreSelect = page.getByLabel(msg(lang, "Wizard", "scoreLabel"), { exact: true });
    await scoreSelect.selectOption("1");
    await saveWizardStep(page, lang, "1.1");

    await aiButton.click();
    await expect(page.getByText(msg(lang, "Wizard", "aiSourceFallback"))).toBeVisible();
    const suggestionText = await page
      .getByText(msgPattern(lang, "Wizard", "suggestedScoreLabel", "score"))
      .innerText();
    const suggested = suggestionText.match(/(\d)\s*$/)?.[1];
    expect(suggested).toBeDefined();
    // Predlog se NE upisuje sam: poslije prihvatanja mijenja se samo izbor u formi.
    await page.getByRole("button", { name: msg(lang, "Wizard", "aiConsensusAccept") }).click();
    await expect(scoreSelect).toHaveValue(suggested as string);
    await expect(page.getByLabel(msg(lang, "Wizard", "evidenceLabel"), { exact: true })).toHaveValue(
      EVIDENCE
    );
    await saveWizardStep(page, lang, "1.1");
    await page.reload();
    await expect(scoreSelect).toHaveValue(suggested as string);

    await page.locator('input[type="file"][name="file"]').setInputFiles({
      name: "e2e-dokaz.pdf",
      mimeType: "application/pdf",
      buffer: PDF,
    });
    await page.getByRole("button", { name: msg(lang, "Evidence", "uploadButton") }).click();
    await expect(
      page.getByText(msg(lang, "Evidence", "uploadSuccess", { filename: "e2e-dokaz.pdf" }))
    ).toBeVisible();
    await expect(
      page.getByText(msg(lang, "Evidence", AV_DISABLED ? "scanPending" : "scanClean"), {
        exact: true,
      })
    ).toBeVisible();

    // Regresija (16.9.2026): "Sledeći" je prebacivao engleski UI na crnogorski.
    await page.getByRole("link", { name: new RegExp(msg(lang, "Wizard", "nextStep")) }).click();
    await expect(page).toHaveURL(new RegExp(`/${lang}/wizard/1\\.2$`));
    await expect(page.locator("html")).toHaveAttribute("lang", lang);

    // ---------------------------------------------------------------- //
    // 3. Ostalih 27 podkriterijuma preko API-ja
    // ---------------------------------------------------------------- //
    const leadToken = await apiLogin(seed.lead, seed.password, lang);
    await fillRemainingSubcriteria(leadToken, sarId, ["1.1"]);

    // ---------------------------------------------------------------- //
    // 4. CIP stavka
    // ---------------------------------------------------------------- //
    const cipTitle = `E2E CIP ${lang} ${Date.now()}`;
    await page.goto(`/${lang}/cip`);
    await page
      .getByRole("button", { name: `+ ${msg(lang, "Cip", "addItem")}` })
      .first()
      .click();
    await page.getByLabel(msg(lang, "Cip", "titleLabel"), { exact: true }).fill(cipTitle);
    await page.getByLabel(msg(lang, "Cip", "titleEnLabel"), { exact: true }).fill(cipTitle);
    await page.getByLabel(msg(lang, "Cip", "asIsLabel"), { exact: true }).fill("Nema praćenja.");
    await page.getByLabel(msg(lang, "Cip", "toBeLabel"), { exact: true }).fill("Kvartalno praćenje.");
    await page.getByRole("button", { name: msg(lang, "Cip", "create"), exact: true }).click();
    await expect(page.getByText(cipTitle)).toBeVisible();
    await page.reload();
    await expect(page.getByText(cipTitle)).toBeVisible();

    await logout(page, lang);

    // ---------------------------------------------------------------- //
    // 5. Sponsor: radar + Approved Lock
    // ---------------------------------------------------------------- //
    await login(page, lang, seed.sponsor, seed.password);
    await expect(page.getByText(msg(lang, "Sar", "maturityOverviewHeading"))).toBeVisible();
    await expect(page.getByText(msgPattern(lang, "Sar", "maturityIndexLabel", "index"))).toBeVisible();

    await page.goto(`/${lang}/sar/${sarId}`);
    await expect(
      page.getByText(msg(lang, "Sar", "progressLabel", { done: 28, total: 28 }))
    ).toBeVisible();
    page.once("dialog", (dialog) => void dialog.accept());
    const approveButton = page.getByRole("button", { name: msg(lang, "Sar", "approveButton") });
    await approveButton.click();
    await expect(page.getByText(msgPattern(lang, "Sar", "approvedBadge", "date"))).toBeVisible();
    await expect(approveButton).toHaveCount(0);

    // ---------------------------------------------------------------- //
    // 6. Sve je zaključano — UI i API
    // ---------------------------------------------------------------- //
    await page.goto(`/${lang}/wizard/1.1`);
    await expect(page.getByText(msg(lang, "Wizard", "lockedBanner"))).toBeVisible();
    await expect(page.getByLabel(msg(lang, "Wizard", "evidenceLabel"), { exact: true })).toBeDisabled();
    await expect(
      page.getByRole("button", { name: msg(lang, "Wizard", "save"), exact: true })
    ).toHaveCount(0);
    await expect(page.getByRole("button", { name: msg(lang, "Evidence", "uploadButton") })).toBeDisabled();
    await expect(page.getByRole("button", { name: msg(lang, "Wizard", "aiConsensusButton") })).toHaveCount(0);

    await page.goto(`/${lang}/cip`);
    await expect(page.getByText(msg(lang, "Cip", "lockedNote"))).toBeVisible();
    await expect(page.getByRole("button", { name: `+ ${msg(lang, "Cip", "addItem")}` })).toHaveCount(0);

    const sponsorToken = await apiLogin(seed.sponsor, seed.password, lang);
    const locked = await patchSubcriteria(sponsorToken, sarId, "1.1", 5);
    expect(locked).toEqual({ status: 409, error: "sar_locked" });
  });
}
