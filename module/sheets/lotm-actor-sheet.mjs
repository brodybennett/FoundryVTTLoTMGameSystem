import { ATTRIBUTE_KEYS, CREATION_STEPS, SKILL_RANKS } from "../constants.mjs";
import { buildActorRepairUpdate } from "../actor/validation.mjs";
import {
  evaluateCreationState,
  getSkillRegistryEntries,
  validateCreationStep
} from "../creation/creation-engine.mjs";

const ATTRIBUTE_LABELS = {
  str: "Strength",
  dex: "Dexterity",
  wil: "Willpower",
  con: "Constitution",
  cha: "Charisma",
  int: "Intellect",
  luck: "Luck"
};

function titleCaseToken(value) {
  if (!value || typeof value !== "string") return "";
  return value
    .replace(/[_-]/g, " ")
    .split(" ")
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(" ");
}

function buildSkillRows(skills = {}) {
  return Object.entries(skills)
    .map(([id, entry]) => ({
      id,
      label: titleCaseToken(id),
      linkedAttr: entry?.linkedAttr ?? "wil",
      rank: entry?.rank ?? "familiar",
      misc: Number(entry?.misc ?? 0) || 0
    }))
    .sort((a, b) => a.label.localeCompare(b.label));
}

function groupItems(items) {
  const groups = {
    ability: [],
    ritual: [],
    artifact: [],
    pathway: [],
    feature: [],
    gear: []
  };

  for (const item of items) {
    if (item.type === "ability") groups.ability.push(item);
    else if (item.type === "ritual") groups.ritual.push(item);
    else if (item.type === "artifact") groups.artifact.push(item);
    else if (item.type === "pathway" || item.type === "sequenceNode") groups.pathway.push(item);
    else if (item.type === "background" || item.type === "conditionTemplate" || item.type === "feature") groups.feature.push(item);
    else groups.gear.push(item);
  }

  return groups;
}

function sortByName(items = []) {
  return [...items].sort((a, b) => String(a.name ?? "").localeCompare(String(b.name ?? "")));
}

function normalizeCreationState(system, actorType) {
  if (actorType !== "character") {
    return {
      state: "complete",
      completedSteps: [...CREATION_STEPS.filter((step) => step !== "complete")],
      version: 1
    };
  }

  const creation = system.creation ?? {};
  const state = creation.state ?? "draft";
  const completedSteps = Array.isArray(creation.completedSteps) ? [...creation.completedSteps] : [];
  return {
    state,
    completedSteps,
    version: Number(creation.version ?? 1)
  };
}

function buildStepView(state, completedSteps) {
  const allSteps = ["draft", ...CREATION_STEPS];
  return allSteps.map((step, index) => {
    const isComplete = step === "complete" ? state === "complete" : completedSteps.includes(step);
    return {
      key: step,
      label: step.charAt(0).toUpperCase() + step.slice(1),
      index,
      active: state === step,
      complete: isComplete
    };
  });
}

function uniqueSteps(steps) {
  return [...new Set(steps.filter((step) => CREATION_STEPS.includes(step) && step !== "complete"))];
}

function clampResourcesToDerived(system, derived) {
  const patch = {};
  const hp = Number(system.resources?.hp ?? derived.hpMax);
  const spirit = Number(system.resources?.spirit ?? derived.spiritMax);
  patch["system.resources.hp"] = Math.max(-99999, Math.min(hp, derived.hpMax));
  patch["system.resources.spirit"] = Math.max(0, Math.min(spirit, derived.spiritMax));
  return patch;
}

function uniqueMessages(messages = []) {
  return [...new Set((messages ?? []).filter((entry) => typeof entry === "string" && entry.trim().length > 0))];
}

function formatErrorList(messages = []) {
  const unique = uniqueMessages(messages);
  if (unique.length === 0) return "Unknown error.";
  return unique.join("; ");
}

async function invokeLotmApi(method, payload, failureLabel) {
  const apiFn = game.lotm?.[method];
  if (typeof apiFn !== "function") {
    const msg = `LoTM API '${method}' is unavailable.`;
    ui.notifications?.error(msg);
    console.error(msg);
    return null;
  }

  try {
    return await apiFn(payload);
  } catch (err) {
    console.error(`LoTM action failed (${method})`, err);
    ui.notifications?.error(failureLabel ?? `LoTM action failed (${method}). Check console.`);
    return null;
  }
}

export class LotMActorSheet extends ActorSheet {
  static get defaultOptions() {
    return foundry.utils.mergeObject(super.defaultOptions, {
      classes: ["lotm", "sheet", "actor"],
      width: 920,
      height: 820,
      tabs: [{ navSelector: ".sheet-tabs", contentSelector: ".sheet-body", initial: "overview" }],
      dragDrop: [{ dragSelector: ".item", dropSelector: null }],
      submitOnChange: true
    });
  }

