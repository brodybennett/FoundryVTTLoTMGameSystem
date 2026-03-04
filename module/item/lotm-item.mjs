import { normalizeItemSystemForRuntime, validateItemSystemForType } from "./validation.mjs";

export class LotMItem extends Item {
  prepareDerivedData() {
    super.prepareDerivedData();
    if (!this.system) return;

    const normalized = normalizeItemSystemForRuntime(this.system);
    this.system.tags = normalized.tags;
    this.system.effects = normalized.effects;
    this.system.allowedPathwayIds = normalized.allowedPathwayIds;
    this.system.pathwayData = normalized.pathwayData;
    this.system.sequenceData = normalized.sequenceData;
    this.system.dependencies = normalized.dependencies;
    this.system.cost = Number(this.system.cost ?? 0) || 0;
    this.system.cooldown = Number(this.system.cooldown ?? 0) || 0;
  }

  async _preCreate(data, options, user) {
    await super._preCreate(data, options, user);
    const itemType = data.type ?? this.type;
    const system = data.system ?? {};
    const validation = validateItemSystemForType(itemType, system);
    if (validation.ok) return;

    const msg = `Cannot create item: ${validation.errors.join("; ")}`;
    ui.notifications?.error(msg);
    throw new Error(msg);
  }

  async _preUpdate(changed, options, user) {
    await super._preUpdate(changed, options, user);
    const nextType = changed.type ?? this.type;
    const nextSystem = foundry.utils.mergeObject(
      foundry.utils.deepClone(this.system ?? {}),
      changed.system ?? {},
      { inplace: false }
    );
    const validation = validateItemSystemForType(nextType, nextSystem);
    if (validation.ok) return;

    const msg = `Cannot update item '${this.name}': ${validation.errors.join("; ")}`;
    ui.notifications?.error(msg);
    throw new Error(msg);
  }
}
