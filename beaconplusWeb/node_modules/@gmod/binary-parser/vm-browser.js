// https://github.com/ionic-team/rollup-plugin-node-polyfills/blob/9b5fe1a9cafffd4871e6d65613ed224f807ea251/polyfills/vm.js#L129-L132
function runInThisContext(code) {
  const fn = new Function('code', 'return eval(code);');
  return fn.call(globalThis, code);
}

module.exports.runInThisContext = runInThisContext;