  get template() {
    return `systems/${game.system.id}/templates/sheets/actor-sheet.hbs`;
  }

  async getData(options = {}) {
    const context = await super.getData(options);
    const actor = context.actor ?? this.actor;
    const system = actor.system;
    const items = actor.items.map((entry) => entry.toObject(false));

    const isCharacter = actor.type === "character";
    const creation = normalizeCreationState(system, actor.type);

    let validation = { ok: true, errors: [], warnings: [] };
    if (game.lotm?.validateActorForPlay) {
      validation = game.lotm.validateActorForPlay(system, actor.type, items);
    }

    let derivedPreview = {
      hpMax: system.derived?.hpMax,
      spiritMax: system.derived?.spiritMax,
      sanityMax: system.derived?.sanityMax,
      defenseShift: system.derived?.defenseShift,
      initiativeTarget: system.derived?.initiativeTarget,
      corruptionPenalty: system.resources?.corruptionPenalty ?? 0
    };
    if (game.lotm?.deriveActorStats) {
      derivedPreview = game.lotm.deriveActorStats(system);
    }

    let creationValidation = {
      byStep: {},
      canFinalize: true,
      finalizeErrors: [],
      finalizeWarnings: [],
      pathwayOptions: [],
      sequenceOptions: []
    };
    if (isCharacter) {
      creationValidation = await evaluateCreationState({
        type: actor.type,
        system,
        items
      });
    }

    context.actor = actor;
    context.system = system;
    context.isCharacter = isCharacter;
    context.isNpc = !isCharacter;
    context.attributeKeys = ATTRIBUTE_KEYS;
    context.attributeOptions = ATTRIBUTE_KEYS.map((key) => ({
      key,
      label: ATTRIBUTE_LABELS[key] ?? key.toUpperCase()
    }));
    context.skillRanks = SKILL_RANKS;
    context.itemGroups = groupItems(items);
    context.skillRows = buildSkillRows(system.skills ?? {});
    context.creation = creation;
    context.creationSteps = buildStepView(creation.state, creation.completedSteps);
    context.validation = validation;
    context.derivedPreview = derivedPreview;
    context.creationValidation = creationValidation;
    context.pathwayOptions = creationValidation.pathwayOptions ?? [];
    context.sequenceOptions = creationValidation.sequenceOptions ?? [];
    context.creationCompletedCount = uniqueSteps(creation.completedSteps).length;
    context.creationRequiredCount = CREATION_STEPS.filter((step) => step !== "complete").length;
    context.currentCreationStep = creation.state;
    context.currentStepValidation = creationValidation.byStep?.[creation.state] ?? { ok: true, errors: [], warnings: [] };
    context.itemCounts = {
      abilities: context.itemGroups.ability.length,
      rituals: context.itemGroups.ritual.length,
      artifacts: context.itemGroups.artifact.length,
      pathway: context.itemGroups.pathway.length,
      features: context.itemGroups.feature.length,
      gear: context.itemGroups.gear.length
    };
    context.npcLoadoutItems = sortByName([
      ...context.itemGroups.gear,
      ...context.itemGroups.ritual,
      ...context.itemGroups.artifact,
      ...context.itemGroups.feature,
      ...context.itemGroups.pathway
    ]);
    context.itemCounts.npcLoadout = context.npcLoadoutItems.length;
    context.hasAnyInventory = (context.itemCounts.gear + context.itemCounts.rituals + context.itemCounts.artifacts) > 0;

    return context;
  }

