const editor = document.getElementById('editor');
const indicator = document.getElementById('line-type-indicator');
const syncDot = document.getElementById('syncDot');
const syncText = document.getElementById('syncText');

// State Machine Rules for Tab and Enter behavior
const workflowRules = {
    'scene-heading': { enter: 'action', tab: 'action' },
    'action':        { enter: 'action', tab: 'character' },
    'character':     { enter: 'dialogue', tab: 'transition' },
    'parenthetical': { enter: 'dialogue', tab: 'dialogue' },
    'dialogue':      { enter: 'character', tab: 'action' },
    'transition':    { enter: 'scene-heading', tab: 'scene-heading' },
    'shot':          { enter: 'action', tab: 'action' },
    'dual':          { enter: 'character', tab: 'character' },
    'page-break':    { enter: 'scene-heading', tab: 'scene-heading' }
};

function insertPageBreak() {
    const p = getCurrentParagraph();
    if (!p) return;
    
    let pageBreakNode;
    if (p.textContent.replace(/\u200B/g, '').trim() === '') {
        setLineType('page-break', p);
        pageBreakNode = p;
    } else {
        pageBreakNode = document.createElement('p');
        pageBreakNode.className = 'page-break';
        pageBreakNode.innerHTML = '&#8203;';
        p.parentNode.insertBefore(pageBreakNode, p.nextSibling);
    }

    const actionP = document.createElement('p');
    actionP.className = 'action';
    actionP.innerHTML = '&#8203;';
    pageBreakNode.parentNode.insertBefore(actionP, pageBreakNode.nextSibling);

    const range = document.createRange();
    const sel = window.getSelection();
    range.setStart(actionP, 0);
    range.collapse(true);
    sel.removeAllRanges();
    sel.addRange(range);
    
    actionP.focus();
    triggerBackup();
    updateStats();
}

// Helper tracking currently selected element
function getCurrentParagraph() {
    const selection = window.getSelection();
    if (!selection.rangeCount) return null;
    let node = selection.getRangeAt(0).startContainer;
    if (node.nodeType === Node.TEXT_NODE) node = node.parentNode;
    while (node && node.parentNode !== editor) {
        node = node.parentNode;
    }
    return node && node.tagName === 'P' ? node : null;
}

function getLineType(p) {
    if (!p) return 'action';
    const types = ['scene-heading', 'action', 'character', 'parenthetical', 'dialogue', 'transition', 'shot', 'dual', 'page-break'];
    for (let type of types) {
        if (p.classList.contains(type)) return type;
    }
    return 'action';
}

function setLineType(type, element = getCurrentParagraph()) {
    if (!element) return;
    element.className = ''; 
    element.classList.add(type);
    updateToolbarUI(type);
}

