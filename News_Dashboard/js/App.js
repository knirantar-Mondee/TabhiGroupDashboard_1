import { DataManager } from './DataManager.js';
import { UIManager } from './UIManager.js';

export class App {
  constructor() {
    this.dataManager = new DataManager();
    this.uiManager = new UIManager(this);
  }
  
  async init() {
    this.uiManager.showLoading();
    try {
      await this.dataManager.loadAllBrandsData();
      this.uiManager.initPortal();
    } catch (err) {
      console.error("App initialization failed:", err);
      this.uiManager.showToast("DATABASE READ ERROR. OFFLINE MODE LOADED.");
    }
  }
  
  loadBrand(brandId) {
    const brandData = this.dataManager.getBrandData(brandId);
    if (!brandData) {
      this.uiManager.showToast("DATABASE NOT YET LOADED. SYNCING...");
      return;
    }
    this.uiManager.renderBrandDashboard(brandId, brandData);
  }
  
  goHome() {
    this.uiManager.showPortal();
  }
}
