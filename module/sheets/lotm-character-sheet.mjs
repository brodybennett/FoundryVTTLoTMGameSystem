import { ATTRIBUTE_KEYS, PROFICIENCY_BY_RANK, SYSTEM_ID } from "../constants.mjs";
import { deriveActorStats } from "../actor/validation.mjs";

const ATTRIBUTE_ORDER = ["str", "dex", "con", "int", "wil", "cha", "luck"];

const ATTRIBUTE_META = {
  str: { label: "Strength", abbr: "STR" },
  dex: { label: "Dexterity", abbr: "DEX" },
  con: { label: "Constitution", abbr: "CON" },
  int: { label: "Intellect", abbr: "INT" },
  wil: { label: "Willpower", abbr: "WIL" },
  cha: { label: "Charisma", abbr: "CHA" },
  luck: { label: "Luck", abbr: "LCK" }
};

const TAB_DEFINITIONS = [
  { id: "details", icon: "fa-solid fa-cog", label: "Details" },
  { id: "inventory", icon: "fa-solid fa-backpack", label: "Inventory" },
  { id: "features", icon: "fa-solid fa-list", label: "Features" },
  { id: "spells", icon: "fa-solid fa-book", label: "Spells" },
  { id: "effects", icon: "fa-solid fa-bolt", label: "Effects" },
  { id: "biography", icon: "fa-solid fa-feather", label: "Biography" },
  { id: "special-traits", icon: "fa-solid fa-star", label: "Special Traits" }
];

const INVENTORY_SECTION_DEFINITIONS = [
  { id: "weapons", label: "Weapons", itemType: "weapon", createType: "weapon" },
  { id: "armor", label: "Armor", itemType: "armor", createType: "armor" },
  { id: "gear", label: "Gear", itemType: "gear", createType: "gear" },
  { id: "consumables", label: "Consumables", itemType: "consumable", createType: "consumable" },
  { id: "ingredients", label: "Ingredients", itemType: "ingredient", createType: "ingredient" },
  { id: "artifacts", label: "Artifacts", itemType: "artifact", createType: "artifact" }
];

const FEATURE_SECTION_DEFINITIONS = [
  { id: "features", label: "Features", itemType: "feature", createType: "feature" },
  { id: "backgrounds", label: "Backgrounds", itemType: "background", createType: "background" },
  {
    id: "conditionTemplates",
    label: "Condition Templates",
    itemType: "conditionTemplate",
    createType: "conditionTemplate"
  }
];

const SPELL_SECTION_DEFINITIONS = [
  { id: "abilities", label: "Abilities", itemType: "ability", createType: "ability" },
  { id: "rituals", label: "Rituals", itemType: "ritual", createType: "ritual" }
];

const FILTER_IDS = ["inventory", "features", "spells", "effects"];
const DEFAULT_FILTER_STATE = Object.freeze({ query: "", sort: "alpha" });

const CREATION_COMPLETED_BASE = ["identity", "attributes", "skills", "equipment"];

let conditionLibraryPromise = null;

function stringOrEmpty(value) {
  return typeof value === "string" ? value.trim() : "";
}

