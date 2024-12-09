# canvas-sequencer

[![Node.js CI](https://github.com/mvanderkamp/canvas-sequencer/actions/workflows/node.js.yml/badge.svg)](https://github.com/mvanderkamp/canvas-sequencer/actions/workflows/node.js.yml)
[![Coverage Status](https://coveralls.io/repos/github/mvanderkamp/canvas-sequencer/badge.svg?branch=master)](https://coveralls.io/github/mvanderkamp/canvas-sequencer?branch=master)
[![Maintainability](https://api.codeclimate.com/v1/badges/777e9d732d4ceece8124/maintainability)](https://codeclimate.com/github/mvanderkamp/canvas-sequencer/maintainability)

Store, serialize, parse, and execute series of canvas context instructions!

## Contents

* [Why](#why)
* [Importing](#importing)
* [CanvasSequence API](#canvassequence-api)
* [CanvasBlueprint](#canvasblueprint-api)
* [Limitations](#limitations)
* [What's new in 2.0](#changes)

## Why

Normally, if you have a sequence of canvas instructions, you might predefine
them in a function which will be distributed in a script file to all your
clients.

Suppose, however, that you wish to be able to dynamically define instructions
from the server, and have those instructions executed on the canvas contexts of
your clients. One option would be to wrap the instructions up in a string on the
server, distribute the string, then have the clients call `eval()` on the
string.  This is error-prone and risky however, and exposes you to all the
incumbent problems of the `eval()` function.

With `canvas-sequencer` you can package those instructions up in a sequence and
transmit them. Once on the client side, you can unpack the instructions and
execute them on any given context (or even multiple contexts), and all the
issues with the `eval()` technique fade away.

## Importing:

Server side, or in a Node environment.

```javascript
const { CanvasSequence, CanvasBlueprint } = require('canvas-sequencer');
```

The code is also available pre-bundled, via `parcel-bundler`. You should
probably create your own bundle though, so that you have control over browser
targets, etc.

```javascript
const { CanvasSequence, CanvasBlueprint } = require('canvas-sequencer/dist');
```

Client side, to access the bundled code in a script tag:

```html
<script src="path/to/node_modules/canvas-sequencer/dist/index.js"></script>
```

## CanvasSequence API

### Creating a sequence:

```javascript
const seq = new CanvasSequence();
```

### Defining instructions:

You have access to the standard library of `CanvasRenderingContext2D`
instructions, with the exception of access to the underlying `canvas` object,
for safety reasons. You can access these instructions just as you would with a
normal `CanvasRenderingContext2D` object. Each instruction will be added onto
the end of the sequence.

```javascript
seq.beginPath();
seq.arc(25,25,42, 0, 2 * Math.PI);
seq.fillStyle = 'green';
seq.fill();
seq.lineWidth = 15;
seq.closePath();
seq.stroke();
```

### Transmitting the sequence

The sequencer exposes a `toJSON()` function, ensuring that with any library
which uses JSON methods to bundle data into packets for transmission (such as
`socket.io`) you will not need to do anything fancy for transmission of your
sequences. Just send the sequence object as you would any other piece of
serializable data.

```javascript
emitter.emit('new-sequence', seq);
```

### Unpacking the sequence.

The transmitted sequence needs to be revived in order for the CanvasSequence
functionality to be available. This can be done by passing the transmitted data
object to the constructor:

```javascript
// Assumes that you have recieve the packaged sequence in a 'data' variable.
const seq = new CanvasSequence(data);
```

### Executing the sequence.

You can execute the sequence on any `CanvasRenderingContext2D` as such:

```javascript
const ctx1 = document.querySelector('#canvas1').getContext('2d');
seq.execute(ctx1);

// And again on another context!
const ctx2 = document.querySelector('#canvas2').getContext('2d');
seq.execute(ctx2);
```

## CanvasBlueprint API

Also accessible through this library are sequence 'blueprints'. These allow you
to define a sequence once using placeholder tags for values, then build
executable sequences using the blueprint and a set of values to take the place
of the tags.

### How does it work?

The tags you can pass to a blueprint are strings wrapped in curly braces. The
string inside the curly braces should be the name of a property on the object
with which you intend to build the executable sequence.

Don't worry- if you want to pass the name of such a property into an actual
context function, you can still do that. Strings without curly braces are
ignored. If you want to pass a string wrapped in curly braces through to a
context object, just add an extra set of curly braces.

Here's an example that demonstrates the complete system in action:

```javascript
const { CanvasBlueprint } = require('canvas-sequencer');
const values = { x: 250, y: 99 };
const bp = new CanvasBlueprint();
const ctx = document.querySelector('#canvas1').getContext('2d');

bp.fillText('y',7,8);
bp.fillText('{{x}}',5,6);
bp.fillRect('{x}','{y}',30,40);

bp.build(values).execute(ctx);

/*
 * The result will be the same as if you had done:
 *
 * ctx.fillText('y',7,8);
 * ctx.fillText('{x}',5,6);
 * ctx.fillRect(250,99,30,40);
 */

// If you later change the x,y values:
values.x = 101;
values.y = 42;

// You can simply rebuild and execute:
bp.build(values).execute(ctx);

/*
 * Now the result will be the same as if you had done:
 *
 * ctx.fillText('y',7,8);
 * ctx.fillText('{x}',5,6);
 * ctx.fillRect(101,42,30,40);
 */
```

### Transmitting and unpacking blueprints

You can transmit and unpack a `CanvasBlueprint` just as you would with the
regular `CanvasSequence` object:

Transmitting:

```javascript
emitter.emit('new-blueprint', bp);
```

Unpacking:

```javascript
const bp = new CanvasBlueprint(data);
```

## Limitations

The canvas sequences will be executed one at a time, in the correct sequence,
but you cannot retrieve values in a useful manner. Therefore any context method
which is intended as a getter has been removed and is currently unavailable. If
you have a good idea for how to make it possible to remotely access these return
values, let me know!

Also be warned that I have not yet fully tested the API with complex arguments,
for example Path objects. I suspect the library will need a bit of fine tuning
to make sure this can happen.

## Changes

- __3.1.0__ Switch from parcel-bunlder to parcel for distribution, add github CI
- __3.0.6__ Fix typo in new instruction support
- __3.0.5__ Slight performance improvement, fixed a buggy test, added support
  for some newer experimental instructions.
- __3.0.4__ Added badges, fixed up the README a bit.
- __3.0.3__ Fixed a minor bug in the CanvasSequence class, improved test
  coverage, update dependencies.
- __3.0.2__ Switched to `parcel-bundler` for the bundle. Simpler to use, more
  efficient.
- __3.0.1__ Added babelify transform for the bundle.
- CanvasSequencer was renamed to CanvasSequence.
- Internal documentation was added.

## Future Work

At some point I will get around to testing the API with complex arguments (e.g.
`Path` objects).

