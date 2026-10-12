// Parses source text without executing submitted code.
const fs = require('fs');
const parser = require(process.argv[2]);
const items = JSON.parse(fs.readFileSync(0, 'utf8'));
const result = items.map(item => {
  const plugins=[];
  if (['.ts','.tsx'].includes(item.ext)) plugins.push('typescript');
  if (['.jsx','.tsx'].includes(item.ext)) plugins.push('jsx');
  try { parser.parse(item.source, {sourceType:item.sourceType||'unambiguous',plugins,errorRecovery:false}); return {id:item.id,status:'pass',diagnostic:''}; }
  catch(e) { return {id:item.id,status:'fail',diagnostic:e.message}; }
});
process.stdout.write(JSON.stringify({parser_version:require(require('path').join(require('path').dirname(process.argv[2]),'../package.json')).version,result}));