function updateToolbarUI(activeType) {
    indicator.textContent = `Current Element: ${activeType.replace('-', ' ').toUpperCase()}`;
    document.querySelectorAll('.tool-btn').forEach(btn => {
        if (btn.getAttribute('data-type') === activeType) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
}

// Monitors context changes to match active styling buttons
document.addEventListener('selectionchange', () => {
    const p = getCurrentParagraph();
    if (p) {
        updateToolbarUI(getLineType(p));
        updateMiniToolbarState();
    }
});

// Translates keystrokes into saveable string formats (e.g., 'ctrl+shift+p')
function getHotkeyString(e) {
    let keys = [];
    if (e.ctrlKey) keys.push('ctrl');
    if (e.altKey) keys.push('alt');
    if (e.shiftKey) keys.push('shift');
    if (e.key !== 'Control' && e.key !== 'Alt' && e.key !== 'Shift') {
        keys.push(e.key.toLowerCase());
    }
    return keys.join('+');
}

// Intercepting and mapping keystrokes explicitly
editor.addEventListener('keydown', (e) => {
    const p = getCurrentParagraph();
    if (!p) return;

    // Handle F11 for Focus Mode
    if (e.key === 'F11') {
        e.preventDefault();
        toggleFocusMode();
        return;
    }

    const currentType = getLineType(p);
    const textContent = p.textContent.trim();

    // Handle Ctrl+Enter for Page Breaks
    if (e.key === 'Enter' && e.ctrlKey) {
        e.preventDefault();
        insertPageBreak();
        return;
    }

    // Handle Enter Key Behavior
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        
        let nextType = workflowRules[currentType].enter;

        // Traditional Option Context Overrides
        if (currentType === 'action' && textContent === '') {
            nextType = 'character';
        }

        const newP = document.createElement('p');
        newP.className = nextType;
        newP.innerHTML = '&#8203;'; // Set zero-width space to hold layout cursor open safely
        p.parentNode.insertBefore(newP, p.nextSibling);

        // Re-focus cursor down to new line
        const range = document.createRange();
        const sel = window.getSelection();
        range.setStart(newP, 0);
        range.collapse(true);
        sel.removeAllRanges();
        sel.addRange(range);
        
        newP.focus();
        triggerBackup();
        updateStats();
        return;
    }

    // Handle Tab Key Cycling Mechanics
    if (e.key === 'Tab') {
        e.preventDefault();
        const nextType = workflowRules[currentType].tab;
        setLineType(nextType, p);
        return;
    }

    // Dynamic Hotkeys Engine 
    const hotkeyStr = getHotkeyString(e);
    for (const [action, keyCombo] of Object.entries(appSettings.hotkeys || {})) {
        if (hotkeyStr === keyCombo && hotkeyStr !== '') {
            e.preventDefault();
            setLineType(action, p);
            return;
        }
    }

    // Bindings for Explicit Line Conversions (Ctrl + Number combinations)
    if (e.ctrlKey && !e.altKey && !e.shiftKey) {
        const numMap = { '1': 'scene-heading', '2': 'action', '3': 'character', '4': 'parenthetical', '5': 'dialogue', '6': 'transition', '7': 'shot' };
        if (numMap[e.key]) {
            e.preventDefault();
            setLineType(numMap[e.key], p);
        }
    }

    // Bindings for Alt Key Conversions
    if (e.altKey && !e.ctrlKey && !e.shiftKey) {
        const altMap = { 's': 'scene-heading', 'a': 'action', 'c': 'character', 'p': 'parenthetical', 'd': 'dialogue', 't': 'transition', 'h': 'shot' };
        const targetKey = e.key.toLowerCase();
        if (altMap[targetKey]) {
            e.preventDefault();
            setLineType(altMap[targetKey], p);
        }
    }
    
    // Strikethrough binding
    if (e.ctrlKey && e.altKey && e.key.toLowerCase() === 'x') {
        e.preventDefault();
        document.execCommand('strikeThrough');
    }
});

// Global Settings and Application State
let appSettings = {
    localDir: null,
    cloudDir: null,
    autoSaveInterval: 5,
    recentProjects: [],
    projectName: 'Quiet Hours 4th Draft',
    currentProjectFile: null,
    sharedFolderLink: 'https://drive.google.com/',
    isRevisionMode: false,
    isFocusMode: false,
    darkMode: false,
    snapshots: [],
    projectDocuments: {
        'Default Document': '',
        'Private Pad': '',
        'Title Page': ''
    },
    hotkeys: {
        'scene-heading': 'ctrl+1',
        'action': 'ctrl+2',
        'character': 'ctrl+3',
        'parenthetical': 'ctrl+4',
        'dialogue': 'ctrl+5',
        'transition': 'ctrl+6',
        'shot': 'ctrl+7'
    }
};
let currentDocument = 'Default Document';

// Setup Support for Multiple Menu Dropdowns
document.querySelectorAll('.dropdown').forEach(menu => {
    menu.addEventListener('click', (e) => {
        document.querySelectorAll('.dropdown').forEach(m => {
            if (m !== menu) m.classList.remove('open');
        });
        menu.classList.toggle('open');
        e.stopPropagation();
    });
});
document.addEventListener('click', () => { document.querySelectorAll('.dropdown').forEach(m => m.classList.remove('open')); });

// Core Initialization (Load via PyWebView or LocalStorage)
let isAppReady = false;

function initApp() {
    if (isAppReady) return;
    isAppReady = true;
    initializeEnvironment();
}

window.addEventListener('pywebviewready', async () => {
    const loaded = await window.pywebview.api.load_settings();
    if (loaded && Object.keys(loaded).length > 0) {
        appSettings = { ...appSettings, ...loaded };
        if (!appSettings.hotkeys) appSettings.hotkeys = {
            'scene-heading': 'ctrl+1', 'action': 'ctrl+2', 'character': 'ctrl+3', 
            'parenthetical': 'ctrl+4', 'dialogue': 'ctrl+5', 'transition': 'ctrl+6', 'shot': 'ctrl+7'
        };
    }
    initApp();
});

window.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
        if (!window.pywebview && !isAppReady) {
            const cache = localStorage.getItem('kindred_script_settings');
            if (cache) {
                appSettings = { ...appSettings, ...JSON.parse(cache) };
                if (!appSettings.hotkeys) appSettings.hotkeys = {
                    'scene-heading': 'ctrl+1', 'action': 'ctrl+2', 'character': 'ctrl+3', 
                    'parenthetical': 'ctrl+4', 'dialogue': 'ctrl+5', 'transition': 'ctrl+6', 'shot': 'ctrl+7'
                };
            }
            const legacyBackup = localStorage.getItem('kindred_script_backup');
            if (legacyBackup && !appSettings.projectDocuments['Default Document']) {
                appSettings.projectDocuments['Default Document'] = legacyBackup;
            }
            initApp();
        }
    }, 750); // Give Python wrapper a moment to inject before falling back
});

function initializeEnvironment() {
    applySettingsToUI();
    loadCurrentDocument();
    rebuildDocumentSidebar();
}