function numberOr(value, fallback = 0) {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function titleCaseToken(value) {
  if (!value || typeof value !== "string") return "";
  return value
    .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
    .replace(/[_.-]/g, " ")
    .split(" ")
    .filter((segment) => segment.length > 0)
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(" ");
}

function scoreMod(total) {
  return Math.floor((numberOr(total, 10) - 10) / 2);
}

function attrTotal(system, key) {
  const stat = system?.attributes?.[key] ?? {};
  return numberOr(stat.total, numberOr(stat.base, 10) + numberOr(stat.temp, 0));
}

function mapToPips(max, value) {
  const current = Math.max(0, Math.min(numberOr(value, 0), max));
  return Array.from({ length: max }, (_unused, index) => ({
    n: index + 1,
    filled: index < current
  }));
}

function csvToList(value) {
  if (!value || typeof value !== "string") return [];
  return [...new Set(value
    .split(",")
    .map((entry) => entry.trim())
    .filter((entry) => entry.length > 0))];
}

function listToCsv(values = []) {
  if (!Array.isArray(values)) return "";
  return values.filter((entry) => typeof entry === "string" && entry.trim().length > 0).join(", ");
}

function normalizeTraits(system = {}) {
  const traits = system.traits ?? {};
  const ensure = (key) => Array.isArray(traits[key]) ? traits[key] : [];

  return {
    senses: ensure("senses"),
    resistances: ensure("resistances"),
    immunities: ensure("immunities"),
    conditionImmunities: ensure("conditionImmunities"),
    vulnerabilities: ensure("vulnerabilities"),
    damageModification: ensure("damageModification")
  };
}

function normalizeDetails(system = {}) {
  const details = system.details ?? {};
  const biography = details.biography ?? {};

  return {
    alignment: stringOrEmpty(details.alignment),
    faith: stringOrEmpty(details.faith),
    gender: stringOrEmpty(details.gender),
    eyes: stringOrEmpty(details.eyes),
    hair: stringOrEmpty(details.hair),
    skin: stringOrEmpty(details.skin),
    height: stringOrEmpty(details.height),
    weight: stringOrEmpty(details.weight),
    age: stringOrEmpty(details.age),
    ideal: stringOrEmpty(details.ideal),
    bond: stringOrEmpty(details.bond),
    flaw: stringOrEmpty(details.flaw),
    trait: stringOrEmpty(details.trait),
    appearance: stringOrEmpty(details.appearance),
    biography: {
      value: stringOrEmpty(biography.value),
      public: stringOrEmpty(biography.public)
    }
  };
}

function sortItemsByName(items = []) {
  return [...items].sort((lhs, rhs) => String(lhs.name ?? "").localeCompare(String(rhs.name ?? ""), game.i18n.lang));
}

function sortItems(items = [], sort = "alpha") {
  if (sort === "type") {
    return [...items].sort((lhs, rhs) => {
      const typeCompare = String(lhs.type ?? "").localeCompare(String(rhs.type ?? ""), game.i18n.lang);
      if (typeCompare !== 0) return typeCompare;
      return String(lhs.name ?? "").localeCompare(String(rhs.name ?? ""), game.i18n.lang);
    });
  }
  return sortItemsByName(items);
}

function buildListEntry(item, { favoriteMap = {}, expandedSet = new Set() } = {}) {
  return {
    _id: item._id,
    id: item._id,
    name: item.name,
    img: item.img,
    type: item.type,
    systemId: item.system?.id,
    summary: stringOrEmpty(item.system?.description),
    expanded: expandedSet.has(item._id),
    isFavorite: Boolean(favoriteMap[item._id])
  };
}

function applySectionFilters(items = [], filterState = DEFAULT_FILTER_STATE) {
  const query = stringOrEmpty(filterState.query).toLowerCase();
  const sorted = sortItems(items, filterState.sort);

  if (!query) return sorted;
  return sorted.filter((item) => {
    const haystack = [item.name, item.type, item.system?.id, item.system?.pathwayId]
      .map((value) => String(value ?? "").toLowerCase())
      .join(" ");
    return haystack.includes(query);
  });
}

function buildSectionContext(definitions, itemMap, filterState, { favoriteMap = {}, expandedSet = new Set() } = {}) {
  return definitions.map((def) => {
    const source = itemMap[def.itemType] ?? [];
    const filtered = applySectionFilters(source, filterState);
    return {
      ...def,
      items: filtered.map((item) => buildListEntry(item, { favoriteMap, expandedSet })),
      count: filtered.length,
      hasItems: filtered.length > 0
    };
  });
}

function groupItemsByType(items = []) {
  const groups = {
    pathway: [],
    sequenceNode: [],
    ability: [],
    ritual: [],
    weapon: [],
    armor: [],
    gear: [],
    consumable: [],
    ingredient: [],
    artifact: [],
    feature: [],
    background: [],
    conditionTemplate: [],
    other: []
  };

  for (const item of items) {
    if (item.type in groups) groups[item.type].push(item);
    else groups.other.push(item);
  }

  return groups;
}

async function getConditionLibrary() {
  if (conditionLibraryPromise) return conditionLibraryPromise;

  conditionLibraryPromise = (async () => {
    const path = `systems/${game.system.id}/data/conditions.library.v1.1.json`;
    try {
      const response = await fetch(path, { cache: "no-store" });
      if (!response.ok) throw new Error(`Failed to load ${path}`);
      const payload = await response.json();
      return Array.isArray(payload.conditions) ? payload.conditions : [];
    } catch (err) {
      console.warn("LoTM failed to load condition library", err);
      return [];
    }
  })();

  return conditionLibraryPromise;
}

function resolvePathwayIdentity(items = []) {
  const pathways = items.filter((item) => item.type === "pathway");
  const sequenceNodes = items
    .filter((item) => item.type === "sequenceNode")
    .map((item) => ({
      pathwayId: stringOrEmpty(item.system?.pathwayId),
      sequence: Number(item.system?.sequence),
      item
    }))
    .filter((entry) => entry.pathwayId && Number.isInteger(entry.sequence))
    .sort((lhs, rhs) => lhs.sequence - rhs.sequence);

  if (sequenceNodes.length > 0) {
    const chosen = sequenceNodes[0];
    return {
      pathwayId: chosen.pathwayId,
      sequence: chosen.sequence,
      hasPathway: true
    };
  }

  if (pathways.length > 0) {
    const firstPathway = pathways[0];
    return {
      pathwayId: stringOrEmpty(firstPathway.system?.pathwayId) || stringOrEmpty(firstPathway.system?.id),
      sequence: null,
      hasPathway: true
    };
  }

  return {
    pathwayId: "",
    sequence: null,
    hasPathway: false
  };
}

function normalizeFavoriteIds(actor) {
  const value = actor.getFlag(SYSTEM_ID, "favorites.items");
  if (!Array.isArray(value)) return [];
  return [...new Set(value.filter((entry) => typeof entry === "string" && entry.trim().length > 0))];
}

function toCreationMetadata(pathwaySelected) {
  return {
    state: "complete",
    completedSteps: pathwaySelected ? [...CREATION_COMPLETED_BASE, "pathway"] : [...CREATION_COMPLETED_BASE],
    version: 1
  };
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

export class LotMCharacterSheet extends ActorSheet {
  constructor(...args) {
    super(...args);
    this._filters = FILTER_IDS.reduce((state, key) => {
      state[key] = { ...DEFAULT_FILTER_STATE };
      return state;
    }, {});
    this._expandedItems = new Set();
    this._activePrimaryTab = "details";
    this._sidebarCollapsed = false;
  }

  static get defaultOptions() {
    return foundry.utils.mergeObject(super.defaultOptions, {
      classes: ["sheet", "actor", "character", "dnd5e2", "vertical-tabs", "lotm-character-sheet"],
      width: 980,
      height: 930,
      tabs: [{ navSelector: ".sheet-tabs", contentSelector: ".sheet-body", initial: "details" }],
      dragDrop: [{ dragSelector: ".item", dropSelector: null }],
      submitOnChange: true
    });
  }

  get template() {
    return `systems/${game.system.id}/templates/sheets/character/character-sheet.hbs`;
  }

  async getData(options = {}) {
    const context = await super.getData(options);
    const actor = context.actor ?? this.actor;
    const system = actor.system ?? {};
    const details = normalizeDetails(system);
    const traits = normalizeTraits(system);
    const items = actor.items.map((entry) => entry.toObject(false));
    const groupedItems = groupItemsByType(items);

    const derivedPreview = typeof game.lotm?.deriveActorStats === "function"
      ? game.lotm.deriveActorStats(system)
      : deriveActorStats(system);

    let favoriteIds = normalizeFavoriteIds(actor);
    const validFavoriteIds = favoriteIds.filter((id) => actor.items.has(id));
    if (validFavoriteIds.length !== favoriteIds.length && actor.isOwner) {
      await actor.setFlag(SYSTEM_ID, "favorites.items", validFavoriteIds);
      favoriteIds = validFavoriteIds;
    } else {
      favoriteIds = validFavoriteIds;
    }
    const favoriteMap = Object.fromEntries(favoriteIds.map((id) => [id, true]));

    const abilityEntries = ATTRIBUTE_ORDER
      .filter((key) => ATTRIBUTE_KEYS.includes(key))
      .map((key) => {
        const total = attrTotal(system, key);
        return {
          key,
          label: ATTRIBUTE_META[key]?.label ?? titleCaseToken(key),
          abbr: ATTRIBUTE_META[key]?.abbr ?? key.toUpperCase(),
          base: numberOr(system?.attributes?.[key]?.base, 10),
          total,
          mod: scoreMod(total)
        };
      });

    const skillRows = Object.entries(system.skills ?? {})
      .map(([id, entry]) => {
        const linkedAttr = entry?.linkedAttr ?? "wil";
        const rank = entry?.rank ?? "familiar";
        const misc = numberOr(entry?.misc, 0);
        const proficiency = numberOr(PROFICIENCY_BY_RANK[rank], 0);
        const attrScore = attrTotal(system, linkedAttr);
        const display = Math.floor(attrScore / 3) + proficiency + misc;
        return {
          id,
          label: titleCaseToken(id),
          linkedAttr,
          linkedAttrAbbr: ATTRIBUTE_META[linkedAttr]?.abbr ?? linkedAttr.toUpperCase(),
          rank,
          misc,
          proficiency,
          display
        };
      })
      .sort((lhs, rhs) => lhs.label.localeCompare(rhs.label, game.i18n.lang));

    const saveRows = abilityEntries.map((entry) => ({
      key: entry.key,
      abbr: entry.abbr,
      label: `${entry.label} Save`,
      bonus: Math.floor(entry.total / 3)
    }));

    const inventoryFilter = this._filters.inventory ?? DEFAULT_FILTER_STATE;
    const featuresFilter = this._filters.features ?? DEFAULT_FILTER_STATE;
    const spellsFilter = this._filters.spells ?? DEFAULT_FILTER_STATE;

    const inventorySections = buildSectionContext(INVENTORY_SECTION_DEFINITIONS, groupedItems, inventoryFilter, {
      favoriteMap,
      expandedSet: this._expandedItems
    });

    const featureSections = buildSectionContext(FEATURE_SECTION_DEFINITIONS, groupedItems, featuresFilter, {
      favoriteMap,
      expandedSet: this._expandedItems
    });

    const spellSections = buildSectionContext(SPELL_SECTION_DEFINITIONS, groupedItems, spellsFilter, {
      favoriteMap,
      expandedSet: this._expandedItems
    });

    const classPills = sortItemsByName(groupedItems.pathway).map((pathwayItem) => {
      const pathwayId = stringOrEmpty(pathwayItem.system?.pathwayId);
      const sequenceNodes = groupedItems.sequenceNode
        .filter((node) => stringOrEmpty(node.system?.pathwayId) === pathwayId)
        .sort((lhs, rhs) => numberOr(lhs.system?.sequence, 99) - numberOr(rhs.system?.sequence, 99))
        .map((entry) => ({
          id: entry._id,
          name: entry.name,
          sequence: numberOr(entry.system?.sequence, 0),
          img: entry.img,
          isFavorite: Boolean(favoriteMap[entry._id])
        }));

      return {
        id: pathwayItem._id,
        name: pathwayItem.name,
        pathwayId,
        img: pathwayItem.img,
        sequenceNodes,
        isFavorite: Boolean(favoriteMap[pathwayItem._id])
      };
    });

    const primaryBackground = sortItemsByName(groupedItems.background)[0] ?? null;
    const identityFromItems = resolvePathwayIdentity(items);
    const effectivePathwayId = stringOrEmpty(identityFromItems.pathwayId || system.identity?.pathwayId);
    const effectiveSequence = Number.isInteger(numberOr(identityFromItems.sequence, NaN))
      ? numberOr(identityFromItems.sequence, 0)
      : (Number.isInteger(numberOr(system.identity?.sequence, NaN)) ? numberOr(system.identity?.sequence, 0) : null);
    const pathwayLabel = classPills[0]?.name
      || titleCaseToken(effectivePathwayId)
      || "Civilian";

    const spiritCurrent = numberOr(system.resources?.spirit, 0);
    const spiritMax = Math.max(0, numberOr(derivedPreview.spiritMax, 0));
    const spiritPct = spiritMax > 0 ? Math.max(0, Math.min((spiritCurrent / spiritMax) * 100, 100)) : 0;
    const hpCurrent = numberOr(system.resources?.hp, 0);
    const hpMax = Math.max(1, numberOr(derivedPreview.hpMax, 1));
    const hpPct = hpMax > 0 ? Math.max(0, Math.min((hpCurrent / hpMax) * 100, 100)) : 0;

    const favoriteItems = favoriteIds
      .map((id) => actor.items.get(id))
      .filter((item) => item)
      .map((item) => ({
        id: item.id,
        name: item.name,
        img: item.img,
        type: item.type
      }));

    const conditionLibrary = await getConditionLibrary();
    const activeConditionById = new Map(
      actor.effects
        .filter((effect) => effect.getFlag(SYSTEM_ID, "conditionId"))
        .map((effect) => [effect.getFlag(SYSTEM_ID, "conditionId"), effect])
    );
    const effectsFilter = this._filters.effects ?? DEFAULT_FILTER_STATE;
    const effectsQuery = stringOrEmpty(effectsFilter.query).toLowerCase();

    let conditionGrid = conditionLibrary.map((condition) => {
      const activeEffect = activeConditionById.get(condition.id);
      const data = {
        id: condition.id,
        name: condition.name,
        description: condition.description,
        active: Boolean(activeEffect),
        effectId: activeEffect?.id ?? ""
      };
      return data;
    });
    if (effectsQuery) {
      conditionGrid = conditionGrid.filter((condition) => (
        `${condition.name} ${condition.description}`.toLowerCase().includes(effectsQuery)
      ));
    }
    if (effectsFilter.sort === "type") {
      conditionGrid = conditionGrid.sort((lhs, rhs) => Number(rhs.active) - Number(lhs.active)
        || lhs.name.localeCompare(rhs.name, game.i18n.lang));
    } else {
      conditionGrid = conditionGrid.sort((lhs, rhs) => lhs.name.localeCompare(rhs.name, game.i18n.lang));
    }

    let activeEffects = actor.effects
      .map((effect) => ({
        id: effect.id,
        name: effect.name,
        icon: effect.icon,
        disabled: effect.disabled,
        conditionId: effect.getFlag(SYSTEM_ID, "conditionId")
      }))
      .sort((lhs, rhs) => lhs.name.localeCompare(rhs.name, game.i18n.lang));
    if (effectsQuery) {
      activeEffects = activeEffects.filter((effect) => (
        `${effect.name} ${effect.conditionId ?? ""}`.toLowerCase().includes(effectsQuery)
      ));
    }
    if (effectsFilter.sort === "type") {
      activeEffects = activeEffects.sort((lhs, rhs) => Number(lhs.disabled) - Number(rhs.disabled)
        || lhs.name.localeCompare(rhs.name, game.i18n.lang));
    }

    const proficiencyEstimate = Math.max(
      0,
      ...Object.values(system.skills ?? {}).map((entry) => Math.floor(numberOr(PROFICIENCY_BY_RANK[entry?.rank], 0) / 5))
    );

    const speedEstimate = Math.max(0, 30 - numberOr(system.combat?.encumbrancePenalty, 0));

    this._sidebarCollapsed = Boolean(await game.user?.getFlag?.(SYSTEM_ID, "characterSheet.sidebarCollapsed"));

    context.actor = actor;
    context.system = system;
    context.details = details;
    context.traits = traits;
    context.traitsCsv = {
      senses: listToCsv(traits.senses),
      resistances: listToCsv(traits.resistances),
      immunities: listToCsv(traits.immunities),
      conditionImmunities: listToCsv(traits.conditionImmunities),
      vulnerabilities: listToCsv(traits.vulnerabilities),
      damageModification: listToCsv(traits.damageModification)
    };
    context.abilityRows = {
      top: abilityEntries.slice(0, 3),
      bottom: abilityEntries.slice(3)
    };
    context.skillRows = skillRows;
    context.skillRanks = Object.keys(PROFICIENCY_BY_RANK);
    context.saveRows = saveRows;
    context.tabNav = TAB_DEFINITIONS;
    context.inventorySections = inventorySections;
    context.featureSections = featureSections;
    context.spellSections = spellSections;
    context.primaryBackground = primaryBackground;
    context.classPills = classPills;
    context.hasClassPills = classPills.length > 0;
    context.favoriteItems = favoriteItems;
    context.favoriteCount = favoriteItems.length;
    context.favoriteMap = favoriteMap;
    context.expandedItems = [...this._expandedItems];
    context.filters = this._filters;
    context.pathwayLabel = pathwayLabel;
    context.sequenceLabel = Number.isInteger(numberOr(effectiveSequence, NaN))
      ? `Sequence ${numberOr(effectiveSequence, 0)}`
      : "No Sequence";
    context.header = {
      spiritCurrent,
      spiritMax,
      spiritPct,
      tier: titleCaseToken(system.identity?.tier)
    };
    context.sidebar = {
      proficiency: proficiencyEstimate,
      speed: speedEstimate,
      deathMarks: mapToPips(3, numberOr(system.resources?.deathMarks, 0)),
      deathSaves: mapToPips(3, numberOr(system.resources?.deathSaves, 0)),
      sidebarCollapsed: this._sidebarCollapsed
    };
    context.resources = {
      hp: hpCurrent,
      hpMax,
      hpPct,
      spirit: spiritCurrent,
      spiritMax,
      corruption: numberOr(system.resources?.corruption, 0),
      corruptionPenalty: numberOr(derivedPreview.corruptionPenalty, 0)
    };
    context.conditionGrid = conditionGrid;
    context.activeEffects = activeEffects;
    context.hasActiveEffects = activeEffects.length > 0;

    return context;
  }

  activateListeners(html) {
    super.activateListeners(html);

    html.find(".sheet-tabs .item").on("click", (event) => {
      this._activePrimaryTab = event.currentTarget?.dataset?.tab || this._activePrimaryTab;
    });

    html.find("[data-action='toggle-sidebar']").on("click", async (event) => {
      event.preventDefault();
      await this._toggleSidebar();
    });

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
      const raw = html.find("[data-lotm-corruption-delta]").val()?.toString() ?? "0";
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

    html.find("[data-action='item-toggle-expand']").on("click", (event) => {
      event.preventDefault();
      const itemId = event.currentTarget.closest(".item")?.dataset?.itemId;
      if (!itemId) return;
      if (this._expandedItems.has(itemId)) this._expandedItems.delete(itemId);
      else this._expandedItems.add(itemId);
      this.render(false);
    });

    html.find("[data-action='item-edit']").on("click", (event) => {
      event.preventDefault();
      const itemId = event.currentTarget.closest(".item")?.dataset?.itemId;
      if (!itemId) return;
      this.actor.items.get(itemId)?.sheet?.render(true);
    });

    html.find("[data-action='item-delete']").on("click", async (event) => {
      event.preventDefault();
      const itemId = event.currentTarget.closest(".item")?.dataset?.itemId;
      if (!itemId) return;
      await this._deleteOwnedItem(itemId);
    });

    html.find("[data-action='item-create']").on("click", async (event) => {
      event.preventDefault();
      const type = event.currentTarget.dataset.type;
      if (!type) return;
      await this.actor.createEmbeddedDocuments("Item", [{
        name: `New ${titleCaseToken(type)}`,
        type,
        img: "icons/svg/item-bag.svg",
        system: {
          id: `item.${Date.now()}`,
          schemaVersion: 1,
          description: "",
          tags: [],
          effects: [],
          dependencies: {
            minSystemVersion: "1.1.0",
            maxTestedSystemVersion: game.system.version,
            requiresIds: []
          }
        }
      }]);
    });

    html.find("[data-action='toggle-favorite']").on("click", async (event) => {
      event.preventDefault();
      const itemId = event.currentTarget.closest(".item")?.dataset?.itemId;
      if (!itemId) return;
      await this._toggleFavorite(itemId);
    });

    html.find("[data-action='favorite-open']").on("click", (event) => {
      event.preventDefault();
      const itemId = event.currentTarget.closest("[data-item-id]")?.dataset?.itemId;
      if (!itemId) return;
      this.actor.items.get(itemId)?.sheet?.render(true);
    });

    html.find("[data-action='favorite-remove']").on("click", async (event) => {
      event.preventDefault();
      const itemId = event.currentTarget.closest("[data-item-id]")?.dataset?.itemId;
      if (!itemId) return;
      await this._toggleFavorite(itemId, { force: false, remove: true });
    });

    html.find("[data-list-search]").on("input", (event) => {
      const input = event.currentTarget;
      const list = input.dataset.listSearch;
      if (!list || !(list in this._filters)) return;
      this._filters[list].query = input.value ?? "";
      this.render(false);
    });

    html.find("[data-list-sort]").on("change", (event) => {
      const select = event.currentTarget;
      const list = select.dataset.listSort;
      if (!list || !(list in this._filters)) return;
      this._filters[list].sort = select.value === "type" ? "type" : "alpha";
      this.render(false);
    });

    html.find("[data-action='toggle-condition']").on("click", async (event) => {
      event.preventDefault();
      const button = event.currentTarget;
      const conditionId = button.dataset.conditionId;
      if (!conditionId) return;
      await this._toggleCondition(conditionId);
    });

    html.find("[data-action='effect-delete']").on("click", async (event) => {
      event.preventDefault();
      const effectId = event.currentTarget.closest("[data-effect-id]")?.dataset?.effectId;
      if (!effectId) return;
      await this._deleteActiveEffect(effectId);
    });

    html.find("[data-action='effect-toggle-disabled']").on("click", async (event) => {
      event.preventDefault();
      const effectId = event.currentTarget.closest("[data-effect-id]")?.dataset?.effectId;
      if (!effectId) return;
      await this._toggleEffectDisabled(effectId);
    });
  }

  async _toggleSidebar() {
    this._sidebarCollapsed = !this._sidebarCollapsed;
    await game.user?.setFlag?.(SYSTEM_ID, "characterSheet.sidebarCollapsed", this._sidebarCollapsed);
    this.render(false);
  }

  async _deleteOwnedItem(itemId) {
    const item = this.actor.items.get(itemId);
    if (!item) return;

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
      this._expandedItems.delete(itemId);
      await this._removeMissingFavorites();
      if (["pathway", "sequenceNode"].includes(item.type)) {
        await this._syncIdentityFromOwnedPathway();
      }
    } catch (err) {
      console.error("Failed deleting embedded item", err);
      ui.notifications?.error(`Unable to delete item '${item.name}'.`);
    }
  }

  async _toggleFavorite(itemId, { remove = false } = {}) {
    const item = this.actor.items.get(itemId);
    if (!item) return;

    const current = normalizeFavoriteIds(this.actor);
    const next = new Set(current);

    if (remove || next.has(itemId)) next.delete(itemId);
    else next.add(itemId);

    await this.actor.setFlag(SYSTEM_ID, "favorites.items", [...next]);
    this.render(false);
  }

  async _removeMissingFavorites() {
    const current = normalizeFavoriteIds(this.actor);
    const valid = current.filter((id) => this.actor.items.has(id));
    if (valid.length === current.length) return;
    await this.actor.setFlag(SYSTEM_ID, "favorites.items", valid);
  }

  async _toggleCondition(conditionId) {
    const existing = this.actor.effects.find((effect) => effect.getFlag(SYSTEM_ID, "conditionId") === conditionId);
    try {
      if (existing) {
        await this.actor.deleteEmbeddedDocuments("ActiveEffect", [existing.id]);
      } else {
        const condition = (await getConditionLibrary()).find((entry) => entry.id === conditionId);
        if (!condition) {
          ui.notifications?.warn(`Condition '${conditionId}' is unavailable.`);
          return;
        }

        await this.actor.createEmbeddedDocuments("ActiveEffect", [{
          name: condition.name,
          icon: "icons/svg/aura.svg",
          disabled: false,
          flags: {
            [SYSTEM_ID]: {
              conditionId
            }
          }
        }]);
      }
    } catch (err) {
      console.error("Failed toggling condition", err);
      ui.notifications?.error("Unable to toggle condition state.");
    }
  }

  async _deleteActiveEffect(effectId) {
    const effect = this.actor.effects.get(effectId);
    if (!effect) return;
    try {
      await this.actor.deleteEmbeddedDocuments("ActiveEffect", [effectId]);
    } catch (err) {
      console.error("Failed deleting active effect", err);
      ui.notifications?.error(`Unable to delete effect '${effect.name}'.`);
    }
  }

  async _toggleEffectDisabled(effectId) {
    const effect = this.actor.effects.get(effectId);
    if (!effect) return;
    try {
      await effect.update({ disabled: !effect.disabled });
    } catch (err) {
      console.error("Failed toggling active effect disabled state", err);
      ui.notifications?.error(`Unable to update effect '${effect.name}'.`);
    }
  }

  async _syncIdentityFromOwnedPathway() {
    const identity = resolvePathwayIdentity(this.actor.items.map((item) => item.toObject(false)));
    const currentPathway = stringOrEmpty(this.actor.system?.identity?.pathwayId);
    const currentSequence = this.actor.system?.identity?.sequence;

    const sequenceMatches = (identity.sequence == null && (currentSequence == null || currentSequence === ""))
      || Number(currentSequence) === Number(identity.sequence);

    if (currentPathway === identity.pathwayId && sequenceMatches) return;

    const creation = toCreationMetadata(identity.hasPathway);
    const patch = {
      "system.identity.pathwayId": identity.pathwayId,
      "system.identity.sequence": identity.sequence,
      "system.creation.state": creation.state,
      "system.creation.completedSteps": creation.completedSteps,
      "system.creation.version": creation.version
    };

    await this.actor.update(patch);
  }

  async _updateObject(event, formData) {
    const expanded = foundry.utils.expandObject(formData);
    expanded.system ??= {};
    expanded.system.traits ??= {};
    expanded.system.details ??= {};

    const lotm = expanded.lotm ?? {};
    const traitCsv = lotm.traits ?? {};

    if (typeof traitCsv.sensesCsv === "string") expanded.system.traits.senses = csvToList(traitCsv.sensesCsv);
    if (typeof traitCsv.resistancesCsv === "string") {
      expanded.system.traits.resistances = csvToList(traitCsv.resistancesCsv);
    }
    if (typeof traitCsv.immunitiesCsv === "string") expanded.system.traits.immunities = csvToList(traitCsv.immunitiesCsv);
    if (typeof traitCsv.conditionImmunitiesCsv === "string") {
      expanded.system.traits.conditionImmunities = csvToList(traitCsv.conditionImmunitiesCsv);
    }
    if (typeof traitCsv.vulnerabilitiesCsv === "string") {
      expanded.system.traits.vulnerabilities = csvToList(traitCsv.vulnerabilitiesCsv);
    }
    if (typeof traitCsv.damageModificationCsv === "string") {
      expanded.system.traits.damageModification = csvToList(traitCsv.damageModificationCsv);
    }

    const identity = expanded.system.identity ?? {};
    expanded.system.identity = identity;
    identity.pathwayId = stringOrEmpty(identity.pathwayId);
    if (identity.sequence === "" || identity.sequence == null) identity.sequence = null;
    else {
      const sequence = Number(identity.sequence);
      identity.sequence = Number.isInteger(sequence) ? sequence : null;
    }

    const creation = toCreationMetadata(Boolean(identity.pathwayId));
    expanded.system.creation ??= {};
    expanded.system.creation.state = creation.state;
    expanded.system.creation.completedSteps = creation.completedSteps;
    expanded.system.creation.version = creation.version;

    delete expanded.lotm;

    const flattened = foundry.utils.flattenObject(expanded);
    return super._updateObject(event, flattened);
  }

  async _onDropItemCreate(itemData) {
    const prepared = foundry.utils.duplicate(itemData);
    prepared.system ??= {};
    prepared.system.cost = Number(prepared.system.cost ?? 0);
    prepared.system.cooldown = Number(prepared.system.cooldown ?? 0);
    if (!Array.isArray(prepared.system.tags)) prepared.system.tags = [];
    if (!Array.isArray(prepared.system.effects)) prepared.system.effects = [];

    const result = await super._onDropItemCreate(prepared);

    if (["pathway", "sequenceNode"].includes(prepared.type)) {
      await this._syncIdentityFromOwnedPathway();
    }

    await this._removeMissingFavorites();
    return result;
  }
}
