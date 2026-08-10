import { expect, test } from "@playwright/test";

test("user can complete a full puzzle cycle", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByTestId("generate-button")).toBeVisible();
  await page.getByTestId("generate-button").click();
  await expect(page.getByTestId("options-grid")).toBeVisible({ timeout: 15_000 });
  await expect(page.locator("[data-action='select-option']")).toHaveCount(6);

  const initialPuzzleNumber = Number(await page.getByTestId("puzzle-number").innerText());
  await page.getByTestId("option-0").click();

  await expect(
    page.locator(".feedback.feedback--correct, .feedback.feedback--incorrect")
  ).toHaveCount(1);
  await expect(page.getByTestId("correct-answer")).toBeVisible();
  await expect(page.getByTestId("explanation-text")).not.toBeEmpty();
  await expect(page.getByTestId("option-0")).toBeDisabled();

  await page.getByTestId("next-puzzle-button").click();
  await expect(page.getByTestId("puzzle-number")).not.toHaveText(String(initialPuzzleNumber));
});

test("session statistics update after answering", async ({ page }) => {
  await page.goto("/");

  const startingScore = Number(await page.getByTestId("current-score").innerText());
  await page.getByTestId("option-1").click();

  const gotCorrect = (await page.locator("p.feedback.feedback--correct").count()) > 0;
  const finalScore = Number(await page.getByTestId("current-score").innerText());

  if (gotCorrect) {
    expect(finalScore).toBe(startingScore + 1);
  } else {
    expect(finalScore).toBe(startingScore);
  }
});

test("health page renders backend diagnostics", async ({ page }) => {
  await page.goto("/health-check");

  await expect(page.getByRole("heading", { level: 1, name: /driftskontroll/i })).toBeVisible();
  await expect(page.locator(".health-item")).toHaveCount(6);
  await expect(page.locator(".health-item span")).toHaveCount(6);
  await expect(page.locator(".health-item strong")).toHaveCount(6);

  const values = await page.locator(".health-item strong").allTextContents();
  for (const value of values) {
    expect(value.trim()).not.toBe("");
    expect(value.trim()).not.toBe("--");
  }
});
