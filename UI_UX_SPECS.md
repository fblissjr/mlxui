# UI/UX Component Specification for MLXUI

## 1. Introduction

This document provides a detailed, framework-agnostic specification for the user interface and user experience components of the MLXUI application. The goal is to create a blueprint that can be used to rebuild the frontend with a different technology stack while preserving the original design, behavior, and nuances.

---

## 2. Main Application Layout

**Objective:** To provide the main structure for the application, including a header, a content area that adapts to the current mode, a footer, and side panels for settings and performance monitoring.

**Components:**

*   **Header:** A persistent header at the top of the page.
*   **Main Content:** A flexible content area that displays the primary user interface based on the application's current mode (`chat` or `notebook`).
*   **Footer:** A persistent footer at the bottom of the page.
*   **Settings Panel:** A sliding panel that appears from the right side of the screen when activated.
*   **Performance Dashboard:** A sliding panel that also appears from the right side of the screen when activated.
*   **Error Display:** A notification that appears at the top of the main content area when an error occurs.
*   **Backend Status Display:** The main content area also reflects the status of the backend server (e.g., "online," "offline," "connecting").

**Layout:**

*   The layout is a full-screen, flexbox-based column.
*   The `Header` is fixed at the top.
*   The `Main Content` area takes up the remaining vertical space.
*   The `Footer` is fixed at the bottom.
*   The `Settings Panel` and `Performance Dashboard` are positioned absolutely, and their visibility is controlled by the application state. They slide in from the right, overlaying the main content.
*   The `Error Display` is a fixed-position element that appears at the top of the screen when an error is present.

**Behavior:**

*   The application initializes by checking the backend health, fetching the current model status, and loading the list of available models.
*   The theme (light/dark) is initialized and applied to the root HTML element.
*   The main content area dynamically renders either the `ChatMode` or `NotebookMode` component based on the `currentMode` state variable.
*   If the backend is offline, a message is displayed with a "Retry Connection" button.
*   If the application is connecting to the backend, a loading indicator is shown.
*   The `Settings Panel` and `Performance Dashboard` can be opened and closed, and their state is managed by the `appStore`.
*   When the `Performance Dashboard` is opened, it starts streaming performance metrics from the backend. When closed, it stops streaming.
*   Errors from the backend are displayed in the `Error Display` component, and can be dismissed by the user.

---

## 3. Core UI Components

### 3.1. Header Component

**Objective:** To provide consistent branding, navigation, and access to key application-level controls at the top of the application.

**Location:** A sticky header that remains fixed at the top of the viewport during scrolling.

**Elements & Behavior:**

1.  **Branding:**
    *   **Visual:** Displays "mlxui". The "mlx" part is bold, while "ui" is a lighter weight.
    *   **Functionality:** Acts as a static brand identifier.

2.  **Mode Switcher (Primary Navigation):**
    *   **Visual:** A set of two buttons, "Chat" and "Notebook", each with a corresponding icon.
    *   **Functionality:**
        *   Allows the user to toggle between the two main application modes.
        *   The button for the currently active mode has a distinct visual state (e.g., highlighted background) to indicate it is selected.
        *   This component is hidden on smaller screen sizes (e.g., mobile) to save space.

3.  **Status Indicators:**
    *   **Backend Status:**
        *   **Visual:** A small, colored circular indicator next to the word "Backend".
        *   **Functionality:** Green for online, Red for offline, Yellow (pulsing) for connecting. A tooltip on hover provides a text description.
    *   **Model Status:**
        *   **Visual:** A circular indicator, the truncated name of the loaded AI model, and a potential loading icon.
        *   **Functionality:** Indicator is green if a model is loaded, gray otherwise. It pulses while loading. Displays the model's name (truncated) or "None Loaded". A spinning loader icon appears during loading.

4.  **Action Buttons (Toolbar):**
    *   A set of icon-only buttons for global controls.
    *   **Theme Toggle:** Cycles through "dark", "light", and "system" UI themes.
    *   **Performance Dashboard Toggle:** Toggles the visibility of the Performance Dashboard side panel.
    *   **Settings Toggle:** Toggles the visibility of the Settings side panel.

### 3.2. Common Components & Styling Conventions

**Objective:** To define a set of reusable components and styling patterns that ensure a consistent look and feel across the entire application.

#### Spinner Component

**Objective:** To provide a consistent, animated loading indicator.

**Visual:** A circular, spinning SVG graphic.

**Configuration (Props):**
*   **`size`:** `xs`, `sm`, `md` (default), `lg`, `xl`.
*   **`color`:** Any Tailwind CSS text color utility class. Defaults to the primary brand color.
*   **`stroke`:** The thickness of the SVG lines.

#### Iconography

**Objective:** To use a consistent set of icons.

**Implementation:** The application uses the **Lucide** icon set for a unified, modern, line-art style.

#### Styling Conventions

*   **Buttons (`.btn`)**
    *   **Base Style:** Shared padding, font size, rounded corners, focus ring.
    *   **Variants:** `.btn-primary` (brand color), `.btn-secondary` (gray), `.btn-danger` (red).
    *   **States:** Hover and disabled states with distinct visual feedback.

*   **Form Inputs**
    *   **Style:** Consistent full-width design, padding, borders, and colors for light/dark modes.
    *   **States:** A colored focus ring appears when a field is active.

*   **Scrollbars**
    *   Custom-styled to be subtle and themed for light/dark modes.

---

## 4. Application Features

### 4.1. Chat Mode

**Objective:** To provide a real-time, streaming, conversational interface for a user to interact with a backend AI model.

#### Main Chat View

**Objective:** Orchestrates the entire chat experience.