function applySettingsToUI() {
    if (appSettings.cloudDir) {
        const cStatus = document.getElementById('cloud-dir-status');
        if (cStatus) {
            cStatus.textContent = `Saving to: ${appSettings.cloudDir}`;
            cStatus.style.color = '#10b981';
        }
    }
    if (appSettings.localDir) {
        const lStatus = document.getElementById('local-dir-status');
        if (lStatus) {
            lStatus.textContent = `Saving to: ${appSettings.localDir}`;
            lStatus.style.color = '#10b981';
        }
    }
    const intervalSelect = document.getElementById('auto-save-interval');
    if (intervalSelect && appSettings.autoSaveInterval !== undefined) {
        intervalSelect.value = appSettings.autoSaveInterval;
    }
    startAutoSaveInterval();
    
    // If updateRecentProjectsUI is meant to be implemented later, wrap it so it doesn't cause errors
    if(typeof updateRecentProjectsUI === 'function') updateRecentProjectsUI();
    
    const projectNameDisplay = document.getElementById('project-name-display');
    if(projectNameDisplay) {
        projectNameDisplay.innerHTML = `⬅ &nbsp; ${appSettings.projectName || 'Untitled Project'}`;
    }
    
    const statusProjectName = document.getElementById('status-project-name');
    if(statusProjectName) {
        statusProjectName.textContent = appSettings.projectName || 'Untitled Project';
    }
    const revCheck = document.getElementById('rev-mode-check');
    if (revCheck) {
        revCheck.style.visibility = appSettings.isRevisionMode ? 'visible' : 'hidden';
    }
    const darkModeCheck = document.getElementById('dark-mode-check');
    if (darkModeCheck) {
        darkModeCheck.style.visibility = appSettings.darkMode ? 'visible' : 'hidden';
    }
    const focusModeCheck = document.getElementById('focus-mode-check');
    if (focusModeCheck) {
        focusModeCheck.style.visibility = appSettings.isFocusMode ? 'visible' : 'hidden';
    }
    if (appSettings.darkMode) {
        document.body.classList.add('dark-mode');
    } else {
        document.body.classList.remove('dark-mode');
    }
    if (appSettings.isFocusMode) {
        document.body.classList.add('focus-mode');
    } else {
        document.body.classList.remove('focus-mode');
    }
}

function updateProjectName(newName) {
    appSettings.projectName = newName;
    applySettingsToUI();
}

function addToRecent(filepath) {
    // Placeholder function to prevent reference errors, to be expanded later
    if (!appSettings.recentProjects) appSettings.recentProjects = [];
    if (!appSettings.recentProjects.includes(filepath)) {
        appSettings.recentProjects.unshift(filepath);
    }
}

function saveSettings() {
    if (window.pywebview) {
        window.pywebview.api.save_settings(appSettings);
    } else {
        localStorage.setItem('kindred_script_settings', JSON.stringify(appSettings));
    }
}

function loadCurrentDocument() {
    editor.innerHTML = appSettings.projectDocuments[currentDocument] || '<p class="action">&#8203;</p>';
    updateToolbarUI(getLineType(getCurrentParagraph()));
    updateStats();
}

function saveCurrentDocument() {
    appSettings.projectDocuments[currentDocument] = editor.innerHTML;
    saveSettings();
}

document.getElementById('file-menu-new').addEventListener('click', () => {
    if (confirm("Create a new project? Any unsaved changes will be lost.")) {
        appSettings.projectDocuments = { 'Default Document': '<p class="action">&#8203;</p>', 'Private Pad': '', 'Title Page': '' };
        currentDocument = 'Default Document';
        appSettings.currentProjectFile = null;
        updateProjectName("Untitled Project");
        saveSettings();
        initializeEnvironment();
    }
});

async function handleOpenProject() {
    if (window.pywebview) {
        const result = await window.pywebview.api.open_project_dialog();
        if (result && result.data) {
            try {
                const parsed = JSON.parse(result.data);
                appSettings.projectDocuments = parsed;
                currentDocument = Object.keys(parsed)[0] || 'Default Document';
                appSettings.currentProjectFile = result.filepath;
                const filename = result.filepath.split('\\').pop().split('/').pop().replace('.ksp', '');
                updateProjectName(filename);
                saveSettings();
                initializeEnvironment();
                addToRecent(result.filepath);
            } catch (e) { alert("Invalid project file."); }
        } else if (result && result.error) { alert(result.error); }
    } else { alert("Native opening requires the Python app wrapper."); }
}

document.getElementById('file-menu-open').addEventListener('click', handleOpenProject);
document.getElementById('sidebar-open-project').addEventListener('click', handleOpenProject);

