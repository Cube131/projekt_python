let currentUser = null;
let authToken = null;
let ws = null;

function generateNumbersGrid() {
    const container = document.getElementById("numbers-container");
    container.innerHTML = "";
    const redNums = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36];

    for (let i = 1; i <= 36; i++) {
        const btn = document.createElement("button");
        btn.innerHTML = `<span class="num">${i}</span><span class="multiplier">x36</span>`;
        btn.className = "bet-btn num-btn " + (redNums.includes(i) ? "btn-red" : "btn-black");
        btn.onclick = () => placeBet('number', i.toString());
        container.appendChild(btn);
    }
}

function connectWebSocket() {
    ws = new WebSocket("ws://" + window.location.host + "/ws/game");

    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        
        if (data.server_time) document.getElementById("server-clock").innerText = data.server_time;

        if (data.type === "timer") {
            document.getElementById("timer").innerText = data.value;
            const statusEl = document.getElementById("status");
            
            if (data.value > 0) {
                statusEl.innerText = "OBSTAWIANIE";
                statusEl.style.color = "#2ecc71";
                document.getElementById("timer-container").style.display = "inline";
                document.getElementById("table-overlay").style.display = "none";

                if (data.value === 20 && currentUser) {
                    forceRefreshUserData();
                    clearBetsDisplay();
                }

            } else {
                statusEl.innerText = "KONIEC ZAKŁADÓW";
                statusEl.style.color = "#e74c3c";
                document.getElementById("timer-container").style.display = "none";
                document.getElementById("table-overlay").style.display = "flex";
                document.getElementById("table-overlay").innerText = "KONIEC CZASU";
                resetWheelDisplay();
            }
            
        } else if (data.type === "status" && data.value === "rolling") {
            document.getElementById("status").innerText = "LOSOWANIE...";
            document.getElementById("timer-container").style.display = "none";
            document.getElementById("table-overlay").style.display = "flex";
            document.getElementById("table-overlay").innerText = "LOSOWANIE...";
            resetWheelDisplay();

        } else if (data.type === "result") {
            document.getElementById("status").innerText = "WYNIK: " + data.number;
            document.getElementById("status").style.color = "#f1c40f";
            document.getElementById("timer-container").style.display = "none";
            updateDisplay(data.number, data.color);
            renderHistory(data.history);
            
            if (currentUser && data.winners) {
                const userIdStr = String(currentUser.id);
                const hasBets = document.getElementById("active-bets-container").style.display !== "none";
                
                if (data.winners[userIdStr]) {
                    const win = data.winners[userIdStr];
                    
                    const statusEl = document.getElementById("status");
                    statusEl.innerText = `WYGRANA! +${win.toFixed(2)} PLN | Wynik: ${data.number}`;
                    statusEl.style.color = "#2ecc71";
                    
                    setTimeout(() => forceRefreshUserData(), 500);
                } else if (hasBets) {
                    const statusEl = document.getElementById("status");
                    statusEl.innerText = `Przegrana | Wynik: ${data.number}`;
                    statusEl.style.color = "#e74c3c";
                }
            }
            document.getElementById("bet-message").innerText = "";

        } else if (data.type === "init") {
            renderHistory(data.history);

        } else if (data.type === "bet_confirmed") {
            currentUser.balance = data.new_balance;
            updateNavbarBalance();

            const msg = document.getElementById("bet-message");
            msg.innerText = data.message;
            setTimeout(() => msg.innerText = "", 3000);

            addBetToDisplay(data.bet_info);
            
        } else if (data.type === "error") {
            alert(data.message);
        }
    };
    
    ws.onclose = () => setTimeout(connectWebSocket, 1000);
}

function resetWheelDisplay() {
    const el = document.getElementById("last-result");
    el.innerText = "?";
    el.className = "wheel-result"; 
}

function updateDisplay(number, color) {
    const el = document.getElementById("last-result");
    el.innerText = number;
    el.className = "wheel-result " + color;
}

function renderHistory(history) {
    const container = document.getElementById("history-list");
    container.innerHTML = "";
    history.forEach(item => {
        const div = document.createElement("div");
        div.className = "history-item " + item.color;
        div.innerText = item.number;
        container.appendChild(div);
    });
}

