Hooks.once("init", () => {
  console.log("LoTM | Initializing lotm-system");

  CONFIG.lotmSystem = {
    id: "lotm-system",
    title: game.system.title,
    version: game.system.version
  };
});
