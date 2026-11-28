
document.addEventListener("DOMContentLoaded", () => {
    const addChannelButton = document.getElementById("add-channel-toggle");
    const closeChannelButton = document.getElementById("close-add-channel");
    const addChannelPanel = document.getElementById("add-channel");

    const searchInput = document.getElementById("channel-twitch-search");
    const searchButton = document.getElementById("channel-twitch-search-button");
    const searchResults = document.getElementById("channel-search-results");
    const selectionPreview = document.getElementById("channel-selection-preview");

    let selectedChannel = null;

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
        name.textContent = channel.display_name;

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
        addButton.disabled = true;

        actions.appendChild(addButton);

        card.append(avatarWrapper, details, actions);
        selectionPreview.appendChild(card);
    }

    // Search Twitch for channels.
    async function searchTwitchChannels() {
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

    // Search button.
    searchButton.addEventListener("click", searchTwitchChannels);

    // Allow Enter to submit a search.
    searchInput.addEventListener("keydown", event => {
        if (event.key === "Enter") {
            event.preventDefault();
            searchTwitchChannels();
        }
    });
});
