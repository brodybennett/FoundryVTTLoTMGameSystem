import { ATTRIBUTE_KEYS, CREATION_STEPS, SKILL_RANKS } from "../constants.mjs";
import { buildActorRepairUpdate } from "../actor/validation.mjs";
import {
  evaluateCreationState,
  getSkillRegistryEntries,
  validateCreationStep
} from "../creation/creation-engine.mjs";

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
    return "templates/sheets/actor-sheet.hbs";
  }

  async getData(options = {}) {
    const context = await super.getData(options);
    const system = context.actor.system;
    const items = context.actor.items.map((entry) => entry.toObject(false));

    const isCharacter = context.actor.type === "character";
    const creation = normalizeCreationState(system, context.actor.type);

    let validation = { ok: true, errors: [], warnings: [] };
    if (game.lotm?.validateActorForPlay) {
      validation = game.lotm.validateActorForPlay(system, context.actor.type, items);
    }

    let derivedPreview = {
      hpMax: system.derived?.hpMax,
      spiritMax: system.derived?.spiritMax,
      sanityMax: system.derived?.sanityMax,
      defenseShift: system.derived?.defenseShift,
      initiativeTarget: system.derived?.initiativeTarget
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
        type: context.actor.type,
        system,
        items
      });
    }

    context.system = system;
    context.isCharacter = isCharacter;
    context.attributeKeys = ATTRIBUTE_KEYS;
    context.skillRanks = SKILL_RANKS;
    context.itemGroups = groupItems(items);
    context.skillEntries = Object.entries(system.skills ?? {}).sort(([a], [b]) => a.localeCompare(b));
    context.creation = creation;
    context.creationSteps = buildStepView(creation.state, creation.completedSteps);
    context.validation = validation;
    context.derivedPreview = derivedPreview;
    context.creationValidation = creationValidation;
    context.pathwayOptions = creationValidation.pathwayOptions ?? [];
    context.sequenceOptions = creationValidation.sequenceOptions ?? [];

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
      await game.lotm.rollCheck({ actor: this.actor, attribute, skillId, label });
    });

    html.find("[data-action='roll-ritual-risk']").on("click", async (event) => {
      event.preventDefault();
      await game.lotm.rollRitualRisk({ actor: this.actor, label: "Ritual Risk" });
    });

    html.find("[data-action='roll-artifact-backlash']").on("click", async (event) => {
      event.preventDefault();
      await game.lotm.rollArtifactBacklash({ actor: this.actor, label: "Artifact Backlash" });
    });

    html.find("[data-action='apply-corruption']").on("click", async (event) => {
      event.preventDefault();
      const raw = html.find("[name='lotm-corruption-delta']").val();
      const delta = Number(raw) || 0;
      await game.lotm.applyCorruption({ actor: this.actor, delta, source: "sheet" });
    });

    html.find("[data-action='item-edit']").on("click", (event) => {
      event.preventDefault();
      const li = event.currentTarget.closest(".item");
      const itemId = li?.dataset?.itemId;
      if (!itemId) return;
      const item = this.actor.items.get(itemId);
      item?.sheet?.render(true);
    });

    html.find("[data-action='item-delete']").on("click", async (event) => {
      event.preventDefault();
      const li = event.currentTarget.closest(".item");
      const itemId = li?.dataset?.itemId;
      if (!itemId) return;
      await this.actor.deleteEmbeddedDocuments("Item", [itemId]);
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
    if (!allowed.includes(step)) return;

    await this.actor.update({ "system.creation.state": step, "system.creation.version": 1 });
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

    await this.actor.update({
      "system.creation.state": nextStep,
      "system.creation.completedSteps": uniqueSteps(completed),
      "system.creation.version": 1
    });
  }

  async _finalizeCreation() {
    if (this.actor.type !== "character") return;

    const creationValidation = await evaluateCreationState(this.actor);
    if (!creationValidation.canFinalize) {
      ui.notifications?.error(`Cannot finalize character: ${creationValidation.finalizeErrors.join("; ")}`);
      return;
    }

    const derived = game.lotm.deriveActorStats(this.actor.system);
    const validation = game.lotm.validateActorForPlay(
      this.actor.system,
      this.actor.type,
      this.actor.items.map((item) => item.toObject(false))
    );

    if (validation.errors.length > 0) {
      ui.notifications?.error(`Cannot finalize character: ${validation.errors.join("; ")}`);
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

    await this.actor.update(patch);
    ui.notifications?.info("Character creation finalized.");
  }

  async _repairActorData() {
    const skillRegistryEntries = await getSkillRegistryEntries();
    const patch = buildActorRepairUpdate(this.actor.system, this.actor.type, skillRegistryEntries);
    if (Object.keys(patch).length === 0) {
      ui.notifications?.info("No repair actions required.");
      return;
    }
    await this.actor.update(patch);
    ui.notifications?.info("Actor data repaired and normalized.");
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
