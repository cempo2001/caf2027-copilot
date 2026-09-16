# Dev-orijentisan Dockerfile (isti nivo jednostavnosti kao backend/Dockerfile).
# Multi-stage produkcioni build (standalone output, non-root user, itd.) je
# DevOps/Deployment agent posao za Fazu 5 (CLAUDE.md Sekcija 7.8) — ovdje
# ciljamo `docker compose up` lokalni dev sa hot-reload-om (volumes u
# docker-compose.yml montiraju ./frontend/src preko ovoga).

FROM node:20-slim

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

ENV NEXT_TELEMETRY_DISABLED=1
EXPOSE 3000

CMD ["npm", "run", "dev"]
