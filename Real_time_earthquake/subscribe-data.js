/**
 * TREM-Lite 指定區域震度監測工具
 * 專門監測臺北南港區、臺中中區、臺南永康區和新竹市東區的震度
 */


// 11248668 大安
// 13190428


const path = require('path');
const WebSocket = require('ws');
const { v4: uuidv4 } = require('uuid');

// 配置參數
const CONFIG = {
  // 訂閱間隔 (毫秒)
  interval: 1000, // 符合 TREM-Lite 原始設置
  // 請求超時時間 (毫秒)
  timeout: {
    RTS: 2000,
    EEW: 2000,
    INTENSITY: 2000,
    LPGM: 2000,
    STATION: 3500  // 新增 station info 超時設定
  },
  // API 服務器
  servers: {
    api: ['api-1.exptech.dev', 'api-2.exptech.dev'],
    lb: [
      'lb-1.exptech.dev',
      'lb-2.exptech.dev',
      'lb-3.exptech.dev',
      'lb-4.exptech.dev'
    ]
  },
  // 指定監測的區域
  targetAreas: [
    { code: 106, name: '臺北市大安區' },
    { code: 402, name: '臺中市南區' },
    { code: 710, name: '臺南市永康區' },
    { code: 301, name: '新竹市東區' }
  ],
  // 顯示震度閾值（即使沒有震動也要顯示0） 
  displayThreshold: 0,
  // WebSocket 端口
  wsPort: process.env.WS_PORT ? parseInt(process.env.WS_PORT) : 3000
};

// 原始 TREM-Lite 使用的震度等級文字表示
const INTENSITY_LIST = ['0', '1', '2', '3', '4', '5⁻', '5⁺', '6⁻', '6⁺', '7'];

// 上次成功獲取數據的時間
let lastFetchTime = 0;
// 請求計數器
let requestCounter = 0;
// 離線狀態跟踪
let isOffline = false;
// 儲存每個區域的最後數據
const areaStatus = {};
// 儲存測站資訊
let stationInfo = null;
// 上次獲取測站資訊的時間
let lastStationInfoFetch = 0;
// 測站資訊更新間隔 (5分鐘)
const STATION_INFO_INTERVAL = 5 * 60 * 1000;
// 統一規模
let unifiedMagnitude = 0;

// 初始化每個區域的狀態
CONFIG.targetAreas.forEach(area => {
  areaStatus[area.code] = {
    name: area.name,
    pga: 0,
    intensity: 0,
    intensityText: '0',
    lastUpdate: null
  };
});

/**
 * 計算震度相關實用函數
 * 從原始 TREM-Lite 代碼複製並修改
 */

