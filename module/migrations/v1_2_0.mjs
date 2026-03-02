import { SYSTEM_ID, WORLD_SCHEMA_VERSION, semverCompare } from "../constants.mjs";
import { buildActorRepairUpdate } from "../actor/validation.mjs";

function ensureActorShape(actorData) {
  const update = buildActorRepairUpdate(actorData.system ?? {}, actorData.type ?? "character");
  const system = actorData.system ?? {};

  if (system.resources?.deathSaves == null) update["system.resources.deathSaves"] = 0;
  if (system.tracks?.investigationIP == null) update["system.tracks.investigationIP"] = 0;

  if (system.combat?.armor == null) update["system.combat.armor"] = 0;
  if (system.combat?.cover == null) update["system.combat.cover"] = 0;
  if (system.combat?.encumbrancePenalty == null) update["system.combat.encumbrancePenalty"] = 0;
  if (system.combat?.damageReduction == null) update["system.combat.damageReduction"] = 0;
  if (system.combat?.actionBudget?.actions == null) update["system.combat.actionBudget.actions"] = 1;
  if (system.combat?.actionBudget?.moves == null) update["system.combat.actionBudget.moves"] = 1;
  if (system.combat?.actionBudget?.reactions == null) update["system.combat.actionBudget.reactions"] = 1;
  if (system.combat?.actionBudget?.bonusActions == null) update["system.combat.actionBudget.bonusActions"] = 0;

  if (system.version?.schemaVersion == null) update["system.version.schemaVersion"] = 1;
  return update;
}

function ensureItemShape(itemData) {
  const update = {};
  const system = itemData.system ?? {};

  if (system.dependencies == null) {
    update["system.dependencies"] = {
      minSystemVersion: "1.1.0",
      maxTestedSystemVersion: WORLD_SCHEMA_VERSION,
      requiresIds: []
    };
  }

  if (system.schemaVersion == null) update["system.schemaVersion"] = 1;
  if (Array.isArray(system.tags) === false) update["system.tags"] = [];
  if (Array.isArray(system.effects) === false) update["system.effects"] = [];

  return update;
}

async function migrateActors() {
  let migrated = 0;
  for (const actor of game.actors ?? []) {
    const update = ensureActorShape(actor.toObject());
    if (Object.keys(update).length > 0) {
      await actor.update(update, { diff: false, recursive: false });
      migrated += 1;
    }
  }
  return migrated;
}

async function migrateWorldItems() {
  let migrated = 0;
  for (const item of game.items ?? []) {
    const update = ensureItemShape(item.toObject());
    if (Object.keys(update).length > 0) {
      await item.update(update, { diff: false, recursive: false });
      migrated += 1;
    }
  }
  return migrated;
}

async function migrateEmbeddedItems() {
  let migrated = 0;
  for (const actor of game.actors ?? []) {
    for (const item of actor.items ?? []) {
      const update = ensureItemShape(item.toObject());
      if (Object.keys(update).length > 0) {
        await item.update(update, { diff: false, recursive: false });
        migrated += 1;
      }
    }
  }
  return migrated;
}

export async function runWorldMigrationV120() {
  const previous = game.settings.get(SYSTEM_ID, "worldSchemaVersion") || "0.0.0";
  if (semverCompare(previous, WORLD_SCHEMA_VERSION) >= 0) return;

  ui.notifications?.info(`LoTM migration ${previous} -> ${WORLD_SCHEMA_VERSION} started`);

  const actorCount = await migrateActors();
  const worldItemCount = await migrateWorldItems();
  const embeddedItemCount = await migrateEmbeddedItems();

  await game.settings.set(SYSTEM_ID, "worldSchemaVersion", WORLD_SCHEMA_VERSION);

  const summary = `LoTM migration complete. Actors: ${actorCount}, World Items: ${worldItemCount}, Embedded Items: ${embeddedItemCount}.`;
  console.log(summary);
  ui.notifications?.info(summary);
}
