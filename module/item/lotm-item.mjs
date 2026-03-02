export class LotMItem extends Item {
  prepareDerivedData() {
    super.prepareDerivedData();
    const system = this.system;
    if (!system) return;

    if (typeof system.cost !== "undefined") {
      system.cost = Number(system.cost) || 0;
    }
    if (typeof system.cooldown !== "undefined") {
      system.cooldown = Number(system.cooldown) || 0;
    }
    if (Array.isArray(system.tags) === false) {
      system.tags = [];
    }
    if (Array.isArray(system.effects) === false) {
      system.effects = [];
    }
  }
}