const IntensityCalculator = {
  /**
   * 將PGA轉換為震度浮點值
   * @param {number} pga - PGA值 (gal)
   * @returns {number} 震度浮點值
   */
  pgaToFloat(pga) {
    return 2 * (Math.log(pga) / Math.log(10)) + 0.7;
  },

  /**
   * 將PGA轉換為整數震度
   * @param {number} pga - PGA值 (gal)
   * @returns {number} 整數震度值 (0-9)
   */
  pgaToIntensity(pga) {
    return this.intensityFloatToInt(this.pgaToFloat(pga));
  },

  /**
   * 將浮點震度轉換為整數震度
   * @param {number} floatValue - 浮點震度值
   * @returns {number} 整數震度值 (0-9)
   */
  intensityFloatToInt(floatValue) {
    if (floatValue < 0) {
      return 0;
    }
    if (floatValue < 4.5) {
      return Math.round(floatValue);
    }
    if (floatValue < 5) {
      return 5;
    }
    if (floatValue < 5.5) {
      return 6;
    }
    if (floatValue < 6) {
      return 7;
    }
    if (floatValue < 6.5) {
      return 8;
    }
    return 9;
  },

  /**
   * 將整數震度轉換為文字表示
   * @param {number} level - 整數震度值 (0-9)
   * @returns {string} 震度文字表示
   */
  intensityToText(level) {
    if (level >= 0 && level < INTENSITY_LIST.length) {
      return INTENSITY_LIST[level];
    }
    return '不明';
  },

  /**
   * 根據震度和距離估算地震規模
   * @param {number} intensity - 震度值
   * @param {number} distance - 震源距離(公里)
   * @returns {number} 估算的地震規模
   */
  estimateMagnitude(intensity, distance) {
    // 使用 Kawasumi 公式估算規模
    // M = 0.58I + 1.5log10(D) - 0.007D + 0.5
    // I: 震度, D: 震源距離(km)
    return 0.58 * intensity + 1.5 * Math.log10(distance) - 0.007 * distance + 0.5;
  },

  /**
   * 根據震度估算合理的地震規模
   * @param {number} intensity - 震度值
   * @returns {number} 估算的地震規模
   */
  estimateReasonableMagnitude(intensity) {
    // 根據震度估算合理的震源距離
    let estimatedDistance;
    
    if (intensity <= 0) {
      // 微弱震度，可能是近距離小地震或遠距離中等地震
      estimatedDistance = 30;
    } else if (intensity <= 2) {
      // 輕微震度，估計是中距離地震
      estimatedDistance = 40;
    } else if (intensity <= 4) {
      // 中等震度，可能是近距離中等地震
      estimatedDistance = 50;
    } else if (intensity <= 6) {
      // 強震，可能是中距離大地震
      estimatedDistance = 60;
    } else {
      // 劇烈震動，可能是近距離大地震
      estimatedDistance = 70;
    }
    
    // 根據估算距離計算規模
    let magnitude = this.estimateMagnitude(intensity, estimatedDistance);
    
    // 對於非常小的震度，確保規模不會不合理地大
    if (intensity < 0 && magnitude > 3) {
      magnitude = 2 + (intensity + 3) * 0.3;
    }
    
    // 確保規模在合理範圍內
    if (magnitude < 0) magnitude = 0;
    if (magnitude > 9) magnitude = 9;
    
    return magnitude;
  },

  /**
   * 根據震度估算最小規模
   * @param {number} intensity - 震度值
   * @returns {number} 估算的最小規模
   */
  estimateMinMagnitude(intensity) {
    // 根據經驗公式估算最小規模
    // 假設震源距離為10公里
    return this.estimateMagnitude(intensity, 10);
  },

  /**
   * 根據震度估算最大規模
   * @param {number} intensity - 震度值
   * @returns {number} 估算的最大規模
   */
  estimateMaxMagnitude(intensity) {
    // 根據經驗公式估算最大規模
    // 假設震源距離為100公里
    return this.estimateMagnitude(intensity, 100);
  }
};

/**
 * 自訂 fetch 函數，支持超時和錯誤處理
 */
async function fetchData(url, timeout = 1000) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);
  try {
    const response = await fetch(url, { signal: controller.signal, cache: 'no-cache' });
    clearTimeout(timeoutId);

    if (isOffline) {
      console.info(`[subscribe-data.js] -> 網絡連接已恢復`);
      isOffline = false;
    }

    return response;
  }
  catch (error) {
    if (!isOffline) {
      if (error.name === 'AbortError') {
        console.error(`[subscribe-data.js] -> 請求超時 | ${url}`);
      }
      else {
        console.error(`[subscribe-data.js] -> 請求失敗: ${url} | ${error.message}`);
      }
      isOffline = true;
    }

    return null;
  }
}

/**
 * 獲取隨機服務器
 */
function getRandomServer(type) {
  const servers = CONFIG.servers[type] || CONFIG.servers.lb;
  return servers[Math.floor(Math.random() * servers.length)];
}

/**
 * 獲取測站資訊
 */
async function getStationInfo() {
  const now = Date.now();
  
  // 如果已經有測站資訊且未超過更新間隔，直接返回
  if (stationInfo && (now - lastStationInfoFetch < STATION_INFO_INTERVAL)) {
    return stationInfo;
  }
  
  const server = getRandomServer('api');
  const response = await fetchData(
    `https://${server}/api/v1/trem/station`,
    CONFIG.timeout.STATION
  );
  
  if (response && response.ok) {
    stationInfo = await response.json();
    lastStationInfoFetch = now;
    console.log(`[subscribe-data.js] -> 測站資訊更新成功`);
    return stationInfo;
  }
  
  console.error(`[subscribe-data.js] -> 獲取測站資訊失敗`);
  return null;
}

/**
 * 處理RTS數據，尋找指定地區的數據
 * @param {Object} data - 原始RTS數據
 * @returns {Object} 處理後的指定地區數據
 */
