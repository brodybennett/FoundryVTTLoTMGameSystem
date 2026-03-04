export const SYSTEM_ID = "lotm-system";
export const WORLD_SCHEMA_VERSION = "1.2.13";

export const ATTRIBUTE_KEYS = ["str", "dex", "wil", "con", "cha", "int", "luck"];
export const SKILL_RANKS = ["untrained", "familiar", "trained", "expert", "master", "legendary"];

export const CREATION_STEPS = ["identity", "attributes", "skills", "pathway", "equipment", "complete"];

export const ROLLTABLE_SEGMENTS = ["resources", "abilities", "rituals", "artifacts", "corruption", "encounters"];

export const PROFICIENCY_BY_RANK = {
  untrained: 0,
  familiar: 5,
  trained: 10,
  expert: 15,
  master: 20,
  legendary: 25
};

export const CORRUPTION_PENALTY_BANDS = [
  { startPct: 0, endPct: 9, penalty: 0 },
  { startPct: 10, endPct: 19, penalty: -1 },
  { startPct: 20, endPct: 29, penalty: -2 },
  { startPct: 30, endPct: 39, penalty: -3 },
  { startPct: 40, endPct: 49, penalty: -4 },
  { startPct: 50, endPct: 59, penalty: -5 },
  { startPct: 60, endPct: 69, penalty: -6 },
  { startPct: 70, endPct: 79, penalty: -7 },
  { startPct: 80, endPct: 89, penalty: -8 },
  { startPct: 90, endPct: 100, penalty: -10 }
];

export const CORRUPTION_TRIGGERS = [30, 60, 90, 100];

export function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

export function resolveCorruptionPenalty(corruptionPct = 0) {
  const pct = Number(corruptionPct) || 0;
  const band = CORRUPTION_PENALTY_BANDS.find((entry) => pct >= entry.startPct && pct <= entry.endPct);
  return band ? band.penalty : -10;
}

export function semverCompare(a, b) {
  const ap = String(a).split(".").map((part) => Number(part) || 0);
  const bp = String(b).split(".").map((part) => Number(part) || 0);
  for (let i = 0; i < 3; i += 1) {
    if (ap[i] > bp[i]) return 1;
    if (ap[i] < bp[i]) return -1;
  }
  return 0;
}
