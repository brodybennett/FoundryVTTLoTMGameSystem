import { PROFICIENCY_BY_RANK, clamp, resolveCorruptionPenalty } from "../constants.mjs";
import { createLotMCheckCard, createLotMInfoCard } from "../chat/chat-cards.mjs";

function getActorFromInput(actorOrId) {
  if (!actorOrId) return null;
  if (actorOrId instanceof Actor) return actorOrId;
  if (typeof actorOrId === "string") {
    return game.actors?.get(actorOrId) ?? null;
  }
  return null;
}

function getLinkedSkill(actor, skillId) {
  const skills = actor?.system?.skills ?? {};
  return skills[skillId] ?? null;
}

function buildSuccessBand(roll, target, margin) {
  if (roll === 1) return "criticalSuccess";
  if (roll === 100) return "criticalFailure";
  if (roll > target) {
    if (margin >= 30) return "catastrophicFailure";
    if (margin >= 15) return "hardFailure";
    return "failure";
  }
  if (margin >= 30) return "overwhelmingSuccess";
  if (margin >= 15) return "strongSuccess";
  return "success";
}

export async function rollCheck({ actor: actorInput, attribute = "wil", skillId = null, situational = 0, status = 0, label = "Check" } = {}) {
  const actor = getActorFromInput(actorInput);
  if (!actor) throw new Error("LoTM rollCheck requires a valid actor");

  const attributes = actor.system?.attributes ?? {};
  const attrData = attributes[attribute] ?? { base: 10, temp: 0, total: 10 };
  const attrTotal = Number(attrData.total ?? (Number(attrData.base || 0) + Number(attrData.temp || 0))) || 0;

  const skill = skillId ? getLinkedSkill(actor, skillId) : null;
  const proficiencyBonus = skill ? (PROFICIENCY_BY_RANK[skill.rank] ?? 0) : 0;
  const skillMisc = skill ? (Number(skill.misc) || 0) : 0;

  const luckTotal = Number(attributes.luck?.total ?? (Number(attributes.luck?.base || 0) + Number(attributes.luck?.temp || 0))) || 0;
  const baseTarget = 25 + Math.floor(attrTotal / 3) + proficiencyBonus + Math.floor(luckTotal / 10);
  const corruptionPct = Number(actor.system?.resources?.corruption) || 0;
  const corruptionPenalty = resolveCorruptionPenalty(corruptionPct);
  const statusMod = Number(status) || 0;
  const situationalMod = Number(situational) || 0;

  const unclampedTarget = baseTarget + skillMisc + statusMod + situationalMod + corruptionPenalty;
  const finalTarget = clamp(unclampedTarget, 1, 95);

  const roll = await (new Roll("1d100")).evaluate();
  const rolled = Number(roll.total);
  const margin = Math.abs(finalTarget - rolled);
  const success = rolled <= finalTarget || rolled === 1;
  const band = buildSuccessBand(rolled, finalTarget, margin);

  const payload = {
    type: "check",
    actorId: actor.id,
    actorName: actor.name,
    label,
    skillId,
    attribute,
    components: {
      baseTarget,
      proficiencyBonus,
      skillMisc,
      statusMod,
      situationalMod,
      corruptionPenalty
    },
    finalTarget,
    roll: rolled,
    margin,
    success,
    band,
    timestamp: Date.now()
  };

  await createLotMCheckCard(payload);
  return payload;
}

export async function rollDamage({ actor: actorInput, baseDamage = 1, flatBonus = 0, multiplier = null, targetDamageReduction = 0, label = "Damage" } = {}) {
  const actor = getActorFromInput(actorInput);
  if (!actor) throw new Error("LoTM rollDamage requires a valid actor");

  const computedMultiplier = multiplier == null
    ? Number(actor.system?.tracks?.damageOutMultiplier ?? 1)
    : Number(multiplier);

  const reduction = Number(targetDamageReduction) || 0;
  const value = Math.max(1, Math.floor((Number(baseDamage) + Number(flatBonus)) * computedMultiplier) - reduction);

  const payload = {
    type: "damage",
    actorId: actor.id,
    actorName: actor.name,
    label,
    components: {
      baseDamage: Number(baseDamage),
      flatBonus: Number(flatBonus),
      multiplier: computedMultiplier,
      targetDamageReduction: reduction
    },
    total: value,
    timestamp: Date.now()
  };

  await createLotMInfoCard({
    title: `${label} (${actor.name})`,
    summary: `Total damage: ${value}`,
    details: payload.components
  });

  return payload;
}

