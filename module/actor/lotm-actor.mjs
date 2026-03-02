import { ATTRIBUTE_KEYS, resolveCorruptionPenalty } from "../constants.mjs";
import { deriveActorStats } from "./validation.mjs";

export class LotMActor extends Actor {
  prepareDerivedData() {
    super.prepareDerivedData();
    const system = this.system;
    if (!system) return;

    const attributes = system.attributes ?? {};
    for (const key of ATTRIBUTE_KEYS) {
      const stat = attributes[key] ?? { base: 10, temp: 0 };
      stat.base = Number(stat.base) || 0;
      stat.temp = Number(stat.temp) || 0;
      stat.total = stat.base + stat.temp;
      attributes[key] = stat;
    }

    system.resources ??= {};
    system.resources.corruption ??= 0;
    system.resources.corruptionPenalty = resolveCorruptionPenalty(system.resources.corruption);

    system.creation ??= {};
    system.creation.state ??= "draft";
    system.creation.completedSteps ??= [];
    system.creation.version ??= 1;

    system.tracks ??= {};
    system.tracks.damageOutMultiplier = Number(system.tracks.damageOutMultiplier ?? 1);
    if (!Number.isFinite(system.tracks.damageOutMultiplier) || system.tracks.damageOutMultiplier <= 0) {
      system.tracks.damageOutMultiplier = 1;
    }

    system.combat ??= {};
    system.combat.damageReduction = Number(system.combat.damageReduction ?? 0);

    system.derived ??= {};
    const derived = deriveActorStats(system);
    system.derived.hpMax = derived.hpMax;
    system.derived.spiritMax = derived.spiritMax;
    system.derived.sanityMax = derived.sanityMax;
    system.derived.defenseShift = derived.defenseShift;
    system.derived.initiativeTarget = derived.initiativeTarget;
  }

  get linkedSkills() {
    return this.system?.skills ?? {};
  }
}
