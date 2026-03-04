import { SYSTEM_ID, WORLD_SCHEMA_VERSION } from "../module/constants.mjs";
import { LotMActor } from "../module/actor/lotm-actor.mjs";
import { LotMItem } from "../module/item/lotm-item.mjs";
import { LotMActorSheet } from "../module/sheets/lotm-actor-sheet.mjs";
import { LotMCharacterSheet } from "../module/sheets/lotm-character-sheet.mjs";
import { LotMItemSheet } from "../module/sheets/lotm-item-sheet.mjs";
import {
  rollCheck,
  rollDamage,
  applyCorruption,
  rollRitualRisk,
  rollArtifactBacklash
} from "../module/rolls/roll-engine.mjs";
import { rollOnSegment, rollOnTableId } from "../module/rolls/rolltable-engine.mjs";
import { deriveActorStats, validateActorForPlay } from "../module/actor/validation.mjs";
import { runWorldMigrationV120 } from "../module/migrations/v1_2_0.mjs";
import { organizeCompendiums } from "../module/compendium/organizer.mjs";
import {
  getPathwayOptions,
  getSequenceOptions,
  validateCreationStep
} from "../module/creation/creation-engine.mjs";

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

  game.settings.register(SYSTEM_ID, "autoOrganizeCompendiums", {
    name: "LOTM.Settings.AutoOrganizeCompendiums.Name",
    hint: "LOTM.Settings.AutoOrganizeCompendiums.Hint",
    scope: "world",
    config: true,
    type: Boolean,
    default: true
  });
}

function registerDocumentsAndSheets() {
  CONFIG.Actor.documentClass = LotMActor;
  CONFIG.Item.documentClass = LotMItem;

  Actors.unregisterSheet("core", ActorSheet);
  Actors.registerSheet(SYSTEM_ID, LotMCharacterSheet, {
    makeDefault: true,
    label: "LOTM.Sheets.Actor",
    types: ["character"]
  });
  Actors.registerSheet(SYSTEM_ID, LotMActorSheet, {
    makeDefault: true,
    label: "LOTM.Sheets.Actor",
    types: ["npc"]
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

async function preloadCharacterSheetTemplates() {
  const base = `systems/${SYSTEM_ID}/templates/sheets/character`;
  const partials = [
    `${base}/character-header.hbs`,
    `${base}/character-sidebar.hbs`,
    `${base}/shared/sidebar-tabs.hbs`,
    `${base}/shared/ability-scores.hbs`,
    `${base}/shared/list-controls.hbs`,
    `${base}/shared/trait-pills.hbs`,
    `${base}/shared/biography-textbox.hbs`,
    `${base}/shared/class-pills.hbs`,
    `${base}/tabs/details.hbs`,
    `${base}/tabs/inventory.hbs`,
    `${base}/tabs/features.hbs`,
    `${base}/tabs/spells.hbs`,
    `${base}/tabs/effects.hbs`,
    `${base}/tabs/biography.hbs`,
    `${base}/tabs/special-traits.hbs`
  ];
  await loadTemplates(partials);
}

function registerGameApi() {
  game.lotm = {
    version: game.system.version,
    schemaVersion: WORLD_SCHEMA_VERSION,
    rollCheck,
    rollDamage,
    applyCorruption,
    rollRitualRisk,
    rollArtifactBacklash,
    rollOnSegment,
    rollOnTableId,
    validateActorForPlay,
    deriveActorStats,
    organizeCompendiums,
    validateCreationStep,
    getPathwayOptions,
    getSequenceOptions
  };
}

function checkPackAvailability() {
  const expected = (game.system?.packs ?? []).map((pack) => `${SYSTEM_ID}.${pack.name}`);
  const missing = expected.filter((packId) => !game.packs?.get(packId));
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

Hooks.once("init", async () => {
  console.log("LoTM | Initializing lotm-system v" + game.system.version);
  registerSettings();
  registerDocumentsAndSheets();
  registerGameApi();
  await preloadCharacterSheetTemplates();

  CONFIG.lotmSystem = {
    id: SYSTEM_ID,
    title: game.system.title,
    version: game.system.version,
    schemaVersion: WORLD_SCHEMA_VERSION,
    rolltableHooks: {
      ritualFailure: { segment: "rituals" },
      artifactBacklash: { segment: "artifacts" },
      corruptionThresholdCross: { segment: "corruption" }
    }
  };
});

Hooks.once("ready", async () => {
  await runWorldMigrationV120();
  checkPackAvailability();
  checkSchemaVersionHints();

  if (game.user?.isGM && game.settings.get(SYSTEM_ID, "autoOrganizeCompendiums")) {
    try {
      await organizeCompendiums({ notify: false });
    } catch (err) {
      console.warn("LoTM compendium auto-organization failed", err);
      ui.notifications?.warn("LoTM could not auto-organize compendium folders. Use game.lotm.organizeCompendiums() to retry.");
    }
  }
});
