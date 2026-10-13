"use strict";
const { test } = require("node:test");
const assert = require("node:assert/strict");
const engine = require("../web/engine.js");
const config = {count: 20, seed: 42, ageMin: 20, ageMax: 65, femaleFraction: 0.4, maxEncounters: 3};

test("same seed and config produce identical fictional records", () => {
  const rows = engine.generateCohort(config);
  assert.deepEqual(rows, engine.generateCohort(config));
  assert.ok(rows.length >= 20 && rows.length <= 60);
  assert.equal(new Set(rows.map(row => row.patient_id)).size, 20);
  assert.equal(new Set(rows.map(row => row.encounter_id)).size, rows.length);
  for (const row of rows) {
    assert.ok(row.age_years >= 20 && row.age_years <= 65);
    assert.ok(row.systolic_bp_mm_hg >= 75 && row.systolic_bp_mm_hg <= 220);
    assert.ok(row.patient_id.startsWith("SYN-"));
  }
});

test("invalid and excessive generation parameters are rejected", () => {
  assert.throws(() => engine.generateCohort({...config, count: 2001}), /Patient count/);
  assert.throws(() => engine.generateCohort({...config, ageMin: 80, ageMax: 20}), /Maximum age/);
  assert.throws(() => engine.generateCohort({...config, femaleFraction: NaN}), /Female fraction/);
});

test("audit returns expected urgency and ignores absent anomalies", () => {
  const base = {task_id:"DEMO-1", target_identifier:"SYN-01", primary_metric:10, secondary_metric:5,
    status_descriptor:"NOMINAL", is_critical_flag:false};
  assert.equal(engine.auditTask(base).overall_urgency, "ROUTINE");
  assert.equal(engine.auditTask({...base, primary_metric:30}).total_alerts, 1);
  assert.equal(engine.auditTask({...base, is_critical_flag:true}).overall_urgency, "CRITICAL_STAT_PANIC");
  assert.equal(engine.auditTask({...base, status_descriptor:"DISCORDANT"}).total_alerts, 1);
  assert.throws(() => engine.auditTask({...base, primary_metric:Infinity}), /finite/);
  assert.throws(() => engine.auditTask({...base, task_id:"../etc/passwd"}), /identifier/);
});

test("CSV encoding preserves the schema", () => {
  const rows = engine.generateCohort({...config, count:1});
  const csv = engine.toCSV(rows);
  assert.ok(csv.startsWith('"patient_id","encounter_id"'));
  assert.ok(csv.includes(rows[0].patient_id));
  assert.equal(csv.trim().split("\r\n").length, rows.length + 1);
});
