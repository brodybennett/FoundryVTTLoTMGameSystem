import { SYSTEM_ID } from "../constants.mjs";

const FOLDER_FLAG_SCOPE = "lotm";
const FOLDER_FLAG_KEY = "folderKey";
const AUTO_FLAG_KEY = "autoOrganizer";

const PACK_IDS = {
  pathways: `${SYSTEM_ID}.pathways`,
  rolltables: `${SYSTEM_ID}.rolltables`,
  items: `${SYSTEM_ID}.items`,
  actors: `${SYSTEM_ID}.actors`
};

const ROLLTABLE_SEGMENT_LABELS = {
  resources: "Resources",
  abilities: "Abilities",
  rituals: "Rituals",
  artifacts: "Artifacts",
  corruption: "Corruption",
  encounters: "Encounters"
};

const ACTOR_CATEGORY_LABELS = {
  "actors-factions": "Faction NPCs",
  "actors-beyonder-monsters": "Beyonder Monsters",
  "actors-civilians": "Civilians"
};

function titleFromPathwayId(pathwayId) {
  if (!pathwayId || typeof pathwayId !== "string") return "Other";
  const raw = pathwayId.split(".").pop() ?? "other";
  return raw
    .split("_")
    .filter((segment) => segment)
    .map((segment) => segment.charAt(0).toUpperCase() + segment.slice(1))
    .join(" ");
}

function asArray(collectionLike) {
  if (!collectionLike) return [];
  if (Array.isArray(collectionLike)) return collectionLike;
  return [...collectionLike];
}

function getFolderKey(prefix, value) {
  const safe = String(value ?? "other");
  return `${prefix}:${safe}`;
}

function getItemGroup(itemType) {
  if (itemType === "weapon") return { key: "weapons", label: "Weapons" };
  if (itemType === "armor") return { key: "armor", label: "Armor" };
  if (itemType === "consumable") return { key: "consumables", label: "Consumables" };
  if (itemType === "ingredient") return { key: "ingredients", label: "Ingredients" };
  if (["gear", "feature", "background", "conditionTemplate"].includes(itemType)) {
    return { key: "gear_features", label: "Gear & Features" };
  }
  return { key: "other", label: "Other" };
}

function getRolltableGroup(segment) {
  return {
    key: segment || "other",
    label: ROLLTABLE_SEGMENT_LABELS[segment] ?? "Other"
  };
}

function getActorGroup(category) {
  return {
    key: category || "actors-other",
    label: ACTOR_CATEGORY_LABELS[category] ?? "Other"
  };
}

async function withPackWriteAccess(pack, operation) {
  const wasLocked = Boolean(pack.locked);
  if (wasLocked) {
    await pack.configure({ locked: false });
  }

  try {
    return await operation();
  } finally {
    if (wasLocked) {
      await pack.configure({ locked: true });
    }
  }
}

function findMatchingFolder(pack, key, name) {
  const folders = asArray(pack.folders);
  const byFlag = folders.find((folder) => folder.getFlag(FOLDER_FLAG_SCOPE, FOLDER_FLAG_KEY) === key);
  if (byFlag) return byFlag;
  return folders.find((folder) => folder.name === name && folder.folder == null);
}

async function ensureFolder(pack, key, name, sort = 0) {
  const existing = findMatchingFolder(pack, key, name);
  if (existing) return existing;

  const created = await Folder.create(
    {
      name,
      type: pack.documentName,
      folder: null,
      sorting: "a",
      sort,
      color: null,
      flags: {
        [FOLDER_FLAG_SCOPE]: {
          [FOLDER_FLAG_KEY]: key,
          [AUTO_FLAG_KEY]: true
        }
      }
    },
    { pack: pack.collection }
  );
  return created;
}

async function setDocumentFolder(doc, folder) {
  const currentFolderId = doc.folder?.id ?? doc.folder ?? null;
  if (currentFolderId === folder.id) return false;
  if (typeof doc.setFolder === "function") {
    await doc.setFolder(folder);
  } else {
    await doc.update({ folder: folder.id });
  }
  return true;
}