async function processTargetAreaData(data) {
  if (!data || !data.station) return null;
  // 獲取測站資訊
  const stationInfo = await getStationInfo();
  if (!stationInfo) {
    console.error(`[subscribe-data.js] -> 無法處理RTS數據：缺少測站資訊`);
    return null;
  }
  
  // 處理結果
  const result = {
    time: data.time || Date.now(),
    updatedAreas: []
  };
  
  // 所有測站的總震度
  let totalIntensity = 0;
  let countedStations = 0;
  
  // 遍歷所有測站數據
  for (const [stationId, stationData] of Object.entries(data.station)) {
    // 獲取測站資訊
    const station = stationInfo[stationId];
    if (!station || !station.info || !station.info.length) {
      continue;
    }
    
    // 獲取最新的測站資訊
    const latestInfo = station.info[station.info.length - 1];
    const areaCode = latestInfo.code;
    
    // 檢查是否為目標地區
    const targetArea = CONFIG.targetAreas.find(area => area.code === areaCode);
    if (!targetArea) continue;
    
    // 計算震度
    const pga = stationData.pga || 0;
    const intensityFloat = stationData.i;
    const intensityInt = stationData.I;
    const intensityText = stationData.i;

    // 估算地震規模
    const magnitude = IntensityCalculator.estimateReasonableMagnitude(intensityFloat);
    
    // 累計震度以計算平均值
    totalIntensity += intensityFloat;
    countedStations++;
    
    // 檢查值是否有變化
    const changed = (
      areaStatus[areaCode].pga !== pga ||
      areaStatus[areaCode].intensity !== intensityInt
    );
    
    // 更新狀態
    if (changed || !areaStatus[areaCode].lastUpdate) {
      areaStatus[areaCode] = {
        name: targetArea.name,
        pga: pga,
        intensity: intensityInt,
        intensityText: intensityText,
        magnitude: magnitude.toFixed(1),
        lastUpdate: new Date()
      };
      
      result.updatedAreas.push({
        code: areaCode,
        name: targetArea.name,
        pga: pga,
        intensityFloat: intensityFloat.toFixed(2),
        intensity: intensityInt,
        intensityText: intensityText,
        magnitude: magnitude.toFixed(1),
        stationId: stationId,
        location: {
          lat: latestInfo.lat,
          lon: latestInfo.lon
        }
      });
    }
  }
  
  // 計算統一規模（基於所有測站的平均震度）
  if (countedStations > 0) {
    const averageIntensity = totalIntensity / countedStations;
    unifiedMagnitude = IntensityCalculator.estimateReasonableMagnitude(averageIntensity);
  }
  
  return result;
}

// 添加 WebSocket 服務器功能
let wss;

function formatAreaData(areaStatus, timestamp) {
  // Create base earthquake data
  const earthquakeData = {
    id: uuidv4(),
    source: "TREM-Lite",
    origin_time: new Date(timestamp).toISOString(),
    epicenter_location: "Unknown", // We don't have this information in real-time data
    magnitude_value: parseFloat(unifiedMagnitude.toFixed(1)),
    focal_depth: 0, // We don't have this information in real-time data
    shaking_area: []
  };

  // Format each area's data
  for (const [areaCode, status] of Object.entries(areaStatus)) {
    if (status.intensity > CONFIG.displayThreshold || CONFIG.displayThreshold === 0) {
      const areaData = {
        county_name: {
          name: status.name,
          code: parseInt(areaCode)
        },
        area_intensity: parseFloat(status.intensityFloat || status.intensity),
        pga: parseFloat(status.pga.toFixed(2))
      };
      earthquakeData.shaking_area.push(areaData);
    }
  }

  return earthquakeData;
}

function setupWebSocketServer() {
  wss = new WebSocket.Server({ port: CONFIG.wsPort });
  console.log(`WebSocket 服務器運行於 ws://localhost:${CONFIG.wsPort}`);

  wss.on('connection', (ws) => {
    console.log('新的客戶端連接');
    
    // 發送當前狀態
    const formattedData = formatAreaData(areaStatus, Date.now());
    ws.send(JSON.stringify(formattedData));
  });
}

/**
 * 在終端顯示最新的地區狀態
 */