document.getElementById('file-menu-save').addEventListener('click', async () => {
    saveCurrentDocument();
    const projectData = JSON.stringify(appSettings.projectDocuments);
    const projectName = appSettings.projectName || "Untitled Project";
    if (window.pywebview) {
        const result = await window.pywebview.api.save_project_dialog(projectData, projectName);
        if (result && !result.startsWith("Error")) {
            appSettings.currentProjectFile = result;
            const filename = result.split('\\').pop().split('/').pop().replace('.ksp', '');
            updateProjectName(filename);
            addToRecent(result);
            alert("Project saved successfully!");
        } else if (result) { alert(result); }
    } else { alert("Native saving requires the Python app wrapper."); }
});

document.getElementById('file-menu-rename').addEventListener('click', () => {
    const currentName = appSettings.projectName || "Untitled Project";
    const newName = prompt("Rename Project:", currentName);
    if (newName) updateProjectName(newName);
});

document.getElementById('file-menu-duplicate').addEventListener('click', () => {
    appSettings.currentProjectFile = null;
    const currentName = appSettings.projectName || "Untitled Project";
    updateProjectName(currentName + " (Copy)");
    alert("Project duplicated in memory. Use 'Save Project' to write it to a new file.");
});

// Smart Cloud Auto-Save Trigger
let backupTimeout;
function triggerBackup() {
    syncDot.style.backgroundColor = '#f59e0b';
    syncText.textContent = 'Saving Changes...';
    clearTimeout(backupTimeout);
    backupTimeout = setTimeout(async () => {
        saveCurrentDocument(); // Update Memory & settings.json
        
        if (window.pywebview) {
            window.pywebview.api.save_backup(editor.innerHTML, appSettings.cloudDir, appSettings.localDir, appSettings.projectName).then(response => {
                syncDot.style.backgroundColor = '#10b981';
                syncText.textContent = response;
            });
        } else {
            syncDot.style.backgroundColor = '#10b981';
            syncText.textContent = 'Saved to Settings (Browser Mode)';
        }
    }, 1200);
}

function updateStats() {
    // Get raw text, remove our zero-width cursor spacers, and split by whitespace
    let text = editor.innerText || "";
    text = text.replace(/\u200B/g, '').trim();
    const words = text ? text.split(/\s+/).filter(word => word.length > 0).length : 0;
    
    // A standard page is 11 inches. Assuming standard 96 CSS pixels per inch
    const pageHeightPixels = 11 * 96;
    const pages = Math.max(1, Math.ceil(editor.scrollHeight / pageHeightPixels));
    
    const statsEl = document.getElementById('status-stats');
    if (statsEl) statsEl.textContent = `${words} words | ${pages} page${pages !== 1 ? 's' : ''}`;
}

editor.addEventListener('input', () => {
    if (appSettings.isRevisionMode) {
        const p = getCurrentParagraph();
        if (p && !p.classList.contains('revision') && !p.classList.contains('page-break')) {
            p.classList.add('revision');
        }
    }
    triggerBackup();
    updateStats();
});

const backupModal = document.getElementById('backup-modal');

let autoSaveTimer = null;
function startAutoSaveInterval() {
    clearInterval(autoSaveTimer);
    const minutes = parseInt(appSettings.autoSaveInterval, 10);
    if (!isNaN(minutes) && minutes > 0) {
        autoSaveTimer = setInterval(() => {
            triggerBackup();
        }, minutes * 60 * 1000);
    }
}

document.getElementById('auto-save-interval').addEventListener('change', (e) => {
    appSettings.autoSaveInterval = parseInt(e.target.value, 10);
    saveSettings();
    startAutoSaveInterval();
});

document.getElementById('btn-select-cloud-dir').addEventListener('click', async () => {
    if (window.pywebview) {
        const folderPath = await window.pywebview.api.choose_directory();
        if (folderPath && folderPath !== "None") {
            appSettings.cloudDir = folderPath;
            applySettingsToUI();
            saveSettings();
            triggerBackup();
        }
    } else {
        alert("Folder picker requires running through the Python app wrapper.");
    }
});

document.getElementById('btn-select-local-dir').addEventListener('click', async () => {
    if (window.pywebview) {
        const folderPath = await window.pywebview.api.choose_directory();
        if (folderPath && folderPath !== "None") {
            appSettings.localDir = folderPath;
            applySettingsToUI();
            saveSettings();
            triggerBackup();
        }
    } else {
        alert("Folder picker requires running through the Python app wrapper.");
    }
});

document.getElementById('btn-external-backups').addEventListener('click', () => {
    backupModal.style.display = 'flex';
});
document.getElementById('file-menu-backups').addEventListener('click', () => {
    backupModal.style.display = 'flex';
});
document.getElementById('btn-close-modal').addEventListener('click', () => {
    backupModal.style.display = 'none';
});

// Hotkeys Modal Logic
const hotkeysModal = document.getElementById('hotkeys-modal');

document.getElementById('menu-edit-hotkeys').addEventListener('click', () => {
    document.querySelectorAll('.hotkey-input').forEach(input => {
        const action = input.getAttribute('data-action');
        if (appSettings.hotkeys && appSettings.hotkeys[action]) {
            input.value = appSettings.hotkeys[action];
        }
    });
    hotkeysModal.style.display = 'flex';
});