export async function applyCorruption({ actor: actorInput, delta = 0, source = "system" } = {}) {
  const actor = getActorFromInput(actorInput);
  if (!actor) throw new Error("LoTM applyCorruption requires a valid actor");

  const current = Number(actor.system?.resources?.corruption) || 0;
  const next = clamp(current + Number(delta || 0), 0, 100);

  await actor.update({ "system.resources.corruption": next });

  const oldPenalty = resolveCorruptionPenalty(current);
  const newPenalty = resolveCorruptionPenalty(next);
  const crossed = [30, 60, 90, 100].filter((threshold) => current < threshold && next >= threshold);

  const payload = {
    type: "corruption",
    actorId: actor.id,
    actorName: actor.name,
    source,
    previous: current,
    current: next,
    delta: next - current,
    oldPenalty,
    newPenalty,
    triggersCrossed: crossed,
    timestamp: Date.now()
  };

  await createLotMInfoCard({
    title: `Corruption Update (${actor.name})`,
    summary: `${current} -> ${next} (penalty ${oldPenalty} -> ${newPenalty})`,
    details: { source, triggersCrossed: crossed }
  });

  return payload;
}

export async function rollRitualRisk({ actor: actorInput, complexity = 0, circleBonus = 0, label = "Ritual Risk" } = {}) {
  const actor = getActorFromInput(actorInput);
  if (!actor) throw new Error("LoTM rollRitualRisk requires a valid actor");

  const attrs = actor.system?.attributes ?? {};
  const wil = Number(attrs.wil?.total ?? (Number(attrs.wil?.base || 0) + Number(attrs.wil?.temp || 0))) || 0;
  const intScore = Number(attrs.int?.total ?? (Number(attrs.int?.base || 0) + Number(attrs.int?.temp || 0))) || 0;
  const luck = Number(attrs.luck?.total ?? (Number(attrs.luck?.base || 0) + Number(attrs.luck?.temp || 0))) || 0;

  const corruptionPenalty = resolveCorruptionPenalty(actor.system?.resources?.corruption ?? 0);
  const baseTarget = 35 + Math.floor((wil + intScore + luck) / 9);
  const finalTarget = clamp(baseTarget - Number(complexity || 0) + Number(circleBonus || 0) + corruptionPenalty, 1, 95);

  const roll = await (new Roll("1d100")).evaluate();
  const rolled = Number(roll.total);
  const margin = Math.abs(finalTarget - rolled);
  const success = rolled <= finalTarget || rolled === 1;

  const payload = {
    type: "ritualRisk",
    actorId: actor.id,
    actorName: actor.name,
    label,
    finalTarget,
    roll: rolled,
    margin,
    success,
    band: buildSuccessBand(rolled, finalTarget, margin),
    components: {
      baseTarget,
      complexity: Number(complexity || 0),
      circleBonus: Number(circleBonus || 0),
      corruptionPenalty
    },
    timestamp: Date.now()
  };

  await createLotMCheckCard(payload);
  return payload;
}

export async function rollArtifactBacklash({ actor: actorInput, riskClass = "volatile", misuse = false, label = "Artifact Backlash" } = {}) {
  const actor = getActorFromInput(actorInput);
  if (!actor) throw new Error("LoTM rollArtifactBacklash requires a valid actor");

  const baseByRisk = {
    stable: 20,
    volatile: 35,
    catastrophic: 55
  };
  const baseTarget = baseByRisk[riskClass] ?? baseByRisk.volatile;
  const corruptionPenalty = resolveCorruptionPenalty(actor.system?.resources?.corruption ?? 0);
  const misusePenalty = misuse ? -20 : 0;
  const finalTarget = clamp(baseTarget + corruptionPenalty + misusePenalty, 1, 95);

  const roll = await (new Roll("1d100")).evaluate();
  const rolled = Number(roll.total);
  const failure = rolled > finalTarget && rolled !== 1;
  const severe = rolled === 100 || rolled - finalTarget >= 30;

  const payload = {
    type: "artifactBacklash",
    actorId: actor.id,
    actorName: actor.name,
    label,
    riskClass,
    misuse,
    finalTarget,
    roll: rolled,
    failure,
    severe,
    components: {
      baseTarget,
      corruptionPenalty,
      misusePenalty
    },
    timestamp: Date.now()
  };

  await createLotMInfoCard({
    title: `${label} (${actor.name})`,
    summary: failure ? (severe ? "Severe backlash" : "Backlash") : "Stable activation",
    details: payload
  });

  return payload;
}