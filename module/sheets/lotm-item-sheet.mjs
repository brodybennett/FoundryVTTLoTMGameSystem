function parseCsv(value) {
  if (typeof value !== "string") return [];
  return [...new Set(
    value
      .split(",")
      .map((part) => part.trim())
      .filter((part) => part.length > 0)
  )];
}

function defaultEffectPayload() {
  return {
    id: "effect.custom.new",
    op: "add",
    path: "system.tracks.actionLock",
    value: 0,
    sourceCategory: "ability",
    target: "self",
    trigger: "onApply",
    stackGroup: "",
    oncePerTurn: false,
    applyPhase: "immediate",
    tickPhase: "none",
    durationRounds: 1,
    saveType: "none",
    saveTarget: 0,
    stackRule: "refresh",
    removeOn: ["durationEnd"]
  };
}

function normalizeEffects(rawEffects) {
  if (!rawEffects) return [];

  const list = Array.isArray(rawEffects)
    ? rawEffects
    : Object.keys(rawEffects)
      .sort((a, b) => Number(a) - Number(b))
      .map((key) => rawEffects[key]);

  return list
    .map((entry) => {
      const merged = foundry.utils.mergeObject(defaultEffectPayload(), entry ?? {}, { inplace: false });
      const removeOnCsv = typeof merged.removeOnCsv === "string" ? merged.removeOnCsv : "";
      merged.removeOn = removeOnCsv ? parseCsv(removeOnCsv) : (Array.isArray(merged.removeOn) ? merged.removeOn : []);
      merged.oncePerTurn = merged.oncePerTurn === true || merged.oncePerTurn === "true" || merged.oncePerTurn === "on";
      merged.value = Number(merged.value ?? 0) || 0;
      merged.durationRounds = Number(merged.durationRounds ?? 0) || 0;
      merged.saveTarget = Number(merged.saveTarget ?? 0) || 0;
      if (merged.maxStacks != null && merged.maxStacks !== "") {
        merged.maxStacks = Number(merged.maxStacks) || 0;
      } else {
        delete merged.maxStacks;
      }
      delete merged.removeOnCsv;
      return merged;
    })
    .filter((entry) => entry.id || entry.path || entry.stackGroup);
}

function buildTypeFlags(itemType) {
  return {
    isPathway: itemType === "pathway",
    isSequenceNode: itemType === "sequenceNode",
    isAbility: itemType === "ability",
    isRitual: itemType === "ritual",
    isArtifact: itemType === "artifact",
    isWeapon: itemType === "weapon",
    isArmor: itemType === "armor"
  };
}

export class LotMItemSheet extends ItemSheet {
  static get defaultOptions() {
    return foundry.utils.mergeObject(super.defaultOptions, {
      classes: ["lotm", "sheet", "item"],
      width: 620,
      height: 680,
      tabs: [{ navSelector: ".sheet-tabs", contentSelector: ".sheet-body", initial: "details" }],
      submitOnChange: true
    });
  }

  get template() {
    return `systems/${game.system.id}/templates/sheets/item-sheet.hbs`;
  }

  async getData(options = {}) {
    const context = await super.getData(options);
    const item = context.item ?? this.item;
    const system = item.system;
    const effects = normalizeEffects(system.effects);

    context.item = item;
    context.system = system;
    context.itemType = item.type;
    context.typeFlags = buildTypeFlags(context.itemType);
    context.activationTypes = ["action", "bonusAction", "reaction", "passive", "special"];
    context.resourceTypes = ["spirit", "hp", "none", "item"];
    context.targetModes = ["self", "ally", "enemy", "area", "scene", "special"];
    context.riskClasses = ["stable", "volatile", "catastrophic"];
    context.tagsCsv = (system.tags ?? []).join(", ");
    context.allowedPathwayIdsCsv = (system.allowedPathwayIds ?? []).join(", ");
    context.requiresIdsCsv = (system.dependencies?.requiresIds ?? []).join(", ");
    context.sequenceMilestonesCsv = (system.sequenceData?.milestones ?? []).join(", ");
    context.effects = effects.map((entry, index) => ({
      ...entry,
      index,
      removeOnCsv: (entry.removeOn ?? []).join(", ")
    }));
    context.effectOps = ["add", "set", "mul", "cost"];
    context.effectTargets = ["self", "ally", "enemy", "area", "scene", "special"];
    context.effectTriggers = ["onApply", "startOfTurn", "endOfTurn", "onRemove"];
    context.effectApplyPhases = ["immediate", "deferred", "none"];
    context.effectTickPhases = ["startOfTurn", "endOfTurn", "none"];
    context.effectSaveTypes = ["none", "str", "dex", "wil", "con", "cha", "int", "luck"];
    context.effectStackRules = ["refresh", "replace", "stackLimited"];
    return context;
  }

  activateListeners(html) {
    super.activateListeners(html);

    html.find("[data-action='effect-add']").on("click", async (event) => {
      event.preventDefault();
      const effects = normalizeEffects(this.item.system?.effects);
      effects.push(defaultEffectPayload());
      await this.item.update({ "system.effects": effects });
      this.render(true);
    });

    html.find("[data-action='effect-remove']").on("click", async (event) => {
      event.preventDefault();
      const index = Number(event.currentTarget.dataset.index);
      if (!Number.isInteger(index) || index < 0) return;

      const effects = normalizeEffects(this.item.system?.effects).filter((_entry, idx) => idx !== index);
      await this.item.update({ "system.effects": effects });
      this.render(true);
    });
  }

  async _updateObject(event, formData) {
    const expanded = foundry.utils.expandObject(formData);
    expanded.system ??= {};

    const lotm = expanded.lotm ?? {};
    if (typeof lotm.tagsCsv === "string") {
      expanded.system.tags = parseCsv(lotm.tagsCsv);
    }
    if (typeof lotm.allowedPathwayIdsCsv === "string") {
      expanded.system.allowedPathwayIds = parseCsv(lotm.allowedPathwayIdsCsv);
    }
    if (typeof lotm.requiresIdsCsv === "string") {
      expanded.system.dependencies ??= {};
      expanded.system.dependencies.requiresIds = parseCsv(lotm.requiresIdsCsv);
    }
    if (typeof lotm.sequenceMilestonesCsv === "string") {
      expanded.system.sequenceData ??= {};
      expanded.system.sequenceData.milestones = parseCsv(lotm.sequenceMilestonesCsv);
    }

    expanded.system.effects = normalizeEffects(expanded.system.effects);

    delete expanded.lotm;
    const flattened = foundry.utils.flattenObject(expanded);
    return super._updateObject(event, flattened);
  }
}