async function organizePack(pack, docs, groupResolver, prefix) {
  const grouped = new Map();
  for (const doc of docs) {
    const group = groupResolver(doc);
    const key = getFolderKey(prefix, group.key);
    if (!grouped.has(key)) {
      grouped.set(key, { label: group.label, docs: [] });
    }
    grouped.get(key).docs.push(doc);
  }

  const sortedGroups = [...grouped.entries()].sort((a, b) => a[1].label.localeCompare(b[1].label));
  let moved = 0;
  let created = 0;

  for (let i = 0; i < sortedGroups.length; i += 1) {
    const [folderKey, payload] = sortedGroups[i];
    const existing = findMatchingFolder(pack, folderKey, payload.label);
    const folder = existing ?? await ensureFolder(pack, folderKey, payload.label, i * 10);
    if (!existing) created += 1;

    for (const doc of payload.docs) {
      if (await setDocumentFolder(doc, folder)) moved += 1;
    }
  }

  return { moved, created, groups: sortedGroups.length };
}

async function resolvePack(packId) {
  const pack = game.packs?.get(packId);
  if (!pack) return null;
  return pack;
}

async function getPackDocuments(pack) {
  const docs = await pack.getDocuments();
  return Array.isArray(docs) ? docs : [];
}

export async function organizeCompendiums({ notify = true } = {}) {
  const report = {
    pathways: { moved: 0, created: 0, groups: 0 },
    rolltables: { moved: 0, created: 0, groups: 0 },
    items: { moved: 0, created: 0, groups: 0 },
    actors: { moved: 0, created: 0, groups: 0 }
  };

  const pathwayPack = await resolvePack(PACK_IDS.pathways);
  if (pathwayPack) {
    await withPackWriteAccess(pathwayPack, async () => {
      const docs = await getPackDocuments(pathwayPack);
      const pathwayDocs = docs.filter((doc) => ["pathway", "sequenceNode"].includes(doc.type));
      report.pathways = await organizePack(
        pathwayPack,
        pathwayDocs,
        (doc) => {
          const pathwayId = doc.system?.pathwayId ?? "pathway.other";
          return { key: pathwayId, label: titleFromPathwayId(pathwayId) };
        },
        "pathway"
      );
    });
  }

  const rolltablePack = await resolvePack(PACK_IDS.rolltables);
  if (rolltablePack) {
    await withPackWriteAccess(rolltablePack, async () => {
      const docs = await getPackDocuments(rolltablePack);
      report.rolltables = await organizePack(
        rolltablePack,
        docs,
        (doc) => getRolltableGroup(doc.getFlag("lotm", "groups")?.segment),
        "rolltable"
      );
    });
  }

  const itemsPack = await resolvePack(PACK_IDS.items);
  if (itemsPack) {
    await withPackWriteAccess(itemsPack, async () => {
      const docs = await getPackDocuments(itemsPack);
      report.items = await organizePack(
        itemsPack,
        docs,
        (doc) => getItemGroup(doc.type),
        "item"
      );
    });
  }

  const actorsPack = await resolvePack(PACK_IDS.actors);
  if (actorsPack) {
    await withPackWriteAccess(actorsPack, async () => {
      const docs = await getPackDocuments(actorsPack);
      report.actors = await organizePack(
        actorsPack,
        docs,
        (doc) => getActorGroup(doc.getFlag("lotm", "groups")?.category),
        "actor"
      );
    });
  }

  if (notify) {
    const created = report.pathways.created + report.rolltables.created + report.items.created + report.actors.created;
    const moved = report.pathways.moved + report.rolltables.moved + report.items.moved + report.actors.moved;
    ui.notifications?.info(`LoTM compendiums organized. Folders created: ${created}, docs moved: ${moved}.`);
  }

  return report;
}