document.getElementById('btn-close-hotkeys').addEventListener('click', () => {
    hotkeysModal.style.display = 'none';
});

document.getElementById('btn-save-hotkeys').addEventListener('click', () => {
    document.querySelectorAll('.hotkey-input').forEach(input => {
        const action = input.getAttribute('data-action');
        appSettings.hotkeys[action] = input.value;
    });
    saveSettings();
    hotkeysModal.style.display = 'none';
});

document.querySelectorAll('.hotkey-input').forEach(input => {
    input.addEventListener('keydown', (e) => {
        e.preventDefault(); 
        const keyStr = getHotkeyString(e);
        if (keyStr !== 'ctrl' && keyStr !== 'alt' && keyStr !== 'shift') input.value = keyStr;
    });
});

const docList = document.getElementById('project-documents-list');

function rebuildDocumentSidebar() {
    docList.innerHTML = '';
    Object.keys(appSettings.projectDocuments).forEach(docName => {
        const div = document.createElement('div');
        div.className = `sidebar-item ${docName === currentDocument ? 'active' : ''}`;
        div.dataset.docname = docName;
        div.innerHTML = `<span class="sidebar-icon">📄</span> ${docName}`;
        docList.appendChild(div);
    });
    
    const addBtn = document.createElement('div');
    addBtn.className = 'sidebar-item';
    addBtn.id = 'add-document-btn';
    addBtn.innerHTML = '<span class="sidebar-icon">➕</span> Add Document';
    docList.appendChild(addBtn);
}

docList.addEventListener('click', (e) => {
    const item = e.target.closest('.sidebar-item');
    if (!item) return;

    if (item.id === 'add-document-btn') {
        const name = prompt("Enter new document name:");
        if (name && !appSettings.projectDocuments[name]) {
            appSettings.projectDocuments[name] = '<p class="action">&#8203;</p>';
            saveSettings();
            rebuildDocumentSidebar();
        }
    } else if (item.dataset.docname) {
        saveCurrentDocument();
        currentDocument = item.dataset.docname;
        rebuildDocumentSidebar();
        loadCurrentDocument();
    }
});

// Universal Export Integration
function handleExport(format) {
    if (window.pywebview) {
        const lines = Array.from(editor.querySelectorAll('p')).map(p => ({
            type: getLineType(p),
            text: p.textContent,
            revision: p.classList.contains('revision')
        }));
        syncDot.style.backgroundColor = '#f59e0b';
        syncText.textContent = `Generating ${format.toUpperCase()}...`;
        const projectName = appSettings.projectName || "Untitled Project";
        
        let apiCall;
        if (format === 'pdf') apiCall = window.pywebview.api.export_pdf(lines, projectName);
        else if (format === 'fdx') apiCall = window.pywebview.api.export_fdx(lines, projectName);
        else if (format === 'fountain') apiCall = window.pywebview.api.export_writersduet(lines, projectName);

        apiCall.then(response => {
            if (response.includes('Error') || response.includes('Missing')) {
                syncDot.style.backgroundColor = '#ef4444';
                alert(response);
            } else {
                syncDot.style.backgroundColor = '#10b981';
            }
            syncText.textContent = response;
        });
    } else {
        alert("Export requires running the Python app wrapper (desktop.py).");
    }
}
document.getElementById('export-pdf-sidebar-btn').addEventListener('click', () => handleExport('pdf'));
document.getElementById('file-menu-export-pdf').addEventListener('click', () => handleExport('pdf'));
document.getElementById('file-menu-export-fdx').addEventListener('click', () => handleExport('fdx'));
document.getElementById('file-menu-export-wd').addEventListener('click', () => handleExport('fountain'));

// Print Integration
document.getElementById('file-menu-print').addEventListener('click', () => {
    window.print();
});
document.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key.toLowerCase() === 'p') {
        e.preventDefault();
        window.print();
    }
    if (e.ctrlKey && e.key.toLowerCase() === 'o') {
        e.preventDefault();
        handleOpenProject();
    }
    if (e.ctrlKey && e.key.toLowerCase() === 's') {
        e.preventDefault();
        e.shiftKey ? document.getElementById('file-menu-backups').click() : document.getElementById('file-menu-save').click();
    }
});

