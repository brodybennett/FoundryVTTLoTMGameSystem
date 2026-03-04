import { ROLLTABLE_SEGMENTS } from "../constants.mjs";
import { createLotMInfoCard } from "../chat/chat-cards.mjs";

function getAutomationLevel() {
  return game.settings?.get("lotm-system", "automationLevel") ?? "assisted";
}

function hashKey(value) {
  const str = String(value ?? "");
  let hash = 0;
  for (let i = 0; i < str.length; i += 1) {
    hash = ((hash << 5) - hash) + str.charCodeAt(i);
    hash |= 0;
  }
  return Math.abs(hash);
}

function getRollTablePacks() {
  const names = new Set(
    (game.system?.packs ?? [])
      .filter((pack) => pack.type === "RollTable")
      .map((pack) => `lotm-system.${pack.name}`)
  );
  return [...(game.packs ?? [])].filter((pack) => names.has(pack.collection));
}

async function resolveTableDocsFromPack(pack) {
  const index = await pack.getIndex({ fields: ["name", "flags"] });
  const ids = index.map((entry) => entry._id);
  const docs = [];
  for (const id of ids) {
    const doc = await pack.getDocument(id);
    if (doc) docs.push(doc);
  }
  return docs;
}

export async function resolveTableBySegment(segment) {
  if (!ROLLTABLE_SEGMENTS.includes(segment)) {
    throw new Error(`Unknown roll-table segment: ${segment}`);
  }

  const packId = "lotm-system.rolltables";
  const pack = game.packs?.get(packId);
  if (!pack) {
    throw new Error(`Missing roll-table pack '${packId}'. Rebuild compendiums.`);
  }

  const docs = await resolveTableDocsFromPack(pack);
  if (docs.length === 0) {
    throw new Error(`Roll-table pack '${packId}' is empty`);
  }

  const docsForSegment = docs.filter((doc) => doc.getFlag("lotm", "groups")?.segment === segment);
  if (docsForSegment.length === 0) {
    throw new Error(`Roll-table pack '${packId}' has no entries for segment '${segment}'`);
  }

  return { packId, docs: docsForSegment };
}

function pickTableDeterministically(docs, context = {}) {
  const sorted = [...docs].sort((a, b) => String(a.id).localeCompare(String(b.id)));
  if (sorted.length === 1) return sorted[0];

  const seedKey = context.seed ?? context.deterministicKey;
  if (seedKey == null) {
    const idx = Math.floor(Math.random() * sorted.length);
    return sorted[idx];
  }

  const idx = hashKey(seedKey) % sorted.length;
  return sorted[idx];
}

async function drawFromTable(table, drawOptions = {}) {
  const draw = await table.draw(drawOptions);
  const results = (draw?.results ?? []).map((entry) => entry.text);
  return {
    tableId: table.id,
    tableName: table.name,
    results,
    draw
  };
}

async function askAssistedConfirmation(tableName, segment) {
  if (typeof Dialog?.confirm !== "function") return false;
  return Dialog.confirm({
    title: "LoTM Roll Table Trigger",
    content: `<p>Draw from <strong>${tableName}</strong> for segment <strong>${segment}</strong>?</p>`,
    yes: () => true,
    no: () => false,
    defaultYes: true
  });
}

export async function rollOnSegment(segment, context = {}) {
  const { docs } = await resolveTableBySegment(segment);
  const table = pickTableDeterministically(docs, context);

  const automationLevel = getAutomationLevel();
  let drawPayload = null;

  if (automationLevel === "full") {
    drawPayload = await drawFromTable(table, { displayChat: true });
  } else if (automationLevel === "assisted") {
    const confirmed = await askAssistedConfirmation(table.name, segment);
    if (confirmed) {
      drawPayload = await drawFromTable(table, { displayChat: true });
    }
  }

  const payload = {
    segment,
    automationLevel,
    tableId: table.id,
    tableName: table.name,
    drawn: drawPayload != null,
    results: drawPayload?.results ?? [],
    context,
    timestamp: Date.now()
  };

  await createLotMInfoCard({
    title: `Roll Table Trigger (${segment})`,
    summary: payload.drawn ? `Drew from ${table.name}` : `Selected ${table.name} (no auto-draw)`,
    details: {
      automationLevel,
      table: table.name,
      drawn: payload.drawn,
      results: payload.results.join(" | ")
    }
  });

  return payload;
}

export async function rollOnTableId(contentId, context = {}) {
  const packs = getRollTablePacks();
  for (const pack of packs) {
    const docs = await resolveTableDocsFromPack(pack);
    const match = docs.find((doc) => doc.getFlag("lotm", "contentId") === contentId);
    if (!match) continue;

    const automationLevel = getAutomationLevel();
    let drawPayload = null;
    if (automationLevel === "full") {
      drawPayload = await drawFromTable(match, { displayChat: true });
    } else if (automationLevel === "assisted") {
      const confirmed = await askAssistedConfirmation(match.name, "tableId");
      if (confirmed) drawPayload = await drawFromTable(match, { displayChat: true });
    }

    return {
      contentId,
      automationLevel,
      tableId: match.id,
      tableName: match.name,
      drawn: drawPayload != null,
      results: drawPayload?.results ?? [],
      context,
      timestamp: Date.now()
    };
  }

  throw new Error(`No roll table found for contentId: ${contentId}`);
}