function addBetToDisplay(info) {
    const container = document.getElementById("active-bets-container");
    container.style.display = "block";
    const list = document.getElementById("current-bets-list");
    const li = document.createElement("li");
    li.innerText = info;
    li.style.borderBottom = "1px solid rgba(255,255,255,0.1)";
    list.appendChild(li);
}

function clearBetsDisplay() {
    document.getElementById("current-bets-list").innerHTML = "";
    document.getElementById("active-bets-container").style.display = "none";
}


function placeBet(type, value) {
    if (!currentUser) return alert("Zaloguj się!");
    const amount = parseFloat(document.getElementById("betAmount").value);
    if (!amount || amount <= 0) return alert("Błędna stawka");

    ws.send(JSON.stringify({
        type: "place_bet",
        user_id: currentUser.id,
        bet_type: type,
        value: value,
        amount: amount
    }));
}

async function handleLogin() {
    const u = document.getElementById("loginUsername").value;
    const p = document.getElementById("loginPassword").value;
    try {
        const res = await fetch("/login", {
            method:"POST", 
            headers:{"Content-Type":"application/json"}, 
            body:JSON.stringify({username:u, password:p})
        });
        if(res.ok){ 
            const data = await res.json();
            currentUser = data.user;
            authToken = data.access_token;
            localStorage.setItem('authToken', authToken);
            initGameInterface(); 
        } else {
            alert("Błąd logowania");
        }
    } catch(e) { 
        console.error(e);
        alert("Błąd połączenia z serwerem");
    }
}

async function handleRegister() {
    const u = document.getElementById("regUsername").value;
    const p = document.getElementById("regPassword").value;
    try {
        const res = await fetch("/register", {
            method:"POST", 
            headers:{"Content-Type":"application/json"}, 
            body:JSON.stringify({username:u, password:p})
        });
        if(res.ok) {
            alert("Konto założone. Zaloguj się.");
        } else {
            const error = await res.json();
            alert("Błąd rejestracji: " + (error.detail || "Nieznany błąd"));
        }
    } catch(e) {
        console.error(e);
        alert("Błąd połączenia z serwerem");
    }
}

function handleLogout(){ 
    currentUser = null; 
    authToken = null;
    localStorage.removeItem('authToken');
    location.reload(); 
}

function initGameInterface() {
    document.getElementById("auth-section").style.display = "none";
    document.getElementById("game-section").style.display = "block";
    document.getElementById("navbar").style.display = "flex"; 

    document.getElementById("displayUsername").innerText = currentUser.username;
    updateNavbarBalance();
    
    if (currentUser.is_admin) {
        const adminBtn = document.getElementById("navAdminBtn");
        adminBtn.style.display = "inline-block";
        console.log("Admin zalogowany - przycisk pokazany");
    }
}

function updateNavbarBalance() {
    if(currentUser) document.getElementById("displayBalance").innerText = currentUser.balance;
}


async function forceRefreshUserData() {
    if(!authToken) return;
    try {
        const res = await fetch("/api/me", {
            method:"GET", 
            headers:{
                "Authorization": `Bearer ${authToken}`
            }
        });
        if(res.ok) {
            currentUser = await res.json();
            updateNavbarBalance();
        } else if(res.status === 401) {
            alert("Sesja wygasła. Zaloguj się ponownie.");
            handleLogout();
        }
    } catch(e) { 
        console.log("Błąd odświeżania danych:", e); 
    }
}

generateNumbersGrid();
connectWebSocket();

window.addEventListener('DOMContentLoaded', async () => {
    const savedToken = localStorage.getItem('authToken');
    if (savedToken && !currentUser) {
        authToken = savedToken;
        try {
            const res = await fetch("/api/me", {
                method: "GET",
                headers: { "Authorization": `Bearer ${authToken}` }
            });
            if (res.ok) {
                currentUser = await res.json();
                initGameInterface();
            } else {
                localStorage.removeItem('authToken');
                authToken = null;
            }
        } catch(e) {
            console.log("Błąd auto-logowania:", e);
            localStorage.removeItem('authToken');
            authToken = null;
        }
    }
});