// File Import Handling
async function handleImport() {
    if (window.pywebview) {
        const fileInfo = await window.pywebview.api.open_file_dialog();
        if (!fileInfo) return; 
        if (fileInfo.error) {
            alert("Error reading file: " + fileInfo.error);
            return;
        }

        // Decode base64 file data securely from Python
        const byteCharacters = atob(fileInfo.data);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
            byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const ext = fileInfo.ext;

        if (ext === 'pdf') {
            const pdf = await pdfjsLib.getDocument(byteArray).promise;
            let fullText = "";
            for (let i = 1; i <= pdf.numPages; i++) {
                const page = await pdf.getPage(i);
                const content = await page.getTextContent();
                let lastY = -1;
                let pageText = '';
                for (let item of content.items) {
                    if (lastY !== -1) {
                        const yDiff = Math.abs(lastY - item.transform[5]);
                        if (yDiff > 16) { // Detect standard double-space breaks
                            pageText += '\n\n';
                        } else if (yDiff > 4) {
                            pageText += '\n';
                        }
                    }
                    if (lastY === -1 || Math.abs(lastY - item.transform[5]) > 4) {
                        const spaces = Math.max(0, Math.floor(item.transform[4] / 6));
                        pageText += ' '.repeat(spaces);
                    }
                    pageText += item.str;
                    lastY = item.transform[5];
                }
                fullText += pageText + "\n\n";
            }
            processImportedText(fullText);
        } else {
            const text = new TextDecoder().decode(byteArray);
            ext === 'html' ? (editor.innerHTML = text, triggerBackup()) : processImportedText(text);
        }
    } else {
        document.getElementById('file-import').click();
    }
}
document.getElementById('import-btn').addEventListener('click', handleImport);
document.getElementById('file-menu-import').addEventListener('click', handleImport);

// Configure PDF.js worker for background parsing
pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.16.105/pdf.worker.min.js';

function processImportedText(content) {
    const lines = content.split(/\r?\n/);
    editor.innerHTML = '';
    
    let previousType = '';
    let previousSpaces = 0;
    let blankLineBefore = false;

    for (let i = 0; i < lines.length; i++) {
        const rawLine = lines[i];
        const trimmed = rawLine.trim();

        // Register empty space to map element associations, but let CSS handle physical margins
        if (!trimmed) {
            blankLineBefore = true;
            continue;
        }
        let type = 'action';
        let isAllCaps = (trimmed === trimmed.toUpperCase() && /[A-Z]/.test(trimmed));
        const leadingSpaces = rawLine.length - rawLine.trimStart().length;

        // Fountain-style Heuristic Ruleset
        if (trimmed.startsWith('===')) {
            type = 'page-break';
        } else if (/^SCENE\b/i.test(trimmed)) {
            type = 'shot';
        } else if (/^(INT\.|EXT\.|INT\/EXT\.|I\/E\.|INT |EXT )/i.test(trimmed)) {
            type = 'scene-heading';
        } else if (isAllCaps && (trimmed.endsWith(' TO:') || trimmed === 'FADE IN:' || trimmed === 'FADE OUT.')) {
            type = 'transition';
        } else if (isAllCaps && (leadingSpaces > 10 || blankLineBefore) && trimmed.length < 45 && !trimmed.startsWith('(') && previousType !== 'character') {
            type = 'character';
        } else if (trimmed.startsWith('(') && trimmed.endsWith(')')) {
            type = 'parenthetical';
        } else if (previousType === 'character' || previousType === 'parenthetical') {
            type = 'dialogue';
        } else if (previousType === 'dialogue' && !blankLineBefore) {
            // If the indent suddenly decreases back to the left, it's an action line that missed a blank line
            if (leadingSpaces < previousSpaces - 5) {
                type = 'action';
            } else {
                type = 'dialogue';
            }
        }

        if (type === 'scene-heading' && editor.childNodes.length > 0) {
            const lastNode = editor.lastChild;
            if (lastNode && lastNode.textContent.replace(/\u200B/g, '').trim() !== '') {
                const spacer = document.createElement('p');
                spacer.className = 'action';
                spacer.innerHTML = '&#8203;';
                editor.appendChild(spacer);
            }
        }

        const p = document.createElement('p');
        p.className = type;              p.textContent = trimmed;
        editor.appendChild(p);

        previousType = type;
        previousSpaces = leadingSpaces;
        blankLineBefore = false;
    }

    if (editor.innerHTML === '') {
        const p = document.createElement('p');
        p.className = 'action';
        p.innerHTML = '&#8203;';
        editor.appendChild(p);
    }

    triggerBackup();
    updateStats();
}

document.getElementById('file-import').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const ext = file.name.split('.').pop().toLowerCase();

    if (ext === 'pdf') {
        const reader = new FileReader();
        reader.onload = async function() {
            const typedarray = new Uint8Array(this.result);
            const pdf = await pdfjsLib.getDocument(typedarray).promise;
            let fullText = "";
            for (let i = 1; i <= pdf.numPages; i++) {
                const page = await pdf.getPage(i);
                const content = await page.getTextContent();
                
                let lastY = -1;
                let pageText = '';
                
                // Map X/Y coordinate positions into visual formatting approximations
                for (let item of content.items) {
                    if (lastY !== -1) {
                        const yDiff = Math.abs(lastY - item.transform[5]);
                        if (yDiff > 16) {
                            pageText += '\n\n';
                        } else if (yDiff > 4) {
                            pageText += '\n';
                        }
                    }
                    if (lastY === -1 || Math.abs(lastY - item.transform[5]) > 4) {
                        const spaces = Math.max(0, Math.floor(item.transform[4] / 6)); // Rough font space mapping
                        pageText += ' '.repeat(spaces);
                    }
                    pageText += item.str;
                    lastY = item.transform[5];
                }
                fullText += pageText + "\n\n";
            }
            processImportedText(fullText);
        };
        reader.readAsArrayBuffer(file);
    } else {
        const reader = new FileReader();
        reader.onload = (event) => {
            if (ext === 'html') {
                editor.innerHTML = event.target.result;
                triggerBackup();
            } else {
                processImportedText(event.target.result);
            }
        };
        reader.readAsText(file);
    }
});

