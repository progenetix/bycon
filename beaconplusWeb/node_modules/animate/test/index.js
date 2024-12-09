var tape = require('tape')
var animate = require('../')

var nextTick = function(fn) {
  setTimeout(fn, 0)
}

// Allow two frames difference
var correctish = function(a, b) {
  return Math.abs(a - b) <= 1
}

tape('it runs at the given frame rate', function(test) {
  test.plan(1)

  var count = 0
  var fps = 3
  var counter = animate(function() {
    count++
  }, fps)

  nextTick(function() {
    // Wait a second
    setTimeout(function() {
      test.ok(correctish(count, fps), 'it does')
    }, 1000)
  })
})

tape('it pauses', function(test) {
  test.plan(1)

  var count = 0
  var fps = 3
  var counter = animate(function() {
    count++
  }, fps)

  nextTick(function() {
    // Wait half a second
    setTimeout(function() {
      test.ok(correctish(count, Math.floor(fps / 2)), 'it does')
      counter.pause()
    }, 500) 
  })
})

tape('it resumes', function(test) {
  test.plan(1)

  var count = 0
  var fps = 3
  var counter = animate(function() {
    count++
  }, fps)

  nextTick(function() {
    // Wait half a second
    setTimeout(function() {
      counter.pause()

      // Wait half a second
      setTimeout(function() {
        counter.resume()

        // Wait half a second
        setTimeout(function() {
          test.ok(correctish(count, fps), 'it does')
          counter.pause()
        }, 500)
      }, 500)
    }, 500) 
  })
})
