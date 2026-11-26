#!/usr/bin/env bash
# sh /c/Development/config/daily-dev-tools/src/sh/update-pom.sh

# Salir si ocurre un error inesperado
set -e

# Módulos a revisar en orden
MODULES=(
  "dependencies"
  "library"
  "parent"
  "model-domain"
  "cross-model-json"
)

# Propiedades a actualizar
PROPERTIES=(
  "backend-dependencies.version"
  "backend-library.version"
  "backend-parent.version"
  "cross.model.json.version"
  "backend-cross-model-json.version"
  "backend-model-domain.version"
  "cross.model.json"
)

NEW_VERSION="workspace"

echo "=========================================================="
echo "🔧 Paso 1: Actualizando versiones (preservando comentarios)"
echo "=========================================================="

for module in "${MODULES[@]}"; do
  target_dir=$(find . -maxdepth 1 -type d -name "*${module}*" ! -name "." | head -n 1)

  if [ -z "$target_dir" ] || [ ! -d "$target_dir" ]; then
    echo "⚠️  No se encontró directorio para: '$module'. Omitiendo..."
    continue
  fi

  pom_file="$target_dir/pom.xml"
  if [ ! -f "$pom_file" ]; then
    echo "⚠️  No se encontró pom.xml en: '$target_dir'. Omitiendo..."
    continue
  fi

  echo "📄 Procesando: $pom_file"

  # Procesamiento de texto puro línea a línea (conserva comentarios y espacios)
  python3 - <<EOF
import re

pom_path = "$pom_file"
new_val = "$NEW_VERSION"
props = set("${PROPERTIES[*]}".split())

with open(pom_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Actualizar las propiedades en <properties>
for prop in props:
    pattern = rf"(<{prop}>)[^<]*(</{prop}>)"
    if re.search(pattern, content):
        content = re.sub(pattern, rf"\g<1>{new_val}\g<2>", content)
        print(f"  ✔ Propiedad <{prop}> actualizada a {new_val}")

# 2. Manejo de bloques <parent> (respetar Spring Boot, actualizar si es interno)
def update_parent(match):
    block = match.group(0)
    # Si el parent es spring-boot, no lo tocamos
    if "spring-boot" in block or "org.springframework" in block:
        print("  ℹ Bloque <parent> de Spring Boot intacto.")
        return block
    # Si es un parent interno, actualizamos su <version>
    print(f"  ✔ <parent> interno actualizado a {new_val}")
    return re.sub(r"(<version>)[^<]*(</version>)", rf"\g<1>{new_val}\g<2>", block, count=1)

content = re.sub(r"<parent>.*?</parent>", update_parent, content, flags=re.DOTALL)

# 3. Actualizar la versión PROPIA del proyecto (fuera de <parent> y antes de <dependencies>)
# Buscamos el tag <version> que está a nivel de proyecto (después de modelVersion/parent/groupId/artifactId)
lines = content.splitlines(keepends=True)
new_lines = []
in_parent = False
in_dependencies = False
project_version_updated = False

for line in lines:
    if "<parent>" in line:
        in_parent = True
    if "</parent>" in line:
        in_parent = False
        new_lines.append(line)
        continue

    if "<dependencies>" in line:
        in_dependencies = True

    # Solo actualizar la primera versión que no esté dentro de <parent> ni de <dependencies>
    if not in_parent and not in_dependencies and not project_version_updated:
        if re.search(r"<version>[^<]*</version>", line):
            old_ver = re.search(r"<version>([^<]*)</version>", line).group(1)
            if old_ver != new_val:
                line = re.sub(r"(<version>)[^<]*(</version>)", rf"\g<1>{new_val}\g<2>", line)
                print(f"  ✔ Versión propia del proyecto: {old_ver} -> {new_val}")
            project_version_updated = True

    new_lines.append(line)

content = "".join(new_lines)

with open(pom_path, 'w', encoding='utf-8') as f:
    f.write(content)
EOF

done

echo ""
echo "=========================================================="
echo "🚀 Paso 2: Compilando e instalando con Maven (clean install)"
echo "=========================================================="

for module in "${MODULES[@]}"; do
  target_dir=$(find . -maxdepth 1 -type d -name "*${module}*" ! -name "." | head -n 1)

  if [ -z "$target_dir" ] || [ ! -f "$target_dir/pom.xml" ]; then
    continue
  fi

  echo "--------------------------------------------------------"
  echo "🔨 Compilando: $target_dir"
  echo "--------------------------------------------------------"

  mvn clean install -f "$target_dir/pom.xml" -DskipTests

  echo "✅ $target_dir instalado correctamente en .m2."
done

echo ""
echo "🎉 ¡Todo listo! Versiones actualizadas, comentarios intactos y módulos instalados."