// --- Custom Context Menu Implementation ---
const contextMenu = document.getElementById('context-menu');

editor.addEventListener('contextmenu', (e) => {
    e.preventDefault(); // Suppress the default browser right-click menu
    
    contextMenu.style.display = 'block';
    
    // Prevent the menu from clipping off the edges of the screen
    let x = e.clientX;
    let y = e.clientY;
    if (x + contextMenu.offsetWidth > window.innerWidth) x = window.innerWidth - contextMenu.offsetWidth;
    if (y + contextMenu.offsetHeight > window.innerHeight) y = window.innerHeight - contextMenu.offsetHeight;
    
    contextMenu.style.top = `${y}px`;
    contextMenu.style.left = `${x}px`;
});

// Hide menu on outside click
document.addEventListener('mousedown', (e) => {
    if (!e.target.closest('#context-menu')) {
        contextMenu.style.display = 'none';
    }
});

// Execute standard clipboard commands. 
// We use `mousedown` instead of `click` to prevent the editor from losing cursor focus before the command fires!
['cut', 'copy', 'selectAll', 'undo', 'redo'].forEach(action => {
    const dashAction = action.replace(/[A-Z]/g, letter => `-${letter.toLowerCase()}`);
    
    const ctxBtn = document.getElementById(`ctx-${dashAction}`);
    if (ctxBtn) {
        ctxBtn.addEventListener('mousedown', (e) => {
            e.preventDefault(); 
            document.execCommand(action);
            contextMenu.style.display = 'none';
            triggerBackup(); updateStats();
        });
    }
    
    const editBtn = document.getElementById(`edit-${dashAction}`);
    if (editBtn) {
        editBtn.addEventListener('mousedown', (e) => {
            e.preventDefault(); 
            document.execCommand(action);
            triggerBackup(); updateStats();
        });
    }
});

const handlePaste = async (e) => {
    e.preventDefault();
    try {
        const text = await navigator.clipboard.readText();
        document.execCommand('insertText', false, text); // Insert as pure plain text
    } catch (err) { document.execCommand('paste'); }
    if (contextMenu) contextMenu.style.display = 'none';
    triggerBackup(); updateStats();
};

document.getElementById('ctx-paste').addEventListener('mousedown', handlePaste);

const editPasteBtn = document.getElementById('edit-paste');
if (editPasteBtn) {
    editPasteBtn.addEventListener('mousedown', handlePaste);
}

const editPageBreakBtn = document.getElementById('edit-page-break');
if (editPageBreakBtn) {
    editPageBreakBtn.addEventListener('mousedown', (e) => {
        e.preventDefault();
        insertPageBreak();
        document.querySelectorAll('.dropdown').forEach(m => m.classList.remove('open'));
    });
}

// --- Share Menu Logic ---
document.getElementById('share-gdrive').addEventListener('click', () => {
    const link = appSettings.sharedFolderLink || 'https://drive.google.com/';
    if (window.pywebview) {
        window.pywebview.api.open_url(link);
    } else {
        window.open(link, '_blank');
    }
});

document.getElementById('share-configure').addEventListener('click', () => {
    const currentLink = appSettings.sharedFolderLink || '';
    const newLink = prompt("Enter your Google Drive / Shared Folder link:", currentLink);
    if (newLink !== null && newLink.trim() !== "") {
        appSettings.sharedFolderLink = newLink.trim();
        saveSettings();
        alert("Share link updated successfully!");
    }
});

// --- View Menu Logic ---
function toggleFocusMode() {
    appSettings.isFocusMode = !appSettings.isFocusMode;
    applySettingsToUI();
    saveSettings();
}
document.getElementById('view-toggle-focus').addEventListener('click', toggleFocusMode);

// --- Customize Menu Logic ---
document.getElementById('menu-toggle-darkmode').addEventListener('click', () => {
    appSettings.darkMode = !appSettings.darkMode;
    applySettingsToUI();
    saveSettings();
});

