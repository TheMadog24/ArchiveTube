
document.addEventListener("DOMContentLoaded", () => {
    const addChannelButton = document.getElementById("add-channel-toggle");
    const closeChannelButton = document.getElementById("close-add-channel");
    const addChannelPanel = document.getElementById("add-channel");

    const searchInput = document.getElementById("channel-twitch-search");
    const searchButton = document.getElementById("channel-twitch-search-button");
    const clearButton = document.getElementById("channel-twitch-clear-button");
    const searchResults = document.getElementById("channel-search-results");
    const selectionPreview = document.getElementById("channel-selection-preview");
    const channelList = document.getElementById("channel-list");
    const gridViewButton = document.getElementById("channel-grid-view");
    const listViewButton = document.getElementById("channel-list-view");

    let selectedChannel = null;

    // Load channels from the ArchiveTube library.
    async function loadChannels() {
        try {
            const response = await fetch("/api/channels");
            const channels = await response.json();

            if (!response.ok) {
                throw new Error("Unable to load channels.");
            }

            renderChannels(channels);

        } catch (error) {
            console.error("Error loading channels:", error);
            channelList.textContent = "Unable to load your channel library.";
        }
    }

    // Change the Channel Library layout.
    function setChannelView(view) {
        channelList.classList.remove(
            "channel-library-grid",
            "channel-library-list"
        );

        channelList.classList.add(`channel-library-${view}`);

        gridViewButton.classList.toggle("active", view === "grid");
        listViewButton.classList.toggle("active", view === "list");

        localStorage.setItem("channelLibraryView", view);
    }

    // Display channels in the Channel Library.
    function renderChannels(channels) {
        channelList.replaceChildren();

        if (channels.length === 0) {
            const emptyState = document.createElement("div");
            emptyState.className = "empty-state";

            const title = document.createElement("p");
            title.textContent = "Your channel library is empty.";

            const description = document.createElement("p");
            description.textContent =
                "Add a Twitch channel or archive content from a channel to get started.";

            emptyState.append(title, description);
            channelList.appendChild(emptyState);

            return;
        }

        channels.forEach(channel => {
            const card = document.createElement("div");
            card.className = "channel-library-card";

            // Channel avatar.
            const avatar = document.createElement("img");
            avatar.src = channel.profile_image_url || "";
            avatar.alt = "";
            avatar.className = "channel-library-avatar";
            const avatarLink = document.createElement("a");
            avatarLink.href = `/channels/${channel.id}`;
            avatarLink.appendChild(avatar);

            // Channel information.
            const info = document.createElement("div");
            info.className = "channel-library-info";

            // Channel details.
            const details = document.createElement("div");
            details.className = "channel-library-details";

            const name = document.createElement("h3");

            const nameLink = document.createElement("a");
            nameLink.href = `/channels/${channel.id}`;
            nameLink.textContent = channel.display_name;

            name.appendChild(nameLink);

            const username = document.createElement("p");
            username.textContent = `@${channel.username}`;

            const tracking = document.createElement("div");
            tracking.className = "tracker-status channel-tracking-status";

            const statusIndicator = document.createElement("span");
            statusIndicator.className = "status-indicator";

            const trackingLabel = document.createElement("strong");
            trackingLabel.textContent = channel.tracking_enabled
                ? "Tracking"
                : "Not Tracking";

            if (channel.tracking_enabled) {
                tracking.classList.add("is-tracking");
            }

            tracking.append(statusIndicator, trackingLabel);

            details.append(name, username);

            // Channel actions.
            const actions = document.createElement("div");
            actions.className = "channel-library-actions";

            const editButton = document.createElement("a");
            editButton.className = "control-button secondary";
            editButton.href = `/channels/${channel.id}/manage`;
            editButton.textContent = "Edit";

            const removeButton = document.createElement("button");
            removeButton.type = "button";
            removeButton.className = "control-button secondary";
            removeButton.textContent = "Remove";

            removeButton.addEventListener("click", async () => {
                const confirmed = confirm(
                    `Are you sure you want to remove ${channel.display_name} from your library?`
                );

                if (!confirmed) {
                    return;
                }

                try {
                    const response = await fetch(`/api/channels/${channel.id}`, {
                        method: "DELETE",
                    });

                    const result = await response.json();

                    if (!response.ok) {
                        alert(result.error || "Unable to remove channel.");
                        return;
                    }

                    await loadChannels();

                } catch (error) {
                    console.error("Error removing channel:", error);
                    alert("Unable to connect to ArchiveTube.");
                }
            });

            actions.append(editButton, removeButton);

            info.append(avatarLink, details, tracking);
            card.append(info, actions);
            channelList.appendChild(card);
        });
    }

    // Clear the current search and selected channel.
    function clearChannelSearch() {
        selectedChannel = null;
        searchInput.value = "";
        searchResults.replaceChildren();
        selectionPreview.replaceChildren();
    }

    if (!addChannelButton || !addChannelPanel) {
        return;
    }

    // Open the Add Channel modal.
    addChannelButton.addEventListener("click", () => {
        addChannelPanel.hidden = false;
    });

    // Close the Add Channel modal.
    if (closeChannelButton) {
        closeChannelButton.addEventListener("click", () => {
            addChannelPanel.hidden = true;
            clearChannelSearch();
        });
    }

    // Display a preview of the selected Twitch channel.
    function showChannelPreview(channel) {
        selectionPreview.replaceChildren();

        const card = document.createElement("div");
        card.className = "channel-selection-card";

        // Channel avatar.
        const avatarWrapper = document.createElement("div");
        avatarWrapper.className = "channel-result-avatar-wrapper";

        const avatar = document.createElement("img");
        avatar.src = channel.thumbnail_url;
        avatar.alt = "";
        avatar.className = "channel-selection-avatar";
        const avatarLink = document.createElement("a");
        avatarLink.href = `/channels/${channel.id}`;
        avatarLink.appendChild(avatar);

        avatarWrapper.appendChild(avatar);

        if (channel.is_live) {
            const liveBadge = document.createElement("span");
            liveBadge.className = "channel-result-live-badge";
            liveBadge.textContent = "LIVE";

            avatarWrapper.appendChild(liveBadge);
        }

        // Channel details.
        const details = document.createElement("div");
        details.className = "channel-selection-details";

        const name = document.createElement("h3");

        const nameLink = document.createElement("a");
        nameLink.href = `/channels/${channel.id}`;
        nameLink.textContent = channel.display_name;

        name.appendChild(nameLink);

        const username = document.createElement("p");
        username.textContent = `@${channel.broadcaster_login}`;

        details.append(name, username);

        if (!channel.is_live) {
            const status = document.createElement("p");
            status.textContent = "Offline";
            details.appendChild(status);
        }

        // Add button.
        const actions = document.createElement("div");
        actions.className = "channel-selection-actions";

        const addButton = document.createElement("button");
        addButton.type = "button";
        addButton.className = "control-button primary";
        addButton.textContent = "Add to Library";

        addButton.addEventListener("click", async () => {
            if (!selectedChannel) {
                return;
            }

            try {
                const response = await fetch("/api/channels", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify(selectedChannel),
                });

                const result = await response.json();

                if (!response.ok) {
                    alert(result.error || "Unable to add channel.");
                    return;
                }

                alert(result.message);

            } catch (error) {
                console.error("Error adding channel:", error);
                alert("Unable to connect to ArchiveTube.");
            }
        });

        actions.appendChild(addButton);

        card.append(avatarWrapper, details, actions);
        selectionPreview.appendChild(card);
    }

    // Search Twitch for channels.
    async function searchTwitchChannels() {
        selectedChannel = null;
        selectionPreview.replaceChildren();

        const query = searchInput.value.trim();

        if (!query) {
            searchResults.textContent = "Please enter a channel name.";
            return;
        }

        searchButton.disabled = true;
        searchResults.textContent = "Searching Twitch...";

        try {
            const response = await fetch(
                `/api/channels/search?q=${encodeURIComponent(query)}`
            );

            const channels = await response.json();

            if (!response.ok) {
                throw new Error(channels.error || "Twitch search failed.");
            }

            if (channels.length === 0) {
                searchResults.textContent = "No channels found.";
                return;
            }

            searchResults.replaceChildren();

            channels.forEach(channel => {
                const result = document.createElement("button");
                result.type = "button";
                result.className = "channel-search-result";

                result.addEventListener("click", () => {
                    selectedChannel = channel;
                    showChannelPreview(channel);
                });

                const avatar = document.createElement("img");
                avatar.src = channel.thumbnail_url;
                avatar.alt = "";
                avatar.className = "channel-result-avatar";

                const details = document.createElement("div");
                details.className = "channel-result-details";

                const name = document.createElement("strong");
                name.textContent = channel.display_name;

                const username = document.createElement("span");
                username.textContent = `@${channel.broadcaster_login}`;

                const status = document.createElement("span");
                status.className = channel.is_live
                    ? "channel-result-live"
                    : "channel-result-offline";
                status.textContent = channel.is_live ? "Live" : "Offline";

                details.append(name, username, status);
                const avatarWrapper = document.createElement("div");
                avatarWrapper.className = "channel-result-avatar-wrapper";

                avatarWrapper.appendChild(avatar);

                if (channel.is_live) {
                    const liveBadge = document.createElement("span");
                    liveBadge.className = "channel-result-live-badge";
                    liveBadge.textContent = "LIVE";

                    avatarWrapper.appendChild(liveBadge);
                }

                result.append(avatarWrapper, details);

                searchResults.appendChild(result);
            });

        } catch (error) {
            searchResults.textContent = error.message;
        } finally {
            searchButton.disabled = false;
        }
    }

    // Clear search and selection.
    clearButton.addEventListener("click", clearChannelSearch);

    // Search button.
    searchButton.addEventListener("click", searchTwitchChannels);

    // Allow Enter to submit a search.
    searchInput.addEventListener("keydown", event => {
        if (event.key === "Enter") {
            event.preventDefault();
            searchTwitchChannels();
        }
    });
    // Restore the previously selected Channel Library view.
    const savedView = localStorage.getItem("channelLibraryView");

    if (savedView === "grid" || savedView === "list") {
        setChannelView(savedView);
    }
    // Load the Channel Library when the page opens.
    loadChannels();
    // Channel Library view controls.
    gridViewButton.addEventListener("click", () => {
        setChannelView("grid");
    });

    listViewButton.addEventListener("click", () => {
        setChannelView("list");
    });
});

