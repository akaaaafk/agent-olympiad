// Compile reviewed style text only. No browser, puzzle scripts, imports or JS expressions.
'use strict';
const fs = require('fs');
const less = require('../data/.cache/mystery_2013_static_20260913/less_tool/node_modules/less');
if (less.version.join('.') !== '1.3.0') throw new Error('LESS version drift');
const input = fs.readFileSync(0, 'utf8');
if (/@import|`|javascript:|expression\s*\(/i.test(input)) throw new Error('Unreviewed active/imported style');
less.Parser.importer = function () { throw new Error('Imports are disabled'); };
new less.Parser({}).parse(input, (error, tree) => {
  if (error) throw new Error(error.message);
  process.stdout.write(tree.toCSS({compress: false}));
});
