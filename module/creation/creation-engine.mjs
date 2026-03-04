import { ATTRIBUTE_KEYS, CREATION_STEPS, SKILL_RANKS, SYSTEM_ID } from "../constants.mjs";

const SKILL_REGISTRY_FALLBACK = [
  { id: "ritualism", linkedAttr: "wil" },
  { id: "investigation", linkedAttr: "int" },
  { id: "perception", linkedAttr: "int" },
  { id: "insight", linkedAttr: "wil" },
  { id: "persuasion", linkedAttr: "cha" },
  { id: "deception", linkedAttr: "cha" },
  { id: "intimidation", linkedAttr: "cha" },
  { id: "etiquette", linkedAttr: "cha" },
  { id: "willpower", linkedAttr: "wil" },
  { id: "endurance", linkedAttr: "con" },
  { id: "medicine", linkedAttr: "int" },
  { id: "occult", linkedAttr: "int" },
  { id: "athletics", linkedAttr: "str" },
  { id: "melee", linkedAttr: "str" },
  { id: "firearms", linkedAttr: "dex" },
  { id: "stealth", linkedAttr: "dex" },
  { id: "acrobatics", linkedAttr: "dex" },
  { id: "streetwise", linkedAttr: "int" },
  { id: "commerce", linkedAttr: "int" },
  { id: "crafting", linkedAttr: "int" }
];

let skillRegistryCache = null;

