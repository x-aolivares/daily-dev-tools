#!/usr/bin/env bash

# Salir inmediatamente si algún comando falla
set -e

# Orden estricto de compilación
MODULES=(
  "dependencies"
  "library"
  "parent"
  "model-domain"
  "cross-model-json"
)

echo "Iniciando compilación de módulos en orden..."

for module in "${MODULES[@]}"; do
  # Buscar el directorio en la ruta actual que coincida con el nombre/patrón
  target_dir=$(find . -maxdepth 1 -type d -name "*${module}*" ! -name "." | head -n 1)

  if [ -z "$target_dir" ] || [ ! -d "$target_dir" ]; then
    echo "⚠️  No se encontró directorio para: '$module'. Omitiendo..."
    continue
  fi

  if [ ! -f "$target_dir/pom.xml" ]; then
    echo "⚠️  '$target_dir' no contiene pom.xml. Omitiendo..."
    continue
  fi

  echo "--------------------------------------------------------"
  echo "🚀 Construyendo: $target_dir"
  echo "--------------------------------------------------------"

  # Ejecutar maven clean install sin pruebas
  mvn clean install -f "$target_dir/pom.xml" -DskipTests

  echo "✅ $target_dir instalado correctamente."
done

echo "🎉 Todos los módulos se compilaron e instalaron con éxito."