  activateListeners(html) {
    super.activateListeners(html);

    html.find("[data-action='roll-check']").on("click", async (event) => {
      event.preventDefault();
      const button = event.currentTarget;
      const attribute = button.dataset.attribute || "wil";
      const skillId = button.dataset.skillId || null;
      const label = button.dataset.label || "Check";
      await invokeLotmApi("rollCheck", { actor: this.actor, attribute, skillId, label }, "Unable to roll check.");
    });

    html.find("[data-action='roll-ritual-risk']").on("click", async (event) => {
      event.preventDefault();
      await invokeLotmApi("rollRitualRisk", { actor: this.actor, label: "Ritual Risk" }, "Unable to roll ritual risk.");
    });

    html.find("[data-action='roll-artifact-backlash']").on("click", async (event) => {
      event.preventDefault();
      await invokeLotmApi(
        "rollArtifactBacklash",
        { actor: this.actor, label: "Artifact Backlash" },
        "Unable to roll artifact backlash."
      );
    });

    html.find("[data-action='apply-corruption']").on("click", async (event) => {
      event.preventDefault();
      const raw = html.find("[name='lotm-corruption-delta']").val()?.toString() ?? "0";
      const delta = Number(raw);
      if (!Number.isFinite(delta)) {
        ui.notifications?.error("Corruption delta must be a number.");
        return;
      }
      await invokeLotmApi(
        "applyCorruption",
        { actor: this.actor, delta, source: "sheet" },
        "Unable to apply corruption delta."
      );
    });

    html.find("[data-action='item-edit']").on("click", (event) => {
      event.preventDefault();
      const li = event.currentTarget.closest(".item");
      const itemId = li?.dataset?.itemId;
      if (!itemId) {
        ui.notifications?.warn("No item selected to edit.");
        return;
      }
      const item = this.actor.items.get(itemId);
      if (!item) {
        ui.notifications?.warn("Selected item could not be found on actor.");
        return;
      }
      item.sheet?.render(true);
    });

    html.find("[data-action='item-delete']").on("click", async (event) => {
      event.preventDefault();
      const li = event.currentTarget.closest(".item");
      const itemId = li?.dataset?.itemId;
      if (!itemId) {
        ui.notifications?.warn("No item selected to delete.");
        return;
      }

      const item = this.actor.items.get(itemId);
      if (!item) {
        ui.notifications?.warn("Selected item could not be found on actor.");
        return;
      }

      const confirmed = await Dialog.confirm({
        title: "Delete Item",
        content: `<p>Delete <strong>${item.name}</strong> from this actor?</p>`,
        yes: () => true,
        no: () => false,
        defaultYes: false
      });
      if (!confirmed) return;

      try {
        await this.actor.deleteEmbeddedDocuments("Item", [itemId]);
      } catch (err) {
        console.error("Failed deleting embedded item", err);
        ui.notifications?.error(`Unable to delete item '${item.name}'.`);
      }
    });

    html.find("[data-action='wizard-step']").on("click", async (event) => {
      event.preventDefault();
      await this._setWizardState(event.currentTarget.dataset.step);
    });

    html.find("[data-action='wizard-next']").on("click", async (event) => {
      event.preventDefault();
      await this._stepWizard(1);
    });

    html.find("[data-action='wizard-prev']").on("click", async (event) => {
      event.preventDefault();
      await this._stepWizard(-1);
    });

    html.find("[data-action='wizard-finalize']").on("click", async (event) => {
      event.preventDefault();
      await this._finalizeCreation();
    });

    html.find("[data-action='wizard-repair']").on("click", async (event) => {
      event.preventDefault();
      await this._repairActorData();
    });

    html.find("[data-action='import-pathway']").on("click", async (event) => {
      event.preventDefault();
      await this._importPathwayPackage();
    });
  }

  _getCreationState() {
    return normalizeCreationState(this.actor.system, this.actor.type);
  }

  async _setWizardState(step) {
    if (this.actor.type !== "character") return;
    const allowed = ["draft", ...CREATION_STEPS];
    if (!allowed.includes(step)) {
      ui.notifications?.warn(`Invalid wizard step '${step}'.`);
      return;
    }

    try {
      await this.actor.update({ "system.creation.state": step, "system.creation.version": 1 });
    } catch (err) {
      console.error("Failed updating wizard step", err);
      ui.notifications?.error("Unable to update creation step.");
    }
  }

  async _stepWizard(direction) {
    if (this.actor.type !== "character") return;

    const state = this._getCreationState();
    const order = ["draft", ...CREATION_STEPS];
    const currentIndex = Math.max(0, order.indexOf(state.state));
    const nextIndex = Math.max(0, Math.min(order.length - 1, currentIndex + direction));
    const currentStep = order[currentIndex];
    const nextStep = order[nextIndex];

    const completed = [...state.completedSteps];
    if (direction > 0 && currentStep !== "draft" && currentStep !== "complete") {
      const check = await validateCreationStep(this.actor, currentStep);
      if (!check.ok) {
        ui.notifications?.error(`Cannot advance from '${currentStep}': ${check.errors.join("; ")}`);
        return;
      }
    }

    if (direction > 0 && currentStep !== "draft" && currentStep !== "complete" && !completed.includes(currentStep)) {
      completed.push(currentStep);
    }

    try {
      await this.actor.update({
        "system.creation.state": nextStep,
        "system.creation.completedSteps": uniqueSteps(completed),
        "system.creation.version": 1
      });
    } catch (err) {
      console.error("Failed advancing wizard step", err);
      ui.notifications?.error("Unable to advance creation step.");
    }
  }