function displayAreaStatus() {
  // 清除終端
  console.clear();
  
  // 顯示標題
  console.log('\n=== 指定地區即時震度監測 ===');
  console.log(`更新時間: ${new Date().toLocaleString()}`);
  console.log(`統一規模: ${unifiedMagnitude.toFixed(1)}`);
  console.log('-----------------------------------');
  
  // 顯示每個地區的狀態
  CONFIG.targetAreas.forEach(area => {
    const status = areaStatus[area.code];
    const lastUpdateText = status.lastUpdate 
      ? status.lastUpdate.toLocaleTimeString()
      : '尚無數據';
    
    // 根據震度選擇顏色
    let color = '\x1b[0m'; // 默認
    
    if (status.intensity >= 7) {
      color = '\x1b[41m\x1b[37m'; // 紅底白字
    } else if (status.intensity >= 5) {
      color = '\x1b[43m\x1b[30m'; // 黃底黑字
    } else if (status.intensity >= 3) {
      color = '\x1b[42m\x1b[30m'; // 綠底黑字
    } else if (status.intensity >= 1) {
      color = '\x1b[44m\x1b[37m'; // 藍底白字
    }
    
    const resetColor = '\x1b[0m';
    const magnitudeText = status.magnitude 
      ? `規模 ${status.magnitude}`
      : '規模未知';
    
    console.log(`${area.name}: ${color}震度 ${status.intensityText}${resetColor} (${status.pga.toFixed(2)} gal) ${magnitudeText} [${lastUpdateText}]`);
  });
  
  console.log('-----------------------------------');
  console.log('按 Ctrl+C 結束監測');
}

/**
 * 獲取實時數據
 */
async function fetchRealtimeData() {
  const now = Date.now();
  
  // 限制請求頻率
  if (now - lastFetchTime < CONFIG.interval) {
    return;
  }
  lastFetchTime = now;
  
  requestCounter++;
  
  const server = getRandomServer('lb');
  
  try {
    // 獲取 RTS 數據
    const rtsResponse = await fetchData(
      `https://${server}/api/v2/trem/rts`, 
      CONFIG.timeout.RTS
    );
    
    if (rtsResponse && rtsResponse.ok) {
      const rtsData = await rtsResponse.json();
      // console.log(rtsData);
      // process.exit(1);
      //  
      // 處理目標地區數據
      const targetAreaData = await processTargetAreaData(rtsData);
      
      // 顯示最新狀態
      displayAreaStatus();
      
      // 向所有連接的 WebSocket 客戶端發送更新
      if (wss && wss.clients) {
        const formattedData = formatAreaData(areaStatus, targetAreaData ? targetAreaData.time : Date.now());
        wss.clients.forEach(client => {
          if (client.readyState === WebSocket.OPEN) {
            client.send(JSON.stringify(formattedData));
          }
        });
      }
      
      // 顯示有變化的區域 (額外資訊)
      if (targetAreaData && targetAreaData.updatedAreas.length > 0) {
        targetAreaData.updatedAreas.forEach(area => {
          // 只在震度大於0時顯示更新訊息
          if (area.intensity > 0) {
            console.log(`\n${new Date().toLocaleTimeString()} - ${area.name} 震度更新為 ${area.intensityText} (${area.pga.toFixed(2)} gal)`);
          }
        });
      }
    }
    
    // 每1分鐘更新一次，即使數據沒變
    if (requestCounter % 60 === 0) {
      displayAreaStatus();
    }
    
  } catch (error) {
    console.error(`獲取數據失敗: ${error.message}`);
  }
}

/**
 * 主函數
 */
async function main() {
  console.log(`
TREM-Lite 指定地區震度監測工具
------------------------------
監測以下地區的即時震度:
- 臺北市南港區 (115)
- 臺中市中區 (400)
- 臺南市永康區 (710)
- 新竹市東區 (301)
------------------------------
`);
  
  // 初始化測站資訊
  await getStationInfo();
  
  // 設置 WebSocket 服務器
  setupWebSocketServer();
  
  // 顯示初始狀態
  displayAreaStatus();
  
  // 立即執行一次
  await fetchRealtimeData();
  
  // 設置定時器持續獲取數據
  setInterval(fetchRealtimeData, CONFIG.interval);
}

// 確保 fetch 在 Node.js 環境中可用
if (!globalThis.fetch) {
  console.error("您的 Node.js 版本不支持原生 fetch API，請升級到 Node.js 18+ 或安裝 'node-fetch' 套件");
  process.exit(1);
}

// 啟動程序
main().catch(error => {
  console.error(`啟動失敗: ${error.message}`);
  process.exit(1);
});