function ensureNumber(value, fallback = NaN) {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function normalizePathwayId(value) {
  if (typeof value !== "string") return "";
  return value.trim();
}

function hasExplicitSequence(value) {
  return !(value === "" || value == null);
}

function toOwnedItemObjects(items) {
  if (!Array.isArray(items)) return [];
  return items.map((item) => {
    if (item?.toObject) return item.toObject(false);
    return item;
  });
}

function pathwayLabel(pathwayId) {
  if (!pathwayId || typeof pathwayId !== "string") return "Unknown Pathway";
  const token = pathwayId.split(".").pop() ?? "unknown";
  return token
    .split("_")
    .filter((part) => part)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function normalizeSkillRegistryEntries(entries) {
  if (!Array.isArray(entries) || entries.length === 0) return [...SKILL_REGISTRY_FALLBACK];
  const seen = new Set();
  const normalized = [];
  for (const entry of entries) {
    const id = entry?.id;
    const linkedAttr = entry?.linkedAttr;
    if (typeof id !== "string" || !ATTRIBUTE_KEYS.includes(linkedAttr)) continue;
    if (seen.has(id)) continue;
    seen.add(id);
    normalized.push({ id, linkedAttr });
  }
  return normalized.length > 0 ? normalized : [...SKILL_REGISTRY_FALLBACK];
}

function normalizeActorState(actorOrData = {}) {
  if (actorOrData?.system) {
    return {
      system: actorOrData.system ?? {},
      type: actorOrData.type ?? "character",
      items: toOwnedItemObjects(actorOrData.items ?? [])
    };
  }

  return {
    system: actorOrData.system ?? actorOrData ?? {},
    type: actorOrData.type ?? "character",
    items: toOwnedItemObjects(actorOrData.items ?? [])
  };
}

async function getPathwayPack() {
  const packId = `${SYSTEM_ID}.pathways`;
  return game.packs?.get(packId) ?? null;
}

export async function getSkillRegistryEntries() {
  if (skillRegistryCache) return [...skillRegistryCache];

  const registryPath = `systems/${SYSTEM_ID}/data/skills.registry.v1.1.json`;
  try {
    const response = await fetch(registryPath, { cache: "no-store" });
    if (!response.ok) throw new Error(`Failed fetch ${registryPath}`);
    const payload = await response.json();
    skillRegistryCache = normalizeSkillRegistryEntries(payload?.skills ?? []);
  } catch (err) {
    console.warn("LoTM failed to load skills registry from file; using fallback registry", err);
    skillRegistryCache = [...SKILL_REGISTRY_FALLBACK];
  }

  return [...skillRegistryCache];
}

export function buildDefaultSkills(skillRegistryEntries = []) {
  const entries = normalizeSkillRegistryEntries(skillRegistryEntries);
  const defaults = {};
  for (const entry of entries) {
    defaults[entry.id] = {
      linkedAttr: entry.linkedAttr,
      rank: "familiar",
      misc: 0
    };
  }
  return defaults;
}

export async function getPathwayOptions() {
  const pack = await getPathwayPack();
  if (!pack) return [];

  const docs = await pack.getDocuments();
  return docs
    .filter((doc) => doc.type === "pathway")
    .map((doc) => ({
      id: doc.system?.pathwayId ?? doc.system?.id ?? doc.id,
      name: doc.name,
      label: pathwayLabel(doc.system?.pathwayId ?? doc.system?.id)
    }))
    .sort((a, b) => a.label.localeCompare(b.label));
}

export async function getSequenceOptions(pathwayId) {
  const normalizedPathwayId = normalizePathwayId(pathwayId);
  if (!normalizedPathwayId) return [];

  const pack = await getPathwayPack();
  if (!pack) return [];

  const docs = await pack.getDocuments();
  return docs
    .filter((doc) => doc.type === "sequenceNode" && doc.system?.pathwayId === normalizedPathwayId)
    .map((doc) => ({
      id: doc.system?.id ?? doc.id,
      name: doc.name,
      pathwayId: doc.system?.pathwayId,
      sequence: Number(doc.system?.sequence)
    }))
    .filter((entry) => Number.isInteger(entry.sequence))
    .sort((a, b) => b.sequence - a.sequence);
}

export async function validateCreationStep(actorOrData, step, options = {}) {
  const actor = normalizeActorState(actorOrData);
  const system = actor.system ?? {};
  const items = actor.items ?? [];
  const identity = system.identity ?? {};

  const errors = [];
  const warnings = [];
  const stepKey = String(step ?? "draft");

  if (stepKey === "identity") {
    const pathwayOptions = options.pathwayOptions ?? await getPathwayOptions();
    const pathwayId = normalizePathwayId(identity.pathwayId);
    const sequence = ensureNumber(identity.sequence);

    if (!pathwayId) {
      if (hasExplicitSequence(identity.sequence)) {
        errors.push("Sequence must be blank when no pathway is selected.");
      }
      return { ok: errors.length === 0, errors, warnings };
    }

    const knownPathway = pathwayOptions.some((entry) => entry.id === pathwayId);
    if (!knownPathway) {
      errors.push("Selected pathway does not exist in the pathway compendium.");
      return { ok: false, errors, warnings };
    }

    if (!Number.isInteger(sequence) || sequence < 0 || sequence > 9) {
      errors.push("Sequence must be an integer in 0..9.");
      return { ok: false, errors, warnings };
    }

    const sequenceOptions = options.sequenceOptions ?? await getSequenceOptions(pathwayId);
    const hasSequence = sequenceOptions.some((entry) => entry.sequence === sequence);
    if (!hasSequence) {
      errors.push("Selected sequence is not available for the chosen pathway.");
    }

    return { ok: errors.length === 0, errors, warnings };
  }

  if (stepKey === "attributes") {
    const attrs = system.attributes ?? {};
    for (const key of ATTRIBUTE_KEYS) {
      const base = ensureNumber(attrs?.[key]?.base);
      if (!Number.isFinite(base)) {
        errors.push(`Attribute '${key}' base value is missing.`);
      } else if (base < 0 || base > 100) {
        errors.push(`Attribute '${key}' must be 0..100.`);
      }
    }
    return { ok: errors.length === 0, errors, warnings };
  }

  if (stepKey === "skills") {
    const skillRegistryEntries = options.skillRegistryEntries ?? await getSkillRegistryEntries();
    const skills = system.skills ?? {};

    for (const entry of skillRegistryEntries) {
      const skill = skills[entry.id];
      if (!skill || typeof skill !== "object") {
        errors.push(`Skill '${entry.id}' is missing.`);
        continue;
      }
      if (!SKILL_RANKS.includes(skill.rank)) {
        errors.push(`Skill '${entry.id}' rank is invalid.`);
      }
      if (skill.linkedAttr !== entry.linkedAttr) {
        warnings.push(`Skill '${entry.id}' linked attribute should be '${entry.linkedAttr}'.`);
      }
      const misc = ensureNumber(skill.misc);
      if (!Number.isFinite(misc) || misc < -50 || misc > 50) {
        errors.push(`Skill '${entry.id}' misc must be in -50..50.`);
      }
    }

    return { ok: errors.length === 0, errors, warnings };
  }

  if (stepKey === "pathway") {
    const pathwayId = normalizePathwayId(identity.pathwayId);
    const sequence = ensureNumber(identity.sequence);

    if (!pathwayId) {
      if (hasExplicitSequence(identity.sequence)) {
        errors.push("Clear identity.sequence when no pathway is selected.");
      }
      return { ok: errors.length === 0, errors, warnings };
    }
    if (!Number.isInteger(sequence)) {
      errors.push("Set identity.sequence before validating pathway step.");
      return { ok: false, errors, warnings };
    }

    const matchingSequence = items.some(
      (item) => item.type === "sequenceNode"
        && item.system?.pathwayId === pathwayId
        && Number(item.system?.sequence) === sequence
    );

    if (!matchingSequence) {
      errors.push("Import pathway package so owned sequence node matches identity.pathwayId and identity.sequence.");
    }

    return { ok: errors.length === 0, errors, warnings };
  }

  if (stepKey === "equipment") {
    const hasInventoryItem = items.some((item) => !["pathway", "sequenceNode"].includes(item.type));
    if (!hasInventoryItem) {
      warnings.push("No equipment items are currently owned.");
    }
    return { ok: true, errors, warnings };
  }

  return { ok: true, errors, warnings };
}

export async function evaluateCreationState(actorOrData, options = {}) {
  const actor = normalizeActorState(actorOrData);
  const pathwayOptions = options.pathwayOptions ?? await getPathwayOptions();
  const skillRegistryEntries = options.skillRegistryEntries ?? await getSkillRegistryEntries();

  const stepKeys = CREATION_STEPS.filter((step) => step !== "complete");
  const byStep = {};
  const finalizeErrors = [];
  const finalizeWarnings = [];

  for (const step of stepKeys) {
    const sequenceOptions = step === "identity"
      ? await getSequenceOptions(actor.system?.identity?.pathwayId)
      : [];
    const result = await validateCreationStep(actor, step, {
      pathwayOptions,
      sequenceOptions,
      skillRegistryEntries
    });
    byStep[step] = result;
    finalizeErrors.push(...result.errors);
    finalizeWarnings.push(...result.warnings);
  }

  return {
    byStep,
    canFinalize: finalizeErrors.length === 0,
    finalizeErrors,
    finalizeWarnings,
    pathwayOptions,
    sequenceOptions: await getSequenceOptions(normalizePathwayId(actor.system?.identity?.pathwayId)),
    skillRegistryEntries
  };
}
