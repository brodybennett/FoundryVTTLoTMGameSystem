async function renderFallbackContent({ title, summary, details }) {
  const lines = Object.entries(details || {}).map(([key, value]) => {
    const rendered = typeof value === "object" ? JSON.stringify(value) : String(value);
    return `<li><strong>${key}</strong>: ${rendered}</li>`;
  });
  return `<section class="lotm-chat-card"><h3>${title}</h3><p>${summary}</p><ul>${lines.join("")}</ul></section>`;
}

export async function createLotMCheckCard(payload) {
  const templatePath = "templates/chat/check-card.hbs";
  const content = await renderTemplate(templatePath, payload).catch(() => {
    const summary = `${payload.success ? "Success" : "Failure"} | Roll ${payload.roll} vs ${payload.finalTarget}`;
    return renderFallbackContent({ title: payload.label ?? "Check", summary, details: payload.components ?? {} });
  });

  return ChatMessage.create({
    speaker: ChatMessage.getSpeaker({ actor: game.actors?.get(payload.actorId) }),
    content,
    type: CONST.CHAT_MESSAGE_TYPES.ROLL,
    rolls: [],
    flags: {
      lotm: {
        payload
      }
    }
  });
}

export async function createLotMInfoCard({ title, summary, details = {} }) {
  const templatePath = "templates/chat/info-card.hbs";
  const content = await renderTemplate(templatePath, { title, summary, details }).catch(() => {
    return renderFallbackContent({ title, summary, details });
  });

  return ChatMessage.create({
    content,
    type: CONST.CHAT_MESSAGE_TYPES.OTHER
  });
}