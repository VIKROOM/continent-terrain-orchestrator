# Continent Terrain Orchestrator (Unity + Python)

¡Hola! Soy estudiante de programación de la **Universidad Tecnológica Nacional (UTN)** y me apasiona el **desarrollo de videojuegos**. Este proyecto nació con esa mezcla de curiosidad técnica y ganas de construir herramientas prácticas para mundos interactivos.

---

## ¿De qué va este proyecto?

**Continent Terrain Orchestrator** es un orquestador por etapas (en Python) pensado para trabajar junto a **Unity** (enfoque Unity 6 LTS / URP) en la generación de **continentes base fijos por semilla**.

En lugar de armar mapas al azar sin control o acoplar el generador directamente al ciclo en vivo del editor, el sistema:
- Toma una idea o referencia de inspiración y propone variantes **sin copiar literalmente** la referencia.
- Mantiene el foco en el **continente base**: dimensiones, semilla fija, capas de ruido multi-octava, borde oceánico y **zonas planas para futuras ciudades/asentamientos** (sin colocar vegetación, rocas, props ni edificios).
- Te deja elegir qué **skills** y **MCP** activar, qué opción usar y **qué cambios (`changes`) puntuales aprobar o rechazar** antes de escribir en el archivo destino de Unity.
- Guarda **checkpoints** e historial por sesión para hacer **recovery** si quieres retomar desde una etapa anterior.
- Permite elegir idioma en consola (**Español** o **Inglés**) y soporta **presets opcionales exportados desde Unity** (con *fallback* automático si aún no existen).

---

## Cómo fundarlo y hacerlo funcionar (paso a paso)

### 1. Estructura base del proyecto
Mantén el orquestador en su propia carpeta, separada de tu proyecto de Unity, para trabajar con orden y buen control de versiones:

```text
continent-terrain-orchestrator/
├── README.md
├── .gitignore
├── requirements.txt
├── config/
│   ├── settings.example.json
│   └── settings.json          # Local (no se sube a Git)
├── skills/
│   └── catalog.json
├── mcp/
│   └── catalog.json
├── src/
│   ├── cli.py
│   ├── orchestrator.py
│   ├── planner_and_selection.py
│   ├── state_manager.py
│   ├── recovery.py
│   └── i18n.py
├── state/                     # Checkpoints e historial local (ignorado en Git)
└── unity_addon/
    └── ContinentHeightmapBuilder.cs
```

### 2. Clonar y preparar el entorno
1. Clona el repositorio y entra a la carpeta del proyecto:
   ```powershell
   git clone <URL_DE_TU_REPO>
   cd <CARPETA_DEL_REPO>
   ```
2. Crea y activa un entorno virtual en Python:
   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```
3. Instala las dependencias:
   ```powershell
   python -m pip install --upgrade pip
   python -m pip install -r requirements.txt
   ```
4. Verifica que las librerías base estén listas:
   ```powershell
   python -c "import langgraph, pydantic, dotenv; print('OK - Dependencies ready')"
   ```

### 3. Configurar rutas y catálogos
1. Copia `config/settings.example.json` a `config/settings.json`.
2. Edita `unity_project_root` en `config/settings.json` con la ruta real a tu proyecto de Unity.
3. Revisa `skills/catalog.json` y `mcp/catalog.json` para ver o ampliar las opciones disponibles.

### 4. Ejecutar el orquestador
Desde la raíz del proyecto (con `.venv` activo):

```powershell
$env:PYTHONPATH="src"
python src\cli.py
```

- **Idioma:** elige `[1] Español` o `[2] English`.
- **Nueva ejecución (`[1]`):** recorre las 6 etapas (`foundation_check` → `reference_and_options` → `selection_gate` → `diff_and_approval` → `apply_changes` → `unity_handoff`), te muestra las opciones y te deja aprobar cambios por número (`1,2,5`), `all` o `none`.
- **Recovery (`[2]`):** selecciona una sesión previa y un checkpoint (o presiona `Enter` para el último) para continuar desde la etapa correspondiente.

### 5. Generar el terreno en Unity
1. Copia `unity_addon/ContinentHeightmapBuilder.cs` dentro de tu proyecto de Unity (por ejemplo en `Assets/_Project/Scripts/Terrain/`).
2. En tu escena, crea un objeto con el componente `ContinentHeightmapBuilder` y verifica que `configRelativePath` apunte a tu JSON generado (por ejemplo `Assets/_Project/TerrainData/Configs/continent_master.json`).
3. Haz clic en **Generate Fixed Continent From JSON** desde el Inspector para construir el terreno base fijo por semilla.

---

## Explicación del código (para modificarlo a gusto)

Cada módulo tiene una responsabilidad clara para que puedas tocar una parte sin romper el resto:

- **`src/cli.py`**: es la interfaz por terminal. Maneja la interacción con el usuario, menús, selección múltiple (`all`, `none`, listas de números), disparo de nuevas ejecuciones y modo *recovery*. Si quieres cambiar cómo se pide un dato o agregar un atajo de consola, este es el lugar.
- **`src/orchestrator.py`**: coordina el flujo de las 6 etapas, guarda el estado tras cada paso, compara lo existente contra lo propuesto, aplica solo los `changes` aprobados sobre el archivo destino en Unity y arma la información de *handoff*. Ideal si quieres sumar etapas, validaciones extra o cambiar cómo se fusionan los campos.
- **`src/planner_and_selection.py`**: contiene el `SYSTEM_PROMPT_EN`, genera las opciones de continente a partir de la referencia (variando semillas, coordenadas y proporciones, y leyendo *presets* de Unity si existen) y arma la lista granular de `change_items`. Aquí es donde conviene ajustar tamaños de mapa, cantidad de zonas planas para ciudades o reglas de generación.
- **`src/state_manager.py`**: administra los identificadores de sesión, lectura de `config/settings.json` y catálogos, guardado/carga de checkpoints en `state/checkpoints/` y registro de eventos en `state/history/`.
- **`src/recovery.py`**: busca checkpoints guardados (específicos o el último `latest.json`), valida su existencia y registra en el historial cuándo y desde qué etapa se recuperó una sesión.
- **`src/i18n.py`**: centraliza los textos en español (`es`) e inglés (`en`). Si agregas nuevos mensajes en la CLI, súmalos aquí en ambos idiomas para mantener la paridad.
- **`skills/catalog.json` y `mcp/catalog.json`**: definen los catálogos seleccionables desde la CLI. Puedes agregar nuevas *skills* o servidores/conectores *MCP* editando estos JSON y conectando su lógica en `planner_and_selection.py` u `orchestrator.py`.
- **`unity_addon/ContinentHeightmapBuilder.cs`**: lee el JSON configurado, evalúa el ruido por capas y semilla fija, aplica la máscara oceánica y aplana/suaviza las zonas de ciudades sobre un `TerrainData` de Unity. Puedes modificarlo para ajustar resolución de *heightmap*, curvas de suavizado o exportación de *presets*.
