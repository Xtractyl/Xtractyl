FROM node:20-bullseye
WORKDIR /app

COPY package.json package-lock.json ./
RUN npm install

COPY . .

ENV ROLLUP_USE_NODE_BUILTINS=true

EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]