  async _finalizeCreation() {
    if (this.actor.type !== "character") return;

    const creationValidation = await evaluateCreationState(this.actor);
    if (!creationValidation.canFinalize) {
      ui.notifications?.error(`Cannot finalize character: ${formatErrorList(creationValidation.finalizeErrors)}`);
      return;
    }

    if (typeof game.lotm?.deriveActorStats !== "function" || typeof game.lotm?.validateActorForPlay !== "function") {
      ui.notifications?.error("LoTM actor validation APIs are unavailable.");
      return;
    }

    let derived = null;
    let validation = null;
    try {
      derived = game.lotm.deriveActorStats(this.actor.system);
      validation = game.lotm.validateActorForPlay(
        this.actor.system,
        this.actor.type,
        this.actor.items.map((item) => item.toObject(false))
      );
    } catch (err) {
      console.error("Failed deriving/validating actor during finalize", err);
      ui.notifications?.error("Unable to finalize character due to a validation runtime failure.");
      return;
    }

    const validationErrors = validation?.errors ?? [];
    if (validationErrors.length > 0) {
      ui.notifications?.error(`Cannot finalize character: ${formatErrorList(validationErrors)}`);
      return;
    }

    const completed = uniqueSteps(["identity", "attributes", "skills", "pathway", "equipment"]);

    const patch = {
      "system.creation.state": "complete",
      "system.creation.completedSteps": completed,
      "system.creation.version": 1,
      "system.derived.hpMax": derived.hpMax,
      "system.derived.spiritMax": derived.spiritMax,
      "system.derived.sanityMax": derived.sanityMax,
      "system.derived.defenseShift": derived.defenseShift,
      "system.derived.initiativeTarget": derived.initiativeTarget
    };

    foundry.utils.mergeObject(patch, clampResourcesToDerived(this.actor.system, derived));

    try {
      await this.actor.update(patch);
      ui.notifications?.info("Character creation finalized.");
    } catch (err) {
      console.error("Failed finalizing character", err);
      ui.notifications?.error("Finalize failed while saving actor data.");
    }
  }

  async _repairActorData() {
    const skillRegistryEntries = await getSkillRegistryEntries();
    const patch = buildActorRepairUpdate(this.actor.system, this.actor.type, skillRegistryEntries);
    if (Object.keys(patch).length === 0) {
      ui.notifications?.info("No repair actions required.");
      return;
    }
    try {
      await this.actor.update(patch);
      ui.notifications?.info("Actor data repaired and normalized.");
    } catch (err) {
      console.error("Failed repairing actor data", err);
      ui.notifications?.error("Unable to repair actor data.");
    }
  }

  async _importPathwayPackage() {
    if (this.actor.type !== "character") return;

    const pathwayId = this.actor.system?.identity?.pathwayId;
    if (!pathwayId || typeof pathwayId !== "string") {
      ui.notifications?.warn("Set identity.pathwayId before importing pathway package.");
      return;
    }

    const packId = "lotm-system.pathways";
    const pack = game.packs?.get(packId);
    if (!pack) {
      ui.notifications?.warn(`No pathway pack found: ${packId}. Rebuild compendiums.`);
      return;
    }

    const docs = await pack.getDocuments();
    const pathwayDocs = docs.filter((doc) => (
      ["pathway", "sequenceNode"].includes(doc.type) && doc.system?.pathwayId === pathwayId
    ));
    if (pathwayDocs.length === 0) {
      ui.notifications?.warn(`No pathway entries found for ${pathwayId} in ${packId}.`);
      return;
    }

    const existingSystemIds = new Set(
      this.actor.items.map((item) => item.system?.id).filter((id) => typeof id === "string")
    );

    const toCreate = pathwayDocs
      .map((doc) => doc.toObject())
      .filter((item) => !existingSystemIds.has(item.system?.id));

    try {
      if (toCreate.length === 0) {
        ui.notifications?.info("Pathway package already imported on this actor.");
      } else {
        await this.actor.createEmbeddedDocuments("Item", toCreate);
        ui.notifications?.info(`Imported ${toCreate.length} pathway entries.`);
      }

      const creation = this._getCreationState();
      const completed = uniqueSteps([...creation.completedSteps, "pathway"]);
      await this.actor.update({
        "system.creation.state": "pathway",
        "system.creation.completedSteps": completed,
        "system.creation.version": 1
      });
    } catch (err) {
      console.error("Failed importing pathway package", err);
      ui.notifications?.error("Unable to import pathway package.");
    }
  }

  async _onDropItemCreate(itemData) {
    const prepared = foundry.utils.duplicate(itemData);
    prepared.system ??= {};
    prepared.system.cost = Number(prepared.system.cost ?? 0);
    prepared.system.cooldown = Number(prepared.system.cooldown ?? 0);
    if (!Array.isArray(prepared.system.tags)) prepared.system.tags = [];
    if (!Array.isArray(prepared.system.effects)) prepared.system.effects = [];
    return super._onDropItemCreate(prepared);
  }
}
