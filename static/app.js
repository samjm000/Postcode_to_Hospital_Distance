/**
 * Postcode to Hospital Distance Calculator
 * Frontend JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements - Main Form
    const apiKeyInput = document.getElementById('api-key');
    const toggleKeyBtn = document.getElementById('toggle-key');
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const browseBtn = document.getElementById('browse-btn');
    const fileInfo = document.getElementById('file-info');
    const fileName = document.getElementById('file-name');
    const removeFileBtn = document.getElementById('remove-file');
    const destinationsList = document.getElementById('destinations-list');
    const processBtn = document.getElementById('process-btn');
    const mainForm = document.getElementById('main-form');
    const progressSection = document.getElementById('progress-section');
    const progressText = document.getElementById('progress-text');
    const resultsSection = document.getElementById('results-section');
    const resultsText = document.getElementById('results-text');
    const downloadBtn = document.getElementById('download-btn');
    const resetBtn = document.getElementById('reset-btn');
    const errorSection = document.getElementById('error-section');
    const errorText = document.getElementById('error-text');
    const errorResetBtn = document.getElementById('error-reset-btn');

    // DOM Elements - Settings
    const manageDestinationsBtn = document.getElementById('manage-destinations-btn');
    const settingsModal = document.getElementById('settings-modal');
    const closeSettingsBtn = document.getElementById('close-settings');
    const destinationsManager = document.getElementById('destinations-manager');
    const addDestinationBtn = document.getElementById('add-destination-btn');

    // DOM Elements - Destination Form
    const destinationFormModal = document.getElementById('destination-form-modal');
    const destinationFormTitle = document.getElementById('destination-form-title');
    const destinationForm = document.getElementById('destination-form');
    const destEditId = document.getElementById('dest-edit-id');
    const destName = document.getElementById('dest-name');
    const destShortName = document.getElementById('dest-short-name');
    const destAddress = document.getElementById('dest-address');
    const closeDestFormBtn = document.getElementById('close-destination-form');
    const cancelDestBtn = document.getElementById('cancel-destination');

    // State
    let selectedFile = null;
    let resultsCsv = null;
    let destinations = {};

    // Supported file extensions
    const SUPPORTED_EXTENSIONS = ['.csv', '.xlsx', '.xls'];

    // Initialize
    loadDestinations();
    setupEventListeners();

    /**
     * Load available destinations from the API
     */
    async function loadDestinations() {
        try {
            const response = await fetch('/api/destinations');
            destinations = await response.json();
            renderDestinations();
            renderDestinationsManager();
        } catch (error) {
            console.error('Failed to load destinations:', error);
        }
    }

    /**
     * Render destination checkboxes in main form
     */
    function renderDestinations() {
        destinationsList.innerHTML = '';

        const entries = Object.entries(destinations);

        if (entries.length === 0) {
            destinationsList.innerHTML = '<p class="empty-state">No destinations configured. Click the settings icon to add hospitals.</p>';
            return;
        }

        for (const [id, dest] of entries) {
            const item = document.createElement('div');
            item.className = 'destination-item selected';
            item.innerHTML = `
                <input type="checkbox" id="dest-${id}" name="destination" value="${id}" checked>
                <label for="dest-${id}">
                    <span class="name">${dest.name}</span>
                    <span class="address">${dest.address}</span>
                </label>
            `;

            const checkbox = item.querySelector('input');
            checkbox.addEventListener('change', () => {
                item.classList.toggle('selected', checkbox.checked);
                validateForm();
            });

            destinationsList.appendChild(item);
        }
    }

    /**
     * Render destinations in settings manager
     */
    function renderDestinationsManager() {
        destinationsManager.innerHTML = '';

        const entries = Object.entries(destinations);

        if (entries.length === 0) {
            destinationsManager.innerHTML = '<p class="empty-state">No hospitals added yet</p>';
            return;
        }

        for (const [id, dest] of entries) {
            const item = document.createElement('div');
            item.className = 'dest-item';
            item.innerHTML = `
                <div class="dest-item-info">
                    <div class="dest-item-name">${dest.name} (${dest.short_name})</div>
                    <div class="dest-item-address">${dest.address}</div>
                </div>
                <div class="dest-item-actions">
                    <button type="button" class="edit-btn" data-id="${id}" title="Edit">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                        </svg>
                    </button>
                    <button type="button" class="delete-btn" data-id="${id}" title="Delete">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="3 6 5 6 21 6"/>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                        </svg>
                    </button>
                </div>
            `;

            // Edit button
            item.querySelector('.edit-btn').addEventListener('click', () => openEditForm(id));

            // Delete button
            item.querySelector('.delete-btn').addEventListener('click', () => deleteDestination(id));

            destinationsManager.appendChild(item);
        }
    }

    /**
     * Set up event listeners
     */
    function setupEventListeners() {
        // Toggle API key visibility
        toggleKeyBtn.addEventListener('click', function() {
            apiKeyInput.type = apiKeyInput.type === 'password' ? 'text' : 'password';
        });

        // API key input
        apiKeyInput.addEventListener('input', validateForm);

        // File drop zone
        dropZone.addEventListener('click', () => fileInput.click());
        browseBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            fileInput.click();
        });

        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            if (e.dataTransfer.files.length > 0) {
                handleFileSelect(e.dataTransfer.files[0]);
            }
        });

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFileSelect(e.target.files[0]);
            }
        });

        removeFileBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            selectedFile = null;
            fileInput.value = '';
            fileInfo.classList.add('hidden');
            dropZone.style.display = 'block';
            validateForm();
        });

        // Process button
        processBtn.addEventListener('click', processFile);

        // Reset buttons
        resetBtn.addEventListener('click', resetForm);
        errorResetBtn.addEventListener('click', resetForm);

        // Download button
        downloadBtn.addEventListener('click', downloadResults);

        // Settings modal
        manageDestinationsBtn.addEventListener('click', () => {
            settingsModal.classList.remove('hidden');
        });

        closeSettingsBtn.addEventListener('click', closeSettingsModal);
        settingsModal.querySelector('.modal-backdrop').addEventListener('click', closeSettingsModal);

        // Add destination
        addDestinationBtn.addEventListener('click', openAddForm);

        // Destination form
        closeDestFormBtn.addEventListener('click', closeDestinationForm);
        cancelDestBtn.addEventListener('click', closeDestinationForm);
        destinationFormModal.querySelector('.modal-backdrop').addEventListener('click', closeDestinationForm);
        destinationForm.addEventListener('submit', handleDestinationSubmit);
    }

    /**
     * Close settings modal
     */
    function closeSettingsModal() {
        settingsModal.classList.add('hidden');
    }

    /**
     * Open add destination form
     */
    function openAddForm() {
        destEditId.value = '';
        destName.value = '';
        destShortName.value = '';
        destAddress.value = '';
        destinationFormTitle.textContent = 'Add Hospital';
        destinationFormModal.classList.remove('hidden');
        destName.focus();
    }

    /**
     * Open edit destination form
     */
    function openEditForm(id) {
        const dest = destinations[id];
        if (!dest) return;

        destEditId.value = id;
        destName.value = dest.name;
        destShortName.value = dest.short_name;
        destAddress.value = dest.address;
        destinationFormTitle.textContent = 'Edit Hospital';
        destinationFormModal.classList.remove('hidden');
        destName.focus();
    }

    /**
     * Close destination form
     */
    function closeDestinationForm() {
        destinationFormModal.classList.add('hidden');
    }

    /**
     * Handle destination form submit
     */
    async function handleDestinationSubmit(e) {
        e.preventDefault();

        const editId = destEditId.value;
        const data = {
            name: destName.value.trim(),
            short_name: destShortName.value.trim(),
            address: destAddress.value.trim()
        };

        try {
            let response;

            if (editId) {
                // Update existing
                response = await fetch(`/api/destinations/${editId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
            } else {
                // Create new - generate ID from short name
                data.id = data.short_name.toLowerCase().replace(/[^a-z0-9]/g, '_');
                response = await fetch('/api/destinations', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
            }

            const result = await response.json();

            if (!response.ok) {
                alert(result.error || 'Failed to save destination');
                return;
            }

            closeDestinationForm();
            await loadDestinations();
            validateForm();

        } catch (error) {
            alert('Failed to save destination: ' + error.message);
        }
    }

    /**
     * Delete a destination
     */
    async function deleteDestination(id) {
        const dest = destinations[id];
        if (!confirm(`Delete "${dest.name}"?`)) return;

        try {
            const response = await fetch(`/api/destinations/${id}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                const result = await response.json();
                alert(result.error || 'Failed to delete destination');
                return;
            }

            await loadDestinations();
            validateForm();

        } catch (error) {
            alert('Failed to delete destination: ' + error.message);
        }
    }

    /**
     * Check if file has a supported extension
     */
    function isSupportedFile(filename) {
        const lower = filename.toLowerCase();
        return SUPPORTED_EXTENSIONS.some(ext => lower.endsWith(ext));
    }

    /**
     * Handle file selection
     */
    function handleFileSelect(file) {
        if (!isSupportedFile(file.name)) {
            showError('Please select a CSV or Excel file (.csv, .xlsx, .xls)');
            return;
        }

        selectedFile = file;
        fileName.textContent = file.name;
        fileInfo.classList.remove('hidden');
        dropZone.style.display = 'none';
        validateForm();
    }

    /**
     * Validate form and enable/disable process button
     */
    function validateForm() {
        const hasApiKey = apiKeyInput.value.trim().length > 0;
        const hasFile = selectedFile !== null;
        const hasDestinations = document.querySelectorAll('input[name="destination"]:checked').length > 0;

        processBtn.disabled = !(hasApiKey && hasFile && hasDestinations);
    }

    /**
     * Process the uploaded file
     */
    async function processFile() {
        const apiKey = apiKeyInput.value.trim();
        const selectedDestinations = Array.from(
            document.querySelectorAll('input[name="destination"]:checked')
        ).map(cb => cb.value);

        // Show progress
        mainForm.classList.add('hidden');
        progressSection.classList.remove('hidden');
        progressText.textContent = 'Uploading file and calculating distances...';

        try {
            const formData = new FormData();
            formData.append('file', selectedFile);

            for (const dest of selectedDestinations) {
                formData.append('destinations', dest);
            }

            const response = await fetch('/api/process', {
                method: 'POST',
                headers: {
                    'X-API-Key': apiKey
                },
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'An error occurred');
            }

            // Success
            resultsCsv = data.csv;
            resultsText.textContent = `Successfully processed ${data.rows_processed} rows`;

            progressSection.classList.add('hidden');
            resultsSection.classList.remove('hidden');

        } catch (error) {
            showError(error.message);
        }
    }

    /**
     * Show error message
     */
    function showError(message) {
        mainForm.classList.add('hidden');
        progressSection.classList.add('hidden');
        resultsSection.classList.add('hidden');

        errorText.textContent = message;
        errorSection.classList.remove('hidden');
    }

    /**
     * Download results as CSV
     */
    function downloadResults() {
        if (!resultsCsv) return;

        const blob = new Blob([resultsCsv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');

        const originalName = selectedFile.name.replace(/\.(csv|xlsx|xls)$/i, '');
        a.href = url;
        a.download = `${originalName}_with_distances.csv`;

        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    /**
     * Reset the form to initial state
     */
    function resetForm() {
        selectedFile = null;
        resultsCsv = null;
        fileInput.value = '';

        fileInfo.classList.add('hidden');
        dropZone.style.display = 'block';

        errorSection.classList.add('hidden');
        resultsSection.classList.add('hidden');
        progressSection.classList.add('hidden');
        mainForm.classList.remove('hidden');

        validateForm();
    }
});
