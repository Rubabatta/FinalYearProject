// LOGIN FUNCTION
async function login() {
    let username = document.getElementById("username").value.trim();
    let password = document.getElementById("password").value.trim();

    if (!username || !password) {
        showMessage("⚠️ Username aur Password dono fill karo!", "warning", "loginMsg");
        return;
    }

    try {
        let response = await fetch("http://127.0.0.1:5000/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password })
        });

        let data = await response.json();

        if (data.status === "success") {
            showMessage(`✅ Login Successful! Role: ${data.role}`, "success", "loginMsg");
        } else {
            showMessage("❌ Invalid Username or Password!", "error", "loginMsg");
        }
    } catch (err) {
        console.error(err);
        showMessage("⚠️ Server ya Network error!", "warning", "loginMsg");
    }
}

// SEND LOCATION FUNCTION
async function sendLocation() {
    if (!navigator.geolocation) {
        showMessage("⚠️ Geolocation not supported", "warning", "locationMsg");
        return;
    }

    navigator.geolocation.getCurrentPosition(async function(position) {
        let data = {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude
        };

        try {
            let response = await fetch("http://127.0.0.1:5000/update_location", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(data)
            });

            let result = await response.json();

            if (result.status === "Location Updated") {
                showMessage("✅ Location Updated Successfully", "success", "locationMsg");
            } else {
                showMessage("⚠️ Something went wrong", "error", "locationMsg");
            }

        } catch (err) {
            console.error(err);
            showMessage("⚠️ Server Error", "error", "locationMsg");
        }

    }, function() {
        showMessage("⚠️ Unable to get location", "warning", "locationMsg");
    });
}

// SHOW MESSAGE FUNCTION - stays until user clicks
function showMessage(text, type, elementId) {
    let msg = document.getElementById(elementId);
    msg.innerText = text;
    msg.className = "msg";
    msg.classList.add(type);
    msg.style.display = "block";
    msg.style.opacity = 1; // stays visible
}

// HIDE MESSAGE manually
function hideMessage(elementId) {
    let msg = document.getElementById(elementId);
    msg.style.display = "none";
}async function login() {
    let username = document.getElementById("username").value.trim();
    let password = document.getElementById("password").value.trim();
    let msg = document.getElementById("msg");

    // Simple validation
    if (!username || !password) {
        msg.innerText = "⚠️ Username aur Password dono fill karo!";
        msg.style.color = "yellow";
        return;
    }

    try {
        let response = await fetch("http://127.0.0.1:5000/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ username, password })
        });

        let data = await response.json();

        if (data.status === "success") {
            msg.innerText = `✅ Login Successful! Role: ${data.role}`;
            msg.style.color = "#22c55e";
            // Optional: redirect to dashboard or driver/index.html
            // window.location.href = "index.html";
        } else {
            msg.innerText = "❌ Invalid Username or Password!";
            msg.style.color = "red";
        }
    } catch (err) {
        msg.innerText = "⚠️ Server ya Network error!";
        msg.style.color = "orange";
        console.error(err);
    }
}