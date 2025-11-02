# 💻 GPT Specification for Braid 3D Simulation

This specification outlines the requirements for a JavaScript application that simulates and utilizes a 3D Kumihimo (braid) using **THREE.js** for rendering and a **Mass-Spring System** for physics.

## I. Core Dependencies

The application must assume the availability of the **THREE.js** library for 3D visualization and **jQuery ($)** for DOM manipulation (as suggested by the minified code snippets).

## II. Mathematical and Utility Constants

| Constant | Value | Purpose |
| :--- | :--- | :--- |
| `maxRange` | `20` | Radius of the virtual marudai (braiding stand). |
| `forceMultiplier` | `0.1` | Initial force damping/scaling factor for physics updates. |
| `tamaWeightRatio` | `2` | Ratio used to calculate the approximate vertical tension angle. |
| `braidTipHeight` | (Dynamic) | Average Y-coordinate of the deepest movable points in the braid. |

## III. Data Structures

### 1. BraidBlob (The Mass/Point)

* **Properties:**
    * `pos` (`THREE.Vector3`): Current position.
    * `prev`, `next` (`BraidBlob | null`): Pointers to adjacent blobs in the thread.
    * `fixed` (`boolean`): If true, this blob does not move during physics updates (used for the start of the braid).
    * `queued` (`boolean`): Used by the physics solver to track if the blob is in the `blobUpdateQueue`.
    * `near` (`Object`): A reference to the local cell in the `BlobMap` for collision checks.
* **Methods: Physics**
    * `tension(targetBlob)`: Calculates the spring force between this blob and a `targetBlob` (either `prev` or `next`). Force should be proportional to `(distance - 1)` scaled by `10` if `distance > 1`. If `targetBlob` is null (the thread end), it uses `BraidThread.tension()` to simulate tama weight/tension.
    * `repulsion(otherBlob)`: Calculates a repulsion force from `otherBlob`. Force should be proportional to `(2 - distance)` scaled by `10` if `distance < 2`.
    * `update()`: The core physics step. Calculates total force (tension + repulsion), applies dampening (`forceMultiplier`), clamps the max force (`0.3`), updates `pos`, and queues neighboring blobs if movement occurred.
    * `queueUpdate()`: Adds the blob to the global `blobUpdateQueue` if not fixed or already queued.
    * `setPos(newPos)`: Updates the position and uses `BlobMap.update` to refresh spatial hash data.

### 2. BraidThread (The Spring/Rope)

* **Properties:**
    * `dir` (`number`): Current angle (in radians) of the thread on the marudai.
    * `blobs` (`BraidBlob[]`): Array of physical points, starting from the fixed end.
    * `mesh`, `tube`, `end` (`THREE.Object3D`): THREE.js elements for visualization.
    * `target` (`THREE.Vector3`): The gravitational target for the free end, calculated based on `braidTipHeight` and `dir`.
* **Methods: Braiding & Geometry**
    * `nextDir(newDir, isUndo)`: The core braiding move.
        1.  Sets `this.dir = newDir`.
        2.  **Extrusion**: Adds new placeholder blobs from the current end point towards the new position (calculated using `circPos` at `braidTipHeight`). The length of the extrusion is determined by the required path and the `ThreadHeightMap.highest` Y value.
        3.  `tightenEnd(isUndo)`: An iterative relaxation loop (multiple passes) to locally tighten the new segment and prevent initial interpenetration by nudging blobs sideways if they are too close to other threads (checked via `nearOthers`).
        4.  `remapEnd()`: Respaces the blobs (ensuring roughly unit distance) along the new path to smooth out the initial movement artifact.
        5.  Queues the last blob for the global physics solver.
    * `updateScene()`: Recreates or updates the `THREE.SplineCurve3` and `THREE.TubeGeometry` based on the current blob positions and applies the thread's color.

### 3. ThreadHeightMap (2D Spatial Hash for Y-Coord)

* **Functionality**: A 2D grid storing the highest Y-coordinate (`h`) and the `threadId` (`t`) that created it for any given `(x, z)` grid cell (scaled by `2`).
* **Purpose**: Used to determine the minimum safe height for a new thread path during `BraidThread.nextDir` extrusion, ensuring the thread starts above the existing braid structure.

### 4. BlobMap (3D Spatial Hash for Collision)

* **Functionality**: A 3D hash map (`map[x][z][y]`) where each cell stores a list of nearby `BraidBlob` references. It is a sparse map and only manages the movable parts of the braid.
* **Method: `update(blob, oldPos)`**: The key method. It intelligently removes the blob reference from the cells associated with `oldPos` and adds it to the cells associated with `blob.pos` (covering a 5x5x5 cube around the center position) to minimize updates when a blob moves slightly.

## IV. Global Simulation Functions

* **`updateThreads()`**: The main asynchronous physics driver.
    1.  `updateThreadsStart()`: Initializes the `blobUpdateQueue` (queuing tips of threads that moved).
    2.  `updateThreadsChunk()`: Executes a maximum number of physics updates (e.g., 20,000) from the queue. Damps `forceMultiplier` with each chunk.
    3.  `updateThreadsDone()`: Finalizes the step by:
        * Calling `recalcHeightMap()`.
        * Calling `calcBraidTipHeight()`.
        * Calling `balanceRotation()`.
        * Calling `cutBlobMap()` (optimization to delete old/deep layers of the `BlobMap`).
* **`balanceRotation()`**:
    1.  Calculates the center point of the tamas (`center.y=0`).
    2.  Calculates the rotational torque required by all tamas relative to this center.
    3.  Uses a **Ternary Search** (minimization algorithm) to find the rotation angle that minimizes the total torque (the most balanced position).
    4.  Calls `rotateBraid(center, optimalAngle)` to apply the rotation to all blobs in all threads.

## V. State Management and Execution

* **`StepDesc`**: Represents a recordable step in the pattern (e.g., "Thread 1 moves to Thread 5's position"). Stores the type, thread indices, and the pre-step state.
* **`ExecMove`, `ExecTighten*`, `ExecUpdateScene`**: Classes that represent individual, atomic tasks in the overall simulation flow.
* **`executeStep()`**: The main game loop function. It is called using `requestAnimationFrame`. It executes the first step in the `execSteps` queue until it completes (returns `true`), then shifts the array.
* **`BraidState`**: A class responsible for capturing the full global state (thread positions, colors, and all steps executed) for saving, loading, and **Undo/Redo** functionality (`braidStates` global object).

## VI. Visualization and Interaction

* **`init3D()`**: Standard THREE.js setup (Scene, Camera, Renderer, Lights).
* **`updateScene()`**: Iterates through all `BraidThread`s and calls `thread.updateScene()` to refresh the geometry.
* **`MarudaiView`**: Handles the 2D canvas visualization of the marudai table. It must implement the **Drag-and-Drop** logic that allows a user to select a thread end and visually define a `threadMove` step, which then queues the `nextDir` call.

The recreated code should maintain the original logic flow: **User Action (Drag-and-Drop) $\rightarrow$ `StepDesc` Created $\rightarrow$ `Exec*` Commands Queued $\rightarrow$ `executeStep()` Loop $\rightarrow$ `BraidThread.nextDir` $\rightarrow$ `updateThreads()` Physics Solve $\rightarrow$ UI Update.**