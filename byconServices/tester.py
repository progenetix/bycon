from bycon import print_html_response

################################################################################

def tester():
    """
    """

    test = """<head>
  <style> body { margin: 0; } </style>

  <script src="//cdn.jsdelivr.net/npm/globe.gl"></script>
<!--    <script src="../../dist/globe.gl.js"></script>-->
</head>

<body>
<div id="globeViz"></div>

<script type="module">
  const world = new Globe(document.getElementById('globeViz'))
    .globeTileEngineUrl((x, y, l) => `https://tile.openstreetmap.org/${l}/${x}/${y}.png`)
    .pointsData([{ lat: 0, lng: 0, pop: 20000 }])

    // Add auto-rotation
    world.controls().autoRotate = true;
    world.controls().autoRotateSpeed = 0.6;
</script>
</body>
"""
    print_html_response(test)
