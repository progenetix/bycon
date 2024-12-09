var raf = require('rafl')

var Animate = function(frame, fps) {
  if (!(this instanceof Animate)) {
    return new Animate(frame, fps)
  }

  this.id = null
  this.now = null
  this.then = +new Date
  this.delta = null
  this.frame = frame
  this.interval = 1000 / fps
  this.start = this.start.bind(this)

  this.start()
}

Animate.prototype.pause = function() {
  raf.cancel(this.id)
  this.id = null  
  return this
}

Animate.prototype.resume = function() {
  if (this.id == null) {
    this.start()
  }

  return this
}

Animate.prototype.start = function() {
  this.id = raf(this.start)

  this.now = +new Date
  this.delta = this.now - this.then

  if (this.delta < this.interval) {
    return
  }

  this.frame()
  this.then = this.now - (this.delta % this.interval)
}

module.exports = Animate
