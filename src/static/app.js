document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities", { cache: "no-store", headers: { Accept: "application/json" } });
      const activities = await response.json();

      // Clear loading message and reset activity select options
      activitiesList.innerHTML = "";
      activitySelect.innerHTML = '<option value="">-- Select an activity --</option>';

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft = details.max_participants - details.participants.length;

        // Build participants list HTML (show "No participants yet" if none)
        let participantsHtml = "";
        if (details.participants && details.participants.length) {
          participantsHtml = '<ul class="participants-list">';
          details.participants.forEach((p) => {
            // show user-friendly label (email or name)
            const label = p;
            // add a remove button with data attributes so we can handle clicks via event delegation
            participantsHtml += `<li class="participant-item" data-activity="${encodeURIComponent(name)}" data-email="${encodeURIComponent(p)}"><span class="avatar">${label.charAt(0).toUpperCase()}</span><span class="participant-label">${label}</span><button class="participant-remove" title="Remove participant">&times;</button></li>`;
          });
          participantsHtml += "</ul>";
        } else {
          participantsHtml = '<p class="muted">No participants yet — be the first!</p>';
        }

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          <div class="participants">
            <h5>Participants</h5>
            ${participantsHtml}
          </div>
        `;

        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
        const response = await fetch(
          `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
          {
            method: "POST",
            headers: { Accept: "application/json" },
          }
        );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();

        // Refresh activities so participants & availability update immediately
        await fetchActivities();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // Initialize app
  fetchActivities();

  // Event delegation for participant remove buttons
  activitiesList.addEventListener("click", async (event) => {
    const removeBtn = event.target.closest(".participant-remove");
    if (!removeBtn) return;

    // Find the parent li which contains data attributes
    const item = removeBtn.closest(".participant-item");
    if (!item) return;

    const activityName = decodeURIComponent(item.dataset.activity);
    const email = decodeURIComponent(item.dataset.email);

    if (!activityName || !email) return;

    // Confirm before removing
    const sure = window.confirm(`Unregister ${email} from ${activityName}?`);
    if (!sure) return;

    try {
      const resp = await fetch(`/activities/${encodeURIComponent(activityName)}/participants?email=${encodeURIComponent(email)}`, { method: "DELETE", headers: { Accept: "application/json" }, cache: "no-store" });
      const resJson = await resp.json();

      if (resp.ok) {
        messageDiv.textContent = resJson.message;
        messageDiv.className = "success";
        messageDiv.classList.remove("hidden");

        // refresh the list so UI updates
        await fetchActivities();
      } else {
        messageDiv.textContent = resJson.detail || "Failed to remove participant";
        messageDiv.className = "error";
        messageDiv.classList.remove("hidden");
      }

      setTimeout(() => messageDiv.classList.add("hidden"), 5000);
    } catch (err) {
      console.error("Failed to remove participant:", err);
      messageDiv.textContent = "Failed to remove participant";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      setTimeout(() => messageDiv.classList.add("hidden"), 5000);
    }
  });
});
