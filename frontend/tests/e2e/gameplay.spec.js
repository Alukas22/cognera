import { expect, test } from "@playwright/test";

test("user can complete a full puzzle cycle", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByTestId("generate-button")).toBeVisible();
  await expect(page.getByTestId("options-grid")).toBeVisible();
  await expect(page.locator("[data-testid^='option-']")).toHaveCount(6);

  const initialPuzzleNumber = Number(await page.getByTestId("puzzle-number").innerText());
  await page.getByTestId("option-0").click();

  await expect(page.getByTestId("feedback-block")).toContainText(/Correct|Incorrect/);
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

  await expect(page.getByText("Cognera Health Check")).toBeVisible();
  await expect(page.getByText("Backend Status")).toBeVisible();
  await expect(page.getByText("Backend Version")).toBeVisible();
  await expect(page.getByText("Environment")).toBeVisible();
});
