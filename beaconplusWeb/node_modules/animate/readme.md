# animate
animate is a small wrapper around requestAnimationFrame that adds a frame rate constraint. It also provides simple `pause` and `resume` methods. The code is based on [this blog article](http://codetheory.in/controlling-the-frame-rate-with-requestanimationframe/).

[![Browser support](https://ci.testling.com/michaelrhodes/animate.png)](https://ci.testling.com/michaelrhodes/animate)

<small>Older browsers might require a polyfill for [Function.prototype.bind](http://kangax.github.io/es5-compat-table/#Function.prototype.bind).</small>

## Install
```sh
$ npm install animate
```

### Example
``` js
var animate = require('animate')

// Run the frame 24 times a second.
var animation = animate(function frame() {
  // Blah, blah, some animation.
}, 24)

animation.pause()
animation.resume()
```

### License
[MIT](http://opensource.org/licenses/MIT)
