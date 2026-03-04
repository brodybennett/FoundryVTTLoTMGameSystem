import { ATTRIBUTE_KEYS, CREATION_STEPS, SKILL_RANKS, clamp, resolveCorruptionPenalty } from "../constants.mjs";
import { buildDefaultSkills } from "../creation/creation-engine.mjs";

function numberOr(value, fallback = 0) {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function normalizePathwayId(value) {
  if (typeof value !== "string") return "";
  return value.trim();
}

function creationCompletedSteps(pathwayId) {
  return pathwayId
    ? ["identity", "attributes", "skills", "pathway", "equipment"]
    : ["identity", "attributes", "skills", "equipment"];
}

function hasExplicitSequence(value) {
  return !(value === "" || value == null);
}

function attrTotal(attributes, key) {
  const entry = attributes?.[key] ?? {};
  return numberOr(entry.total, numberOr(entry.base, 10) + numberOr(entry.temp, 0));
}

export function deriveActorStats(actorSystem = {}) {
  const attributes = actorSystem.attributes ?? {};
  const combat = actorSystem.combat ?? {};
  const resources = actorSystem.resources ?? {};

  const str = attrTotal(attributes, "str");
  const dex = attrTotal(attributes, "dex");
  const wil = attrTotal(attributes, "wil");
  const con = attrTotal(attributes, "con");
  const intScore = attrTotal(attributes, "int");
  const luck = attrTotal(attributes, "luck");

  const hpMax = Math.max(1, Math.round(20 + (str * 1.5) + (con * 2.5)));
  const spiritMax = Math.max(0, Math.round(15 + (wil * 2.2) + (intScore * 1.2) + Math.floor(luck / 4)));
  const sanityMax = Math.max(1, Math.round(30 + (wil * 1.8) + (con * 1.1) + Math.floor(luck / 5)));

  const armor = numberOr(combat.armor, 0);
  const cover = numberOr(combat.cover, 0);
  const enc = Math.max(0, numberOr(combat.encumbrancePenalty, 0));

  const defenseShift = clamp(Math.floor((dex + con - 20) / 8) + armor + cover, -20, 25);
  const initiativeTarget = clamp(20 + Math.floor((dex * 0.5) + (intScore * 0.35) + (luck * 0.15)) - enc, 1, 95);

  const corruptionPenalty = resolveCorruptionPenalty(numberOr(resources.corruption, 0));

  return {
    hpMax,
    spiritMax,
    sanityMax,
    defenseShift,
    initiativeTarget,
    corruptionPenalty
  };
}

export function validateActorForPlay(actorSystem = {}, actorType = "character", ownedItems = []) {
  const errors = [];
  const warnings = [];

  if (actorType !== "character") {
    return { ok: true, errors, warnings };
  }

  const identity = actorSystem.identity ?? {};
  const pathwayId = normalizePathwayId(identity.pathwayId);
  const rawSequence = identity.sequence;
  const hasSequence = hasExplicitSequence(rawSequence);
  const sequence = numberOr(rawSequence, NaN);

  if (!pathwayId && hasSequence) {
    errors.push("identity.sequence cannot be set when identity.pathwayId is blank");
  } else if (pathwayId) {
    if (!Number.isInteger(sequence) || sequence < 0 || sequence > 9) {
      errors.push("identity.sequence must be an integer 0..9 when identity.pathwayId is set");
    }
  }

  const attributes = actorSystem.attributes ?? {};
  for (const key of ATTRIBUTE_KEYS) {
    const base = numberOr(attributes?.[key]?.base, NaN);
    if (!Number.isFinite(base)) {
      errors.push(`attributes.${key}.base is required`);
      continue;
    }
    if (base < 0 || base > 100) {
      errors.push(`attributes.${key}.base must be 0..100`);
    }
  }

  const skills = actorSystem.skills ?? {};
  for (const [skillId, entry] of Object.entries(skills)) {
    if (!SKILL_RANKS.includes(entry?.rank)) {
      errors.push(`skills.${skillId}.rank must be one of ${SKILL_RANKS.join(", ")}`);
    }
    const misc = numberOr(entry?.misc, NaN);
    if (!Number.isFinite(misc) || misc < -50 || misc > 50) {
      errors.push(`skills.${skillId}.misc must be -50..50`);
    }
  }

  const resources = actorSystem.resources ?? {};
  const hp = numberOr(resources.hp, NaN);
  const spirit = numberOr(resources.spirit, NaN);
  const corruption = numberOr(resources.corruption, NaN);
  if (!Number.isFinite(hp)) errors.push("resources.hp is required");
  if (!Number.isFinite(spirit) || spirit < 0) errors.push("resources.spirit must be >= 0");
  if (!Number.isFinite(corruption) || corruption < 0 || corruption > 100) {
    errors.push("resources.corruption must be 0..100");
  }

  const creation = actorSystem.creation ?? {};
  const state = creation.state ?? "draft";
  if (!["draft", ...CREATION_STEPS].includes(state)) {
    errors.push("creation.state is invalid");
  }

  if (pathwayId && Array.isArray(ownedItems) && ownedItems.length > 0) {
    const sequenceNodes = ownedItems.filter((item) => item.type === "sequenceNode" && item.system?.pathwayId === pathwayId);
    if (sequenceNodes.length === 0) {
      warnings.push("No matching sequenceNode found for selected pathway. Drag and drop the required pathway/sequence items.");
    } else if (Number.isInteger(sequence)) {
      const hasMatch = sequenceNodes.some((item) => Number(item.system?.sequence) === sequence);
      if (!hasMatch) {
        warnings.push("Pathway sequence node items do not include actor identity.sequence.");
      }
    }
  }

  return {
    ok: errors.length === 0,
    errors,
    warnings
  };
}

export function buildActorRepairUpdate(actorSystem = {}, actorType = "character", skillRegistryEntries = []) {
  const patch = {};

  if (actorType !== "character") {
    return patch;
  }

  const creation = actorSystem.creation ?? {};
  const completed = Array.isArray(creation.completedSteps) ? creation.completedSteps : [];
  const pathwayId = normalizePathwayId(actorSystem.identity?.pathwayId);
  const canonicalCompleted = creationCompletedSteps(pathwayId);
  if (!creation.state) {
    patch["system.creation.state"] = "complete";
  } else if (creation.state !== "complete") {
    patch["system.creation.state"] = "complete";
  }
  if (!Array.isArray(creation.completedSteps)) {
    patch["system.creation.completedSteps"] = canonicalCompleted;
  } else {
    const uniqueCompleted = [...new Set(completed.filter((step) => canonicalCompleted.includes(step)))];
    const missing = canonicalCompleted.filter((step) => !uniqueCompleted.includes(step));
    if (missing.length > 0 || uniqueCompleted.length !== completed.length) {
      patch["system.creation.completedSteps"] = [...uniqueCompleted, ...missing];
    }
  }
  if (creation.version == null) {
    patch["system.creation.version"] = 1;
  }

  if (!actorSystem.details || typeof actorSystem.details !== "object" || Array.isArray(actorSystem.details)) {
    patch["system.details"] = {
      alignment: "",
      faith: "",
      gender: "",
      eyes: "",
      hair: "",
      skin: "",
      height: "",
      weight: "",
      age: "",
      ideal: "",
      bond: "",
      flaw: "",
      trait: "",
      appearance: "",
      biography: {
        value: "",
        public: ""
      }
    };
  } else {
    const details = actorSystem.details;
    const detailKeys = ["alignment", "faith", "gender", "eyes", "hair", "skin", "height", "weight", "age", "ideal", "bond", "flaw", "trait", "appearance"];
    for (const key of detailKeys) {
      if (typeof details[key] !== "string") {
        patch[`system.details.${key}`] = "";
      }
    }
    if (!details.biography || typeof details.biography !== "object" || Array.isArray(details.biography)) {
      patch["system.details.biography"] = { value: "", public: "" };
    } else {
      if (typeof details.biography.value !== "string") patch["system.details.biography.value"] = "";
      if (typeof details.biography.public !== "string") patch["system.details.biography.public"] = "";
    }
  }

  if (!actorSystem.traits || typeof actorSystem.traits !== "object" || Array.isArray(actorSystem.traits)) {
    patch["system.traits"] = {
      senses: [],
      resistances: [],
      immunities: [],
      conditionImmunities: [],
      vulnerabilities: [],
      damageModification: []
    };
  } else {
    const traits = actorSystem.traits;
    const traitKeys = ["senses", "resistances", "immunities", "conditionImmunities", "vulnerabilities", "damageModification"];
    for (const key of traitKeys) {
      if (!Array.isArray(traits[key])) patch[`system.traits.${key}`] = [];
    }
  }

  for (const key of ATTRIBUTE_KEYS) {
    const base = numberOr(actorSystem.attributes?.[key]?.base, NaN);
    if (!Number.isFinite(base)) {
      patch[`system.attributes.${key}.base`] = 10;
    }
    const temp = numberOr(actorSystem.attributes?.[key]?.temp, NaN);
    if (!Number.isFinite(temp)) {
      patch[`system.attributes.${key}.temp`] = 0;
    }
  }

  const defaultSkills = buildDefaultSkills(skillRegistryEntries);
  const existingSkills = actorSystem.skills;
  if (!existingSkills || typeof existingSkills !== "object" || Array.isArray(existingSkills)) {
    patch["system.skills"] = defaultSkills;
  } else {
    for (const [skillId, fallback] of Object.entries(defaultSkills)) {
      const skill = existingSkills[skillId];
      if (!skill || typeof skill !== "object" || Array.isArray(skill)) {
        patch[`system.skills.${skillId}`] = fallback;
        continue;
      }
      if (skill.linkedAttr !== fallback.linkedAttr) {
        patch[`system.skills.${skillId}.linkedAttr`] = fallback.linkedAttr;
      }
      if (!SKILL_RANKS.includes(skill.rank)) {
        patch[`system.skills.${skillId}.rank`] = fallback.rank;
      }
      const misc = numberOr(skill.misc, NaN);
      if (!Number.isFinite(misc)) {
        patch[`system.skills.${skillId}.misc`] = fallback.misc;
      }
    }
  }

  const derived = deriveActorStats(actorSystem);
  patch["system.derived.hpMax"] = derived.hpMax;
  patch["system.derived.spiritMax"] = derived.spiritMax;
  patch["system.derived.sanityMax"] = derived.sanityMax;
  patch["system.derived.defenseShift"] = derived.defenseShift;
  patch["system.derived.initiativeTarget"] = derived.initiativeTarget;

  return patch;
}
