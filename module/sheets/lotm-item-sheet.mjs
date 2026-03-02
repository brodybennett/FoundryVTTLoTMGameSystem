export class LotMItemSheet extends ItemSheet {
  static get defaultOptions() {
    return foundry.utils.mergeObject(super.defaultOptions, {
      classes: ["lotm", "sheet", "item"],
      width: 620,
      height: 680,
      tabs: [{ navSelector: ".sheet-tabs", contentSelector: ".sheet-body", initial: "details" }],
      submitOnChange: true
    });
  }

  get template() {
    return "templates/sheets/item-sheet.hbs";
  }

  async getData(options = {}) {
    const context = await super.getData(options);
    context.system = context.item.system;
    context.itemType = context.item.type;
    context.activationTypes = ["action", "bonusAction", "reaction", "passive", "special"];
    context.resourceTypes = ["spirit", "hp", "none", "item"];
    context.targetModes = ["self", "ally", "enemy", "area", "scene", "special"];
    context.riskClasses = ["stable", "volatile", "catastrophic"];
    return context;
  }
}