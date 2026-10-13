"use strict";

(function () {
  const engine = window.CohortEngine;
  const byId = id => document.getElementById(id);
  const cohortForm = byId("cohort-form");
  const auditForm = byId("audit-form");
  let records = [];

  function showStatus(id, message, isError) {
    const element = byId(id);
    element.textContent = message;
    element.classList.toggle("error", Boolean(isError));
  }

  function showPreview(rows) {
    const body = byId("cohort-preview");
    body.replaceChildren();
    for (const record of rows.slice(0, 10)) {
      const row = document.createElement("tr");
      for (const field of ["patient_id", "encounter_date", "age_years", "sex", "systolic_bp_mm_hg", "bmi_kg_m2"]) {
        const cell = document.createElement("td");
        cell.textContent = String(record[field]);
        row.appendChild(cell);
      }
      body.appendChild(row);
    }
  }

  cohortForm.addEventListener("submit", function (event) {
    event.preventDefault();
    const config = {
      count: Number(byId("count").value),
      seed: Number(byId("seed").value),
      ageMin: Number(byId("age-min").value),
      ageMax: Number(byId("age-max").value),
      femaleFraction: Number(byId("female-fraction").value),
      maxEncounters: Number(byId("max-encounters").value)
    };
    try {
      const result = engine.generateCohort(config);
      records = result;
      const unique = new Map();
      for (const record of records) unique.set(record.patient_id, record.sex);
      const assignedFemale = [...unique.values()].filter(sex => sex === "F").length;
      const mean = records.reduce((sum, row) => sum + row.systolic_bp_mm_hg, 0) / records.length;
      byId("patients-summary").textContent = unique.size.toLocaleString();
      byId("encounters-summary").textContent = records.length.toLocaleString();
      byId("female-summary").textContent = assignedFemale.toLocaleString();
      byId("systolic-summary").textContent = mean.toFixed(1);
      showPreview(records);
      byId("download-csv").disabled = false;
      byId("download-json").disabled = false;
      showStatus("cohort-status", "Generated fictional data in memory; no data was sent to a server.", false);
    } catch (error) {
      records = [];
      byId("download-csv").disabled = true;
      byId("download-json").disabled = true;
      showStatus("cohort-status", error.message, true);
    }
  });

  function download(text, mime, filename) {
    const blob = new Blob([text], { type: mime });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  byId("download-csv").addEventListener("click", () => {
    if (records.length) download(engine.toCSV(records), "text/csv;charset=utf-8", "synthetic-cohort.csv");
  });
  byId("download-json").addEventListener("click", () => {
    if (records.length) download(JSON.stringify(records, null, 2), "application/json", "synthetic-cohort.json");
  });

  auditForm.addEventListener("submit", function (event) {
    event.preventDefault();
    try {
      const dossier = engine.auditTask({
        task_id: byId("task-id").value.trim(),
        target_identifier: byId("target-id").value.trim(),
        primary_metric: Number(byId("primary-metric").value),
        secondary_metric: Number(byId("secondary-metric").value),
        status_descriptor: byId("status-descriptor").value,
        is_critical_flag: byId("critical-flag").checked
      });
      byId("audit-result").textContent = JSON.stringify(dossier, null, 2);
      showStatus("audit-status", "Rule evaluation complete (local demonstration; not a signed audit).", false);
    } catch (error) {
      byId("audit-result").textContent = "No result: invalid input.";
      showStatus("audit-status", error.message, true);
    }
  });
})();
