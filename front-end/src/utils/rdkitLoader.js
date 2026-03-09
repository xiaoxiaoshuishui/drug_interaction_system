class RDKitLoader {
  constructor() {
    this.instance = null;
    this.promise = null;
    this.scriptLoaded = false;
    this.initPromise = null;
  }

  async load(scriptPath = '/rdkit/RDKit_minimal.js') {
    // 如果已有实例，直接返回
    if (this.instance) {
      return this.instance;
    }

    // 如果正在加载，返回同一个 Promise
    if (this.promise) {
      return this.promise;
    }

    this.promise = new Promise(async (resolve, reject) => {
      try {
        // 检查脚本是否已加载
        if (!this.scriptLoaded) {
          await this.loadScript(scriptPath);
          this.scriptLoaded = true;
        }

        // 初始化 RDKit
        if (!window.RDKit) {
          if (!window.initRDKitModule) {
            throw new Error('RDKit script not loaded properly');
          }
          this.initPromise = window.initRDKitModule();
          window.RDKit = await this.initPromise;
        }

        this.instance = window.RDKit;
        resolve(this.instance);
      } catch (error) {
        console.error('RDKit加载失败:', error);
        reject(error);
      } finally {
        this.promise = null;
      }
    });

    return this.promise;
  }

  loadScript(src) {
    return new Promise((resolve, reject) => {
      // 检查是否已存在相同脚本
      if (document.querySelector(`script[src="${src}"]`)) {
        resolve();
        return;
      }

      const script = document.createElement('script');
      script.src = src;
      script.async = true;
      
      script.onload = () => resolve();
      script.onerror = () => reject(new Error(`Failed to load script: ${src}`));
      
      document.head.appendChild(script);
    });
  }

  // 预加载
  preload(scriptPath) {
    if (!this.scriptLoaded && !this.promise) {
      this.loadScript(scriptPath).catch(() => {});
    }
  }
}

export default new RDKitLoader();