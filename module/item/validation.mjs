const SEMVER_RE = /^\d+\.\d+\.\d+$/;

function asNumber(value, fallback = NaN) {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function ensureArray(value) {
  return Array.isArray(value) ? value : [];
}

function isObject(value) {
  return value != null && typeof value === "object" && !Array.isArray(value);
}

export function normalizeItemSystemForRuntime(system = {}) {
  const normalized = foundry.utils.deepClone(system ?? {});
  normalized.tags = ensureArray(normalized.tags);
  normalized.effects = ensureArray(normalized.effects);
  normalized.allowedPathwayIds = ensureArray(normalized.allowedPathwayIds);
  normalized.pathwayData = isObject(normalized.pathwayData) ? normalized.pathwayData : {
    displayName: "",
    theme: "",
    progressionNote: ""
  };
  normalized.sequenceData = isObject(normalized.sequenceData) ? normalized.sequenceData : {
    title: "",
    summary: "",
    milestones: []
  };

  normalized.dependencies ??= {};
  normalized.dependencies.requiresIds = ensureArray(normalized.dependencies.requiresIds);
  return normalized;
}

export function validateItemSystemForType(itemType, system = {}) {
  const normalized = normalizeItemSystemForRuntime(system);
  const errors = [];

  if (!normalized.id || typeof normalized.id !== "string") {
    errors.push("system.id is required");
  }

  const deps = normalized.dependencies;
  if (!isObject(deps)) {
    errors.push("system.dependencies is required");
  } else {
    if (!SEMVER_RE.test(String(deps.minSystemVersion ?? ""))) {
      errors.push("system.dependencies.minSystemVersion must be semver X.Y.Z");
    }
    if (!SEMVER_RE.test(String(deps.maxTestedSystemVersion ?? ""))) {
      errors.push("system.dependencies.maxTestedSystemVersion must be semver X.Y.Z");
    }
    if (!Array.isArray(deps.requiresIds)) {
      errors.push("system.dependencies.requiresIds must be an array");
    }
  }

  if (normalized.sequence != null && normalized.minSequence != null) {
    const seq = asNumber(normalized.sequence);
    const minSeq = asNumber(normalized.minSequence);
    if (Number.isFinite(seq) && Number.isFinite(minSeq) && minSeq > seq) {
      errors.push("system.minSequence cannot be greater than system.sequence");
    }
  }

  if (itemType === "pathway") {
    if (!normalized.pathwayId || typeof normalized.pathwayId !== "string") {
      errors.push("pathway items require system.pathwayId");
    }
  }

  if (itemType === "sequenceNode") {
    if (!normalized.pathwayId || typeof normalized.pathwayId !== "string") {
      errors.push("sequence nodes require system.pathwayId");
    }
    const sequence = asNumber(normalized.sequence);
    if (!Number.isInteger(sequence) || sequence < 0 || sequence > 9) {
      errors.push("sequence nodes require integer system.sequence in 0..9");
    }
  }

  if (itemType === "ability") {
    if (!isObject(normalized.abilityData)) errors.push("ability items require system.abilityData");
    if (!normalized.pathwayId || typeof normalized.pathwayId !== "string") {
      errors.push("ability items require system.pathwayId");
    }
    const sequence = asNumber(normalized.sequence);
    if (!Number.isInteger(sequence) || sequence < 0 || sequence > 9) {
      errors.push("ability items require integer system.sequence in 0..9");
    }
  }

  if (itemType === "weapon" && !isObject(normalized.weaponData)) {
    errors.push("weapon items require system.weaponData");
  }
  if (itemType === "armor" && !isObject(normalized.armorData)) {
    errors.push("armor items require system.armorData");
  }
  if (itemType === "ritual" && !isObject(normalized.ritualData)) {
    errors.push("ritual items require system.ritualData");
  }
  if (itemType === "artifact" && !isObject(normalized.artifactData)) {
    errors.push("artifact items require system.artifactData");
  }

  return {
    ok: errors.length === 0,
    errors,
    normalized
  };
}
