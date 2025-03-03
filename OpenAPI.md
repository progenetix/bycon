<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" type="text/css" href="/swagger/swagger-ui.css">
<title>OpenAPI Progenetix Beacon Test</title>
<body>
<div id="openapi">
<script src="/swagger/swagger-ui-bundle.js"></script>
<script>
window.onload = function () {
  const ui = SwaggerUIBundle({
    url: "https://progenetix.org/api",
    dom_id: "#openapi"
  })
}
</script>
</body>