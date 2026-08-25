/**
 * OPTIONAL — instant trigger for the GitHub Actions worker.
 *
 * Without this script the worker still runs every 30 minutes on its own.
 * With it, a new form submission starts the worker within ~1 minute.
 *
 * Setup (once):
 *  1. Open the response spreadsheet → Extensions → Apps Script.
 *  2. Paste this file, then Project Settings → Script properties → add:
 *       GITHUB_TOKEN  = fine-grained PAT with "Contents: Read and write"
 *                       on repo andyeunholee/caws-college-list-04292026
 *  3. Triggers (clock icon) → Add Trigger:
 *       function: onFormSubmit, event source: From spreadsheet,
 *       event type: On form submit.
 */

const GITHUB_REPO = "andyeunholee/caws-college-list-04292026";

function onFormSubmit(e) {
  const token = PropertiesService.getScriptProperties().getProperty("GITHUB_TOKEN");
  if (!token) {
    Logger.log("GITHUB_TOKEN script property is missing");
    return;
  }
  const url = `https://api.github.com/repos/${GITHUB_REPO}/dispatches`;
  const response = UrlFetchApp.fetch(url, {
    method: "post",
    contentType: "application/json",
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: "application/vnd.github+json",
    },
    payload: JSON.stringify({
      event_type: "survey_submitted",
      client_payload: { row: e && e.range ? e.range.getRow() : null },
    }),
    muteHttpExceptions: true,
  });
  Logger.log(`GitHub dispatch → HTTP ${response.getResponseCode()}`);
}