// --- Mini Toolbar Logic ---
function updateMiniToolbarState() {
    ['bold', 'italic', 'underline'].forEach(style => {
        const btn = document.getElementById(`mini-${style}`);
        if (document.queryCommandState(style)) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    const p = getCurrentParagraph();
    document.getElementById('mini-align-left').classList.remove('active');
    document.getElementById('mini-align-center').classList.remove('active');
    document.getElementById('mini-align-right').classList.remove('active');
    if (p) {
        if (p.classList.contains('align-center')) {
            document.getElementById('mini-align-center').classList.add('active');
        } else if (p.classList.contains('align-right')) {
            document.getElementById('mini-align-right').classList.add('active');
        } else {
            // Left is default, so we make it active if no other alignment is set
            document.getElementById('mini-align-left').classList.add('active');
        }
    }
}

['bold', 'italic', 'underline'].forEach(style => {
    document.getElementById(`mini-${style}`).addEventListener('mousedown', e => {
        e.preventDefault();
        document.execCommand(style);
    });
});

['left', 'center', 'right'].forEach(align => {
    document.getElementById(`mini-align-${align}`).addEventListener('mousedown', e => {
        e.preventDefault();
        const p = getCurrentParagraph();
        if (p) {
            p.classList.remove('align-center', 'align-right');
            if (align !== 'left') { // left is the default, so we only add classes for others
                p.classList.add(`align-${align}`);
            }
            updateMiniToolbarState();
            triggerBackup();
        }
    });
});

// --- Revisions and Snapshots Logic ---
document.getElementById('rev-toggle-mode').addEventListener('click', () => {
    appSettings.isRevisionMode = !appSettings.isRevisionMode;
    document.getElementById('rev-mode-check').style.visibility = appSettings.isRevisionMode ? 'visible' : 'hidden';
    saveSettings();
});

document.getElementById('rev-clear-marks').addEventListener('click', () => {
    if (confirm("Are you sure you want to clear all revision asterisks from the current document?")) {
        editor.querySelectorAll('.revision').forEach(el => el.classList.remove('revision'));
        triggerBackup();
    }
});

const snapshotsModal = document.getElementById('snapshots-modal');
const snapshotsList = document.getElementById('snapshots-list');

document.getElementById('rev-manage-snapshots').addEventListener('click', () => {
    renderSnapshotsList();
    snapshotsModal.style.display = 'flex';
});

document.getElementById('btn-close-snapshots').addEventListener('click', () => {
    snapshotsModal.style.display = 'none';
});

document.getElementById('btn-create-snapshot').addEventListener('click', () => {
    const nameInput = document.getElementById('snapshot-name-input');
    const name = nameInput.value.trim() || 'Untitled Snapshot';
    
    saveCurrentDocument(); // Flush memory to state before copying
    if (!appSettings.snapshots) appSettings.snapshots = [];
    
    appSettings.snapshots.push({
        id: Date.now(),
        name: name,
        date: new Date().toLocaleString(),
        projectName: appSettings.projectName || 'Untitled Project',
        documents: JSON.parse(JSON.stringify(appSettings.projectDocuments))
    });
    
    nameInput.value = '';
    saveSettings();
    renderSnapshotsList();
});

function renderSnapshotsList() {
    if (!appSettings.snapshots) appSettings.snapshots = [];
    snapshotsList.innerHTML = '';
    
    const currentProjectName = appSettings.projectName || 'Untitled Project';
    const projectSnapshots = appSettings.snapshots.filter(snap => 
        (snap.projectName || 'Untitled Project') === currentProjectName
    );

    if (projectSnapshots.length === 0) {
        snapshotsList.innerHTML = '<p style="text-align:center; margin-top:20px; font-size: 11px;">No snapshots created yet for this project.</p>';
        return;
    }
    
    [...projectSnapshots].reverse().forEach(snap => {
        const div = document.createElement('div');
        div.className = 'hotkey-row';
        div.style.padding = '8px';
        div.style.borderBottom = '1px solid #36424e';
        
        div.innerHTML = `
            <div style="flex:1;">
                <div style="font-weight:bold; font-size:13px;">${snap.name}</div>
                <div style="font-size:10px; color:var(--text-muted);">${snap.date}</div>
            </div>
            <div style="display:flex; gap:5px;">
                <button class="modal-btn" onclick="restoreSnapshot(${snap.id})" style="background-color:#f59e0b; padding:4px 8px; font-size:10px;">Restore</button>
                <button class="modal-btn" onclick="if(confirm('Delete this snapshot?')) { appSettings.snapshots = appSettings.snapshots.filter(s => s.id !== ${snap.id}); saveSettings(); renderSnapshotsList(); }" style="background-color:#ef4444; padding:4px 8px; font-size:10px;">Delete</button>
            </div>
        `;
        snapshotsList.appendChild(div);
    });
}

window.restoreSnapshot = (id) => {
    const snap = appSettings.snapshots.find(s => s.id === id);
    if (snap && confirm(`Restore "${snap.name}"? This will overwrite your current project state.`)) {
        appSettings.projectDocuments = JSON.parse(JSON.stringify(snap.documents));
        currentDocument = Object.keys(appSettings.projectDocuments)[0] || 'Default Document';
        rebuildDocumentSidebar(); loadCurrentDocument(); saveSettings();
        snapshotsModal.style.display = 'none';
    }
};
