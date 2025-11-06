from bycon import print_html_response

################################################################################

def tester():
    """
    """

    test = """<head>
  <style> body { margin: 0; } </style>

  <script src="https://cdn.jsdelivr.net/npm/globe.gl"></script>
<!--    <script src="../../dist/globe.gl.js"></script>-->
</head>

<body>
<div id="globeViz"></div>

<script type="module">
    import { MeshLambertMaterial, DoubleSide } from 'https://esm.sh/three';
    import * as topojson from 'https://esm.sh/topojson-client';

    const world = new Globe(document.getElementById('globeViz'))
      .backgroundColor('rgba(0,0,0,0)')
      .showGlobe(false)
      .showAtmosphere(false)
      .pointsData([{ lat: 0, lng: 0, pop: 200000 }]);

    fetch('https://cdn.jsdelivr.net/npm/world-atlas/land-110m.json').then(res => res.json())
      .then(landTopo => {
        world
          .polygonsData(topojson.feature(landTopo, landTopo.objects.land).features)
          .polygonCapMaterial(new MeshLambertMaterial({ color: 'darkslategrey', side: DoubleSide }))
          .polygonSideColor(() => 'rgba(0,0,0,0)')
          .pointsData([{ lat: 0, lng: 0, pop: 200000 }, { lat: 48, lng: 8, pop: 500000 }]);
      });

    // Add auto-rotation
    world.controls().autoRotate = true;
    world.controls().autoRotateSpeed = 0.6;
</script>
</body>
"""
    print_html_response(test)
    
