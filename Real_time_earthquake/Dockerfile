# 使用 Node.js 18 作為基礎映像
FROM node:18-slim

# 設定工作目錄
WORKDIR /app

# 複製 package.json 文件
COPY ./package.json ./package.json

# 安裝依賴
RUN npm install

# 複製其他文件
COPY . .

# 設定環境變數
ENV NODE_ENV=production
ENV WS_PORT=2487

# 暴露 WebSocket 端口
EXPOSE ${WS_PORT}

# 設定容器啟動命令
CMD ["node", "subscribe-data.js"]