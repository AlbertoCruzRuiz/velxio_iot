# Velxio IoT — Backlog de mantenimiento y arquitectura

**Fecha de creación:** 26/10/2026  
**Estado:** Abierto. Pendiente de implementación.  
**Repositorios:**
- [velxio-qemu](https://github.com/AlbertoCruzRuiz/velxio-qemu)
- [velxio_iot](https://github.com/AlbertoCruzRuiz/velxio_iot)

## ADR-001 — Estrategia de autonomía frente a Velxio upstream

**Estado:** Decisión arquitectónica adoptada.

El objetivo no es abandonar el proyecto Velxio original ni desarrollar un fork completamente desvinculado.

Se establecen dos principios:

**1. Autonomía operativa**

La aplicación personalizada debe poder compilarse, ejecutarse, mantenerse y desplegarse utilizando repositorios y artefactos propios aunque el proyecto original deje de publicar versiones, retire sus descargas o interrumpa sus servicios.

**2. Autonomía de mantenimiento con integración upstream**

Mientras el proyecto original siga activo, se aprovecharán sus actualizaciones, correcciones y mejoras, así como las de otros proyectos públicos compatibles. Los cambios se integrarán de manera controlada, conservando los parches y funcionalidades propios.

No se pretende reimplementar innecesariamente aquello que el proyecto original mantiene correctamente.

**Distribución de responsabilidades acordada:**

- `velxio-qemu`: fuentes del emulador, parches, ROMs, pruebas y publicación de un artefacto autocontenido.
- `velxio_iot`: frontend, backend, toolchain ESP-IDF/Arduino, integración y distribución de la aplicación completa.
- GHCR propio: distribución de imágenes versionadas sin dependencia de servicios de Velxio durante el despliegue.

---

## TODO-QEMU-001 — Centralizar la gestión de ROMs

**Prioridad:** Alta  
**Estado:** Pendiente  
**Repositorio principal:** `velxio-qemu`

### Problema

La gestión de ROMs está repartida entre ambos repositorios, aunque la imagen publicada por `velxio-qemu` ya incorpora las ROMs necesarias.

Esta duplicidad complica el mantenimiento, la trazabilidad y las actualizaciones independientes.

### Trabajo pendiente

- [ ] Analizar la estructura y la procedencia actual de las ROMs.
- [ ] Trasladar la responsabilidad de sincronización a `velxio-qemu`.
- [ ] Evaluar un directorio propio `rom-assets/` separado de `pc-bios/`, evitando conflictos con el importador upstream.
- [ ] Mantener un manifiesto con chip, revisión, origen, versión y SHA-256.
- [ ] Adaptar las pruebas de integridad.
- [ ] Actualizar `Dockerfile.qemu` para distribuir exclusivamente las ROMs aprobadas.
- [ ] Eliminar la gestión duplicada de ROMs en `velxio_iot`, una vez verificada la migración.

### Archivos relevantes

- [Dockerfile.qemu](https://github.com/AlbertoCruzRuiz/velxio-qemu/blob/main/Dockerfile.qemu)
- [sync_velxio_roms.py](https://github.com/AlbertoCruzRuiz/velxio_iot/blob/main/scripts/sync_velxio_roms.py)
- [sync-qemu-dependencies.yml](https://github.com/AlbertoCruzRuiz/velxio_iot/blob/main/.github/workflows/sync-qemu-dependencies.yml)
- [Dockerfile.standalone](https://github.com/AlbertoCruzRuiz/velxio_iot/blob/main/Dockerfile.standalone)

**Criterio de aceptación:** `velxio_iot` puede construir su imagen final a partir del artefacto QEMU publicado, sin descargar, sincronizar o modificar ROMs.

---

## TODO-QEMU-002 — Detectar actualizaciones independientes de ROMs

**Prioridad:** Alta  
**Estado:** Pendiente  
**Repositorio:** `velxio-qemu`

### Problema

El sincronizador actual está orientado a detectar cambios en las fuentes QEMU mediante sus identificadores de versión.

Es necesario gestionar el caso en que cambie una ROM disponible sin cambiar la revisión del código QEMU.

### Trabajo pendiente

- [ ] Revisar la lógica de detección en `maintenance/sync_velxio_qemu.py`.
- [ ] Separar la detección de actualizaciones de QEMU de las actualizaciones de ROMs.
- [ ] Reutilizar las funciones verificadoras del sincronizador existente, adaptándolas al nuevo repositorio.
- [ ] Comparar versiones, tamaños y hashes de las ROMs sin depender de cambios en QEMU.
- [ ] Evitar sustituir ROMs de revisiones de silicio distintas únicamente porque exista una versión más reciente.
- [ ] Crear o adaptar `check-rom-updates.yml` para proponer cambios mediante PR.
- [ ] Exigir validación y aprobación antes de publicar nuevas ROMs.

### Archivos relevantes

- [maintenance/sync_velxio_qemu.py](https://github.com/AlbertoCruzRuiz/velxio-qemu/blob/main/maintenance/sync_velxio_qemu.py)
- [scripts/sync_velxio_roms.py](https://github.com/AlbertoCruzRuiz/velxio_iot/blob/main/scripts/sync_velxio_roms.py)
- [check-velxio-qemu-updates.yml](https://github.com/AlbertoCruzRuiz/velxio-qemu/blob/main/.github/workflows/check-velxio-qemu-updates.yml)

**Criterio de aceptación:** una actualización verificable de ROMs se detecta y puede distribuirse aunque las fuentes QEMU permanezcan intactas.

---

## TODO-QEMU-003 — Preservar mantenimiento upstream y parches propios

**Prioridad:** Alta  
**Estado:** Pendiente de revisión y refuerzo

### Objetivo

Mantener un proceso reproducible para incorporar mejoras del proyecto original y otros proveedores compatibles, sin depender exclusivamente de ellos.

### Trabajo pendiente

- [ ] Documentar las fuentes upstream utilizadas y sus licencias.
- [ ] Mantener un registro de versiones y hashes de los paquetes importados.
- [ ] Identificar los parches y modificaciones propios.
- [ ] Garantizar que una sincronización upstream no sobrescriba inadvertidamente las modificaciones locales.
- [ ] Validar las nuevas versiones mediante PR y pruebas automáticas.
- [ ] Definir un procedimiento alternativo de actualización desde fuentes públicas compatibles.
- [ ] Comprobar que, si upstream desaparece, se puede seguir compilando desde el último código propio validado.

### Archivos relevantes

- [upstream-version.json](https://github.com/AlbertoCruzRuiz/velxio-qemu/blob/main/upstream-version.json)
- [upstream-hashes.json](https://github.com/AlbertoCruzRuiz/velxio-qemu/blob/main/upstream-hashes.json)
- [maintenance/sync_velxio_qemu.py](https://github.com/AlbertoCruzRuiz/velxio-qemu/blob/main/maintenance/sync_velxio_qemu.py)

**Criterio de aceptación:** se pueden integrar nuevas versiones upstream sin perder parches propios, y se puede reconstruir una versión anterior validada aunque no estén disponibles los servidores originales.

---

## TODO-QEMU-004 — Pruebas funcionales ESP32-S3

**Prioridad:** Alta  
**Estado:** Pendiente

### Problema

Una compilación exitosa y la comprobación de integridad de bibliotecas y ROMs no garantizan el funcionamiento de firmware ESP32-S3 en QEMU.

### Trabajo pendiente

- [ ] Incorporar pruebas automáticas con firmware ESP32-S3 conocido.
- [ ] Comprobar arranque, consola serie y ejecución del firmware.
- [ ] Verificar los periféricos emulados realmente soportados.
- [ ] Probar conectividad WiFi/MQTT simulada, cuando corresponda.
- [ ] Distinguir las pruebas propias de QEMU de las pruebas E2E de la aplicación.
- [ ] Impedir la promoción de una imagen incompatible.
- [ ] Comprobar que el evento `qemu-published` notifica correctamente la imagen y su versión a `velxio_iot`.

### Archivos relevantes

- [build-qemu.yml](https://github.com/AlbertoCruzRuiz/velxio-qemu/blob/main/.github/workflows/build-qemu.yml)
- [Dockerfile.qemu](https://github.com/AlbertoCruzRuiz/velxio-qemu/blob/main/Dockerfile.qemu)
- [Workflows de velxio_iot](https://github.com/AlbertoCruzRuiz/velxio_iot/tree/main/.github/workflows)

**Criterio de aceptación:** una imagen QEMU publicada demuestra que puede ejecutar correctamente firmware de prueba ESP32-S3, no solamente que contiene bibliotecas válidas.

---

## Orden propuesto

1. **TODO-QEMU-001:** consolidar la propiedad de las ROMs.
2. **TODO-QEMU-002:** implementar actualizaciones independientes.
3. **TODO-QEMU-004:** reforzar la validación funcional.
4. **TODO-QEMU-003:** completar la política de mantenimiento upstream y recuperación.

Los cuatro trabajos pueden desarrollarse en etapas y mediante PR independientes.

**Precaución:** no eliminar los scripts ni los mecanismos existentes hasta que sus sustitutos hayan sido probados. Las referencias son rutas a consultar; la estructura del repositorio puede evolucionar.

**Estado global:** planificación registrada; ningún cambio aplicado a los repositorios.
