FROM mcr.microsoft.com/playwright@sha256:47b510dd9230bf0b9bfc9b20102241e577ea7a99334ab4c3ca19f19770e9b8ea
WORKDIR /tests
COPY package*.json ./
RUN npm ci --ignore-scripts --no-audit --no-fund
COPY workflows.cjs navigation-actions.json ./
CMD ["node","workflows.cjs"]
