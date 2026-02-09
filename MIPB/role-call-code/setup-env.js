const fs = require('fs');
const content = 'DATABASE_URL="postgresql://postgres:password@localhost:5432/rolecall?schema=public"\n';
fs.writeFileSync('.env', content, { encoding: 'utf8' });
console.log('.env created');
