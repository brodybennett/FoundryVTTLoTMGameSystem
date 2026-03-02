import { SYSTEM_ID, WORLD_SCHEMA_VERSION } from "../module/constants.mjs";
import { LotMActor } from "../module/actor/lotm-actor.mjs";
import { LotMItem } from "../module/item/lotm-item.mjs";
import { LotMActorSheet } from "../module/sheets/lotm-actor-sheet.mjs";
import { LotMItemSheet } from "../module/sheets/lotm-item-sheet.mjs";
import {
  rollCheck,
  rollDamage,
  applyCorruption,
  rollRitualRisk,
  rollArtifactBacklash
} from "../module/rolls/roll-engine.mjs";
import { runWorldMigrationV120 } from "../module/migrations/v1_2_0.mjs";

const REQUIRED_PACKS = [
  "pathways",
  "seer-abilities",
  "seer-items",
  "seer-rituals",
  "seer-artifacts",
  "seer-rolltables"
].map((name) => `${SYSTEM_ID}.${name}`);

function registerSettings() {
  game.settings.register(SYSTEM_ID, "automationLevel", {
    name: "LOTM.Settings.AutomationLevel.Name",
    hint: "LOTM.Settings.AutomationLevel.Hint",
    scope: "world",
    config: true,
    type: String,
    choices: {
      full: "LOTM.Settings.AutomationLevel.Full",
      assisted: "LOTM.Settings.AutomationLevel.Assisted",
      manual: "LOTM.Settings.AutomationLevel.Manual"
    },
    default: "assisted"
  });

  game.settings.register(SYSTEM_ID, "showRollBreakdown", {
    name: "LOTM.Settings.ShowRollBreakdown.Name",
    hint: "LOTM.Settings.ShowRollBreakdown.Hint",
    scope: "client",
    config: true,
    type: Boolean,
    default: true
  });

  game.settings.register(SYSTEM_ID, "worldSchemaVersion", {
    name: "LOTM.Settings.WorldSchemaVersion.Name",
    scope: "world",
    config: false,
    type: String,
    default: "0.0.0"
  });
}

function registerDocumentsAndSheets() {
  CONFIG.Actor.documentClass = LotMActor;
  CONFIG.Item.documentClass = LotMItem;

  Actors.unregisterSheet("core", ActorSheet);
  Actors.registerSheet(SYSTEM_ID, LotMActorSheet, {
    makeDefault: true,
    label: "LOTM.Sheets.Actor",
    types: ["character", "npc"]
  });

  Items.unregisterSheet("core", ItemSheet);
  Items.registerSheet(SYSTEM_ID, LotMItemSheet, {
    makeDefault: true,
    label: "LOTM.Sheets.Item",
    types: [
      "pathway",
      "sequenceNode",
      "ability",
      "ritual",
      "artifact",
      "gear",
      "feature",
      "weapon",
      "armor",
      "consumable",
      "ingredient",
      "background",
      "conditionTemplate"
    ]
  });
}

function registerGameApi() {
  game.lotm = {
    version: game.system.version,
    schemaVersion: WORLD_SCHEMA_VERSION,
    rollCheck,
    rollDamage,
    applyCorruption,
    rollRitualRisk,
    rollArtifactBacklash
  };
}

function checkPackAvailability() {
  const missing = REQUIRED_PACKS.filter((packId) => !game.packs?.get(packId));
  if (missing.length === 0) return;

  const msg = `LoTM missing expected packs: ${missing.join(", ")}. Rebuild system compendiums.`;
  console.warn(msg);
  ui.notifications?.warn(msg);
}

function checkSchemaVersionHints() {
  const staleActors = (game.actors ?? []).filter((actor) => Number(actor.system?.version?.schemaVersion ?? 0) < 1);
  if (staleActors.length > 0) {
    ui.notifications?.warn(`LoTM detected ${staleActors.length} actor(s) with stale system schema data.`);
  }
}

Hooks.once("init", () => {
  console.log("LoTM | Initializing lotm-system v" + game.system.version);
  registerSettings();
  registerDocumentsAndSheets();
  registerGameApi();

  CONFIG.lotmSystem = {
    id: SYSTEM_ID,
    title: game.system.title,
    version: game.system.version,
    schemaVersion: WORLD_SCHEMA_VERSION
  };
});

Hooks.once("ready", async () => {
  await runWorldMigrationV120();
  checkPackAvailability();
  checkSchemaVersionHints();
});