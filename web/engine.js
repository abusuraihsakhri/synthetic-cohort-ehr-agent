/* Illustrative local-only synthetic EHR and rule-based audit engines. */
(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  if (root) root.CohortEngine = api;
})(typeof window !== "undefined" ? window : globalThis, function () {
  "use strict";

  const fields = [
    "patient_id", "encounter_id", "encounter_date", "age_years", "sex",
    "bmi_kg_m2", "systolic_bp_mm_hg", "diastolic_bp_mm_hg",
    "heart_rate_bpm", "creatinine_mg_dl", "bp_flag"
  ];

  function validateInteger(value, name, min, max) {
    if (!Number.isInteger(value) || value < min || value > max) {
      throw new Error(name + " must be an integer between " + min + " and " + max);
    }
  }

  function validateCohortConfig(config) {
    validateInteger(config.count, "Patient count", 1, 2000);
    validateInteger(config.seed, "Seed", 0, 4294967295);
    validateInteger(config.ageMin, "Minimum age", 0, 110);
    validateInteger(config.ageMax, "Maximum age", config.ageMin, 110);
    if (typeof config.femaleFraction !== "number" ||
        !Number.isFinite(config.femaleFraction) ||
        config.femaleFraction < 0 || config.femaleFraction > 1) {
      throw new Error("Female fraction must be between 0 and 1");
    }
    validateInteger(config.maxEncounters, "Maximum encounters", 1, 5);
  }

  function seededRandom(seed) {
    let state = seed >>> 0;
    return function () {
      state = (state + 0x6D2B79F5) >>> 0;
      let t = state;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  function normal(rng, mean, sd) {
    const u = Math.max(rng(), Number.MIN_VALUE);
    const v = rng();
    return mean + sd * Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
  }
  function clamp(value, min, max) {
    return Math.max(min, Math.min(max, value));
  }
  function round(value, places) {
    const scale = Math.pow(10, places);
    return Math.round(value * scale) / scale;
  }

  function generateCohort(config) {
    validateCohortConfig(config);
    const rng = seededRandom(config.seed);
    const records = [];
    const start = Date.UTC(2025, 0, 1);
    for (let i = 0; i < config.count; i++) {
      const patientId = "SYN-" + config.seed.toString(16).toUpperCase().padStart(8, "0") +
        "-" + String(i + 1).padStart(5, "0");
      const age = config.ageMin + Math.floor(rng() * (config.ageMax - config.ageMin + 1));
      const sex = rng() < config.femaleFraction ? "F" : "M";
      const bmi = round(clamp(normal(rng, 26, 4.5), 14, 48), 1);
      const creatinineBase = sex === "F" ? 0.72 : 0.90;
      const firstDay = Math.floor(rng() * 281);
      const encounters = 1 + Math.floor(rng() * config.maxEncounters);
      for (let j = 0; j < encounters; j++) {
        const systolic = Math.round(clamp(normal(rng, 105 + 0.43 * age + 0.65 * (bmi - 25), 12), 75, 220));
        const diastolic = Math.round(clamp(normal(rng, 69 + 0.16 * age + 0.2 * (bmi - 25), 8), 40, 135));
        const heartRate = Math.round(clamp(normal(rng, 74, 11), 40, 150));
        const creatinine = round(clamp(normal(rng, creatinineBase + 0.002 * age, 0.17), 0.3, 4.0), 2);
        records.push({
          patient_id: patientId,
          encounter_id: patientId + "-E" + (j + 1),
          encounter_date: new Date(start + (firstDay + 21 * j) * 86400000).toISOString().slice(0, 10),
          age_years: age,
          sex: sex,
          bmi_kg_m2: bmi,
          systolic_bp_mm_hg: systolic,
          diastolic_bp_mm_hg: diastolic,
          heart_rate_bpm: heartRate,
          creatinine_mg_dl: creatinine,
          bp_flag: systolic >= 140 ? "elevated_systolic_example" : "none"
        });
      }
    }
    return records;
  }

  function auditTask(task) {
    for (const key of ["task_id", "target_identifier"]) {
      if (!/^[A-Za-z0-9_.:-]{1,256}$/.test(task[key] || "")) {
        throw new Error(key + " must be a simple non-empty identifier");
      }
    }
    if (typeof task.status_descriptor !== "string" ||
        !task.status_descriptor || task.status_descriptor.length > 256) {
      throw new Error("Status descriptor must contain 1–256 characters");
    }
    if (!Number.isFinite(task.primary_metric) || !Number.isFinite(task.secondary_metric)) {
      throw new Error("Metrics must be finite numbers");
    }
    const alerts = [];
    if (task.primary_metric > 25) {
      alerts.push({
        worker: "InvariantQCWorker", urgency: "ELEVATED_RISK",
        summary: "Primary metric threshold exceeded",
        details: "Primary measurement exceeds demo threshold of 25."
      });
    }
    if (task.is_critical_flag || task.secondary_metric > 12) {
      alerts.push({
        worker: "SafetyEscalationWorker",
        urgency: task.is_critical_flag ? "CRITICAL_STAT_PANIC" : "ELEVATED_RISK",
        summary: "Safety escalation trigger",
        details: "Critical flag is set or secondary metric exceeds demo threshold of 12."
      });
    }
    if (/(DISCORDANT|ANOMALY|MUTANT|VIOLATION|FAIL|REJECT)/i.test(task.status_descriptor)) {
      alerts.push({
        worker: "ProtocolConformanceWorker", urgency: "ELEVATED_RISK",
        summary: "Descriptor-based rule triggered",
        details: "Status descriptor matched an anomaly keyword."
      });
    }
    const critical = alerts.some(a => a.urgency === "CRITICAL_STAT_PANIC");
    const elevated = alerts.length > 0;
    return {
      mode: "local demonstration (not a clinical assessment or signed audit)",
      task_id: task.task_id,
      target_identifier: task.target_identifier,
      overall_urgency: critical ? "CRITICAL_STAT_PANIC" : elevated ? "ELEVATED_RISK" : "ROUTINE",
      integrity_status: critical ? "RECALIBRATION_REQUIRED" : elevated ? "DISCORDANT_ANOMALY" : "VALIDATED_OPTIMAL",
      total_alerts: alerts.length,
      alerts
    };
  }

  function toCSV(rows) {
    const cell = value => '"' + String(value == null ? "" : value).replace(/"/g, '""') + '"';
    return [fields.map(cell).join(","), ...rows.map(row => fields.map(field => cell(row[field])).join(","))].join("\r\n") + "\r\n";
  }

  return { fields, generateCohort, auditTask, toCSV };
});
