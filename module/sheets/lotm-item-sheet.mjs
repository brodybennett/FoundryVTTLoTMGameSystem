import { validateItemSystemForType } from "../item/validation.mjs";

const ITEM_TYPE_META = {
  pathway: {
    label: "Pathway",
    summary: "Defines pathway identity and progression framing.",
    subtypeGroup: "Pathway"
  },
  sequenceNode: {
    label: "Sequence Node",
    summary: "Defines a progression node tied to a pathway and sequence value.",
    subtypeGroup: "Pathway"
  },
  ability: {
    label: "Ability",
    summary: "Core active/passive mechanics used by actors.",
    subtypeGroup: "Power"
  },
  ritual: {
    label: "Ritual",
    summary: "High-cost ceremonial actions with risk and component requirements.",
    subtypeGroup: "Power"
  },
  artifact: {
    label: "Artifact",
    summary: "Sealed artifacts with risk profile and corruption implications.",
    subtypeGroup: "Power"
  },
  weapon: {
    label: "Weapon",
    summary: "Combat equipment with damage, range, and accuracy data.",
    subtypeGroup: "Equipment"
  },
  armor: {
    label: "Armor",
    summary: "Defense profile and encumbrance data.",
    subtypeGroup: "Equipment"
  },
  gear: {
    label: "Gear",
    summary: "General utility equipment entry.",
    subtypeGroup: "Equipment"
  },
  feature: {
    label: "Feature",
    summary: "Narrative or mechanical feature tied to actor capabilities.",
    subtypeGroup: "Generic"
  },
  consumable: {
    label: "Consumable",
    summary: "Single-use or limited-use utility item.",
    subtypeGroup: "Equipment"
  },
  ingredient: {
    label: "Ingredient",
    summary: "Crafting or ritual input material.",
    subtypeGroup: "Equipment"
  },
  background: {
    label: "Background",
    summary: "Character background or origin package.",
    subtypeGroup: "Generic"
  },
  conditionTemplate: {
    label: "Condition Template",
    summary: "Reusable condition/effect template entry.",
    subtypeGroup: "Generic"
  }
};

function parseCsv(value) {
  if (typeof value !== "string") return [];
  return [...new Set(
    value
      .split(",")
      .map((part) => part.trim())
      .filter((part) => part.length > 0)
  )];
}

function defaultEffectPayload(effectId = "effect.custom.new") {
  return {
    id: effectId,
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

function nextEffectId(effects = []) {
  const used = new Set(
    effects
      .map((entry) => String(entry?.id ?? "").trim())
      .filter((entry) => entry.length > 0)
  );

  for (let i = 1; i < 9999; i += 1) {
    const candidate = `effect.custom.${i}`;
    if (!used.has(candidate)) return candidate;
  }
  return `effect.custom.${Date.now()}`;
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
      merged.id = String(merged.id ?? "").trim();
      merged.path = String(merged.path ?? "").trim();
      merged.sourceCategory = String(merged.sourceCategory ?? "ability").trim() || "ability";
      merged.trigger = String(merged.trigger ?? "onApply").trim() || "onApply";
      merged.target = String(merged.target ?? "self").trim() || "self";
      merged.applyPhase = String(merged.applyPhase ?? "immediate").trim() || "immediate";
      merged.tickPhase = String(merged.tickPhase ?? "none").trim() || "none";
      merged.stackRule = String(merged.stackRule ?? "refresh").trim() || "refresh";
      merged.stackGroup = String(merged.stackGroup ?? "").trim();
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
    isArmor: itemType === "armor",
    isGear: itemType === "gear",
    isFeature: itemType === "feature",
    isConsumable: itemType === "consumable",
    isIngredient: itemType === "ingredient",
    isBackground: itemType === "background",
    isConditionTemplate: itemType === "conditionTemplate"
  };
}

function getItemTypeMeta(itemType) {
  return ITEM_TYPE_META[itemType] ?? {
    label: itemType,
    summary: "Generic item authoring entry.",
    subtypeGroup: "Generic"
  };
}

export class LotMItemSheet extends ItemSheet {
  static get defaultOptions() {
    return foundry.utils.mergeObject(super.defaultOptions, {
      classes: ["lotm", "sheet", "item"],
      width: 700,
      height: 760,
      tabs: [{ navSelector: ".sheet-tabs", contentSelector: ".sheet-body", initial: "overview" }],
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
    const typeMeta = getItemTypeMeta(item.type);

    context.item = item;
    context.system = system;
    context.itemType = item.type;
    context.typeMeta = typeMeta;
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
    context.effectCount = context.effects.length;
    context.effectOps = ["add", "set", "mul", "cost"];
    context.effectTargets = ["self", "ally", "enemy", "area", "scene", "special"];
    context.effectTriggers = ["onApply", "startOfTurn", "endOfTurn", "onRemove"];
    context.effectApplyPhases = ["immediate", "deferred", "none"];
    context.effectTickPhases = ["startOfTurn", "endOfTurn", "none"];
    context.effectSaveTypes = ["none", "str", "dex", "wil", "con", "cha", "int", "luck"];
    context.effectStackRules = ["refresh", "replace", "stackLimited"];

    const validation = validateItemSystemForType(item.type, system);
    context.validationErrors = validation.errors ?? [];
    context.hasValidationErrors = context.validationErrors.length > 0;

    return context;
  }

  activateListeners(html) {
    super.activateListeners(html);

    html.find("[data-action='effect-add']").on("click", async (event) => {
      event.preventDefault();
      const effects = normalizeEffects(this.item.system?.effects);
      effects.push(defaultEffectPayload(nextEffectId(effects)));

      try {
        await this.item.update({ "system.effects": effects });
        this.render(true);
      } catch (err) {
        console.error("Failed adding effect row", err);
        ui.notifications?.error("Unable to add effect row.");
      }
    });

    html.find("[data-action='effect-remove']").on("click", async (event) => {
      event.preventDefault();
      const index = Number(event.currentTarget.dataset.index);
      if (!Number.isInteger(index) || index < 0) {
        ui.notifications?.warn("Invalid effect row index.");
        return;
      }

      const effects = normalizeEffects(this.item.system?.effects).filter((_entry, idx) => idx !== index);
      try {
        await this.item.update({ "system.effects": effects });
        this.render(true);
      } catch (err) {
        console.error("Failed removing effect row", err);
        ui.notifications?.error("Unable to remove effect row.");
      }
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

    expanded.system.dependencies ??= {};
    if (!expanded.system.dependencies.minSystemVersion) {
      expanded.system.dependencies.minSystemVersion = this.item.system?.dependencies?.minSystemVersion ?? game.system.version;
    }
    if (!expanded.system.dependencies.maxTestedSystemVersion) {
      expanded.system.dependencies.maxTestedSystemVersion = this.item.system?.dependencies?.maxTestedSystemVersion ?? game.system.version;
    }

    expanded.system.effects = normalizeEffects(expanded.system.effects);

    delete expanded.lotm;
    const flattened = foundry.utils.flattenObject(expanded);
    return super._updateObject(event, flattened);
  }
}
