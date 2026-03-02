import { ATTRIBUTE_KEYS } from "../constants.mjs";

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

export class LotMActorSheet extends ActorSheet {
  static get defaultOptions() {
    return foundry.utils.mergeObject(super.defaultOptions, {
      classes: ["lotm", "sheet", "actor"],
      width: 880,
      height: 760,
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

    context.system = system;
    context.attributeKeys = ATTRIBUTE_KEYS;
    context.itemGroups = groupItems(items);
    context.skillEntries = Object.entries(system.skills ?? {}).sort(([a], [b]) => a.localeCompare(b));

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