**Layout & Elements:**
*   **New Chat Button:** Clears the current conversation history.
*   **Message Display Area:** A scrollable container for `ChatMessage` components. Automatically scrolls to the bottom on new messages. Shows a placeholder when empty.
*   **Generation Status Indicator:** A "Generating..." message with a spinner, visible only during AI response generation.
*   **Stop Generation Button:** A button to interrupt the AI's response stream.
*   **Input Area & Status Messages:** Contains the `ChatInput` component and displays contextual warnings (e.g., "No model loaded").

#### Chat Input Component

**Objective:** A dedicated component for message composition and submission.

**Layout & Elements:**
*   **Text Area:** Auto-resizing multi-line text input. `Enter` submits, `Shift+Enter` creates a newline. Disabled during generation.
*   **Send Button:** Icon-only button to submit the message. Disabled when input is empty or during generation.

#### Chat Message Component

**Objective:** To render a single message in the conversation with styling that reflects its author.

**Layout & Elements:**
*   **Message Container:** Aligns the message bubble to the right for the 'user' and to the left for the 'assistant'.
*   **Message Bubble:** Colored block containing the message. Style is role-dependent: primary brand color for user, neutral gray for assistant, warning yellow for errors.
*   **Role Label:** For non-user messages, a small text label ("ASSISTANT", "ERROR") is displayed.
*   **Content:** Displays the message text, preserving whitespace and line breaks.

### 4.2. Notebook Mode

**Status:** Under Development (Currently a placeholder in the codebase).

**Stated Objective (from code):** To provide a multi-purpose, document-like interface where users can combine text (Markdown) and interactive AI generation blocks, creating a workflow similar to Jupyter Notebooks.

#### Main Notebook View

**Objective:** To manage and display an ordered list of "blocks" that constitute the notebook.

**Layout & Elements:**
*   **Block Container:** Renders a vertical sequence of `NotebookBlock` components.
*   **"Add Block" Button:** Inserts a new block into the list.

#### Notebook Block Component

**Objective:** A self-contained, modular unit within the notebook.

**Anticipated Functionality:**
*   **Block Toolbar:** Controls to switch block type (Markdown/Generation), run, delete, or move the block.
*   **Type: Markdown:** Has a "View State" (renders formatted HTML) and an "Edit State" (raw text editor).
*   **Type: Generation:** Has an "Input State" (prompt editor), "Executing State" (shows a loader), and "Output State" (shows the AI's response).

---

## 5. Side Panels

### 5.1. Settings Panel

**Objective:** To provide a centralized interface for all user-configurable options.

**Layout & Behavior:**
*   A side panel that slides in from the right.
*   Contains a header with a title and close button.
*   Features a tabbed navigation bar to switch between different settings categories.

#### "Model" Tab

**Objective:** To manage the AI models used by the application.

*   **Currently Loaded Model:** Displays details of the active model and an "Unload Model" button.
*   **Load by Identifier:** Input fields to load a model from a local path or Hugging Face Hub ID, with an optional field for an adapter.
*   **Locally Discovered Models:** A list of auto-detected local models, each with a "Load" button.

#### "Parameters" Tab

**Objective:** To adjust the primary parameters for text generation.

*   Provides sliders and inputs for: Temperature, Max New Tokens, Top-P, Top-K, Repetition Penalty, and Seed.
*   Includes a checkbox to "Ignore Chat Template".
*   A "Reset" button restores default values.

#### "Advanced" Tab

**Objective:** To provide fine-grained control over complex generation features.

*   **Advanced Sampling:** Controls for Min-P sampling.
*   **Speculative Decoding:** An "Enable" checkbox which reveals fields for a "Draft Model Identifier" and "Draft Tokens".
*   **KV Cache Options:** Inputs for configuring KV cache quantization (bits, group size, etc.).
*   **Stopping Criteria:** UI to add/remove extra End-of-Sequence (EOS) tokens and literal stopping strings.
*   **Logit Bias:** UI to specify a bias for or against generating specific token IDs.

#### "KV Cache" Tab

**Objective:** To save, load, and manipulate the model's KV cache.

*   **Filename Input:** To specify the name of the cache file.
*   **Save/Load Buttons:** To save the current in-memory cache to a file or load one from a file.
*   **Trim Controls:** An input and button to remove a specified number of tokens from the beginning of the cache.

### 5.2. Performance Dashboard

**Objective:** To provide a real-time view of the backend's performance metrics.

**Layout & Behavior:**
*   A side panel that slides in from the right, similar to the Settings Panel.
*   When opened, it starts streaming performance data from the backend.

**Sections:**
*   **Performance Cards:** A grid of cards for at-a-glance metrics: Generation Speed (tok/s), Memory Usage (RSS), and CPU Usage (%).
*   **Performance Charts:** Time-series line charts showing the history of Generation Speed and Memory Usage.
*   **Current Setup Summary:** A snapshot of the model and key parameters that are currently active, providing context for the metrics.

---

## 6. State Management (Data Stores)

**Objective:** To manage the application's state in a structured way using dedicated stores.

#### App Store

**Purpose:** Manages global UI state.
*   **State:** `currentMode`, `isSettingsPanelOpen`, `isDashboardOpen`, `backendStatus`, `lastError`, `theme`.

#### Model Store

**Purpose:** Manages all state related to AI models.
*   **State:** `currentModel`, `availableModels`, `isModelLoading`.

#### Generation Store

**Purpose:** Manages state and parameters for the text generation process.
*   **State:** `generationParams`, `isGenerating`, `currentOutputStream`, `cacheOperationStatus`.

#### Performance Store

**Purpose:** Manages state for the Performance Dashboard.
*   **State:** `currentMetrics`, `historicalMetrics`, `isStreaming`.
